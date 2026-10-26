"""Optional, source-linked decision views for general roundtable synthesis."""

from __future__ import annotations

import re
from typing import Any

from lib.contracts import validate_schema
from lib.engine.execution import current_execution

STRINGS = {
    "type": "array",
    "maxItems": 6,
    "items": {"type": "string", "maxLength": 500},
}
SOURCE_IDS = {
    "type": "array",
    "maxItems": 8,
    "items": {"type": "string", "maxLength": 4},
}


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


EXTENSIONS = {
    "claims": {
        "type": "array",
        "maxItems": 6,
        "items": _object(
            {
                "claim": {"type": "string", "maxLength": 500},
                "support": {
                    "type": "string",
                    "enum": ["supplied", "inference", "unknown"],
                },
                "source_ids": SOURCE_IDS,
            }
        ),
    },
    "options": {
        "type": "array",
        "maxItems": 4,
        "items": _object(
            {
                "option": {"type": "string", "maxLength": 200},
                "pros": STRINGS,
                "cons": STRINGS,
                "unknowns": STRINGS,
                "source_ids": SOURCE_IDS,
            }
        ),
    },
    "disagreements": {
        "type": "array",
        "maxItems": 4,
        "items": _object(
            {
                "point": {"type": "string", "maxLength": 300},
                "viewpoints": STRINGS,
                "check": {"type": "string", "maxLength": 500},
                "source_ids": SOURCE_IDS,
                "turn_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 10,
                    "items": {"type": "string", "maxLength": 100},
                },
            }
        ),
    },
}


def decision_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        **schema,
        "required": [*schema["required"], *EXTENSIONS],
        "properties": {**schema["properties"], **EXTENSIONS},
    }


def known_sources() -> set[str]:
    execution = current_execution.get()
    return (
        {item["id"] for item in execution.state.get("sources", [])}
        if execution
        else set()
    )


def normalize_extensions(
    payload: dict[str, Any],
    available_sources: set[str] | None = None,
    available_turns: set[str] | None = None,
) -> dict[str, Any]:
    result = {}
    available = known_sources() if available_sources is None else available_sources
    execution = current_execution.get()
    turns = available_turns
    if turns is None:
        turns = (
            {
                f"R{item.get('round', 1)}/{item.get('role', '')}"
                for item in execution.state.get("transcript", [])
                if item.get("status", "success") == "success"
            }
            if execution
            else set()
        )
    for key, schema in EXTENSIONS.items():
        value = payload.get(key, [])
        validate_schema(value, schema, key)
        for item in value:
            if set(item["source_ids"]) - available:
                raise ValueError("A generated source ID was not supplied to this run")
            if (
                key == "claims"
                and item["support"] == "supplied"
                and not item["source_ids"]
            ):
                raise ValueError("A claim labeled supplied needs a captured source ID")
            if key == "disagreements" and set(item["turn_ids"]) - turns:
                raise ValueError(
                    "A disagreement cited a contribution that did not complete"
                )
        result[key] = value
    return result


def validate_text_citations(value: str) -> None:
    if set(re.findall(r"\[(S\d+)\]", value)) - known_sources():
        raise ValueError("The synthesis cited an unavailable source excerpt")
