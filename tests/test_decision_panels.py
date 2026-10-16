"""New decision panels, compact synthesis, and export preservation."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from lib.experts import build_advisor_context, get_expert, get_panel
from lib.experts.catalog import DEFINITIONS_DIR, load_catalog
from lib.experts.response_format import (
    ACCESSIBILITY_CAPABILITY_INSTRUCTIONS,
    COMPACT_ENDING_INSTRUCTIONS,
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
ACCESSIBILITY_ENDING = {
    **ENDING,
    "user_decision": "No decision is needed to try the starter once.",
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


def _workflow_brief() -> dict:
    return {
        "task_packet": (
            "Goal: Draft release notes from the supplied diff.\n"
            "Input: Use the approved diff; none was included in this discussion.\n"
            "Allowed: Read the diff; write one draft to an approved scratch path.\n"
            "Blocked: Edit the repository; commit, push, merge, or publish.\n"
            "Deliverable: One plain-text draft at a user-approved scratch location.\n"
            "Stop if: The diff is missing or the task exceeds the stated boundary.\n"
            "Enforce with tools: Restrict writes and tools in the agent environment; prompt text is not enforcement.\n"
            "Data boundary: Submit only approved or redacted diff content to the hosted model."
        ),
        "review_checklist": [
            {
                "check": "Trace every material claim to a changed hunk.",
                "evidence_target": "The supplied diff; mark this pending until it is available.",
            },
            {
                "check": "Confirm important changes are included and unsupported details are absent.",
                "evidence_target": "Changed files and relevant supplied release context.",
            },
        ],
        "resume_checkpoint": (
            "Record: [input ref/hash if available] | [instructions] | [draft path] | draft | [next check]\n"
            "Resume: Reopen that exact input and draft; inspect before rerunning or replacing anything."
        ),
        "success_measure": (
            "Manual baseline: Time setup, drafting, and review for a similar manual release note.\n"
            "AI trial: Time setup, review, corrections, and recovery for this draft.\n"
            "Keep only if: Human time is lower and review leaves no material factual errors."
        ),
        "compact_ending": ENDING.copy(),
    }


def _accessibility_brief() -> dict:
    return {
        "starter_template": (
            "Start [task name]. Use background saved at [reference]. "
            "Today I need [one outcome]. Next, do [one small action]."
        ),
        "resume_checkpoint": (
            "RESUME: [task/reference] | Done: [last completed step] | "
            "Next: [one action] | Waiting on: [blocker or none]"
        ),
        "dictation_fallback": (
            "If dictation garbles one field, keep the checkpoint and mark only that field [unclear]. "
            "Repeat that fragment once; if dictation is unavailable, stop and resume from the saved record later."
        ),
        "first_trial": (
            "Try one recurring task. Count repeated background entries and interactions before and after; "
            "keep the starter only if the trial reduces them without losing task state."
        ),
        "compact_ending": ACCESSIBILITY_ENDING.copy(),
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
    provider.generate_json.return_value = (
        _workflow_brief()
        if panel_id == "ai_workflow"
        else _accessibility_brief() if panel_id == "accessibility_effort" else _brief()
    )
    original_schema = json.dumps(_ROUND_TABLE_CONSENSUS_SCHEMA, sort_keys=True)
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await run_roundtable(
            panel.suggested_queries[0]["query"],
            panel.default_roles,
            1,
            advisor_context=build_advisor_context(panel.id, panel.default_roles),
        )
    assert len(result["transcript"]) == 2
    expected_ending = (
        ACCESSIBILITY_ENDING if panel_id == "accessibility_effort" else ENDING
    )
    assert result["consensus_brief"]["compact_ending"] == expected_ending
    assert result["final_answer"].endswith(render_compact_ending(expected_ending))
    assert result["final_answer"].count("## Decision Check") == 1
    assert (
        "compact_ending"
        in provider.generate_json.await_args.kwargs["schema"]["required"]
    )
    if panel_id == "ai_workflow":
        assert "## Task Packet" in result["final_answer"]
        assert "## Review Checklist" in result["final_answer"]
        assert "## Resume Checkpoint" in result["final_answer"]
        assert "## Success Measure" in result["final_answer"]
        assert "## Executive Summary" not in result["final_answer"]
        assert provider.generate_json.await_args.kwargs["schema_name"] == (
            "ai_workflow_handoff_brief"
        )
    elif panel_id == "accessibility_effort":
        for heading in [
            "## Reusable Starter",
            "## Resume Checkpoint",
            "## Dictation Fallback",
            "## First Trial",
        ]:
            assert heading in result["final_answer"]
        assert "## Executive Summary" not in result["final_answer"]
        assert provider.generate_json.await_args.kwargs["schema_name"] == (
            "accessibility_workflow_starter"
        )
    for call in provider.generate.await_args_list:
        assert COMPACT_ENDING_INSTRUCTIONS not in call.args[1]
        assert "Do not ask the user questions or add a Decision Check" in call.args[0]
    assert json.dumps(_ROUND_TABLE_CONSENSUS_SCHEMA, sort_keys=True) == original_schema
    provider.generate.assert_awaited()
    # Every configured advisor participated; no extra fallback call was needed.
    assert provider.generate.await_count == 2


@pytest.mark.asyncio
async def test_compact_roundtable_adds_only_new_points_after_round_one() -> None:
    panel = get_panel("accessibility_effort")
    provider = AsyncMock()
    provider.generate.side_effect = [
        "Voice starter point.",
        "Effort checkpoint point.",
        "A new voice-specific recovery point.",
        "No new point beyond the prior checkpoint.",
    ]
    provider.generate_json.return_value = _accessibility_brief()
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await run_roundtable(
            panel.suggested_queries[0]["query"],
            panel.default_roles,
            2,
            advisor_context=build_advisor_context(panel.id, panel.default_roles),
        )
    prompts = [call.args[0] for call in provider.generate.await_args_list]
    assert len(prompts) == 4
    assert "Voice starter point." in prompts[2]
    assert "Effort checkpoint point." in prompts[2]
    assert "On later rounds, add only a material point" in prompts[2]
    assert "Do not ask the user questions or add a Decision Check" in prompts[2]
    assert result["final_answer"].count("## Decision Check") == 1


@pytest.mark.parametrize("role", get_panel("accessibility_effort").roles)
@pytest.mark.asyncio
async def test_accessibility_grounding_reaches_standalone_and_discussion_requests(role):
    advisor = get_expert(role)
    provider = AsyncMock()
    provider.generate.return_value = "Use a plain text starter and pause safely."
    with patch("lib.experts.base.get_llm_client", return_value=provider):
        await advisor.query("I need a reusable starter. No shortcut is configured.")
        await advisor.contribute_to_discussion(
            "I need a reusable starter. No shortcut is configured.",
            "Another advisor proposed saying 'save checkpoint' and using '/task'.",
            1,
            compact_roundtable=True,
        )
    assert provider.generate.await_count == 2
    for call in provider.generate.await_args_list:
        system_prompt = call.args[1]
        assert system_prompt.count(ACCESSIBILITY_CAPABILITY_INSTRUCTIONS) == 1
        assert "Advisor suggestions are proposals, not evidence" in system_prompt
        assert "generating them does not save anything" in system_prompt


@pytest.mark.parametrize("role", get_panel("accessibility_effort").roles)
@pytest.mark.asyncio
async def test_accessibility_discussion_bans_working_trigger_phrasing(role):
    advisor = get_expert(role)
    provider = AsyncMock()
    provider.generate.return_value = "Proposed draft wording, not configured."
    transcript = (
        "Voice advisor proposed: Starter voice command 'Start [task]' spoken once; "
        "the system inserts placeholders. Say 'type checkpoint' to open a form."
    )
    with patch("lib.experts.base.get_llm_client", return_value=provider):
        await advisor.contribute_to_discussion(
            "I need a reusable starter. No command or alias is configured.",
            transcript,
            1,
            compact_roundtable=True,
        )
    system_prompt = provider.generate.await_args.args[1]
    assert "Do not phrase a proposal as a working trigger" in system_prompt
    assert "proposed draft wording that is not configured" in system_prompt


@pytest.mark.asyncio
async def test_legacy_accessibility_retry_adds_grounding_without_changing_snapshot():
    from lib.services.roundtable_state import CapturedExpert

    snapshot = {
        "role": "accessibility_effort_voice_workflow",
        "label": "Saved voice advisor",
        "system_prompt": "The original saved advisor profile.",
        "limitations": "Use supplied context.",
    }
    original = snapshot.copy()
    provider = AsyncMock()
    provider.generate.return_value = "Use the text record."
    with patch("lib.experts.base.get_llm_client", return_value=provider):
        await CapturedExpert(snapshot).contribute_to_discussion(
            "Reduce repeated input.", "", 1, compact_roundtable=True
        )
    assert snapshot == original
    assert ACCESSIBILITY_CAPABILITY_INSTRUCTIONS in provider.generate.await_args.args[1]
    assert original["system_prompt"] in provider.generate.await_args.args[1]


@pytest.mark.parametrize("use_fallback", [False, True])
@pytest.mark.asyncio
async def test_accessibility_moderator_treats_proposed_commands_as_unverified(
    use_fallback,
):
    provider = AsyncMock()
    provider.generate_json.return_value = {} if use_fallback else _accessibility_brief()
    provider.generate.return_value = "Use a text record.\n\n" + render_compact_ending(
        ACCESSIBILITY_ENDING
    )
    query = "I use dictation and need a reusable starter. No command or alias is configured."
    transcript = [
        {
            "speaker": "Voice advisor",
            "status": "success",
            "text": "Say 'save checkpoint' for automatic saving, then use '/task' to resume.",
        }
    ]
    with patch("lib.services.roundtable_service.get_llm_client", return_value=provider):
        await _generate_consensus(
            query,
            transcript,
            compact_ending=True,
            accessibility_handoff=True,
        )
    structured_call = provider.generate_json.await_args
    assert query in structured_call.args[0]
    assert transcript[0]["text"] in structured_call.args[0]
    assert "Discard unsupported operational claims" in structured_call.args[1]
    assert ACCESSIBILITY_CAPABILITY_INSTRUCTIONS in structured_call.args[1]
    if use_fallback:
        assert query in provider.generate.await_args.args[0]
        assert (
            ACCESSIBILITY_CAPABILITY_INSTRUCTIONS
            in provider.generate.await_args.args[1]
        )
    else:
        provider.generate.assert_not_awaited()


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


@pytest.mark.asyncio
async def test_accessibility_plain_text_fallback_keeps_one_decision_check() -> None:
    provider = AsyncMock()
    incomplete = _accessibility_brief()
    del incomplete["compact_ending"]
    provider.generate_json.return_value = incomplete
    provider.generate.return_value = (
        "## Reusable Starter\n\nStart [task].\n\n"
        + render_compact_ending(ACCESSIBILITY_ENDING)
    )
    with patch("lib.services.roundtable_service.get_llm_client", return_value=provider):
        answer, structured = await _generate_consensus(
            "Build a reusable dictation starter.",
            [],
            compact_ending=True,
            accessibility_handoff=True,
        )

    assert structured is None
    assert answer.count("## Decision Check") == 1
    assert "only when its answer blocks the first trial" in " ".join(
        provider.generate.await_args.args[0].split()
    )
    assert "No decision needed yet" in provider.generate.await_args.args[0]
    assert "Do not require typing" in provider.generate.await_args.args[1]


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


def test_saved_workflow_handoff_survives_exports(tmp_path) -> None:
    from lib.services.roundtable_service import _normalize_workflow_handoff
    from lib.storage import HistoryStore

    panel = get_panel("ai_workflow")
    context = build_advisor_context(panel.id, panel.default_roles)
    brief = _normalize_workflow_handoff(_workflow_brief(), compact_ending=True)
    store = HistoryStore(str(tmp_path / "workflow-handoff"))
    result_id = store.save_result(
        query="Draft release notes from a diff.",
        experts=panel.default_roles,
        responses=[],
        result_type="roundtable",
        advisor_context=context,
        roundtable_data={
            "roles": panel.default_roles,
            "rounds": 1,
            "transcript": [],
            "final_answer": "Workflow handoff",
            "consensus_brief": brief,
        },
    )
    replay = store.get_result_by_id(result_id)
    outputs = [
        build_executive_brief_html(replay),
        build_executive_brief_markdown(replay),
    ]
    for output in outputs:
        for heading in [
            "Task Packet",
            "Review Checklist",
            "Resume Checkpoint",
            "Success Measure",
            "Decision Check",
        ]:
            assert heading in output
        assert "prompt text is not enforcement" in output


def test_saved_accessibility_handoff_survives_exports(tmp_path) -> None:
    from lib.services.roundtable_service import _normalize_accessibility_handoff
    from lib.storage import HistoryStore

    panel = get_panel("accessibility_effort")
    context = build_advisor_context(panel.id, panel.default_roles)
    brief = _normalize_accessibility_handoff(
        _accessibility_brief(), compact_ending=True
    )
    store = HistoryStore(str(tmp_path / "accessibility-handoff"))
    result_id = store.save_result(
        query="Build a reusable dictation starter.",
        experts=panel.default_roles,
        responses=[],
        result_type="roundtable",
        advisor_context=context,
        roundtable_data={
            "roles": panel.default_roles,
            "rounds": 1,
            "transcript": [],
            "final_answer": "Accessibility handoff",
            "consensus_brief": brief,
        },
    )
    replay = store.get_result_by_id(result_id)
    outputs = [
        build_executive_brief_html(replay),
        build_executive_brief_markdown(replay),
    ]
    for output in outputs:
        for heading in [
            "Reusable Starter",
            "Resume Checkpoint",
            "Dictation Fallback",
            "First Trial",
            "Decision Check",
        ]:
            assert heading in output
        assert "Start [task name]" in output
        assert ACCESSIBILITY_ENDING["user_decision"] in output


def test_plain_text_workflow_fallback_survives_exports() -> None:
    final_answer = """## Task Packet

