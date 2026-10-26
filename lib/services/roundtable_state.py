"""Framework-independent roundtable recovery state and provider failure details."""

import copy
import math
import time
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from lib.engine.llm_client import provider_error_metadata
from lib.experts import get_expert
from lib.experts.base import Expert
from lib.experts.catalog import validate_advisor_context
from lib.engine.execution import RunStopped
from lib.contracts import MAX_QUESTION, MAX_TEXT


def failure_details(error: Exception) -> dict[str, Any]:
    """Retain retry guidance without displaying provider URLs or raw tracebacks."""
    if isinstance(error, RunStopped):
        return {"kind": "paused", "message": str(error)}
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status == 429:
            now = time.time()
            retry_at = now + 60
            header = error.response.headers.get("Retry-After", "")
            try:
                delay = float(header)
                if math.isfinite(delay) and delay >= 0:
                    retry_at = now + delay
            except ValueError:
                try:
                    date = parsedate_to_datetime(header)
                    retry_at = max(
                        now,
                        date.replace(tzinfo=date.tzinfo or timezone.utc).timestamp(),
                    )
                except (ValueError, TypeError, OverflowError):
                    pass
            metadata = provider_error_metadata(error.response)
            source = metadata.get("limit_source")
            message = "The provider rate-limited this request. Your completed answers are kept."
            if source == "upstream_provider_shared_pool":
                provider = metadata.get("provider_name", "")
                label = (
                    provider
                    if isinstance(provider, str)
                    and provider.isalnum()
                    and len(provider) <= 64
                    else "The model provider"
                )
                message = (
                    f"{label}'s shared capacity is temporarily exhausted. "
                    "Retry synthesis later; your completed advisor answers are kept. "
                    "The retry timer is a minimum wait, not a confirmed recovery time."
                )
            elif source == "openrouter_in_flight_budget":
                message = (
                    "OpenRouter's in-flight spending budget is temporarily full. "
                    "Wait for other requests to finish, then retry. Your completed answers are kept."
                )
            return {
                "kind": "rate_limit",
                "message": message,
                "status_code": status,
                "retry_at": retry_at,
            }
        return {
            "kind": "provider",
            "message": f"The provider could not complete this request (HTTP {status}).",
            "status_code": status,
        }
    if isinstance(error, httpx.RequestError):
        return {
            "kind": "connection",
            "message": "The provider connection failed. Your completed answers are kept.",
        }
    return {
        "kind": "response",
        "message": "This response could not be completed. Your completed answers are kept.",
    }


def successful_entries(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in transcript
        if entry.get("status") == "success"
        or ("status" not in entry and not entry.get("text", "").startswith("Error:"))
    ]


