"""Service for parallel expert queries."""

import asyncio
import logging
from typing import Dict, List, Any

import httpx

from lib.experts import get_expert
from lib.engine.execution import checkpoint, current_execution, dispatched_question

logger = logging.getLogger(__name__)


async def query_single_expert(role: str, query: str) -> Dict[str, Any]:
    """
    Query a single expert.

    Args:
        role: The expert role key
        query: The user's query

    Returns:
        Dict with role, label, and response or error
    """
    expert = get_expert(role)
    execution = current_execution.get()
    if execution:
        from .roundtable_state import CapturedExpert

        snapshots = (execution.state.get("advisor_context") or {}).get("advisors", [])
        captured = next((item for item in snapshots if item["role"] == role), None)
        if captured:
            expert = CapturedExpert(captured)
    if not expert:
        return {
            "role": role,
            "label": role,
            "error": f"Unknown expert role: {role}",
        }

    try:
        response = await expert.query(dispatched_question(query))
        if not isinstance(response, str) or not response.strip():
            raise ValueError("Provider returned no usable text")
        from .consensus_contracts import validate_text_citations

        validate_text_citations(response)
        logger.info(f"Expert {role} responded successfully")
        return {
            "role": role,
            "label": expert.label,
            "response": response,
        }
    except (httpx.HTTPError, ValueError) as e:
        from .roundtable_state import failure_details

        failure = failure_details(e)
        logger.error("Advisor %s failed (%s)", role, type(e).__name__)
        return {
            "role": role,
            "label": expert.label,
            "error": failure["message"],
            "failure": failure,
        }
    except Exception as e:
        logger.error("Unexpected advisor failure for %s (%s)", role, type(e).__name__)
        raise


async def query_experts(query: str, roles: List[str]) -> Dict[str, Any]:
    """
    Query multiple experts in parallel.

    Args:
        query: The user's query
        roles: List of expert role keys to query

    Returns:
        Dict with query and responses from all experts
    """
    if not roles:
        return {"query": query, "responses": []}

    # Create tasks for parallel execution
    execution = current_execution.get()
    previous = (
        {item.get("role"): item for item in execution.state.get("responses", [])}
        if execution
        else {}
    )
    completed: dict[str, Any] = {
        role: item
        for role, item in previous.items()
        if item.get("response") and not item.get("error")
    }

    async def one(role: str) -> Dict[str, Any]:
        if role in completed:
            return completed[role]
        result = await query_single_expert(role, query)
        completed[role] = result
        retry_at = max(
            (item.get("failure", {}).get("retry_at", 0) for item in completed.values()),
            default=0,
        )
        await checkpoint(
            {
                "responses": [completed[r] for r in roles if r in completed],
                "retry_at": retry_at,
            }
        )
        return result

    tasks = [one(role) for role in roles]

    # Execute all queries in parallel
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    normalized: List[Dict[str, Any]] = []
    for role, response in zip(roles, responses):
        if isinstance(response, BaseException):
            logger.error(
                "Unexpected error querying expert %s",
                role,
            )
            normalized.append(
                {
                    "role": role,
                    "label": role,
                    "error": "Unexpected error querying expert. Check logs.",
                }
            )
        elif isinstance(response, dict):
            normalized.append(response)

    return {
        "query": query,
        "responses": normalized,
    }