Goal: Draft from the supplied diff. Stop if the diff is missing.

## Review Checklist

- Compare every material claim with the supplied diff; mark missing evidence pending.

## Resume Checkpoint

Record the input, instructions, output location, status, and next review step.

## Success Measure

Compare total human time with a similar manual task and keep only if time is lower with no material errors.

## Decision Check

- **Recommended next step:** Supply one bounded diff.
- **Strongest objection:** Review could cost more than it saves.
- **What remains unknown:** No manual baseline is available.
- **What needs your decision:** Choose the first trial task.
"""
    roles = get_panel("ai_workflow").default_roles
    result = {
        "query": "Delegate release-note drafting",
        "experts": roles,
        "responses": [],
        "result_type": "roundtable",
        "advisor_context": build_advisor_context("ai_workflow", roles),
        "transcript": [],
        "final_answer": final_answer,
    }
    outputs = [
        build_executive_brief_html(result),
        build_executive_brief_markdown(result),
    ]
    for output in outputs:
        for heading in [
            "Saved Plain-Text Handoff",
            "Task Packet",
            "Review Checklist",
            "Resume Checkpoint",
            "Success Measure",
            "Decision Check",
        ]:
            assert heading in output
        assert "Compare total human time" in output
        assert output.count("Supply one bounded diff") == 1


def test_plain_text_accessibility_fallback_survives_exports() -> None:
    final_answer = """## Reusable Starter

