"""Tests for FastAPI routes."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from lib.experts import build_advisor_context, expert_registry
from lib.experts.catalog import AdvisorDefinition, ConfiguredExpert
from lib.engine.config import get_settings
from lib.storage import HistoryStore


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a test client with isolated storage and rate-limit state."""
    os.environ["ALLOW_MISSING_API_KEY"] = "true"
    get_settings.cache_clear()
    main.app.state.limiter._storage.reset()
    monkeypatch.setattr(
        main, "history_store", HistoryStore(str(tmp_path / "chromadb-test"))
    )
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.state.limiter._storage.reset()


def _get_csrf_token(client: TestClient) -> str:
    response = client.get("/")
    assert response.status_code == 200
    token = client.cookies.get("csrf_token")
    assert token
    return token


def test_index_page(client: TestClient) -> None:
    """Test that the index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Advisors" in response.text
    assert "Agricultural Science" in response.text


def test_index_shows_all_experts(client: TestClient) -> None:
    """Test that all experts are shown on the index page."""
    response = client.get("/")
    assert response.status_code == 200

    expected_experts = [
        "Agricultural Science",
        "Climate",
        "Commodities",
        "AgriTech",
        "Supply Chain",
        "Soil Health",
        "Pest",
        "Irrigation",
        "Organic",
        "Economics",
    ]

    for expert in expected_experts:
        assert expert in response.text, f"Missing expert: {expert}"


def test_query_requires_experts(client: TestClient) -> None:
    """Test that query endpoint requires at least one expert."""
    csrf_token = _get_csrf_token(client)
    response = client.post(
        "/query", data={"query": "Test query", "csrf_token": csrf_token}
    )
    assert response.status_code == 200
    assert "select at least one expert" in response.text.lower()


def test_query_requires_query_text(client: TestClient) -> None:
    """Test that query endpoint requires non-empty query text."""
    csrf_token = _get_csrf_token(client)
    # Test with whitespace-only query (passes Form validation but fails our check)
    response = client.post(
        "/query",
        data={
            "query": "   ",
            "roles": "agriculture",
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 200
    assert "enter a query" in response.text.lower()


def test_roundtable_requires_two_experts(client: TestClient) -> None:
    """Test that roundtable requires at least 2 experts."""
    csrf_token = _get_csrf_token(client)
    response = client.post(
        "/roundtable",
        data={"query": "Test query", "roles": "agriculture", "csrf_token": csrf_token},
    )
    assert response.status_code == 200
    assert "at least 2 experts" in response.text.lower()


@patch("main.query_experts")
def test_query_success(mock_query: AsyncMock, client: TestClient) -> None:
    """Test successful query."""
    csrf_token = _get_csrf_token(client)
    mock_query.return_value = {
        "query": "Test query",
        "responses": [
            {
                "role": "agriculture",
                "label": "Agricultural Science Expert",
                "response": "Test response",
            }
        ],
    }

    response = client.post(
        "/query",
        data={"query": "Test query", "roles": "agriculture", "csrf_token": csrf_token},
    )

    assert response.status_code == 200
    assert "Test response" in response.text
    assert "Agricultural Science Expert" in response.text


@patch("main.run_roundtable")
def test_roundtable_success(mock_roundtable: AsyncMock, client: TestClient) -> None:
    """Test successful roundtable."""
    csrf_token = _get_csrf_token(client)
    mock_roundtable.return_value = {
        "query": "Test query",
        "roles": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [
            {
                "speaker": "Agricultural Science Expert",
                "text": "Expert 1 says...",
                "round": 1,
            },
            {
                "speaker": "Climate Change Impact Analyst",
                "text": "Expert 2 says...",
                "round": 1,
            },
        ],
        "final_answer": "Consensus answer",
    }

    response = client.post(
        "/roundtable",
        data={
            "query": "Test query",
            "roles": ["agriculture", "climate"],
            "rounds": 2,
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert "Roundtable Discussion" in response.text
    assert "Consensus" in response.text
    mock_roundtable.assert_awaited_once_with(
        "Test query",
        ["agriculture", "climate"],
        2,
        advisor_context=build_advisor_context(
            "agriculture", ["agriculture", "climate"]
        ),
    )


@pytest.mark.parametrize(
    ("submitted_rounds", "expected_rounds"),
    [(0, 1), (1000, 5)],
)
@patch("main.run_roundtable")
def test_roundtable_clamps_rounds_to_supported_bounds(
    mock_roundtable: AsyncMock,
    client: TestClient,
    submitted_rounds: int,
    expected_rounds: int,
) -> None:
    """Test that roundtable rounds are clamped to the supported range."""
    csrf_token = _get_csrf_token(client)
    mock_roundtable.return_value = {
        "query": "Test query",
        "roles": ["agriculture", "climate"],
        "rounds": expected_rounds,
        "transcript": [],
        "final_answer": "Consensus answer",
    }

    response = client.post(
        "/roundtable",
        data={
            "query": "Test query",
            "roles": ["agriculture", "climate"],
            "rounds": submitted_rounds,
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    mock_roundtable.assert_awaited_once_with(
        "Test query",
        ["agriculture", "climate"],
        expected_rounds,
        advisor_context=build_advisor_context(
            "agriculture", ["agriculture", "climate"]
        ),
    )


@patch("main.get_all_experts", side_effect=RuntimeError("boom"))
def test_index_handles_load_error(mock_get_all_experts, client: TestClient) -> None:
    """Test that index failures degrade to the error partial."""
    response = client.get("/")

    assert response.status_code == 500
    assert "failed to load application" in response.text.lower()
    assert "boom" in response.text
    mock_get_all_experts.assert_called_once()


def test_history_endpoint(client: TestClient) -> None:
    """Test history endpoint returns HTML."""
    response = client.get("/history")
    assert response.status_code == 200


def test_history_endpoint_handles_store_error(client: TestClient) -> None:
    """Test history failures degrade to the error partial."""
    with patch.object(
        main.history_store, "get_history", side_effect=RuntimeError("boom")
    ):
        response = client.get("/history")

    assert response.status_code == 500
    assert "failed to load history" in response.text.lower()
    assert "boom" in response.text


def test_export_not_found(client: TestClient) -> None:
    """Test export endpoint with invalid ID."""
    response = client.get("/export/invalid-id")
    assert response.status_code == 404
    assert "Result Not Found" in response.text


def test_brief_export_not_found(client: TestClient) -> None:
    """Test brief export endpoint with invalid ID."""
    response = client.get("/export/invalid-id/brief")
    assert response.status_code == 404
    assert "not found" in response.text.lower()


def test_result_not_found(client: TestClient) -> None:
    """Test result endpoint with invalid ID."""
    response = client.get("/result/invalid-id")
    assert response.status_code == 404
    assert "not found" in response.text.lower()


def test_result_handles_store_error(client: TestClient) -> None:
    """Test result lookup failures degrade to the error partial."""
    with patch.object(
        main.history_store, "get_result_by_id", side_effect=RuntimeError("boom")
    ):
        response = client.get("/result/abc12345")

    assert response.status_code == 500
    assert "failed to load result" in response.text.lower()
    assert "boom" in response.text


def test_export_handles_store_error(client: TestClient) -> None:
    """Test export failures degrade to the error partial."""
    with patch.object(
        main.history_store, "get_result_by_id", side_effect=RuntimeError("boom")
    ):
        response = client.get("/export/abc12345")

    assert response.status_code == 500
    assert "failed to export result" in response.text.lower()
    assert "boom" in response.text


@patch(
    "main.build_executive_brief_html", return_value="<html><body>Brief</body></html>"
)
def test_brief_export_success(mock_render_brief, client: TestClient) -> None:
    """Test successful executive brief export."""
    result_id = main.history_store.save_result(
        query="How do I reduce drought risk?",
        experts=["agriculture"],
        responses=[
            {
                "role": "agriculture",
                "label": "Agricultural Science Expert",
                "response": "Start with soil tests.",
            }
        ],
        result_type="query",
    )

    response = client.get(f"/export/{result_id}/brief")

    assert response.status_code == 200
    assert response.text == "<html><body>Brief</body></html>"
    mock_render_brief.assert_called_once()


def test_brief_export_handles_store_error(client: TestClient) -> None:
    """Test executive brief export failures degrade to the error partial."""
    with patch.object(
        main.history_store, "get_result_by_id", side_effect=RuntimeError("boom")
    ):
        response = client.get("/export/abc12345/brief")

    assert response.status_code == 500
    assert "failed to build executive brief" in response.text.lower()
    assert "boom" in response.text


def test_brief_export_renders_saved_structured_roundtable(client: TestClient) -> None:
    """Test brief export uses persisted structured consensus for roundtables."""
    result_id = main.history_store.save_result(
        query="How should drought planning prioritize?",
        experts=["agriculture", "climate"],
        responses=[],
        result_type="roundtable",
        roundtable_data={
            "roles": ["agriculture", "climate"],
            "rounds": 2,
            "transcript": [
                {
                    "speaker": "Agricultural Science Expert",
                    "text": "Start with soil moisture tracking.",
                    "round": 1,
                }
            ],
            "final_answer": "Legacy fallback that should not drive the brief.",
            "consensus_brief": {
                "governing_insight": "Protect water first, then expand.",
                "executive_summary": [
                    "Irrigation visibility should precede expansion."
                ],
                "key_findings": [
                    {
                        "title": "Water discipline",
                        "claim": "Instrumentation comes before acreage growth.",
                        "evidence_points": ["The experts aligned on sequencing."],
                        "implication": "Avoid capital expansion without telemetry.",
                    }
                ],
                "decision_implications": [
                    "Expansion timing depends on water data quality."
                ],
                "recommendations": [
                    {
                        "owner": "Producers",
                        "action": "Install moisture sensors.",
                        "expected_impact": "Tighter irrigation windows.",
                        "key_risk": "Poor calibration weakens decisions.",
                    }
                ],
                "limitations": [
                    "The roundtable did not quantify local payback periods."
                ],
            },
        },
    )

    response = client.get(f"/export/{result_id}/brief")

    assert response.status_code == 200
    assert "Protect water first, then expand." in response.text
    assert "Install moisture sensors." in response.text
    assert "Legacy fallback that should not drive the brief." not in response.text


def test_query_rejects_invalid_csrf(client: TestClient) -> None:
    """Test that invalid CSRF tokens are rejected."""
    _get_csrf_token(client)
    response = client.post(
        "/query",
        data={
            "query": "Test query",
            "roles": "agriculture",
            "csrf_token": "invalid-token",
        },
    )
    assert response.status_code == 200
    assert "invalid csrf token" in response.text.lower()


def test_save_query_result_success(client: TestClient) -> None:
    """Test saving a standard query result."""
    csrf_token = _get_csrf_token(client)
    responses = [
        {
            "role": "agriculture",
            "label": "Agricultural Science Expert",
            "response": "Use a rotation plan.",
        }
    ]

    with patch.object(
        main.history_store, "save_result", return_value="abc12345"
    ) as mock_save:
        response = client.post(
            "/save",
            data={
                "query": "How do I protect yield?",
                "responses": json.dumps(responses),
                "result_type": "query",
                "csrf_token": csrf_token,
            },
        )

    assert response.status_code == 200
    assert "Saved" in response.text
    assert "/export/abc12345/brief" in response.text
    assert "/export/abc12345" in response.text
    mock_save.assert_called_once_with(
        query="How do I protect yield?",
        experts=["agriculture"],
        responses=responses,
        result_type="query",
    )


def test_save_roundtable_result_success(client: TestClient) -> None:
    """Test saving a roundtable result."""
    csrf_token = _get_csrf_token(client)
    roundtable_data = {
        "roles": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [
            {
                "speaker": "Agricultural Science Expert",
                "text": "Start with soil tests.",
                "round": 1,
            }
        ],
        "final_answer": "Balance irrigation with soil monitoring.",
    }

    with patch.object(
        main.history_store, "save_result", return_value="def67890"
    ) as mock_save:
        response = client.post(
            "/save",
            data={
                "query": "How should I manage drought risk?",
                "result_type": "roundtable",
                "roundtable_data": json.dumps(roundtable_data),
                "csrf_token": csrf_token,
            },
        )

    assert response.status_code == 200
    assert "Saved" in response.text
    assert "Participants" in response.text
    assert "/export/def67890/brief" in response.text
    mock_save.assert_called_once_with(
        query="How should I manage drought risk?",
        experts=["agriculture", "climate"],
        responses=[],
        result_type="roundtable",
        roundtable_data=roundtable_data,
    )


@pytest.mark.parametrize(
    ("result_type", "header_class", "title_id"),
    [
        ("query", "responses-header", "responses-title"),
        ("roundtable", "roundtable-header", "roundtable-title"),
    ],
)
def test_save_and_replay_keep_named_header_and_both_exports(
    client: TestClient, result_type: str, header_class: str, title_id: str
) -> None:
    csrf_token = _get_csrf_token(client)
    result_id = "controls123"
    query = "A fictional saved-result controls check."
    roles = (
        ["agriculture", "climate"] if result_type == "roundtable" else ["agriculture"]
    )
    responses = [
        {
            "role": "agriculture",
            "label": "Agricultural Science Expert",
            "response": "Preserved answer.",
        }
    ]
    roundtable = {
        "roles": roles,
        "rounds": 1,
        "transcript": [
            {
                "role": role,
                "speaker": role,
                "round": 1,
                "status": "success",
                "text": "Preserved answer.",
            }
            for role in roles
        ],
        "final_answer": "Preserved synthesis.",
    }
    record = {
        "id": result_id,
        "query": query,
        "result_type": result_type,
        "experts": roles,
        "responses": responses if result_type == "query" else [],
        **(roundtable if result_type == "roundtable" else {}),
    }
    payload = {"query": query, "result_type": result_type, "csrf_token": csrf_token}
    if result_type == "roundtable":
        payload["roundtable_data"] = json.dumps(roundtable)
    else:
        payload["responses"] = json.dumps(responses)
    with (
        patch.object(main.history_store, "save_result", return_value=result_id) as save,
        patch.object(main.history_store, "get_result_by_id", return_value=record),
        patch("main.run_roundtable", new_callable=AsyncMock) as run,
        patch("main.query_experts", new_callable=AsyncMock) as ask,
    ):
        saved = client.post("/save", data=payload)
        reopened = client.get(f"/result/{result_id}")
    assert saved.status_code == reopened.status_code == 200
    for html in (saved.text, reopened.text):
        assert f'<div class="{header_class}">' in html
        assert f'<h2 id="{title_id}">' in html
        assert f'href="/export/{result_id}/brief"' in html
        assert f'href="/export/{result_id}"' in html
    assert f'aria-labelledby="{title_id}"' in reopened.text
    assert "Preserved answer." in reopened.text
    save.assert_called_once()
    run.assert_not_awaited()
    ask.assert_not_awaited()


@patch("main.query_experts")
def test_query_rate_limit_enforced(mock_query: AsyncMock, client: TestClient) -> None:
    """Test that slowapi rejects requests above the configured threshold."""
    csrf_token = _get_csrf_token(client)
    mock_query.return_value = {
        "query": "Test query",
        "responses": [
            {
                "role": "agriculture",
                "label": "Agricultural Science Expert",
                "response": "Test response",
            }
        ],
    }

    for _ in range(30):
        response = client.post(
            "/query",
            data={
                "query": "Test query",
                "roles": "agriculture",
                "csrf_token": csrf_token,
            },
        )
        assert response.status_code == 200

    limited_response = client.post(
        "/query",
        data={
            "query": "Test query",
            "roles": "agriculture",
            "csrf_token": csrf_token,
        },
    )

    assert limited_response.status_code == 429


@pytest.mark.parametrize("endpoint", ["/query", "/roundtable"])
def test_invalid_panel_roles_do_not_call_provider(endpoint, client: TestClient) -> None:
    csrf_token = _get_csrf_token(client)
    with (
        patch("main.query_experts") as query_mock,
        patch("main.run_roundtable") as rt_mock,
    ):
        response = client.post(
            endpoint,
            data={
                "query": "Review this",
                "roles": ["soil", "climate"],
                "panel_id": "software",
                "csrf_token": csrf_token,
            },
        )
    assert response.status_code == 400
    query_mock.assert_not_called()
    rt_mock.assert_not_called()


@pytest.mark.parametrize("result_type", ["query", "roundtable"])
def test_software_generation_save_reload_and_export_snapshot(
    result_type: str,
    client: TestClient,
    monkeypatch,
) -> None:
    csrf_token = _get_csrf_token(client)
    roles = ["software_architecture", "software_testing"]
    context = build_advisor_context("software", roles)
    provider = AsyncMock()
    provider.generate.return_value = "Start with one module and targeted checks."
    provider.generate_json.return_value = {
        "governing_insight": "Start small.",
        "executive_summary": ["One module is enough."],
        "decision_implications": ["Deployment constraints remain unresolved."],
        "limitations": ["The source code was not supplied."],
    }
    with (
        patch("lib.experts.base.get_llm_client", return_value=provider),
        patch(
            "lib.services.roundtable_service.get_llm_client",
            return_value=provider,
        ),
    ):
        generated = client.post(
            f"/{result_type}",
            data={
                "query": "How should I structure this tool?",
                "roles": roles,
                "panel_id": "software",
                "rounds": 1,
                "csrf_token": csrf_token,
            },
        )
    assert generated.status_code == 200
    assert "Software panel" in generated.text
    assert "software_architecture" in generated.text
    if result_type == "roundtable":
        assert "unresolved" in generated.text
        prompt = provider.generate_json.await_args.args[1]
        assert "agricultural" not in prompt
        assert "Do not force agreement" in prompt

    # Capture the real Save button payload, including the original snapshot.
    from html.parser import HTMLParser

    class SaveButtonParser(HTMLParser):
        payload = ""

        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if values.get("hx-post") == "/save":
                self.payload = values["hx-vals"]

    parser = SaveButtonParser()
    parser.feed(generated.text)
    context_json = parser.payload.split("advisor_context: JSON.stringify(", 1)[1].split(
        "), csrf_token:" if result_type == "query" else "), roundtable_data:",
        1,
    )[0]
    assert json.loads(context_json) == context
    monkeypatch.setitem(
        expert_registry,
        roles[0],
        ConfiguredExpert(
            AdvisorDefinition(
                role=roles[0],
                label="Changed advisor",
                system_prompt="New instructions",
                limitations="New limits",
            )
        ),
    )
    data = {
        "query": "How should I structure this tool?",
        "result_type": result_type,
        "csrf_token": csrf_token,
        "advisor_context": context_json,
    }
    if result_type == "query":
        data["responses"] = json.dumps(
            [
                {"role": role, "label": item["label"], "response": "Start small."}
                for role, item in zip(roles, context["advisors"])
            ]
        )
    else:
        data["roundtable_data"] = json.dumps(
            {
                "roles": roles,
                "rounds": 1,
                "transcript": [],
                "final_answer": "Start small.",
            }
        )
    response = client.post("/save", data=data)
    assert "Saved" in response.text
    saved_id = main.history_store.get_history()[0]["id"]
    saved = main.history_store.get_result_by_id(saved_id)
    assert saved["advisor_context"] == context
    for path in [
        f"/result/{saved_id}",
        f"/export/{saved_id}",
        f"/export/{saved_id}/brief",
    ]:
        replay = client.get(path)
        assert replay.status_code == 200
        assert "Software Architecture Advisor" in replay.text
        assert "Changed advisor" not in replay.text
        assert (
            "Advisor definitions" in replay.text or "Advisor Definitions" in replay.text
        )


def test_legacy_history_has_no_invented_advisor_snapshot(client: TestClient) -> None:
    saved_id = main.history_store.save_result(
        query="Old farm question",
        experts=["agriculture"],
        responses=[
            {
                "role": "agriculture",
                "label": "Original farm advisor",
                "response": "Old answer",
            }
        ],
    )
    for path in [
        f"/result/{saved_id}",
        f"/export/{saved_id}",
        f"/export/{saved_id}/brief",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert "definitions were not captured" in response.text
