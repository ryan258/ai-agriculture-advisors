"""Shared text normalization helpers for service-layer LLM payloads."""

from __future__ import annotations

from typing import Any


def clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := coerce_to_string(item))]


def coerce_to_string(value: Any) -> str:
    """Flatten schema-violating LLM payloads into readable strings."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = [coerce_to_string(item) for item in value.values()]
        return " — ".join(part for part in parts if part)
    if isinstance(value, (list, tuple)):
        parts = [coerce_to_string(item) for item in value]
        return " ".join(part for part in parts if part)
    return str(value).strip()
