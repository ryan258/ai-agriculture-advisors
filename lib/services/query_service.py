"""Service for parallel expert queries."""

import asyncio
import logging
from typing import Dict, List, Any

import httpx

from lib.experts import get_expert

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
    if not expert:
        return {
            "role": role,
            "label": role,
            "error": f"Unknown expert role: {role}",
        }

    try:
        response = await expert.query(query)
        logger.info(f"Expert {role} responded successfully")
        return {
            "role": role,
            "label": expert.label,
            "response": response,
        }
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error querying expert {role}: {e}")
        return {
            "role": role,
            "label": expert.label,
            "error": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error querying expert {role}: {e}")
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
    tasks = [query_single_expert(role, query) for role in roles]

    # Execute all queries in parallel
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    normalized: List[Dict[str, Any]] = []
    for role, response in zip(roles, responses):
        if isinstance(response, BaseException):
            logger.error(
                "Unexpected error querying expert %s",
                role,
                exc_info=(type(response), response, response.__traceback__),
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
