"""New decision panels, compact synthesis, and export preservation."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from lib.experts import build_advisor_context, get_expert, get_panel
from lib.experts.catalog import DEFINITIONS_DIR, load_catalog
from lib.experts.response_format import (
    COMPACT_ENDING_FIELDS,
    extract_compact_ending,
    render_compact_ending,
)
from lib.services import build_executive_brief_html, build_executive_brief_markdown
from lib.services.roundtable_service import (
    _ROUND_TABLE_CONSENSUS_SCHEMA,
    _generate_consensus,
    run_roundtable,
)

PANELS = ["ai_workflow", "accessibility_effort", "evidence_judgment"]
ENDING = {
    "recommended_next_step": "Try a single reversible handoff.",
    "strongest_objection": "A handoff could require more review than it saves.",
    "unknowns": "The current review effort has not been measured.",
    "user_decision": "Choose the task to use for the trial.",
}


def _brief() -> dict:
    return {
        "governing_insight": "Start with a small reversible trial.",
        "executive_summary": ["Review one result before delegating more work."],
        "key_findings": [],
        "decision_implications": [],
        "recommendations": [],
        "limitations": ["The current workflow has not been observed."],
        "compact_ending": ENDING.copy(),
    }


@pytest.mark.parametrize("panel_id", PANELS)
@pytest.mark.asyncio
async def test_decision_panels_use_shared_ending_in_answers_and_discussion(
    panel_id,
) -> None:
    panel = get_panel(panel_id)
    assert len(panel.roles) == 4
    assert len(panel.default_roles) == 2
    assert panel.suggested_queries
    context = build_advisor_context(panel_id, panel.roles)
    for role, snapshot in zip(panel.roles, context["advisors"]):
        advisor = get_expert(role)
        provider = AsyncMock()
        provider.generate.return_value = render_compact_ending(ENDING)
        with patch("lib.experts.base.get_llm_client", return_value=provider):
            await advisor.query("Help me with this task")
            await advisor.contribute_to_discussion("Help me with this task", "", 1)
        for call in provider.generate.await_args_list:
            assert call.args[1] == snapshot["system_prompt"]
            assert "no independent browsing" in call.args[1]
            assert "one brief sentence per bullet" in call.args[1]
            positions = [
                call.args[1].index(label) for _, label in COMPACT_ENDING_FIELDS
            ]
            assert positions == sorted(positions)


@pytest.mark.parametrize("panel_id", PANELS)
@pytest.mark.asyncio
async def test_decision_panel_roundtable_renders_structured_ending(panel_id) -> None:
    panel = get_panel(panel_id)
    provider = AsyncMock()
    provider.generate.return_value = (
        "Try one bounded task; review effort remains unknown."
    )
    provider.generate_json.return_value = _brief()
    original_schema = json.dumps(_ROUND_TABLE_CONSENSUS_SCHEMA, sort_keys=True)
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await run_roundtable(
            panel.suggested_queries[0]["query"], panel.default_roles, 1
        )
    assert len(result["transcript"]) == 2
    assert result["consensus_brief"]["compact_ending"] == ENDING
    assert result["final_answer"].endswith(render_compact_ending(ENDING))
    assert (
        "compact_ending"
        in provider.generate_json.await_args.kwargs["schema"]["required"]
    )
    assert json.dumps(_ROUND_TABLE_CONSENSUS_SCHEMA, sort_keys=True) == original_schema
    provider.generate.assert_awaited()
    # Every configured advisor participated; no extra fallback call was needed.
    assert provider.generate.await_count == 2


@pytest.mark.parametrize("ending", [None, {}, {**ENDING, "unknowns": " "}])
@pytest.mark.asyncio
async def test_missing_or_invalid_ending_uses_instructed_fallback(ending) -> None:
    provider = AsyncMock()
    brief = _brief()
    if ending is None:
        del brief["compact_ending"]
    else:
        brief["compact_ending"] = ending
    provider.generate_json.return_value = brief
    provider.generate.return_value = render_compact_ending(ENDING)
    with patch("lib.services.roundtable_service.get_llm_client", return_value=provider):
        answer, structured = await _generate_consensus(
            "Help me decide", [], compact_ending=True
        )
    assert structured is None
    assert answer.endswith(render_compact_ending(ENDING))
    assert "Decision Check" in provider.generate.await_args.args[1]
    assert "Do not invent" in provider.generate.await_args.args[1]


@pytest.mark.parametrize(
    "kind", ["query", "structured_roundtable", "fallback_roundtable"]
)
def test_exports_retain_actual_closing_points(kind) -> None:
    result = {
        "query": "How should I delegate this task?",
        "experts": ["example"],
        "responses": [],
        "result_type": "roundtable",
    }
    if kind == "query":
        result.update(
            result_type="query",
            responses=[
                {
                    "role": "example",
                    "label": "Workflow Designer",
                    "response": "Try one task.\n\n" + render_compact_ending(ENDING),
                }
            ],
        )
    elif kind == "structured_roundtable":
        result["consensus_brief"] = _brief()
    else:
        result["final_answer"] = "Try one task.\n\n" + render_compact_ending(ENDING)
    markdown = build_executive_brief_markdown(result)
    html = build_executive_brief_html(result)
    for key, label in COMPACT_ENDING_FIELDS:
        assert f"**{label}:** {ENDING[key]}" in markdown
        assert f"<strong>{label}:</strong> {ENDING[key]}" in html
    assert markdown.endswith(ENDING["user_decision"])


def test_incomplete_answers_do_not_get_invented_closing_points() -> None:
    blank_unknown = render_compact_ending({**ENDING, "unknowns": " "})
    assert extract_compact_ending(blank_unknown) == {}
    assert extract_compact_ending("A response without a Decision Check.") == {}
    assert (
        extract_compact_ending("- **Recommended next step:** Ask for more context.")
        == {}
    )


def test_unknown_response_format_is_rejected(tmp_path) -> None:
    advisors = json.loads((DEFINITIONS_DIR / "advisors.json").read_text())
    advisors[0]["response_format"] = "misspelled_format"
    (tmp_path / "advisors.json").write_text(json.dumps(advisors))
    (tmp_path / "panels.json").write_text((DEFINITIONS_DIR / "panels.json").read_text())
    with pytest.raises(ValueError, match="response format"):
        load_catalog(tmp_path)


def test_saved_decision_check_survives_replay_and_exports(tmp_path) -> None:
    from lib.storage import HistoryStore

    panel = get_panel("evidence_judgment")
    context = build_advisor_context(panel.id, panel.default_roles)
    store = HistoryStore(str(tmp_path / "decisions"))
    result_id = store.save_result(
        query="What evidence is missing?",
        experts=panel.default_roles,
        responses=[],
        result_type="roundtable",
        advisor_context=context,
        roundtable_data={
            "roles": panel.default_roles,
            "rounds": 1,
            "transcript": [],
            "final_answer": render_compact_ending(ENDING),
            "consensus_brief": _brief(),
        },
    )
    replay = store.get_result_by_id(result_id)
    assert replay["consensus_brief"]["compact_ending"] == ENDING
    assert replay["advisor_context"] == context
    for output in [
        build_executive_brief_html(replay),
        build_executive_brief_markdown(replay),
    ]:
        assert "Decision Check" in output
        assert ENDING["user_decision"] in output
