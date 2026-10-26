"""Deliberate dispatch bounds and private execution receipts for a local run."""

from __future__ import annotations

import asyncio
import copy
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


class RunStopped(ValueError):
    """No more calls may be scheduled in this attempt."""


@dataclass
class Execution:
    state: dict[str, Any]
    persist: Callable[[dict[str, Any]], Awaitable[None]]
    max_calls: int = 32
    timeout: int = 600
    advisor_model: str = ""
    synthesis_model: str = ""
    paused: bool = False
    receipts: list[dict[str, Any]] = field(default_factory=list)
    started: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def before_call(self) -> None:
        if self.paused:
            raise RunStopped(
                "Paused. Completed work is checkpointed; choose Resume when ready."
            )
        if time.monotonic() - self.started >= self.timeout:
            raise RunStopped("Run deadline reached. Completed work is checkpointed.")
        if len(self.receipts) >= self.max_calls:
            raise RunStopped(
                "This run reached its call limit. Start a smaller follow-up if needed."
            )

    async def checkpoint(self, state: dict[str, Any] | None = None) -> None:
        async with self.lock:
            if state is not None:
                self.state.update(copy.deepcopy(state))
            self.state["execution_receipts"] = copy.deepcopy(self.receipts)
            await self.persist(copy.deepcopy(self.state))


current_execution: ContextVar[Execution | None] = ContextVar(
    "advisor_execution", default=None
)


async def checkpoint(state: dict[str, Any]) -> None:
    execution = current_execution.get()
    if execution is not None:
        await execution.checkpoint(state)


def dispatched_question(question: str) -> str:
    execution = current_execution.get()
    return (
        str(execution.state.get("provider_question", question))
        if execution
        else question
    )
