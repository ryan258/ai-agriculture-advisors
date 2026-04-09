"""Tests for FastAPI routes."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import main
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
    assert "Agri Advisors" in response.text
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
        "Test query", ["agriculture", "climate"], 2
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
        "Test query", ["agriculture", "climate"], expected_rounds
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
