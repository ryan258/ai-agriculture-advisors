"""Reusable input, explicit evidence, and deterministic personal-work helpers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from lib.contracts import task_brief, text, sources
from lib.experts import build_advisor_context, get_panel


def quality_cases() -> list[dict[str, Any]]:
    """Read fictional examples; loading never executes a provider trial."""
    path = (
        Path(__file__).resolve().parents[1]
        / "experts"
        / "definitions"
        / "quality_cases.json"
    )
    cases = json.loads(path.read_text())
    if not isinstance(cases, list) or len(cases) > 20:
        raise ValueError("Invalid quality case catalog")
    for case in cases:
        text(case["query"], "Case question", 24000, blank=False)
        build_advisor_context(case["panel_id"], case["roles"])
        case["sources"] = sources(case.get("sources", []))
    return cases


def reusable_asset(kind: str, value: dict[str, Any]) -> dict[str, Any]:
    if kind not in ("starter", "context"):
        raise ValueError("Choose a starter or background context")
    result: dict[str, Any] = {
        "id": uuid4().hex,
        "name": text(value.get("name", ""), "Name", 120, blank=False),
    }
    if kind == "context":
        result["background"] = text(
            value.get("background", ""), "Background", 4000, blank=False
        )
    else:
        result["query"] = text(value.get("query", ""), "Starter", 24000, blank=False)
        panel = get_panel(value.get("panel_id", "agriculture"))
        roles = value.get("roles") or panel.default_roles
        build_advisor_context(panel.id, roles)
        result.update(
            panel_id=panel.id,
            roles=roles,
            task_brief=task_brief(value.get("task_brief", {})),
        )
    return result


def effort_comparison(values: dict[str, str]) -> dict[str, str]:
    parsed: dict[str, Decimal] = {}
    for key in ("manual", "setup", "review", "correction", "recovery"):
        try:
            number = Decimal(text(values.get(key, ""), key, 50, blank=False))
        except InvalidOperation:
            raise ValueError(
                "Enter measured minutes for each field; use zero for none."
            ) from None
        if not number.is_finite() or not 0 <= number <= 100000:
            raise ValueError("Minutes must be finite and nonnegative (up to 100,000).")
        parsed[key] = number
    assisted = sum(
        (parsed[key] for key in ("setup", "review", "correction", "recovery")),
        Decimal(0),
    )
    return {
        "manual": str(parsed["manual"]),
        "assisted": str(assisted),
        "difference": str(parsed["manual"] - assisted),
        "formula": "assisted = setup + review + correction + recovery; difference = manual − assisted",
        "interpretation": "Positive difference means fewer entered human minutes. This calculator does not establish quality, a fair baseline, or a medical benefit.",
    }
