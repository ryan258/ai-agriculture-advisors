"""Service for multi-round expert discussions."""

import logging
from typing import Dict, List, Any

import httpx

from lib.experts import get_expert
from lib.engine.llm_client import get_llm_client

logger = logging.getLogger(__name__)


async def run_roundtable(
    query: str,
    roles: List[str],
    rounds: int = 3,
) -> Dict[str, Any]:
    """
    Run a multi-round roundtable discussion among experts.

    Args:
        query: The user's query
        roles: List of expert role keys to participate
        rounds: Number of discussion rounds (default: 3)

    Returns:
        Dict with transcript and final consensus answer
    """
    if len(roles) < 2:
        return {
            "error": "At least 2 experts required for roundtable discussion",
            "transcript": [],
            "final_answer": "",
        }

    transcript: List[Dict[str, str]] = []

    # Run discussion rounds
    for round_num in range(1, rounds + 1):
        for role in roles:
            expert = get_expert(role)
            if not expert:
                transcript.append(
                    {
                        "speaker": role,
                        "text": f"Error: Unknown expert role '{role}'",
                        "round": round_num,
                    }
                )
                continue

            # Build transcript text for context
            transcript_text = "\n".join(
                f"{entry['speaker']}: {entry['text']}" for entry in transcript
            )

            try:
                response = await expert.contribute_to_discussion(
                    query=query,
                    transcript=transcript_text,
                    round_num=round_num,
                )
                transcript.append(
                    {
                        "speaker": expert.label,
                        "text": response,
                        "round": round_num,
                    }
                )
                logger.info(
                    f"Roundtable: {expert.label} contributed in round {round_num}"
                )
            except (httpx.HTTPError, ValueError) as e:
                logger.error(f"Error in roundtable from {role}: {e}")
                transcript.append(
                    {
                        "speaker": expert.label,
                        "text": f"Error: {str(e)}",
                        "round": round_num,
                    }
                )
            except Exception as e:
                logger.exception(f"Unexpected error in roundtable from {role}: {e}")
                raise

    # Generate final consensus
    final_answer = await _generate_consensus(query, transcript)

    return {
        "query": query,
        "roles": roles,
        "rounds": rounds,
        "transcript": transcript,
        "final_answer": final_answer,
    }


async def _generate_consensus(
    query: str,
    transcript: List[Dict[str, str]],
) -> str:
    """
    Generate a consensus summary from the discussion.

    Args:
        query: The original user query
        transcript: The discussion transcript

    Returns:
        The consensus/summary response
    """
    transcript_text = "\n".join(
        f"{entry['speaker']}: {entry['text']}" for entry in transcript
    )

    moderator_prompt = """You are a moderator synthesizing a roundtable discussion among agricultural experts. Your role is to:
1. Identify key points of agreement
2. Note any important differences in perspective
3. Provide actionable conclusions

Be concise but comprehensive."""

    summary_prompt = f"""Based on the following expert discussion, provide a consensus answer to the original query.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Provide a clear, actionable consensus that synthesizes the experts' insights."""

    try:
        response = await get_llm_client().generate(summary_prompt, moderator_prompt)
        return response.strip()
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error generating consensus: {e}")
        return f"Error generating consensus: {str(e)}"