def normalize_roundtable_state(value: Any) -> dict[str, Any]:
    """Validate submitted retry state and upgrade legacy transcript error strings."""
    if not isinstance(value, dict):
        raise ValueError("Roundtable data must be an object.")
    state = copy.deepcopy(value)
    query, roles, rounds = (
        state.get("query"),
        state.get("roles", state.get("experts")),
        state.get("rounds"),
    )
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUESTION:
        raise ValueError("The original roundtable question is missing.")
    if (
        not isinstance(roles, list)
        or not 2 <= len(roles) <= 10
        or not all(isinstance(role, str) for role in roles)
        or len(set(roles)) != len(roles)
    ):
        raise ValueError("The roundtable needs distinct advisor roles.")
    if type(rounds) is not int or not 1 <= rounds <= 5:
        raise ValueError("The original round count must be between 1 and 5.")
    context = state.get("advisor_context")
    if context is not None:
        context = validate_advisor_context(context, roles)
        state["advisor_context"] = context
        labels = {item["role"]: item["label"] for item in context["advisors"]}
    else:
        labels = {}
        for role in roles:
            expert = get_expert(role)
            if expert is None:
                raise ValueError(
                    "An advisor definition is unavailable for this older result."
                )
            labels[role] = expert.label
    entries = state.get("transcript", [])
    if not isinstance(entries, list) or len(entries) > rounds * len(roles):
        raise ValueError("Invalid roundtable transcript.")
    transcript = []
    for index in range(rounds * len(roles)):
        role, round_num = roles[index % len(roles)], index // len(roles) + 1
        if index >= len(entries):
            entry = {"speaker": labels[role], "text": "", "status": "pending"}
        else:
            entry = entries[index]
        if (
            not isinstance(entry, dict)
            or entry.get("role", role) != role
            or type(entry.get("round", round_num)) is not int
            or entry.get("round", round_num) != round_num
            or not isinstance(entry.get("text"), str)
            or len(entry.get("text", "")) > MAX_TEXT
        ):
            raise ValueError(
                "Transcript entries must match the original advisor and round order."
            )
        entry["role"], entry["round"] = role, round_num
        entry.setdefault("speaker", labels[role])
        entry.setdefault(
            "status", "failed" if entry["text"].startswith("Error:") else "success"
        )
        if entry["status"] not in ("success", "failed", "pending") or (
            entry["status"] == "success" and not entry["text"].strip()
        ):
            raise ValueError("Invalid contribution status.")
        if entry["status"] == "failed" and not isinstance(entry.get("failure"), dict):
            entry["failure"] = {
                "kind": "legacy",
                "message": "This advisor response failed. Retry will keep the other answers.",
            }
        transcript.append(entry)
    state.update(query=query, roles=roles, rounds=rounds, transcript=transcript)
    if "synthesis_model" in state and (
        not isinstance(state["synthesis_model"], str)
        or len(state["synthesis_model"]) > 200
    ):
        raise ValueError("Invalid synthesis model label.")
    answer = state.get("final_answer", "")
    if not isinstance(answer, str):
        raise ValueError("Invalid synthesis text.")
    if answer.startswith("Error generating consensus:"):
        state["final_answer"] = ""
        state["consensus_brief"] = None
        state["synthesis_error"] = {
            "kind": "legacy",
            "message": "The synthesis failed. Your advisor answers are kept.",
        }
    else:
        state["final_answer"] = answer
    state.setdefault("synthesis_error", None)
    if state["synthesis_error"] is not None and (
        not isinstance(state["synthesis_error"], dict)
        or not isinstance(state["synthesis_error"].get("message"), str)
    ):
        raise ValueError("Invalid synthesis failure details.")
    if state.get("consensus_brief") is not None and not isinstance(
        state["consensus_brief"], dict
    ):
        raise ValueError("Invalid structured synthesis.")
    if "compact_ending" in state and type(state["compact_ending"]) is not bool:
        raise ValueError("Invalid closing format.")
    if not answer and not state["synthesis_error"]:
        state["synthesis_error"] = {
            "kind": "waiting",
            "message": "The synthesis has not completed yet.",
        }
    retry_at = state.get("retry_at", 0)
    if (
        type(retry_at) not in (int, float)
        or not math.isfinite(retry_at)
        or retry_at < 0
    ):
        raise ValueError("Invalid retry time.")
    state["retry_at"] = retry_at
    return state


def roundtable_view(state: dict[str, Any]) -> dict[str, Any]:
    """Add display metadata and a retry payload; legacy results remain readable."""
    try:
        state = normalize_roundtable_state(state)
    except ValueError:
        return {**state, "can_retry": False}
    missing = sum(entry["status"] != "success" for entry in state["transcript"])
    return {
        **state,
        "retry_state": state,
        "missing_responses": missing,
        "completed_responses": len(state["transcript"]) - missing,
        "retry_wait": max(0, math.ceil(state["retry_at"] - time.time())),
        "can_retry": bool(
            missing or state.get("synthesis_error") or state.get("synthesis_stale")
        ),
    }


class CapturedExpert(Expert):
    """Retry with the original captured instructions, even after a catalog edit."""

    def __init__(self, snapshot: dict[str, str]) -> None:
        self.snapshot = snapshot

    @property
    def role(self) -> str:
        return self.snapshot["role"]

    @property
    def label(self) -> str:
        return self.snapshot["label"]

    @property
    def system_prompt(self) -> str:
        return self.snapshot["system_prompt"]
