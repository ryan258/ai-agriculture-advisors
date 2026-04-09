"""Tests for the ChromaDB-backed history store."""

from __future__ import annotations

import importlib
from pathlib import Path

from lib.services import build_executive_brief_markdown
from lib.storage import HistoryStore

history_store_module = importlib.import_module("lib.storage.history_store")


def _build_fake_datetime(*timestamps: str):
    """Create a fresh deterministic datetime stub for one test."""

    class _FakeDateTime:
        _timestamps = iter(timestamps)

        @classmethod
        def now(cls) -> "_FakeDateTime":
            instance = cls()
            instance._value = next(cls._timestamps)
            return instance

        def isoformat(self) -> str:
            return self._value

    return _FakeDateTime


def test_history_store_saves_and_lists_results(tmp_path: Path, monkeypatch) -> None:
    """Test saving results and retrieving history in reverse chronological order."""
    monkeypatch.setattr(
        history_store_module,
        "datetime",
        _build_fake_datetime("2026-04-01T10:00:00", "2026-04-01T10:05:00"),
    )
    store = HistoryStore(str(tmp_path / "chromadb"))

    first_id = store.save_result(
        query="First question",
        experts=["agriculture"],
        responses=[{"role": "agriculture", "response": "First response"}],
    )
    second_id = store.save_result(
        query="Second question",
        experts=["climate"],
        responses=[{"role": "climate", "response": "Second response"}],
    )

    history = store.get_history(limit=10)

    assert len(history) == 2
    assert history[0]["id"] == second_id
    assert history[1]["id"] == first_id
    assert history[0]["experts"] == ["climate"]
    assert history[1]["experts"] == ["agriculture"]


def test_history_store_roundtable_persists_structured_consensus(tmp_path: Path) -> None:
    """Test roundtable persistence for structured consensus data."""
    store = HistoryStore(str(tmp_path / "chromadb"))
    result_id = store.save_result(
        query="How do I reduce drought risk?",
        experts=["agriculture", "climate"],
        responses=[],
        result_type="roundtable",
        roundtable_data={
            "rounds": 2,
            "transcript": [
                {
                    "speaker": "Agricultural Science Expert",
                    "text": "Start with soil moisture tracking.",
                    "round": 1,
                }
            ],
            "final_answer": "Pair irrigation monitoring with drought-tolerant varieties.",
            "consensus_brief": {
                "governing_insight": "Pair irrigation monitoring with drought-tolerant varieties.",
                "executive_summary": [
                    "Start with water discipline before major acreage expansion."
                ],
                "key_findings": [
                    {
                        "title": "Water discipline",
                        "claim": "Soil moisture tracking is the first move.",
                        "evidence_points": ["Experts agreed on instrumentation first."],
                        "implication": "Expansion should follow data, not precede it.",
                    }
                ],
                "decision_implications": [
                    "Capital plans should follow water telemetry."
                ],
                "recommendations": [
                    {
                        "owner": "Producers",
                        "action": "Install soil moisture monitoring.",
                        "expected_impact": "Improved irrigation timing.",
                        "key_risk": "Bad placement reduces confidence.",
                    }
                ],
                "limitations": [
                    "The roundtable did not include farm-specific cost data."
                ],
            },
        },
    )

    saved = store.get_result_by_id(result_id)

    assert saved is not None
    assert saved["result_type"] == "roundtable"
    assert saved["rounds"] == 2
    assert saved["consensus_brief"]["governing_insight"].startswith("Pair irrigation")
    exported = build_executive_brief_markdown(saved)
    assert "## Governing Insight" in exported
    assert "## Recommendations" in exported
    assert "Install soil moisture monitoring." in exported
    assert "Pair irrigation monitoring with drought-tolerant varieties." in exported


def test_history_store_handles_invalid_document(tmp_path: Path) -> None:
    """Test corrupt JSON documents fail closed instead of raising."""
    store = HistoryStore(str(tmp_path / "chromadb"))
    store._collection.add(
        ids=["broken123"],
        documents=["{not-json"],
        metadatas=[
            {
                "query": "Broken",
                "experts": "[]",
                "result_type": "query",
                "timestamp": "2026-04-01T10:00:00",
            }
        ],
    )

    assert store.get_result_by_id("broken123") is None


def test_history_store_missing_result_returns_none(tmp_path: Path) -> None:
    """Test looking up a missing result returns None."""
    store = HistoryStore(str(tmp_path / "chromadb"))

    assert store.get_result_by_id("missing") is None
