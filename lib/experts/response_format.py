"""Shared closing format for practical decision support."""

import re
from typing import Any

COMPACT_DECISION_FORMAT = "compact_decision"
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
