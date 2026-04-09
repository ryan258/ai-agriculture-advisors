"""Tests for the service layer."""

import pytest
from unittest.mock import AsyncMock, patch

from lib.services.query_service import query_experts, query_single_expert
from lib.services.roundtable_service import run_roundtable


@pytest.mark.asyncio
async def test_query_single_expert_invalid_role() -> None:
    """Test querying an invalid expert role."""
    result = await query_single_expert("invalid_role", "Test query")

    assert result["role"] == "invalid_role"
    assert "error" in result
    assert "Unknown expert role" in result["error"]


@pytest.mark.asyncio
async def test_query_experts_empty_roles() -> None:
    """Test querying with empty roles list."""
    result = await query_experts("Test query", [])

    assert result["query"] == "Test query"
    assert result["responses"] == []


@pytest.mark.asyncio
@patch("lib.services.query_service.get_expert")
async def test_query_experts_success(mock_get_expert: AsyncMock) -> None:
    """Test successful parallel expert query."""
    # Create mock expert
    mock_expert = AsyncMock()
    mock_expert.role = "agriculture"
    mock_expert.label = "Agricultural Science Expert"
    mock_expert.query = AsyncMock(return_value="Mock response")
    mock_get_expert.return_value = mock_expert

    result = await query_experts("Test query", ["agriculture"])

    assert result["query"] == "Test query"
    assert len(result["responses"]) == 1
    assert result["responses"][0]["role"] == "agriculture"
    assert result["responses"][0]["response"] == "Mock response"


@pytest.mark.asyncio
async def test_roundtable_requires_two_experts() -> None:
    """Test that roundtable requires at least 2 experts."""
    result = await run_roundtable("Test query", ["agriculture"], rounds=2)

    assert "error" in result
    assert "At least 2 experts" in result["error"]


@pytest.mark.asyncio
@patch("lib.services.roundtable_service.get_expert")
@patch("lib.services.roundtable_service.get_llm_client")
async def test_roundtable_builds_transcript(
    mock_get_llm_client: AsyncMock, mock_get_expert: AsyncMock
) -> None:
    """Test that roundtable builds a transcript."""
    # Create mock experts
    mock_expert1 = AsyncMock()
    mock_expert1.role = "agriculture"
    mock_expert1.label = "Agricultural Science Expert"
    mock_expert1.contribute_to_discussion = AsyncMock(return_value="Expert 1 response")

    mock_expert2 = AsyncMock()
    mock_expert2.role = "climate"
    mock_expert2.label = "Climate Change Impact Analyst"
    mock_expert2.contribute_to_discussion = AsyncMock(return_value="Expert 2 response")

    def get_expert_side_effect(role: str) -> AsyncMock:
        if role == "agriculture":
            return mock_expert1
        elif role == "climate":
            return mock_expert2
        return None

    mock_get_expert.side_effect = get_expert_side_effect
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(
        return_value={
            "governing_insight": "Pair monitoring with drought-tolerant crops.",
            "executive_summary": ["Water discipline should come first."],
            "key_findings": [
                {
                    "title": "Water discipline",
                    "claim": "Soil moisture tracking should precede expansion.",
                    "evidence_points": ["Experts aligned on irrigation discipline."],
                    "implication": "Prioritize instrumentation before acreage growth.",
                }
            ],
            "decision_implications": ["Expansion should wait for water data."],
            "recommendations": [
                {
                    "owner": "Producers",
                    "action": "Install moisture sensors.",
                    "expected_impact": "Better irrigation timing.",
                    "key_risk": "Weak sensor placement reduces value.",
                }
            ],
            "limitations": ["No farm-level cost data was discussed."],
        }
    )
    mock_get_llm_client.return_value = mock_llm

    result = await run_roundtable("Test query", ["agriculture", "climate"], rounds=1)

    assert "transcript" in result
    assert len(result["transcript"]) == 2  # 2 experts x 1 round
    assert result["transcript"][0]["speaker"] == "Agricultural Science Expert"
    assert result["transcript"][1]["speaker"] == "Climate Change Impact Analyst"
    assert "final_answer" in result
    assert result["consensus_brief"]["governing_insight"] == (
        "Pair monitoring with drought-tolerant crops."
    )
    assert "## Governing Insight" in result["final_answer"]


