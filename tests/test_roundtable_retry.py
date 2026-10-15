"""Recover provider failures without paying to regenerate successful answers."""

import copy
import json
import time
from datetime import datetime, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest

import main
from lib.experts import build_advisor_context
from lib.services import retry_roundtable, run_roundtable
from lib.services.roundtable_state import failure_details, normalize_roundtable_state
from lib.services.briefing_service import build_executive_brief_markdown
from tests.test_routes import client, _get_csrf_token

ROLES = ["agriculture", "climate"]
BRIEF = {
    "governing_insight": "Review a bounded change.",
    "executive_summary": ["Keep a recoverable checkpoint."],
    "key_findings": [],
    "recommendations": [],
    "decision_implications": [],
    "limitations": [],
}
WORKFLOW_HANDOFF_BRIEF = {
    "task_packet": (
        "Goal: Delegate only the supplied project task. Input: approved material. "
        "Allowed: produce a reviewable draft. Blocked: irreversible actions. "
        "Deliverable: one draft. Stop if input is missing. Enforce tool limits outside the prompt. "
        "Data boundary: share approved material only."
    ),
    "review_checklist": [
        {
            "check": "Check the draft against its supplied source.",
            "evidence_target": "The source material included with the assignment.",
        },
        {
            "check": "Confirm blocked actions were not taken.",
            "evidence_target": "The reviewable output and tool-enforced boundary.",
        },
    ],
    "resume_checkpoint": (
        "Record: input, instructions, output, status, and next action. "
        "Resume from that record."
    ),
    "success_measure": (
        "Keep only if review and recovery time are lower than the manual baseline "
        "with no material errors."
    ),
    "compact_ending": {
        "recommended_next_step": "Delegate one bounded task.",
        "strongest_objection": "Review may cost more than it saves.",
        "unknowns": "The manual baseline is not measured.",
        "user_decision": "Choose the first task to try.",
    },
}


def _rate_limit(header="60"):
    response = httpx.Response(
        429,
        headers={"Retry-After": header},
        request=httpx.Request("POST", "https://provider.invalid"),
    )
    return httpx.HTTPStatusError(
        "provider rate limit", request=response.request, response=response
    )


def _entry(role, round_num=1, status="success", text=None):
    labels = {
        "agriculture": "Agricultural Science Expert",
        "climate": "Climate Change Impact Analyst",
    }
    return {
        "role": role,
        "speaker": labels[role],
        "round": round_num,
        "status": status,
        "text": text
        or (
            f"Original {role} {round_num}"
            if status == "success"
            else "Error: provider failed"
        ),
    }


def _state(rounds=1):
    return {
        "query": "Original question",
        "roles": ROLES.copy(),
        "rounds": rounds,
        "transcript": [
            _entry(role, round_num)
            for round_num in range(1, rounds + 1)
            for role in ROLES
        ],
        "final_answer": "",
        "advisor_context": build_advisor_context("agriculture", ROLES),
    }


@pytest.mark.asyncio
async def test_retry_only_failed_slots_preserves_answers_and_original_prompts():
    state = _state(2)
    state["transcript"][1] = _entry("climate", 1, "failed")
    state["transcript"][3] = _entry("climate", 2, "failed")
    original = copy.deepcopy(state)
    provider = AsyncMock()
    provider.generate.side_effect = ["Recovered climate one", "Recovered climate two"]
    provider.generate_json.return_value = BRIEF
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await retry_roundtable(state)
    assert state == original
    assert result["transcript"][0] == original["transcript"][0]
    assert result["transcript"][2] == original["transcript"][2]
    assert result["transcript"][1]["text"] == "Recovered climate one"
    assert result["transcript"][3]["text"] == "Recovered climate two"
    assert provider.generate.await_count == 2
    assert provider.generate_json.await_count == 1
    for call in provider.generate.await_args_list:
        assert call.args[1] == state["advisor_context"]["advisors"][1]["system_prompt"]
        assert "Error: provider failed" not in call.args[0]
        assert "Original question" in call.args[0]
    assert "Recovered climate one" in provider.generate.await_args_list[1].args[0]


