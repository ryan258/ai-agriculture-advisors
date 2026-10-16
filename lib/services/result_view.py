"""Prepare saved and fresh results for reading without generating new advice."""

from typing import Any

from lib.experts.response_format import collect_decision_checks


def result_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Expose only captured handoff and decision fields, leaving original text intact."""
    brief = result.get("consensus_brief")
    brief = brief if isinstance(brief, dict) else {}
    fields = (
        ("starter_template", "Reusable starter"),
        ("task_packet", "Task packet"),
        ("resume_checkpoint", "Suggested resume checkpoint"),
        ("dictation_fallback", "Dictation fallback"),
        ("first_trial", "First trial"),
        ("success_measure", "Success measure"),
    )
    handoff = [
        {"label": label, "text": brief[key]}
        for key, label in fields
        if isinstance(brief.get(key), str) and brief[key].strip()
    ]
    summary = {
        "checks": collect_decision_checks(result),
        "handoff": handoff,
        "is_stale": bool(result.get("synthesis_stale")),
        "copy_text": "",
        "copy_label": "",
    }
    if handoff:
        summary["copy_text"] = handoff[0]["text"]
        summary["copy_label"] = handoff[0]["label"]
    return summary


def history_page(
    rows: list[dict[str, Any]], search: str, offset: int, page_size: int = 10
) -> dict[str, Any]:
    """Prepare bounded history pagination from one extra metadata result."""
    return {
        "history": rows[:page_size],
        "q": search,
        "offset": offset,
        "page_size": page_size,
        "has_more": len(rows) > page_size,
    }
