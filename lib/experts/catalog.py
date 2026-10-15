"""File-based advisor definitions and panels, independent of the web framework."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .base import Expert
from .response_format import (
    ACCESSIBILITY_CAPABILITY_INSTRUCTIONS,
    COMPACT_DECISION_FORMAT,
    COMPACT_ENDING_INSTRUCTIONS,
    WORKFLOW_ADVISOR_INSTRUCTIONS,
    WORKFLOW_HANDOFF_FORMAT,
)

DEFINITIONS_DIR = Path(__file__).resolve().with_name("definitions")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _identifier(value: Any, field: str) -> str:
    value = _text(value, field)
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", value):
        raise ValueError(f"Invalid {field}: {value}")
    return str(value)


def _roles(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    roles = [_identifier(role, field) for role in value]
    if len(set(roles)) != len(roles):
        raise ValueError(f"Duplicate roles in {field}")
    return roles


@dataclass(frozen=True)
class AdvisorDefinition:
    role: str
    label: str
    system_prompt: str
    limitations: str


class ConfiguredExpert(Expert):
    """One implementation for every configured advisor."""

    def __init__(
        self, definition: AdvisorDefinition, response_format: str = ""
    ) -> None:
        if response_format not in (
            "",
            COMPACT_DECISION_FORMAT,
            WORKFLOW_HANDOFF_FORMAT,
        ):
            raise ValueError(f"Unknown advisor response format: {response_format}")
        self.definition = definition
        self.response_format = response_format

    @property
    def role(self) -> str:
        return self.definition.role

    @property
    def label(self) -> str:
        return self.definition.label

    @property
    def system_prompt(self) -> str:
        prompt = (
            f"{self.definition.system_prompt}\n\nLimits: {self.definition.limitations}"
        )
        if self.response_format == WORKFLOW_HANDOFF_FORMAT:
            prompt += f"\n\n{WORKFLOW_ADVISOR_INSTRUCTIONS}"
        if self.role.startswith("accessibility_effort_"):
            prompt += f"\n\n{ACCESSIBILITY_CAPABILITY_INSTRUCTIONS}"
        if self.response_format in (COMPACT_DECISION_FORMAT, WORKFLOW_HANDOFF_FORMAT):
            prompt += f"\n\n{COMPACT_ENDING_INSTRUCTIONS}"
        return prompt

    def snapshot(self) -> dict[str, str]:
        return {**asdict(self.definition), "system_prompt": self.system_prompt}


@dataclass(frozen=True)
class PanelDefinition:
    id: str
    label: str
    description: str
    roles: list[str]
    default_roles: list[str]
    suggested_queries: list[dict[str, str]]


def _read_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(data, list)
        or not data
        or not all(isinstance(x, dict) for x in data)
    ):
        raise ValueError(f"{path.name} must contain a non-empty list of objects")
    return data


def load_catalog(
    directory: Path = DEFINITIONS_DIR,
) -> tuple[dict[str, ConfiguredExpert], dict[str, PanelDefinition]]:
    """Fail clearly on invalid files, duplicate IDs, or dangling references."""
    advisors: dict[str, ConfiguredExpert] = {}
    for item in _read_records(directory / "advisors.json"):
        role = _identifier(item.get("role"), "advisor role")
        if role in advisors:
            raise ValueError(f"Duplicate advisor role: {role}")
        definition = AdvisorDefinition(
            role=role,
            label=_text(item.get("label"), "advisor label"),
            system_prompt=_text(item.get("system_prompt"), "system prompt"),
            limitations=_text(item.get("limitations"), "advisor limitations"),
        )
        advisors[role] = ConfiguredExpert(
            definition, response_format=item.get("response_format", "")
        )
    panels: dict[str, PanelDefinition] = {}
    for item in _read_records(directory / "panels.json"):
        panel_id = _identifier(item.get("id"), "panel ID")
        if panel_id in panels:
            raise ValueError(f"Duplicate panel ID: {panel_id}")
        roles = _roles(item.get("roles"), "panel roles")
        defaults = _roles(item.get("default_roles"), "default roles")
        if not set(roles) <= advisors.keys() or not set(defaults) <= set(roles):
            raise ValueError(
                f"Unknown advisor or invalid defaults in panel: {panel_id}"
            )
        suggestions = item.get("suggested_queries", [])
        if not isinstance(suggestions, list) or not all(
            isinstance(x, dict) for x in suggestions
        ):
            raise ValueError(f"Invalid suggested queries in panel: {panel_id}")
        panels[panel_id] = PanelDefinition(
            id=panel_id,
            label=_text(item.get("label"), "panel label"),
            description=_text(item.get("description"), "panel description"),
            roles=roles,
            default_roles=defaults,
            suggested_queries=[
                {
                    "label": _text(x.get("label"), "suggestion label"),
                    "query": _text(x.get("query"), "suggestion query"),
                }
                for x in suggestions
            ],
        )
    return advisors, panels


def validate_advisor_context(context: Any, roles: list[str]) -> dict[str, Any]:
    """Validate a historical snapshot without consulting today's catalog."""
    if not isinstance(context, dict) or not isinstance(context.get("panel"), dict):
        raise ValueError("Invalid advisor context")
    panel = context["panel"]
    panel_data = {
        "id": _identifier(panel.get("id"), "panel ID"),
        "label": _text(panel.get("label"), "panel label"),
    }
    advisors = context.get("advisors")
    if not isinstance(advisors, list) or not all(isinstance(x, dict) for x in advisors):
        raise ValueError("Invalid advisor definitions")
    snapshots = [
        {
            "role": _identifier(item.get("role"), "advisor role"),
            **{
                key: _text(item.get(key), key)
                for key in ("label", "system_prompt", "limitations")
            },
        }
        for item in advisors
    ]
    if [item["role"] for item in snapshots] != roles or len(set(roles)) != len(roles):
        raise ValueError("Advisor definitions must match the result's selected roles")
    return {"panel": panel_data, "advisors": snapshots}
