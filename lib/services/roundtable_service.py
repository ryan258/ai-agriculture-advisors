"""Service for multi-round expert discussions."""

import logging
import time
from typing import Any, Dict, List

import httpx

from lib.experts import get_expert
from lib.engine.config import get_settings
from lib.engine.llm_client import get_llm_client
from lib.experts.response_format import (
    COMPACT_DECISION_FORMAT,
    COMPACT_ENDING_FIELDS,
    COMPACT_ENDING_INSTRUCTIONS,
    normalize_compact_ending,
    render_compact_ending,
)

from ._text_utils import clean_string_list as _clean_string_list
from ._text_utils import coerce_to_string as _coerce_to_string

from .roundtable_state import (
    CapturedExpert,
    failure_details,
    normalize_roundtable_state,
    successful_entries,
)

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
    """Run a discussion, retaining completed contributions if a provider call fails."""
    if len(roles) < 2:
        return {
            "error": "At least 2 experts required for roundtable discussion",
            "transcript": [],
            "final_answer": "",
        }
    return await retry_roundtable(
        {
            "query": query,
            "roles": roles,
            "rounds": rounds,
            "transcript": [],
            "final_answer": "",
        }
    )


async def retry_roundtable(value: dict[str, Any]) -> dict[str, Any]:
    """Fill only missing slots, then synthesize. Never regenerate a successful answer."""
    state = normalize_roundtable_state(value)
    if state["retry_at"] > time.time():
        return state
    if (
        all(entry["status"] == "success" for entry in state["transcript"])
        and not state.get("synthesis_error")
        and not state.get("synthesis_stale")
    ):
        return state
    state["retry_at"] = 0
    snapshots = {
        item["role"]: item
        for item in (state.get("advisor_context") or {}).get("advisors", [])
    }
    changed = False
    for index, entry in enumerate(state["transcript"]):
        if entry["status"] == "success":
            continue
        role = entry["role"]
        expert = (
            CapturedExpert(snapshots[role]) if role in snapshots else get_expert(role)
        )
        if expert is None:
            raise ValueError(f"Advisor definition unavailable for role: {role}")
        prior = successful_entries(state["transcript"][:index])
        transcript_text = "\n".join(
            f"{item['speaker']}: {item['text']}" for item in prior
        )
        try:
            response = await expert.contribute_to_discussion(
                query=state["query"],
                transcript=transcript_text,
                round_num=entry["round"],
            )
            if not response.strip():
                raise ValueError("Empty advisor response")
            state["transcript"][index] = {
                "role": role,
                "speaker": expert.label,
                "round": entry["round"],
                "text": response,
                "status": "success",
            }
            changed = True
            logger.info("Roundtable: %s contributed in round %s", role, entry["round"])
        except Exception as error:
            failure = failure_details(error)
            entry.update(
                status="failed", text=f"Error: {failure['message']}", failure=failure
            )
            logger.warning(
                "Roundtable contribution failed for %s: %s", role, failure["kind"]
            )
            if failure["kind"] == "rate_limit":
                state["retry_at"] = failure["retry_at"]
                state["synthesis_error"] = {
                    "kind": "waiting",
                    "message": "Synthesis is waiting for the rate limit to clear.",
                }
                state["synthesis_stale"] = bool(state.get("final_answer")) and (
                    changed or state.get("synthesis_stale", False)
                )
                return state
    if not successful_entries(state["transcript"]):
        state["synthesis_error"] = {
            "kind": "waiting",
            "message": "At least one advisor response is needed before synthesis.",
        }
        return state
    settings = get_settings()
    synthesis_model = settings.openrouter_synthesis_model or settings.openrouter_model
    state["synthesis_model"] = synthesis_model
    compact_ending = state.get(
        "compact_ending",
        any(
            COMPACT_ENDING_INSTRUCTIONS in item["system_prompt"]
            for item in snapshots.values()
        )
        or any(
            getattr(get_expert(role), "response_format", "") == COMPACT_DECISION_FORMAT
            for role in state["roles"]
        ),
    )
    state["compact_ending"] = compact_ending
    try:
        answer, brief = await _generate_consensus(
            state["query"],
            state["transcript"],
            compact_ending=compact_ending,
            synthesis_model=synthesis_model,
        )
        state.update(
            final_answer=answer,
            consensus_brief=brief,
            synthesis_error=None,
            synthesis_stale=False,
        )
    except Exception as error:
        failure = failure_details(error)
        state["synthesis_error"] = failure
        state["synthesis_stale"] = bool(state.get("final_answer")) and (
            changed or state.get("synthesis_stale", False)
        )
        if failure["kind"] == "rate_limit":
            state["retry_at"] = failure["retry_at"]
        logger.warning("Roundtable synthesis failed: %s", failure["kind"])
    return state