@pytest.mark.asyncio
@patch("lib.services.roundtable_service.get_expert")
@patch("lib.services.roundtable_service.get_llm_client")
async def test_roundtable_multiple_rounds(
    mock_get_llm_client: AsyncMock, mock_get_expert: AsyncMock
) -> None:
    """Test roundtable with multiple rounds."""
    mock_expert = AsyncMock()
    mock_expert.role = "agriculture"
    mock_expert.label = "Expert"
    mock_expert.contribute_to_discussion = AsyncMock(return_value="Response")
    mock_get_expert.return_value = mock_expert
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(
        return_value={
            "governing_insight": "Consensus",
            "executive_summary": ["Summary"],
            "key_findings": [],
            "decision_implications": [],
            "recommendations": [],
            "limitations": [],
        }
    )
    mock_get_llm_client.return_value = mock_llm

    result = await run_roundtable("Test query", ["agriculture", "climate"], rounds=3)

    # 2 experts x 3 rounds = 6 transcript entries
    assert len(result["transcript"]) == 6
    assert result["rounds"] == 3
    assert result["consensus_brief"]["governing_insight"] == "Consensus"


@pytest.mark.asyncio
@patch("lib.services.roundtable_service.get_expert")
@patch("lib.services.roundtable_service.get_llm_client")
async def test_roundtable_falls_back_to_text_consensus_on_structured_error(
    mock_get_llm_client: AsyncMock,
    mock_get_expert: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test structured consensus failures fall back to plain-text synthesis."""
    mock_expert = AsyncMock()
    mock_expert.role = "agriculture"
    mock_expert.label = "Expert"
    mock_expert.contribute_to_discussion = AsyncMock(return_value="Response")
    mock_get_expert.return_value = mock_expert
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(side_effect=ValueError("bad schema response"))
    mock_llm.generate = AsyncMock(return_value="Fallback consensus")
    mock_get_llm_client.return_value = mock_llm

    with caplog.at_level("WARNING"):
        result = await run_roundtable(
            "Test query", ["agriculture", "climate"], rounds=1
        )

    assert result["final_answer"] == "Fallback consensus"
    assert result["consensus_brief"] is None
    assert "Structured consensus generation failed" in caplog.text


@pytest.mark.asyncio
@patch("lib.services.roundtable_service.get_expert")
@patch("lib.services.roundtable_service.get_llm_client")
async def test_roundtable_falls_back_when_structured_consensus_is_semantically_empty(
    mock_get_llm_client: AsyncMock, mock_get_expert: AsyncMock
) -> None:
    """Test empty structured payloads degrade to the plain-text fallback."""
    mock_expert = AsyncMock()
    mock_expert.role = "agriculture"
    mock_expert.label = "Expert"
    mock_expert.contribute_to_discussion = AsyncMock(return_value="Response")
    mock_get_expert.return_value = mock_expert
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(
        return_value={
            "governing_insight": "",
            "executive_summary": [],
            "key_findings": [],
            "decision_implications": [],
            "recommendations": [],
            "limitations": [],
        }
    )
    mock_llm.generate = AsyncMock(return_value="Fallback consensus")
    mock_get_llm_client.return_value = mock_llm

    result = await run_roundtable("Test query", ["agriculture", "climate"], rounds=1)

    assert result["final_answer"] == "Fallback consensus"
    assert result["consensus_brief"] is None


@pytest.mark.asyncio
@patch("lib.services.roundtable_service.get_expert")
@patch("lib.services.roundtable_service.get_llm_client")
async def test_roundtable_flattens_dict_items_from_schema_violations(
    mock_get_llm_client: AsyncMock, mock_get_expert: AsyncMock
) -> None:
    """Dict items returned for string fields should be flattened before persistence."""
    mock_expert = AsyncMock()
    mock_expert.role = "commodities"
    mock_expert.label = "Commodities Expert"
    mock_expert.contribute_to_discussion = AsyncMock(return_value="Response")
    mock_get_expert.return_value = mock_expert
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(
        return_value={
            "governing_insight": "Favor structures with defined risk.",
            "executive_summary": ["Keep tail risk bounded."],
            "key_findings": [],
            "decision_implications": [
                {
                    "tradeoff": "Directional outrights vs. relative-value structures",
                    "detail": "Outrights are exposed to ENSO-transition failure.",
                    "impact_on_execution": "Favor spreads with defined max loss.",
                }
            ],
            "recommendations": [],
            "limitations": [],
        }
    )
    mock_get_llm_client.return_value = mock_llm

    result = await run_roundtable("Test query", ["commodities", "climate"], rounds=1)

    implications = result["consensus_brief"]["decision_implications"]
    assert implications
    assert all(isinstance(item, str) for item in implications)
    assert "Directional outrights vs. relative-value structures" in implications[0]
    assert "Favor spreads with defined max loss." in implications[0]
    assert "{'tradeoff'" not in implications[0]