@pytest.mark.asyncio
async def test_synthesis_only_retry_never_calls_advisors():
    provider = AsyncMock()
    provider.generate_json.return_value = BRIEF
    state = _state()
    with (
        patch("lib.services.roundtable_service.get_llm_client", return_value=provider),
        patch(
            "lib.experts.base.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await retry_roundtable(state)
    provider.generate.assert_not_awaited()
    provider.generate_json.assert_awaited_once()
    assert result["synthesis_error"] is None
    assert result["transcript"] == state["transcript"]


@pytest.mark.asyncio
async def test_empty_plain_text_synthesis_remains_retryable_without_rerunning_advisors():
    provider = AsyncMock()
    provider.generate_json.return_value = {}
    provider.generate.return_value = " \n\t"
    state = _state()
    original = copy.deepcopy(state)
    with (
        patch("lib.services.roundtable_service.get_llm_client", return_value=provider),
        patch(
            "lib.experts.base.get_llm_client",
            side_effect=AssertionError("Advisor must not be called"),
        ),
    ):
        result = await retry_roundtable(state)

    assert result["synthesis_error"]["kind"] == "response"
    assert result["final_answer"] == ""
    assert result["transcript"] == original["transcript"]
    assert state == original
    provider.generate_json.assert_awaited_once()
    provider.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_rate_limit_pauses_unrequested_slots_and_synthesis():
    provider = AsyncMock()
    provider.generate.side_effect = ["Completed first answer", _rate_limit()]
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        partial = await run_roundtable(
            "Question", ["agriculture", "climate", "soil"], 1
        )
    assert [entry["status"] for entry in partial["transcript"]] == [
        "success",
        "failed",
        "pending",
    ]
    assert partial["transcript"][0]["text"] == "Completed first answer"
    provider.generate_json.assert_not_awaited()
    assert provider.generate.await_count == 2
    assert partial["retry_at"] > time.time()
    provider.reset_mock()
    with (
        patch("lib.services.roundtable_service.get_llm_client", return_value=provider),
        patch(
            "lib.experts.base.get_llm_client",
            return_value=provider,
        ),
    ):
        blocked = await retry_roundtable(partial)
    provider.generate.assert_not_awaited()
    provider.generate_json.assert_not_awaited()
    assert blocked == partial


@pytest.mark.asyncio
async def test_synthesis_429_does_not_trigger_text_fallback():
    provider = AsyncMock()
    provider.generate_json.side_effect = _rate_limit()
    state = _state()
    with patch("lib.services.roundtable_service.get_llm_client", return_value=provider):
        result = await retry_roundtable(state)
    provider.generate.assert_not_awaited()
    assert result["synthesis_error"]["kind"] == "rate_limit"
    assert result["transcript"] == state["transcript"]
    assert result["final_answer"] == ""


@pytest.mark.asyncio
async def test_second_rate_limit_still_keeps_all_successful_answers():
    state = _state()
    state["transcript"][1] = _entry("climate", status="failed")
    provider = AsyncMock()
    provider.generate.side_effect = _rate_limit()
    with patch("lib.experts.base.get_llm_client", return_value=provider):
        result = await retry_roundtable(state)
    assert result["transcript"][0] == state["transcript"][0]
    assert result["transcript"][1]["status"] == "failed"
    assert result["retry_at"] > time.time()


@pytest.mark.asyncio
async def test_completed_roundtable_is_noop():
    state = _state()
    state.update(final_answer="Existing synthesis", consensus_brief=BRIEF)
    with patch("lib.services.roundtable_service.get_llm_client") as provider:
        result = await retry_roundtable(state)
    provider.assert_not_called()
    assert result["final_answer"] == "Existing synthesis"


def test_retry_after_seconds_dates_and_default():
    assert 29 <= failure_details(_rate_limit("30"))["retry_at"] - time.time() <= 30
    deadline = int(time.time()) + 120
    header = format_datetime(
        datetime.fromtimestamp(deadline, timezone.utc), usegmt=True
    )
    assert failure_details(_rate_limit(header))["retry_at"] == deadline
    assert 59 <= failure_details(_rate_limit("invalid"))["retry_at"] - time.time() <= 60


def test_partial_export_counts_completed_responses_instead_of_pending_slots():
    state = _state()
    state["transcript"][1].update(status="pending", text="")
    state.update(
        result_type="roundtable",
        experts=ROLES,
        synthesis_error={"kind": "waiting", "message": "Synthesis is waiting."},
    )
    output = build_executive_brief_markdown(state)
    assert "1 of 2 advisor contributions completed" in output
    assert "**Contributions:** 1" in output


@pytest.mark.asyncio
async def test_legacy_saved_failure_can_retry_without_replaying_successes():
    state = _state()
    for entry in state["transcript"]:
        entry.pop("role")
        entry.pop("status")
    state["transcript"][1]["text"] = "Error: 429 Too Many Requests"
    state["final_answer"] = "Error generating consensus: 429 Too Many Requests"
    provider = AsyncMock()
    provider.generate.return_value = "Recovered answer"
    provider.generate_json.return_value = BRIEF
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        result = await retry_roundtable(state)
    provider.generate.assert_awaited_once()
    assert result["transcript"][0]["text"] == state["transcript"][0]["text"]
    assert result["transcript"][1]["text"] == "Recovered answer"
    assert result["synthesis_error"] is None


@pytest.mark.parametrize(
    "change",
    [
        {"rounds": 100},
        {"roles": ["agriculture", "agriculture"]},
        {"query": " "},
        {"transcript": [{"role": "climate", "round": 1, "text": "Wrong slot"}]},
        {"retry_at": float("nan")},
        {"synthesis_error": "bad shape"},
    ],
)
def test_invalid_retry_state_is_rejected(change):
    state = _state()
    state.update(change)
    with pytest.raises(ValueError):
        normalize_roundtable_state(state)


def test_retry_route_csrf_error_keeps_visible_transcript(client):
    _get_csrf_token(client)
    with patch("main.retry_roundtable", new_callable=AsyncMock) as resume:
        response = client.post(
            "/roundtable/retry",
            data={"state": json.dumps(_state()), "csrf_token": "bad"},
        )
    resume.assert_not_awaited()
    assert response.headers["HX-Retarget"] == "#roundtable-retry-status"
    assert "Invalid CSRF" in response.text


def test_saved_partial_roundtable_preserves_retry_state_and_exports(client):
    token = _get_csrf_token(client)
    state = _state()
    state["transcript"][1] = _entry("climate", status="failed")
    state.update(
        synthesis_error={"kind": "rate_limit", "message": "Synthesis is incomplete."},
        retry_at=time.time() + 60,
    )
    result_id = main.history_store.save_result(
        query=state["query"],
        experts=ROLES,
        responses=[],
        result_type="roundtable",
        roundtable_data=state,
        advisor_context=state["advisor_context"],
    )
    saved = main.history_store.get_result_by_id(result_id)
    assert saved["retry_at"] == state["retry_at"]
    assert saved["synthesis_error"] == state["synthesis_error"]
    view = client.get(f"/result/{result_id}")
    assert "Retry failed advisors" in view.text
    assert "data-retry-at" in view.text and "disabled" in view.text
    assert "Synthesis is incomplete." in build_executive_brief_markdown(saved)
    provider = AsyncMock()
    provider.generate.return_value = "Recovered climate answer"
    provider.generate_json.return_value = BRIEF
    state["retry_at"] = 0
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        retried = client.post(
            "/roundtable/retry", data={"state": json.dumps(state), "csrf_token": token}
        )
    assert retried.status_code == 200
    assert "Recovered climate answer" in retried.text
    assert "Original agriculture 1" in retried.text
    assert "Save Result" in retried.text
    assert "Retry failed advisors" not in retried.text
    provider.generate.assert_awaited_once()
    assert (
        main.history_store.get_result_by_id(result_id)["transcript"][1]["status"]
        == "failed"
    )


@pytest.mark.asyncio
async def test_four_saved_answers_survive_real_client_provider_failover():
    import respx
    from lib.engine.llm_client import LLMClient
    from tests.test_llm_client import POOL_ERROR

    roles = [
        "ai_workflow_workflow_designer",
        "ai_workflow_delegation_planner",
        "ai_workflow_privacy_reviewer",
        "ai_workflow_recovery_reviewer",
    ]
    state = {
        "query": "Delegate bounded project work",
        "roles": roles,
        "rounds": 1,
        "transcript": [
            {
                "role": role,
                "speaker": role,
                "round": 1,
                "status": "success",
                "text": f"Preserved answer {i}",
            }
            for i, role in enumerate(roles)
        ],
        "final_answer": "",
        "compact_ending": False,
    }
    original = copy.deepcopy(state)
    provider = LLMClient(
        api_key="test",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model="original-model",
    )
    with (
        respx.mock as router,
        patch("lib.services.roundtable_service.get_llm_client", return_value=provider),
        patch(
            "lib.experts.base.get_llm_client",
            side_effect=AssertionError("Advisor must not be called"),
        ),
    ):
        route = router.post(provider.api_url).mock(
            side_effect=[
                httpx.Response(429, json=POOL_ERROR),
                httpx.Response(
                    200,
                    json={
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(WORKFLOW_HANDOFF_BRIEF)
                                }
                            }
                        ]
                    },
                ),
            ]
        )
        result = await retry_roundtable(state)
    await provider.close()
    assert route.call_count == 2
    assert result["synthesis_error"] is None
    assert result["final_answer"]
    assert result["consensus_brief"]["synthesis_format"] == "workflow_handoff"
    assert result["transcript"] == original["transcript"]
    assert state == original
    assert all(
        "Preserved answer" in json.loads(call.request.content)["messages"][1]["content"]
        for call in route.calls
    )


def test_shared_capacity_failure_explains_timer_without_raw_provider_details():
    from tests.test_llm_client import POOL_ERROR

    response = httpx.Response(
        429, json=POOL_ERROR, request=httpx.Request("POST", "https://provider.invalid")
    )
    error = httpx.HTTPStatusError(
        "rate limit", request=response.request, response=response
    )
    details = failure_details(error)
    assert "shared capacity" in details["message"]
    assert "not a confirmed recovery time" in details["message"]
    assert "raw" not in details
    assert "provider details" not in details["message"]