async def _generate_consensus(
    query: str,
    transcript: List[Dict[str, str]],
    *,
    compact_ending: bool = False,
    synthesis_model: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """
    Generate a consensus summary from the discussion.

    Args:
        query: The original user query
        transcript: The discussion transcript

    Returns:
        Rendered markdown summary plus structured consensus payload when available
    """
    completed = successful_entries(transcript)
    transcript_text = "\n".join(
        f"{entry['speaker']}: {entry['text']}" for entry in completed
    )
    if len(completed) != len(transcript):
        transcript_text = (
            f"Only {len(completed)} of {len(transcript)} contributions completed. "
            "State this limitation; do not infer missing advisors' views.\n\n"
            + transcript_text
        )

    moderator_prompt = """You are a moderator synthesizing a roundtable discussion among the selected AI advisors.
Return a structured consensus object that a reporting system can render directly.
Keep every field concise, decision-oriented, and grounded in the discussion.
Preserve unresolved disagreements in decision_implications and unknowns in limitations.
Do not force agreement or treat agreement between AI personas as independent verification.
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

    schema = _ROUND_TABLE_CONSENSUS_SCHEMA
    if compact_ending:
        schema = {
            **schema,
            "required": [*schema["required"], "compact_ending"],
            "properties": {
                **schema["properties"],
                "compact_ending": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [key for key, _ in COMPACT_ENDING_FIELDS],
                    "properties": {
                        key: {"type": "string", "minLength": 1}
                        for key, _ in COMPACT_ENDING_FIELDS
                    },
                },
            },
        }
        moderator_prompt += (
            "\nPopulate compact_ending with four brief sentences: the smallest useful "
            "recommended_next_step, the strongest_objection, the most consequential "
            "unknowns, and one user_decision (or 'No decision needed yet'). "
            "Do not invent evidence, objections, or decisions to fill a field. "
            "State when no material objection or unknown is apparent within the supplied context. "
            "Use the JSON fields, not Markdown bullets, and do not duplicate the closing points elsewhere."
        )

    try:
        structured_response = await get_llm_client().generate_json(
            summary_prompt,
            moderator_prompt,
            schema_name="roundtable_consensus_brief",
            schema=schema,
            model=synthesis_model,
        )
        consensus_brief = _normalize_consensus_brief(structured_response)
        if compact_ending and "compact_ending" not in consensus_brief:
            raise ValueError("Structured response omitted the Decision Check")
        if not _has_meaningful_consensus_brief(consensus_brief):
            raise ValueError("Structured consensus was semantically empty")
        return _structured_consensus_to_markdown(consensus_brief), consensus_brief
    except (httpx.HTTPError, ValueError) as e:
        if isinstance(e, httpx.HTTPError) and not (
            isinstance(e, httpx.HTTPStatusError)
            and e.response.status_code in (400, 422)
        ):
            raise
        logger.warning(
            "Structured consensus generation failed; falling back to plain-text synthesis: %s",
            e,
        )

    fallback_prompt = f"""Based on the following expert discussion, provide a consensus answer to the original query.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Provide a clear, actionable consensus that synthesizes the experts' insights."""

    fallback_system_prompt = """You are a moderator synthesizing a roundtable discussion among the selected AI advisors. Your role is to:
1. Identify key points of agreement
2. Note any important differences in perspective
3. Provide actionable conclusions
4. Preserve unresolved disagreements and unknowns; do not force agreement
5. Do not treat agreement between AI personas as independent verification

Be concise but comprehensive."""
    if compact_ending:
        fallback_system_prompt += f"\n\n{COMPACT_ENDING_INSTRUCTIONS}"

    try:
        response = await get_llm_client().generate(
            fallback_prompt,
            fallback_system_prompt,
            model=synthesis_model,
        )
        return response.strip(), None
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error generating consensus: {e}")
        raise


def _normalize_consensus_brief(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
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
    if "compact_ending" in payload:
        normalized["compact_ending"] = normalize_compact_ending(
            payload["compact_ending"]
        )
    return normalized


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

    if consensus_brief.get("compact_ending"):
        lines.append(render_compact_ending(consensus_brief["compact_ending"]))

    return "\n".join(lines).strip()
