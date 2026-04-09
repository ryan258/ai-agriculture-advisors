"""Service for multi-round expert discussions."""

import logging
from typing import Any, Dict, List

import httpx

from lib.experts import get_expert
from lib.engine.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# Immutable JSON schema for structured consensus generation. Do not mutate at runtime.
_ROUND_TABLE_CONSENSUS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "governing_insight",
        "executive_summary",
        "key_findings",
        "decision_implications",
        "recommendations",
        "limitations",
    ],
    "properties": {
        "governing_insight": {"type": "string"},
        "executive_summary": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 4,
        },
        "key_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "claim", "evidence_points", "implication"],
                "properties": {
                    "title": {"type": "string"},
                    "claim": {"type": "string"},
                    "evidence_points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "implication": {"type": "string"},
                },
            },
        },
        "decision_implications": {
            "type": "array",
            "items": {"type": "string"},
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["owner", "action", "expected_impact", "key_risk"],
                "properties": {
                    "owner": {"type": "string"},
                    "action": {"type": "string"},
                    "expected_impact": {"type": "string"},
                    "key_risk": {"type": "string"},
                },
            },
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


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
            except Exception as e:
                logger.error(f"Error in roundtable from {role}: {e}")
                transcript.append(
                    {
                        "speaker": expert.label,
                        "text": f"Error: {str(e)}",
                        "round": round_num,
                    }
                )

    # Generate final consensus
    final_answer, consensus_brief = await _generate_consensus(query, transcript)

    return {
        "query": query,
        "roles": roles,
        "rounds": rounds,
        "transcript": transcript,
        "final_answer": final_answer,
        "consensus_brief": consensus_brief,
    }


async def _generate_consensus(
    query: str,
    transcript: List[Dict[str, str]],
) -> tuple[str, dict[str, Any] | None]:
    """
    Generate a consensus summary from the discussion.

    Args:
        query: The original user query
        transcript: The discussion transcript

    Returns:
        Rendered markdown summary plus structured consensus payload when available
    """
    transcript_text = "\n".join(
        f"{entry['speaker']}: {entry['text']}" for entry in transcript
    )

    moderator_prompt = """You are a moderator synthesizing a roundtable discussion among agricultural experts.
Return a structured consensus object that a reporting system can render directly.
Keep every field concise, decision-oriented, and grounded in the discussion.
Do not include markdown fences or commentary outside the schema."""

    summary_prompt = f"""Based on the following expert discussion, produce a structured consensus for the original query.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Requirements:
- governing_insight: ONE short sentence (max ~220 characters) capturing the single
  most important takeaway. Do NOT paste the full analysis here.
- executive_summary: 2 to 4 short paragraphs, each roughly 2-4 sentences. Each paragraph
  must add new information — do not repeat the governing_insight verbatim.
- key_findings: 3-5 distinct findings, each with a specific title (not "Consensus"),
  a concrete claim, supporting evidence_points, and a clear implication.
- decision_implications: plain strings (not objects). Each entry is one tradeoff,
  condition, or disagreement that affects execution.
- recommendations: concrete moves with owner, expected impact, and key risk.
- limitations: only include real uncertainty or missing evidence.
"""

    try:
        structured_response = await get_llm_client().generate_json(
            summary_prompt,
            moderator_prompt,
            schema_name="roundtable_consensus_brief",
            schema=_ROUND_TABLE_CONSENSUS_SCHEMA,
        )
        consensus_brief = _normalize_consensus_brief(structured_response)
        if not _has_meaningful_consensus_brief(consensus_brief):
            raise ValueError("Structured consensus was semantically empty")
        return _structured_consensus_to_markdown(consensus_brief), consensus_brief
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error generating structured consensus: {e}")

    fallback_prompt = f"""Based on the following expert discussion, provide a consensus answer to the original query.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Provide a clear, actionable consensus that synthesizes the experts' insights."""

    fallback_system_prompt = """You are a moderator synthesizing a roundtable discussion among agricultural experts. Your role is to:
1. Identify key points of agreement
2. Note any important differences in perspective
3. Provide actionable conclusions

Be concise but comprehensive."""

    try:
        response = await get_llm_client().generate(
            fallback_prompt, fallback_system_prompt
        )
        return response.strip(), None
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error generating consensus: {e}")
        return f"Error generating consensus: {str(e)}", None


