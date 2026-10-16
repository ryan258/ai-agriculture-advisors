"""Captured summaries remain read-only and tolerate missing legacy fields."""

import copy

from lib.experts.response_format import render_compact_ending
from lib.services.result_view import history_page, result_summary
from jinja2 import Environment, FileSystemLoader, select_autoescape

ENDING = {
    "recommended_next_step": "Try the supplied starter.",
    "strongest_objection": "The current setup is not confirmed.",
    "unknowns": "Where the checkpoint will be saved.",
    "user_decision": "No decision needed yet.",
}


def test_summary_preserves_captured_handoff_and_stale_provenance() -> None:
    result = {
        "result_type": "roundtable",
        "synthesis_stale": True,
        "final_answer": "The original synthesis text remains unchanged.",
        "consensus_brief": {
            "synthesis_format": "accessibility_handoff",
            "starter_template": "Task: supplied wording, not an installed command.",
            "resume_checkpoint": "Next: review the supplied excerpt.",
            "compact_ending": ENDING.copy(),
        },
    }
    original = copy.deepcopy(result)
    summary = result_summary(result)
    assert result == original
    assert summary["is_stale"] is True
    assert summary["copy_text"] == result["consensus_brief"]["starter_template"]
    assert [point["text"] for point in summary["checks"][0]["points"]] == list(
        ENDING.values()
    )
    assert len(summary["handoff"]) == 2


def test_legacy_text_without_complete_closing_is_not_invented_or_removed() -> None:
    result = {
        "result_type": "roundtable",
        "final_answer": "Partial record\n- **Recommended next step:** Keep this text.",
    }
    original = result.copy()
    summary = result_summary(result)
    assert summary["checks"] == []
    assert summary["handoff"] == []
    assert summary["copy_text"] == ""
    assert result == original


def test_individual_closings_keep_their_advisor_attribution() -> None:
    result = {
        "result_type": "query",
        "responses": [
            {"label": "First advisor", "response": render_compact_ending(ENDING)},
            {"label": "Second advisor", "response": "No structured closing here."},
        ],
    }
    summary = result_summary(result)
    assert [check["label"] for check in summary["checks"]] == ["First advisor"]
    assert summary["is_stale"] is False


def test_history_page_does_not_expose_lookahead_as_a_visible_item() -> None:
    rows = [{"id": str(index)} for index in range(11)]
    page = history_page(rows, "older question", 20)
    assert page["history"] == rows[:10]
    assert page["has_more"] is True
    assert page["offset"] == 20
    assert page["q"] == "older question"
    assert history_page(rows[:3], "", 0)["has_more"] is False


def test_mixed_individual_failures_stay_visible_beside_a_successful_summary() -> None:
    responses = [
        {"label": "Completed advisor", "response": render_compact_ending(ENDING)},
        {"label": "Failed advisor", "error": "The provider connection failed."},
    ]
    environment = Environment(
        loader=FileSystemLoader("templates"), autoescape=select_autoescape()
    )
    html = environment.get_template("partials/responses.html").render(
        query="A mixed result",
        responses=responses,
        result_id=None,
        csrf_token="test-token",
        advisor_context=None,
        result_summary=result_summary({"result_type": "query", "responses": responses}),
    )
    assert '<details class="transcript-details" open>' in html
    assert "The provider connection failed." in html
