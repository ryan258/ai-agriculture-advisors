"""Lookup and selection validation for the file-based advisor catalog."""

from dataclasses import asdict
from typing import Any

from .base import Expert
from .catalog import PanelDefinition, load_catalog

expert_registry, panel_registry = load_catalog()
DEFAULT_PANEL_ID = "agriculture"


def get_expert(role: str) -> Expert | None:
    """Get an advisor by its stable role key."""
    return expert_registry.get(role)


def get_all_experts() -> list[dict[str, str]]:
    """Return display metadata for every advisor, without exposing instructions."""
    return [
        {"role": expert.role, "label": expert.label}
        for expert in expert_registry.values()
    ]


def get_panel(panel_id: str) -> PanelDefinition:
    if panel_id not in panel_registry:
        raise ValueError(f"Unknown advisor panel: {panel_id}")
    return panel_registry[panel_id]


def get_all_panels() -> list[dict[str, Any]]:
    return [asdict(panel) for panel in panel_registry.values()]


def build_advisor_context(panel_id: str, roles: list[str]) -> dict[str, Any]:
    """Validate a panel selection and capture exactly the instructions it uses."""
    panel = get_panel(panel_id)
    if not roles or len(set(roles)) != len(roles) or not set(roles) <= set(panel.roles):
        raise ValueError("Select distinct advisors from the chosen panel.")
    return {
        "panel": {"id": panel.id, "label": panel.label},
        "advisors": [expert_registry[role].snapshot() for role in roles],
    }