Start [task]. Reuse background at [saved reference]. Today: [one outcome]. Next: [one action].

## Resume Checkpoint

RESUME: [task] | Done: [last step] | Next: [one action] | Waiting on: [blocker or none]

## Dictation Fallback

Keep the checkpoint, mark the garbled field [unclear], and repeat only that fragment.

## First Trial

Compare repeated background entries and interactions for one recurring task.

- **Recommended next step:** Try the starter once.
- **Strongest objection:** The first template may omit a needed field.
- **What remains unknown:** The recurring task's exact background fields.
- **What needs your decision:** No decision needed yet.
"""
    roles = get_panel("accessibility_effort").default_roles
    result = {
        "query": "Reduce repeated dictation.",
        "experts": roles,
        "responses": [],
        "result_type": "roundtable",
        "advisor_context": build_advisor_context("accessibility_effort", roles),
        "transcript": [],
        "final_answer": final_answer,
    }
    outputs = [
        build_executive_brief_html(result),
        build_executive_brief_markdown(result),
    ]
    for output in outputs:
        for heading in [
            "Saved Accessibility Handoff",
            "Reusable Starter",
            "Resume Checkpoint",
            "Dictation Fallback",
            "First Trial",
            "Decision Check",
        ]:
            assert heading in output
        assert "repeat only that fragment" in output
        assert output.count("Try the starter once") == 1
        assert "No consensus answer was available" not in output


@pytest.mark.parametrize("panel_id", ["ai_workflow", "accessibility_effort"])
def test_incomplete_fallback_closing_is_preserved_on_export(panel_id) -> None:
    roles = get_panel(panel_id).default_roles
    final_answer = """## Saved Plan

Use the existing task reference.

## Decision Check

- **Recommended next step:** Try the preserved partial recommendation.
- **What remains unknown:** Keep this unresolved field visible.
"""
    assert extract_compact_ending(final_answer) == {}
    result = {
        "query": "Keep my incomplete closing visible.",
        "experts": roles,
        "responses": [],
        "result_type": "roundtable",
        "advisor_context": build_advisor_context(panel_id, roles),
        "transcript": [],
        "final_answer": final_answer,
    }
    for output in (
        build_executive_brief_html(result),
        build_executive_brief_markdown(result),
    ):
        assert output.count("Try the preserved partial recommendation.") == 1
        assert output.count("Keep this unresolved field visible.") == 1
