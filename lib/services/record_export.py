"""Lossless archives and explicit abridged-versus-complete export semantics."""

from __future__ import annotations

import json
import re
from typing import Any

from lib.contracts import SCHEMA_VERSION, validate_result


def fenced(value: Any, language: str = "text") -> str:
    source = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, indent=2)
    )
    longest = max((len(item) for item in re.findall(r"`+", source)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{source}\n{fence}"


def complete_markdown(
    record: dict[str, Any], notes: dict[str, str] | None = None
) -> str:
    result = validate_result(record, legacy=True)
    lines = [
        "# Complete AI Advisors record",
        "",
        "AI-generated perspectives. AI agreement is not independent verification. Supplied source passages and personal decisions are labeled separately.",
        "",
        f"Record: {result.get('id', 'unsaved')} · Format: {result['schema_version']}",
        "",
        "## Original question (exact text)",
        "",
        fenced(result["query"]),
        "",
    ]
    if result.get("task_brief"):
        lines += [
            "## Supplied task context",
            "",
            fenced(result["task_brief"], "json"),
            "",
        ]
    for source in result.get("sources", []):
        lines += [
            f"## Supplied source [{source['id']}] — {source['label']}",
            "",
            f"Reference: {source['reference']}\nDate supplied: {source['date'] or 'Unknown'}",
            "",
            fenced(source["passage"]),
            "",
        ]
    if not result.get("sources"):
        lines += [
            "No source excerpts were captured. Participant names identify generated perspectives, not independent citations.",
            "",
        ]
    if result["result_type"] == "query":
        for entry in result.get("responses", []):
            lines += [
                f"## AI participant — {entry.get('label', entry.get('role', 'Advisor'))}",
                "",
                fenced(entry.get("error") or entry.get("response", "")),
                "",
            ]
    else:
        for entry in result.get("transcript", []):
            lines += [
                f"## Round {entry.get('round', '?')} — {entry.get('speaker', 'AI participant')}",
                "",
                f"Status: {entry.get('status', 'legacy / see text')}",
                "",
                fenced(entry.get("text", "")),
                "",
            ]
            if entry.get("failure"):
                lines += [fenced(entry["failure"], "json"), ""]
        lines += [
            "## Saved synthesis (exact text)",
            "",
            fenced(result.get("final_answer", "")),
            "",
        ]
        if result.get("synthesis_error") or result.get("synthesis_stale"):
            lines += [
                "Synthesis is incomplete or predates recovered contributions. Review the recorded status below.",
                "",
            ]
        if result.get("consensus_brief"):
            lines += [
                "## Captured structured synthesis",
                "",
                fenced(result["consensus_brief"], "json"),
                "",
            ]
    context = result.get("advisor_context")
    lines += [
        "## Advisor definitions used",
        "",
        fenced(context, "json") if context else "Not captured for this legacy result.",
        "",
        "## Execution and recovery metadata",
        "",
        fenced(
            {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "query",
                    "responses",
                    "transcript",
                    "final_answer",
                    "consensus_brief",
                    "advisor_context",
                    "sources",
                    "task_brief",
                }
            },
            "json",
        ),
        "",
    ]
    if notes is not None:
        lines += [
            "## User's decision and outcome (included deliberately)",
            "",
            fenced(notes, "json"),
            "",
        ]
    return "\n".join(lines)


def archive_record(
    record: dict[str, Any], notes: dict[str, str] | None = None
) -> dict[str, Any]:
    return {
        "archive_format": "ai-advisors",
        "archive_version": 1,
        "records": [
            {
                "result": validate_result(record, legacy=True),
                **({"annotations": notes} if notes is not None else {}),
            }
        ],
    }


def validate_archive(value: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(value, dict)
        or value.get("archive_format") != "ai-advisors"
        or value.get("archive_version") != 1
    ):
        raise ValueError("Unsupported archive. Expected AI Advisors archive version 1.")
    rows = value.get("records")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("An archive must contain one to one thousand records.")
    validated = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid archive entry")
        result = validate_result(row.get("result"), legacy=True)
        notes = row.get("annotations", {})
        if not isinstance(notes, dict) or any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in notes.items()
        ):
            raise ValueError("Invalid personal annotations in archive")
        from lib.storage.history_store import ANNOTATION_LIMITS, ANNOTATION_STATUSES

        if any(
            key not in ANNOTATION_LIMITS or len(item) > ANNOTATION_LIMITS[key]
            for key, item in notes.items()
        ):
            raise ValueError(
                "Archive contains an unknown or oversized personal note field"
            )
        if notes.get("status", "") not in ANNOTATION_STATUSES or notes.get(
            "outcome_rating", ""
        ) not in ("", "helped", "needed_correction", "not_useful", "not_tried"):
            raise ValueError("Archive contains an invalid personal status")
        validated.append({"result": result, "annotations": notes})
    return validated
