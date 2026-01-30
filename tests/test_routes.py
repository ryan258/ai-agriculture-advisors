"""Tests for FastAPI routes."""

import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    os.environ.setdefault("ALLOW_MISSING_API_KEY", "true")
    return TestClient(app)


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
    response = client.post("/query", data={"query": "Test query", "csrf_token": csrf_token})
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
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert "Roundtable Discussion" in response.text
    assert "Consensus" in response.text


def test_history_endpoint(client: TestClient) -> None:
    """Test history endpoint returns HTML."""
    response = client.get("/history")
    assert response.status_code == 200


def test_export_not_found(client: TestClient) -> None:
    """Test export endpoint with invalid ID."""
    response = client.get("/export/invalid-id")
    assert response.status_code == 404


def test_result_not_found(client: TestClient) -> None:
    """Test result endpoint with invalid ID."""
    response = client.get("/result/invalid-id")
    assert response.status_code == 200
    assert "not found" in response.text.lower()
