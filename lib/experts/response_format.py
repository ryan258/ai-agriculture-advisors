"""Shared closing format for practical decision support."""

import re
from typing import Any

COMPACT_DECISION_FORMAT = "compact_decision"
WORKFLOW_HANDOFF_FORMAT = "workflow_handoff"
ACCESSIBILITY_CAPABILITY_INSTRUCTIONS = """Capability grounding: the user's original request is the only evidence of configured tools.
Advisor suggestions are proposals, not evidence that a feature exists or works. A requested capability
is not a confirmed capability. Do not promote a proposal from the discussion into an available tool.
Present a voice command, alias, macro, automatic save/bookmark, or restoration as usable only when
the original request explicitly confirms that it is already configured and working. Never invent
commands such as 'save checkpoint', 'resume task', or '/task'. A familiar command name is not evidence.
When setup is unknown, provide plain reusable text, not a tool invocation. For example:
'Task: [task]. Background ref: [existing reference or not saved]. Goal: [one outcome]. Next: [one action].'
'RESUME: [task/reference] | Done: [last step] | Next: [one action] | Blocker: [none or issue].'
These are text records; generating them does not save anything or configure voice execution.
For garbled dictation, repeat only the unclear field once. If no reliable input remains, pause at
the last actually saved record. If no record has been saved, say so; do not promise restoration.
Do not require typing or an unconfirmed alias as the fallback, or turn missing setup into a platform choice."""
WORKFLOW_ADVISOR_INSTRUCTIONS = """For a standalone AI workflow or delegation answer, keep the analysis before the Decision Check to at most three concise bullets (about 80 words total). In a roundtable, provide only your assigned perspective in at most two short bullets; omit the Decision Check and leave the combined handoff and final user decision to the moderator. When answering alone, provide the useful deliverable requested without referring to a moderator.
When proposing a coding-agent boundary, distinguish prompt instructions from enforceable tool permissions. A draft may be written only to an approved scratch location; do not imply that prompt text alone prevents repository changes. A hosted model receives submitted text, so recommend sharing only approved, redacted inputs and do not assume provider retention settings.
Never invent file paths, hashes, provider policies, baselines, or checks already performed."""
COMPACT_ENDING_FIELDS = (
    ("recommended_next_step", "Recommended next step"),
    ("strongest_objection", "Strongest objection"),
    ("unknowns", "What remains unknown"),
    ("user_decision", "What needs your decision"),
)
COMPACT_ENDING_INSTRUCTIONS = """Keep your analysis focused and end with a short Decision Check.
Use exactly these four labeled bullets, in this order, with one brief sentence per bullet:
- **Recommended next step:** the smallest useful action supported by the supplied context.
- **Strongest objection:** the most important reason to question the recommendation.
- **What remains unknown:** the missing evidence or unresolved condition that matters most.
- **What needs your decision:** one choice only the user can make; say 'No decision needed yet' when appropriate.
Do not invent objections, evidence, preferences, or required decisions to fill a slot.
If no material objection or unknown is apparent, say so and state the limits of the supplied context.
Keep all four closing bullets at the end; add nothing after them."""


def normalize_compact_ending(value: Any) -> dict[str, str]:
    """Require four usable strings rather than fabricating missing model output."""
    if not isinstance(value, dict):
        raise ValueError("Decision Check must contain all four closing points")
    ending = {}
    for key, _ in COMPACT_ENDING_FIELDS:
        text = value.get(key)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Decision Check is missing {key}")
        ending[key] = text.strip()
    return ending


def render_compact_ending(ending: dict[str, str]) -> str:
    return "## Decision Check\n\n" + "\n".join(
        f"- **{label}:** {ending[key]}" for key, label in COMPACT_ENDING_FIELDS
    )


def extract_compact_ending(text: str) -> dict[str, str]:
    """Read the instructed four-bullet ending from individual or fallback answers."""
    ending = {}
    for key, label in COMPACT_ENDING_FIELDS:
        matches = re.findall(
            rf"^[ \t]*[-*][ \t]+(?:\*\*)?{re.escape(label)}:(?:\*\*)?[ \t]+(.+)$",
            text,
            re.MULTILINE,
        )
        if not matches or not matches[-1].strip():
            return {}
        ending[key] = matches[-1].strip()
    return ending


def collect_decision_checks(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve captured closing points in exports without generating new advice."""
    endings: list[tuple[str, dict[str, str]]] = []
    if result.get("result_type") == "roundtable":
        structured = result.get("consensus_brief") or {}
        ending = {}
        if isinstance(structured, dict) and "compact_ending" in structured:
            try:
                ending = normalize_compact_ending(structured["compact_ending"])
            except ValueError:
                pass
        if not ending:
            ending = extract_compact_ending(result.get("final_answer", ""))
        endings.append(("Roundtable", ending))
    else:
        for response in result.get("responses", []):
            endings.append(
                (
                    response.get("label", response.get("role", "Advisor")),
                    extract_compact_ending(response.get("response", "")),
                )
            )
    return [
        {
            "label": label,
            "points": [
                {"label": title, "text": ending[key]}
                for key, title in COMPACT_ENDING_FIELDS
            ],
        }
        for label, ending in endings
        if ending
    ]
