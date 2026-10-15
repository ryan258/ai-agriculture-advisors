"""Behavioral checks for configurable panels and historical advisor definitions."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from lib.experts import build_advisor_context, get_expert, get_panel
from lib.experts.catalog import DEFINITIONS_DIR, load_catalog, validate_advisor_context


def test_built_in_panels_keep_separate_roles_and_defaults() -> None:
    agriculture = get_panel("agriculture")
    software = get_panel("software")
    assert len(agriculture.roles) == 10
    assert len(software.roles) == 5
    assert agriculture.default_roles == ["agriculture"]
    assert set(software.default_roles) <= set(software.roles)
    assert not set(agriculture.roles) & set(software.roles)


@pytest.mark.parametrize(
    "panel,roles",
    [
        ("missing", ["agriculture"]),
        ("software", ["soil"]),
        ("software", ["software_testing", "software_testing"]),
    ],
)
def test_invalid_panel_selections_fail_before_generation(panel, roles) -> None:
    with pytest.raises(ValueError):
        build_advisor_context(panel, roles)


@pytest.mark.parametrize(
    "problem", ["duplicate", "unknown", "defaults", "blank", "syntax"]
)
def test_invalid_catalog_fails_clearly(tmp_path: Path, problem: str) -> None:
    for name in ["advisors.json", "panels.json"]:
        (tmp_path / name).write_text((DEFINITIONS_DIR / name).read_text())
    advisors = json.loads((tmp_path / "advisors.json").read_text())
    panels = json.loads((tmp_path / "panels.json").read_text())
    if problem == "duplicate":
        advisors.append(advisors[0])
    elif problem == "unknown":
        panels[0]["roles"].append("unknown")
    elif problem == "defaults":
        panels[0]["default_roles"] = ["software_testing"]
    elif problem == "blank":
        advisors[0]["system_prompt"] = " "
    (tmp_path / "advisors.json").write_text(json.dumps(advisors))
    (tmp_path / "panels.json").write_text(
        "{" if problem == "syntax" else json.dumps(panels)
    )
    with pytest.raises(ValueError):
        load_catalog(tmp_path)


def test_custom_panel_can_reuse_advisors(tmp_path: Path) -> None:
    (tmp_path / "advisors.json").write_text(
        (DEFINITIONS_DIR / "advisors.json").read_text()
    )
    panels = json.loads((DEFINITIONS_DIR / "panels.json").read_text())
    panels.append(
        {
            "id": "farm_software",
            "label": "Farm Software",
            "description": "A custom mixed panel.",
            "roles": ["soil", "software_testing"],
            "default_roles": ["soil"],
            "suggested_queries": [],
        }
    )
    (tmp_path / "panels.json").write_text(json.dumps(panels))
    _, loaded = load_catalog(tmp_path)
    assert loaded["farm_software"].roles == ["soil", "software_testing"]


def test_context_cannot_mislabel_selected_roles() -> None:
    context = build_advisor_context("software", ["software_testing"])
    with pytest.raises(ValueError, match="match"):
        validate_advisor_context(context, ["soil"])


@pytest.mark.asyncio
async def test_software_advisor_uses_its_configured_prompt() -> None:
    advisor = get_expert("software_accessibility")
    context = build_advisor_context("software", ["software_accessibility"])
    client = AsyncMock()
    client.generate.return_value = "Check keyboard focus."
    with patch("lib.experts.base.get_llm_client", return_value=client):
        assert await advisor.query("Review my workflow") == "Check keyboard focus."
    assert client.generate.await_args.args[1] == context["advisors"][0]["system_prompt"]
    assert "assistive technology" in client.generate.await_args.args[1]


@pytest.mark.asyncio
async def test_moderator_fallback_retains_disagreement_instructions() -> None:
    from lib.services.roundtable_service import _generate_consensus

    client = AsyncMock()
    client.generate_json.side_effect = ValueError("Unsupported structured response")
    client.generate.return_value = "The advisors disagree; more evidence is needed."
    with patch("lib.services.roundtable_service.get_llm_client", return_value=client):
        text, structured = await _generate_consensus("Review this tool", [])
    assert structured is None
    assert "disagree" in text
    prompt = client.generate.await_args.args[1]
    assert "agricultural" not in prompt
    assert "do not force agreement" in prompt
    assert "independent verification" in prompt
