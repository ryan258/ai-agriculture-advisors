"""Durable, bounded work in one local process; polling never dispatches a model."""

from __future__ import annotations

import asyncio
import copy
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from lib.contracts import (
    MAX_QUESTION,
    fingerprint,
    prepare_input,
    sources,
    task_brief,
    text,
)
from lib.engine.config import get_settings
from lib.engine.execution import Execution, RunStopped, current_execution
from lib.storage.workspace_store import WorkspaceStore


class RunManager:
    def __init__(self, workspace: WorkspaceStore) -> None:
        self.workspace = workspace
        self.tasks: dict[str, asyncio.Task[Any]] = {}
        self.executions: dict[str, Execution] = {}
        self.pause_pending: set[str] = set()

    async def create(
        self,
        state: dict[str, Any],
        executor: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        *,
        key: str = "",
        background: bool = True,
        acknowledge: bool = False,
    ) -> dict[str, Any]:
        settings = get_settings()
        if state.get("retry_at", 0) > time.time():
            raise ValueError("The provider's minimum retry wait has not elapsed.")
        uncertain = [
            item
            for item in state.get("execution_receipts", [])
            if item.get("status") in ("in_flight", "transport_uncertain")
        ]
        if uncertain and not acknowledge:
            raise ValueError(
                "Acknowledge that an interrupted call may have completed remotely before retrying this saved state."
            )
        for receipt in uncertain:
            receipt["status"] = "ambiguous_acknowledged"
        roles = state.get("roles", [])
        rounds = state.get("rounds", 1) if state["result_type"] == "roundtable" else 1
        reserved = 2 if state["result_type"] == "roundtable" else 0
        if state["result_type"] == "roundtable":
            completed = sum(
                item.get(
                    "status",
                    (
                        "failed"
                        if item.get("text", "").startswith("Error:")
                        else "success"
                    ),
                )
                == "success"
                for item in state.get("transcript", [])
            )
            planned = len(roles) * rounds - completed + 1
        else:
            completed = sum(
                bool(item.get("response")) and not item.get("error")
                for item in state.get("responses", [])
            )
            planned = len(roles) - completed
        if not roles or len(roles) > 10 or planned + reserved > settings.max_run_calls:
            raise ValueError(
                f"This plan needs {planned} calls before fallback. Choose fewer advisors/rounds (installation limit {settings.max_run_calls}, including fallback)."
            )
        text(state.get("query"), "Question", MAX_QUESTION, blank=False)
        state["sources"] = sources(state.get("sources", []))
        state["task_brief"] = task_brief(state.get("task_brief", {}))
        if state.get("advisor_context") is None:
            from lib.experts.registry import expert_registry

            if any(role not in expert_registry for role in roles):
                raise ValueError(
                    "A current advisor definition is unavailable for this legacy result. Its saved text remains readable."
                )
            state["advisor_context"] = {
                "panel": {
                    "id": "legacy-current",
                    "label": "Current definitions for a legacy result",
                },
                "advisors": [expert_registry[role].snapshot() for role in roles],
            }
        state["provider_question"] = prepare_input(
            state["query"], state["task_brief"], state["sources"]
        )
        state["advisor_model"] = state.get("advisor_model") or settings.openrouter_model
        state["synthesis_model"] = (
            state.get("synthesis_model")
            or settings.openrouter_synthesis_model
            or state["advisor_model"]
        )
        state["input_sha256"] = fingerprint(
            {
                "query": state["query"],
                "task_brief": state["task_brief"],
                "sources": state["sources"],
            }
        )
        if len(key) > 200:
            raise ValueError("Invalid submission key")
        run_id = (
            fingerprint({"submission": key, "input": state})
            if key
            else uuid.uuid4().hex
        )
        state.update(run_id=run_id, planned_calls=planned)
        record = {
            "id": run_id,
            "status": "queued",
            "attempts": 0,
            "state": state,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        created = await asyncio.to_thread(
            self.workspace.put, "run", run_id, record, create=True
        )
        if not created:
            return await self.get(run_id)
        if background:
            self.tasks[run_id] = asyncio.create_task(self._execute(record, executor))
            return record
        await self._execute(record, executor)
        return await self.get(run_id)

    async def _execute(
        self,
        record: dict[str, Any],
        executor: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        settings = get_settings()
        run_id, state = record["id"], record["state"]
        record.update(status="running", attempts=record["attempts"] + 1, error="")

        async def persist(updated: dict[str, Any]) -> None:
            record["state"] = copy.deepcopy(updated)
            await asyncio.to_thread(self.workspace.put, "run", run_id, record)

        execution = Execution(
            state=copy.deepcopy(state),
            persist=persist,
            max_calls=settings.max_run_calls,
            timeout=settings.max_run_seconds,
            advisor_model=state.get("advisor_model") or settings.openrouter_model,
            synthesis_model=state.get("synthesis_model")
            or settings.openrouter_synthesis_model
            or settings.openrouter_model,
            receipts=copy.deepcopy(state.get("execution_receipts", [])),
        )
        execution.paused = run_id in self.pause_pending
        self.executions[run_id] = execution
        token = current_execution.set(execution)
        try:
            await execution.checkpoint()
            async with asyncio.timeout(settings.max_run_seconds):
                result = await executor(copy.deepcopy(state))
            execution.state.update(result)
            failures = (
                result.get("synthesis_error")
                or any(item.get("error") for item in result.get("responses", []))
                or any(
                    item.get("status", "success") != "success"
                    for item in result.get("transcript", [])
                )
            )
            record["status"] = (
                "paused"
                if execution.paused
                else ("partial" if failures else "complete")
            )
        except (RunStopped, TimeoutError):
            record.update(
                status="paused",
                error="The attempt paused or reached its deadline. Review the checkpoint before resuming.",
            )
        except asyncio.CancelledError:
            record.update(
                status="interrupted",
                error="The application stopped. Check any in-flight receipt before a deliberate retry.",
            )
            raise
        except Exception as error:
            record.update(
                status="partial",
                error=f"The attempt could not finish ({type(error).__name__}). Completed checkpoints are retained.",
            )
        finally:
            try:
                await execution.checkpoint()
            finally:
                current_execution.reset(token)
                self.executions.pop(run_id, None)
                self.tasks.pop(run_id, None)
                self.pause_pending.discard(run_id)

    async def get(self, run_id: str) -> dict[str, Any]:
        record = await asyncio.to_thread(self.workspace.get, "run", run_id)
        if record is None:
            raise ValueError("Working run not found.")
        if (
            record["status"] in ("queued", "running")
            and run_id not in self.tasks
            and run_id not in self.executions
        ):
            record.update(
                status="interrupted",
                error="The previous process stopped. Resume is manual; an in-flight provider request may have completed remotely.",
            )
        record["ambiguous"] = any(
            item.get("status") in ("in_flight", "transport_uncertain")
            for item in record["state"].get("execution_receipts", [])
        )
        record["retry_wait"] = max(
            0, math.ceil(record["state"].get("retry_at", 0) - time.time())
        )
        return record

    async def recent(self) -> list[dict[str, Any]]:
        rows = await asyncio.to_thread(self.workspace.list, "run", 20)
        return [await self.get(row["id"]) for row in rows]

    async def resume(
        self,
        run_id: str,
        executor: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        *,
        acknowledge: bool = False,
    ) -> dict[str, Any]:
        record = await self.get(run_id)
        if run_id in self.tasks or run_id in self.executions:
            return record
        if record["status"] == "complete":
            return record
        if record["attempts"] >= get_settings().max_run_attempts:
            raise ValueError(
                "This run reached its attempt limit. Save it and make a smaller follow-up."
            )
        if (
            len(record["state"].get("execution_receipts", []))
            >= get_settings().max_run_calls
        ):
            raise ValueError(
                "This run reached its call limit. Save it and prepare a smaller linked follow-up."
            )
        if record["state"].get("retry_at", 0) > time.time():
            raise ValueError("The provider's minimum retry wait has not elapsed.")
        if record["ambiguous"] and not acknowledge:
            raise ValueError(
                "An earlier call may have completed remotely. Acknowledge possible duplicate provider work before retrying."
            )
        if record["ambiguous"]:
            for receipt in record["state"].get("execution_receipts", []):
                if receipt.get("status") in ("in_flight", "transport_uncertain"):
                    receipt["status"] = "ambiguous_acknowledged"
        record["status"] = "queued"
        await asyncio.to_thread(self.workspace.put, "run", run_id, record)
        self.tasks[run_id] = asyncio.create_task(self._execute(record, executor))
        return record

    def pause(self, run_id: str) -> None:
        self.pause_pending.add(run_id)
        execution = self.executions.get(run_id)
        if execution:
            execution.paused = True

    async def close(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
