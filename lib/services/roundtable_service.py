"""Service for multi-round expert discussions."""

import logging
import time
from typing import Any, Dict, List

import httpx

from lib.experts import get_expert
from lib.engine.config import get_settings
from lib.engine.llm_client import get_llm_client
from lib.experts.response_format import (
    ACCESSIBILITY_CAPABILITY_INSTRUCTIONS,
    COMPACT_DECISION_FORMAT,
    COMPACT_ENDING_FIELDS,
    COMPACT_ENDING_INSTRUCTIONS,
    WORKFLOW_HANDOFF_FORMAT,
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

_AI_WORKFLOW_HANDOFF_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task_packet",
        "review_checklist",
        "resume_checkpoint",
        "success_measure",
    ],
    "properties": {
        "task_packet": {"type": "string", "minLength": 40, "maxLength": 900},
        "review_checklist": {
            "type": "array",
            "minItems": 2,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["check", "evidence_target"],
                "properties": {
                    "check": {"type": "string", "minLength": 1, "maxLength": 180},
                    "evidence_target": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 180,
                    },
                },
            },
        },
        "resume_checkpoint": {"type": "string", "minLength": 1, "maxLength": 500},
        "success_measure": {"type": "string", "minLength": 1, "maxLength": 500},
    },
}

_ACCESSIBILITY_HANDOFF_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "starter_template",
        "resume_checkpoint",
        "dictation_fallback",
        "first_trial",
    ],
    "properties": {
        "starter_template": {"type": "string", "minLength": 40, "maxLength": 900},
        "resume_checkpoint": {"type": "string", "minLength": 1, "maxLength": 500},
        "dictation_fallback": {"type": "string", "minLength": 1, "maxLength": 500},
        "first_trial": {"type": "string", "minLength": 1, "maxLength": 500},
    },
}


def _schema_with_compact_ending(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        **schema,
        "required": [*schema["required"], "compact_ending"],
        "properties": {
            **schema["properties"],
            "compact_ending": {
                "type": "object",
                "additionalProperties": False,
                "required": [key for key, _ in COMPACT_ENDING_FIELDS],
                "properties": {
                    key: {"type": "string", "minLength": 1, "maxLength": 180}
                    for key, _ in COMPACT_ENDING_FIELDS
                },
            },
        },
    }


