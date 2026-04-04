"""Tests for executive brief rendering from saved advisor results."""

from __future__ import annotations

from lib.services.briefing_service import build_executive_brief_html


def test_builds_query_brief_html() -> None:
    result = {
        "id": "abc12345",
        "query": "How should I manage drought risk this season?",
        "timestamp": "2026-04-04T13:00:00",
        "result_type": "query",
        "experts": ["agriculture", "climate"],
        "responses": [
            {
                "role": "agriculture",
                "label": "Agricultural Science Expert",
                "response": "Start with soil moisture tracking and stagger irrigation windows.",
            },
            {
                "role": "climate",
                "label": "Climate Change Impact Analyst",
                "response": "Plan around heat spikes and preserve groundwater buffers.",
            },
        ],
    }

    html = build_executive_brief_html(result)

    assert "AI Agriculture Advisors" in html
    assert "How should I manage drought risk this season?" in html
    assert "Agricultural Science Expert" in html


def test_builds_roundtable_brief_html() -> None:
    result = {
        "id": "def67890",
        "query": "What should a small farm prioritize for drought resilience?",
        "timestamp": "2026-04-04T13:05:00",
        "result_type": "roundtable",
        "experts": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [
            {
                "speaker": "Agricultural Science Expert",
                "text": "Start with soil moisture tracking.",
                "round": 1,
            },
            {
                "speaker": "Climate Change Impact Analyst",
                "text": "Preserve water buffers before expansion.",
                "round": 1,
            },
        ],
        "final_answer": (
            "Consensus summary for drought resilience.\n\n"
            "### Key Points of Agreement\n"
            "1. **Water discipline:** Farms need soil moisture tracking before expansion.\n"
            "2. **Crop fit:** Drought-tolerant varieties should be prioritized.\n\n"
            "### Important Differences in Perspective\n"
            "| Lens | Primary Focus | Divergence/Tension |\n"
            "|:---|:---|:---|\n"
            "| Trading | Input price volatility | Favors hedging over static buying. |\n"
            "| Agronomy | Soil water retention | Favors on-farm adaptation first. |\n\n"
            "### Actionable Conclusions\n"
            "**For Producers & Origin Aggregators**\n"
            "- Start with soil moisture tracking.\n"
            "- Upgrade irrigation scheduling.\n\n"
            "**Bottom Line:** Pair irrigation monitoring with drought-tolerant varieties."
        ),
    }

    html = build_executive_brief_html(result)

    assert "Roundtable Consensus" in html
    assert "Pair irrigation monitoring with drought-tolerant varieties." in html
    assert "Participants" in html
    assert "Water discipline" in html
    assert "For Producers & Origin Aggregators" in html
    assert "Commodities Trading Specialist" not in html


def test_cleans_markdown_sections_for_query_brief() -> None:
    result = {
        "id": "ghi13579",
        "query": "What are the biggest opportunities for investment in agriculture?",
        "timestamp": "2026-04-04T14:07:03.613279",
        "result_type": "query",
        "experts": ["agriculture"],
        "responses": [
            {
                "role": "agriculture",
                "label": "Agricultural Science Expert",
                "response": (
                    "Top opportunities sit at the intersection of **climate adaptation** and yield stability.\n\n"
                    "---\n\n"
                    "### 1. Climate-Resilient Crop Genetics & Advanced Breeding\n"
                    "**Why it matters:** Traditional varieties are increasingly mismatched to emerging climate baselines.\n"
                    "- Deeper root systems for drought tolerance\n"
                    "- Heat-shock protein expression for thermal resilience\n"
                ),
            }
        ],
    }

    html = build_executive_brief_html(result)

    assert "**" not in html
    assert "###" not in html
    assert "Climate-Resilient Crop Genetics" in html
    assert "1. Climate-Resilient Crop Genetics" not in html
    assert "Traditional varieties are increasingly mismatched to emerging climate baselines." in html