def _normalize_consensus_brief(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "governing_insight": str(payload.get("governing_insight", "")).strip(),
        "executive_summary": _clean_string_list(payload.get("executive_summary", [])),
        "key_findings": [
            {
                "title": str(item.get("title", "")).strip(),
                "claim": str(item.get("claim", "")).strip(),
                "evidence_points": _clean_string_list(item.get("evidence_points", [])),
                "implication": str(item.get("implication", "")).strip(),
            }
            for item in payload.get("key_findings", [])
            if isinstance(item, dict) and str(item.get("title", "")).strip()
        ],
        "decision_implications": _clean_string_list(
            payload.get("decision_implications", [])
        ),
        "recommendations": [
            {
                "owner": str(item.get("owner", "")).strip(),
                "action": str(item.get("action", "")).strip(),
                "expected_impact": str(item.get("expected_impact", "")).strip(),
                "key_risk": str(item.get("key_risk", "")).strip(),
            }
            for item in payload.get("recommendations", [])
            if isinstance(item, dict) and str(item.get("action", "")).strip()
        ],
        "limitations": _clean_string_list(payload.get("limitations", [])),
    }


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _coerce_to_string(item))]


def _coerce_to_string(value: Any) -> str:
    """Flatten schema-violating LLM payloads (dicts, nested lists) into readable strings."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = [_coerce_to_string(item) for item in value.values()]
        return " — ".join(part for part in parts if part)
    if isinstance(value, (list, tuple)):
        parts = [_coerce_to_string(item) for item in value]
        return " ".join(part for part in parts if part)
    return str(value).strip()


def _has_meaningful_consensus_brief(consensus_brief: dict[str, Any]) -> bool:
    if not str(consensus_brief.get("governing_insight", "")).strip():
        return False
    if _clean_string_list(consensus_brief.get("executive_summary", [])):
        return True
    if any(
        isinstance(item, dict) and str(item.get("claim", "")).strip()
        for item in consensus_brief.get("key_findings", [])
    ):
        return True
    if any(
        isinstance(item, dict) and str(item.get("action", "")).strip()
        for item in consensus_brief.get("recommendations", [])
    ):
        return True
    return False


def _structured_consensus_to_markdown(consensus_brief: dict[str, Any]) -> str:
    lines: list[str] = []

    governing_insight = str(consensus_brief.get("governing_insight", "")).strip()
    if governing_insight:
        lines.extend(["## Governing Insight", "", governing_insight, ""])

    summary = _clean_string_list(consensus_brief.get("executive_summary", []))
    if summary:
        lines.extend(["## Executive Summary", ""])
        for item in summary:
            lines.extend([item, ""])

    findings = consensus_brief.get("key_findings", [])
    if isinstance(findings, list) and findings:
        lines.extend(["## Key Findings", ""])
        for item in findings:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip() or "Finding"
            claim = str(item.get("claim", "")).strip()
            lines.extend([f"### {title}", ""])
            if claim:
                lines.extend([claim, ""])
            for point in _clean_string_list(item.get("evidence_points", [])):
                lines.append(f"- {point}")
            implication = str(item.get("implication", "")).strip()
            if implication:
                lines.extend(["", f"**Implication:** {implication}"])
            lines.append("")

    implications = _clean_string_list(consensus_brief.get("decision_implications", []))
    if implications:
        lines.extend(["## Decision Implications", ""])
        for item in implications:
            lines.append(f"- {item}")
        lines.append("")

    recommendations = consensus_brief.get("recommendations", [])
    if isinstance(recommendations, list) and recommendations:
        lines.extend(["## Recommendations", ""])
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            owner = str(item.get("owner", "")).strip() or "Shared"
            lines.extend([f"### {owner}", ""])
            lines.append(f"- Action: {str(item.get('action', '')).strip()}")
            expected_impact = str(item.get("expected_impact", "")).strip()
            if expected_impact:
                lines.append(f"- Expected Impact: {expected_impact}")
            key_risk = str(item.get("key_risk", "")).strip()
            if key_risk:
                lines.append(f"- Key Risk: {key_risk}")
            lines.append("")

    limitations = _clean_string_list(consensus_brief.get("limitations", []))
    if limitations:
        lines.extend(["## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).strip()