async def run_roundtable(
    query: str,
    roles: List[str],
    rounds: int = 3,
    *,
    advisor_context: dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run a discussion, retaining completed contributions if a provider call fails."""
    if len(roles) < 2:
        return {
            "error": "At least 2 experts required for roundtable discussion",
            "transcript": [],
            "final_answer": "",
        }
    initial_state = {
        "query": query,
        "roles": roles,
        "rounds": rounds,
        "transcript": [],
        "final_answer": "",
    }
    if advisor_context is not None:
        initial_state["advisor_context"] = advisor_context
    return await retry_roundtable(initial_state)


def _uses_workflow_handoff(state: dict[str, Any]) -> bool:
    context = state.get("advisor_context")
    panel = context.get("panel") if isinstance(context, dict) else None
    if isinstance(panel, dict) and isinstance(panel.get("id"), str):
        return panel["id"] == "ai_workflow"
    return bool(state.get("roles")) and all(
        getattr(get_expert(role), "response_format", "") == WORKFLOW_HANDOFF_FORMAT
        for role in state["roles"]
    )


def _uses_accessibility_handoff(state: dict[str, Any]) -> bool:
    context = state.get("advisor_context")
    panel = context.get("panel") if isinstance(context, dict) else None
    if isinstance(panel, dict) and isinstance(panel.get("id"), str):
        return panel["id"] == "accessibility_effort"
    return bool(state.get("roles")) and all(
        role.startswith("accessibility_effort_") for role in state["roles"]
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
    workflow_handoff = _uses_workflow_handoff(state)
    accessibility_handoff = _uses_accessibility_handoff(state)
    compact_ending = state.get(
        "compact_ending",
        any(
            COMPACT_ENDING_INSTRUCTIONS in item["system_prompt"]
            for item in snapshots.values()
        )
        or any(
            getattr(get_expert(role), "response_format", "")
            in (COMPACT_DECISION_FORMAT, WORKFLOW_HANDOFF_FORMAT)
            for role in state["roles"]
        ),
    )
    compact_ending = bool(compact_ending or workflow_handoff or accessibility_handoff)
    state["compact_ending"] = compact_ending
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
                compact_roundtable=compact_ending,
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
    try:
        answer, brief = await _generate_consensus(
            state["query"],
            state["transcript"],
            compact_ending=compact_ending,
            workflow_handoff=workflow_handoff,
            accessibility_handoff=accessibility_handoff,
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
    workflow_handoff: bool = False,
    accessibility_handoff: bool = False,
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

    if workflow_handoff:
        moderator_prompt = """You are the moderator for AI Workflow & Delegation.
Return only the requested structured handoff object. Keep it short and immediately usable.
Base checks only on material actually supplied; do not claim to have inspected files, diffs,
permissions, provider settings, or completed actions unless the discussion contains that evidence.
Separate instructions for an agent from tool permissions that must enforce them. A hosted-model
request sends its supplied text to the provider; do not assert retention or privacy settings.
Do not force agreement or treat agreement between AI personas as independent verification.
Do not include markdown fences or commentary outside the schema."""
        summary_prompt = f"""Create the smallest useful delegation handoff for this request.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Fill the schema directly; do not substitute advice to create these deliverables later.
- Task packet: state the objective, exact input (or what's still needed), allowed actions,
  blocked actions, reviewable deliverable, and a clear stop condition. Allow writing only to
  an approved scratch location when a file is requested. Do not invent a path. Put these in
  concise labeled lines: Goal, Input, Allowed, Blocked, Deliverable, Stop if, Enforce with
  tools, and Data boundary.
- Tool enforcement: say that the execution environment must enforce path/tool limits; prompt
  wording alone cannot guarantee that no repository change occurs.
- Data boundary: advise submitting only approved/redacted material. Distinguish the model
  request to its provider from any extra network access by the delegated agent.
- Review checklist: give 2-4 checks. For factual claims, identify the supplied source evidence
  to compare against (for code release notes, the changed file/hunk). If that evidence is absent,
  say the check is pending; never invent filenames, hunks, dates, versions, or links.
- Resume checkpoint: provide two short labeled lines, Record and Resume. The record includes
  input reference/hash if available, exact instructions, output location, status, and next action.
  Never fabricate a hash or path.
- Success measure: provide three short labeled lines, Manual baseline, AI trial, and Keep only if.
  Compare human time on a similar manual task with setup, review, correction,
  and recovery time for the AI trial. Call it a time saver only if measured human time is lower
  and no material factual error remains after review; without a baseline, call the result unknown.
- compact_ending, when requested: one brief sentence for each point, with no repetition of the
  packet, checklist, checkpoint, or success measure.
Omit generic summaries, extra recommendations, and repeated conclusions."""
        schema_name = "ai_workflow_handoff_brief"
        schema = _AI_WORKFLOW_HANDOFF_SCHEMA
        if compact_ending:
            schema = _schema_with_compact_ending(schema)
            moderator_prompt += (
                "\nInclude the four required compact_ending points as brief sentences. "
                "Do not repeat those points elsewhere in the object."
            )
    elif accessibility_handoff:
        moderator_prompt = """You are the moderator for Accessibility & Effort.
Return only the requested structured starter and recovery plan. Make it usable in a short session.
Use the original user query as the only evidence of existing capabilities. The discussion contains
advisor proposals, not proof that tools work. Discard unsupported operational claims from it.
Do not assume the user can type. Preserve the user's final choice. Do not invent saved locations,
aliases, completed setup, or automatic saving."""
        moderator_prompt += f"\n\n{ACCESSIBILITY_CAPABILITY_INSTRUCTIONS}"
        summary_prompt = f"""Turn this request and discussion into a usable, low-effort starter for one recurring task.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Return the actual starter text and recovery steps, not advice to create them later.
- Reusable starter: provide a short, voice-friendly template now. Put reusable background in
  a saved-reference placeholder so it need not be dictated again; include only a few fields for
  today's goal and next step. Mark unknown task details as clear placeholders. Do not choose a
  storage product or invent an alias. This starter is reusable text, not an installed voice command.
- Resume checkpoint: give the exact compact record to save: task/reference, last completed step,
  next action, and blocker or none. Do not promise automatic bookmarks, timestamps, or restoration.
- Dictation fallback: say how to preserve the checkpoint if dictation garbles one field; recover
  only that field, not all background. If dictation is unavailable, stop at the saved checkpoint
  and use an alias or short-code entry point only if the original user query confirms it works.
  If no reliable input is available, pause; if no record has actually been saved, say so. Never make
  typing the required fallback or assume that generating a record has saved it.
- First trial: one small reversible use of the starter. Compare the number of repeated background
  entries and practical interactions with the current routine; claim improvement only after trying it.
- Decision Check: use at most one user decision, and only if it blocks the first trial. Otherwise
  return "No decision needed yet." Do not ask platform-selection questions merely to fill the field.
Omit repeated objections, generic summaries, and extra recommendations."""
        schema_name = "accessibility_workflow_starter"
        schema = _ACCESSIBILITY_HANDOFF_SCHEMA
        if compact_ending:
            schema = _schema_with_compact_ending(schema)
            moderator_prompt += (
                "\nUse one compact Decision Check after the handoff only. "
                "Do not repeat the same question in any handoff field."
            )
    else:
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
        schema_name = "roundtable_consensus_brief"
        schema = _ROUND_TABLE_CONSENSUS_SCHEMA
        if compact_ending:
            schema = _schema_with_compact_ending(schema)
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
            schema_name=schema_name,
            schema=schema,
            model=synthesis_model,
        )
        consensus_brief = (
            _normalize_workflow_handoff(structured_response, compact_ending)
            if workflow_handoff
            else (
                _normalize_accessibility_handoff(structured_response, compact_ending)
                if accessibility_handoff
                else _normalize_consensus_brief(structured_response)
            )
        )
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

    if workflow_handoff:
        fallback_prompt = f"""Create a short AI workflow handoff from this request and discussion.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Return only these sections: Task Packet, Review Checklist, Resume Checkpoint, Success Measure.
Give the actual packet and checks, not advice to create them. Ground checks in supplied evidence;
mark missing evidence pending. Do not invent paths, hashes, baselines, provider policies, or checks.
State that tool permissions must enforce agent boundaries and that submitted text goes to the
hosted model provider. Keep each section brief."""
        fallback_system_prompt = """You are a concise moderator for AI Workflow & Delegation. Synthesize the advisors into an immediately usable handoff. Distinguish model requests from delegated-agent tools, preserve uncertainty, and do not claim unverified controls or evidence. Do not treat AI agreement as independent verification."""
    elif accessibility_handoff:
        fallback_prompt = f"""Create a usable Accessibility & Effort starter from this request and discussion.

Original Query: {query}

Discussion Transcript:
{transcript_text}

Return only these sections: Reusable Starter, Resume Checkpoint, Dictation Fallback, First Trial.
Give the actual voice-friendly template and exact compact checkpoint. Use placeholders for unknown
details. Avoid product or platform claims, do not require typing, and do not invent storage or alias
setup. If dictation garbles one field, preserve the checkpoint and recover only that field. If no
user choice blocks a small first trial, do not ask a question. Add one compact Decision Check after
the four sections only; do not repeat their content. Ask at most one essential question, and only
when its answer blocks the first trial. Otherwise say 'No decision needed yet.'"""
        fallback_system_prompt = """You are a concise Accessibility & Effort moderator. Return an actionable, low-interaction starter and recovery plan. Preserve the user's control and uncertainty. Do not repeat advisor closing points or recommend unverified tools. Do not require typing or invent saved locations, aliases, or configured capabilities."""
        fallback_system_prompt += f"\n\n{ACCESSIBILITY_CAPABILITY_INSTRUCTIONS}"
    else:
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
        answer = response.strip()
        if not answer:
            raise ValueError("Plain-text synthesis was empty")
        return answer, None
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Error generating consensus: {e}")
        raise


def _normalize_workflow_handoff(
    payload: dict[str, Any], compact_ending: bool
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Workflow handoff must be an object")

    def required_text(value: Any, label: str, max_length: int) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > max_length
        ):
            raise ValueError(f"Workflow handoff has an invalid {label}")
        return value.strip()

    raw_checks = payload.get("review_checklist")
    if not isinstance(raw_checks, list) or not 2 <= len(raw_checks) <= 4:
        raise ValueError("Workflow handoff needs two to four review checks")
    review_checklist = []
    for check in raw_checks:
        if not isinstance(check, dict):
            raise ValueError("Workflow handoff has an invalid review check")
        review_checklist.append(
            {
                key: required_text(check.get(key), f"review check {key}", 180)
                for key in ("check", "evidence_target")
            }
        )

    normalized: dict[str, Any] = {
        "synthesis_format": "workflow_handoff",
        "task_packet": required_text(payload.get("task_packet"), "task packet", 900),
        "review_checklist": review_checklist,
        "resume_checkpoint": required_text(
            payload.get("resume_checkpoint"), "resume checkpoint", 500
        ),
        "success_measure": required_text(
            payload.get("success_measure"), "success measure", 500
        ),
    }
    if compact_ending:
        ending = normalize_compact_ending(payload.get("compact_ending"))
        if any(len(value) > 180 for value in ending.values()):
            raise ValueError("Workflow Decision Check is too long")
        normalized["compact_ending"] = ending
    return normalized


def _normalize_accessibility_handoff(
    payload: dict[str, Any], compact_ending: bool
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Accessibility handoff must be an object")

    limits = {
        "starter_template": 900,
        "resume_checkpoint": 500,
        "dictation_fallback": 500,
        "first_trial": 500,
    }
    normalized: dict[str, Any] = {"synthesis_format": "accessibility_handoff"}
    for key, max_length in limits.items():
        value = payload.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > max_length
        ):
            raise ValueError(f"Accessibility handoff has an invalid {key}")
        normalized[key] = value.strip()

    if compact_ending:
        ending = normalize_compact_ending(payload.get("compact_ending"))
        if any(len(value) > 180 for value in ending.values()):
            raise ValueError("Accessibility Decision Check is too long")
        normalized["compact_ending"] = ending
    return normalized


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
    if consensus_brief.get("synthesis_format") == "accessibility_handoff":
        return all(
            bool(consensus_brief.get(key))
            for key in (
                "starter_template",
                "resume_checkpoint",
                "dictation_fallback",
                "first_trial",
            )
        )
    if consensus_brief.get("synthesis_format") == "workflow_handoff":
        return bool(
            consensus_brief.get("task_packet")
            and consensus_brief.get("review_checklist")
            and consensus_brief.get("resume_checkpoint")
            and consensus_brief.get("success_measure")
        )
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
    if consensus_brief.get("synthesis_format") == "accessibility_handoff":
        return _accessibility_handoff_to_markdown(consensus_brief)
    if consensus_brief.get("synthesis_format") == "workflow_handoff":
        return _workflow_handoff_to_markdown(consensus_brief)

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


def _workflow_handoff_to_markdown(brief: dict[str, Any]) -> str:
    lines = [
        "## Task Packet",
        "",
        brief["task_packet"],
        "",
        "## Review Checklist",
        "",
    ]
    lines.extend(
        f"- [ ] {item['check']} **Evidence:** {item['evidence_target']}"
        for item in brief["review_checklist"]
    )
    lines.extend(
        [
            "",
            "## Resume Checkpoint",
            "",
            brief["resume_checkpoint"],
        ]
    )
    lines.extend(
        [
            "",
            "## Success Measure",
            "",
            brief["success_measure"],
        ]
    )
    if brief.get("compact_ending"):
        lines.extend(["", render_compact_ending(brief["compact_ending"])])
    return "\n".join(lines).strip()


def _accessibility_handoff_to_markdown(brief: dict[str, Any]) -> str:
    lines = []
    for key, heading in (
        ("starter_template", "Reusable Starter"),
        ("resume_checkpoint", "Resume Checkpoint"),
        ("dictation_fallback", "Dictation Fallback"),
        ("first_trial", "First Trial"),
    ):
        lines.extend([f"## {heading}", "", brief[key], ""])
    if brief.get("compact_ending"):
        lines.append(render_compact_ending(brief["compact_ending"]))
    return "\n".join(lines).strip()
