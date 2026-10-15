"""Tests for executive brief rendering from saved advisor results."""

from __future__ import annotations

from lib.services.briefing_service import (
    _collapse_duplicate_consensus_sections,
    _compose_executive_summary,
    _extract_headline_and_body,
    _title_case_query,
    build_executive_brief_html,
    build_executive_brief_markdown,
)


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

    assert "AI Advisors" in html
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
    assert "For Producers" in html
    assert "Origin Aggregators" in html
    assert "Commodities Trading Specialist" not in html


def test_builds_roundtable_brief_from_flattened_consensus_matrix() -> None:
    result = {
        "id": "matrix2468",
        "query": "What are the smart investments for summer 2026?",
        "timestamp": "2026-04-08T14:22:42",
        "result_type": "roundtable",
        "experts": ["agriculture", "climate", "commodities"],
        "rounds": 3,
        "transcript": [],
        "final_answer": (
            "Executive Summary\n"
            "Governing Insight\n"
            "Consensus Answer - Smart Investments for Summer 2026 Investment Area | "
            "What to Do (2025-2026) | Why It Is Smart for Summer 2026 | "
            "Key Enablers / Risk-Mitigations | Climate-Resilient Crop Varieties | "
            "• Deploy stacked-trait lines for wheat, maize, soybean.\n"
            "• Use speed-breeding pipelines.\n"
            "• Pair with farmer-led validation trials. | "
            "• Summer heat is the single biggest yield-limiting factor.\n"
            "• Reduces need for emergency irrigation. | "
            "• Open-source trait pools keep seed affordable.\n"
            "• Contingency germplasm banks preserve diversity. | "
            "Precision Water-Management + Real-Time Sensing | "
            "• Install soil-moisture probes.\n"
            "• Link them to irrigation controllers. | "
            "• Cuts water use while preserving yield. | "
            "• Low-cost gateways keep operating costs manageable. |\n\n"
            "Consensus Answer - Smart Investments for Summer 2026 Investment Area | "
            "What to Do (2025-2026) | Why It Is Smart for Summer 2026 | "
            "Key Enablers / Risk-Mitigations | Climate-Resilient Crop Varieties | "
            "• Deploy stacked-trait lines for wheat, maize, soybean.\n"
            "• Use speed-breeding pipelines.\n"
            "• Pair with farmer-led validation trials. | "
            "• Summer heat is the single biggest yield-limiting factor.\n"
            "• Reduces need for emergency irrigation. | "
            "• Open-source trait pools keep seed affordable.\n"
            "• Contingency germplasm banks preserve diversity. | "
            "Precision Water-Management + Real-Time Sensing | "
            "• Install soil-moisture probes.\n"
            "• Link them to irrigation controllers. | "
            "• Cuts water use while preserving yield. | "
            "• Low-cost gateways keep operating costs manageable. |"
        ),
    }

    html = build_executive_brief_html(result)

    assert "Smart Investments for Summer 2026" in html
    assert "Climate-Resilient Crop Varieties" in html
    assert "Precision Water-Management + Real-Time Sensing" in html
    assert "Deploy stacked-trait lines for wheat, maize, soybean." in html
    assert "Low-cost gateways keep operating costs manageable." in html
    assert "Investment Area | What to Do" not in html
    assert "Executive Summary Governing Insight Consensus Answer" not in html


def test_builds_roundtable_brief_from_structured_consensus() -> None:
    result = {
        "id": "structured2468",
        "query": "What should drought planning prioritize?",
        "timestamp": "2026-04-08T15:00:00",
        "result_type": "roundtable",
        "experts": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [
            {
                "speaker": "Agricultural Science Expert",
                "text": "Start with soil moisture tracking.",
                "round": 1,
            }
        ],
        "final_answer": "Legacy fallback text that should not drive the brief.",
        "consensus_brief": {
            "governing_insight": "Protect water first, then expand.",
            "executive_summary": ["Irrigation visibility should precede expansion."],
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
            "limitations": ["The roundtable did not quantify local payback periods."],
        },
    }

    html = build_executive_brief_html(result)
    markdown = build_executive_brief_markdown(result)

    assert "Protect water first, then expand." in html
    assert "Legacy fallback text" not in html
    assert "Install moisture sensors." in html
    assert "## Governing Insight" in markdown
    assert "Install moisture sensors." in markdown
    assert "Legacy fallback text" not in markdown


def test_structured_recommendation_defaults_are_built_in_service_layer() -> None:
    result = {
        "id": "structureddefaults2468",
        "query": "What should drought planning prioritize?",
        "timestamp": "2026-04-08T15:00:00",
        "result_type": "roundtable",
        "experts": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [],
        "final_answer": "",
        "consensus_brief": {
            "governing_insight": "Protect water first, then expand.",
            "executive_summary": ["Irrigation visibility should precede expansion."],
            "key_findings": [],
            "decision_implications": [],
            "recommendations": [
                {
                    "owner": "",
                    "action": "Install moisture sensors.",
                    "expected_impact": "",
                    "key_risk": "",
                }
            ],
            "limitations": [],
        },
    }

    html = build_executive_brief_html(result)
    markdown = build_executive_brief_markdown(result)

    assert "Shared" in html
    assert "Directional upside; validate locally." in html
    assert "Execution quality and timing." in html
    assert "- **Expected Impact:** Directional upside; validate locally." in markdown
    assert "- **Key Risk:** Execution quality and timing." in markdown


def test_flattens_dict_items_in_decision_implications() -> None:
    """Persisted LLM responses that violated the schema with dict items should render as prose."""
    result = {
        "id": "dictimpl1357",
        "query": "Summer 2026 volatility strategy?",
        "timestamp": "2026-04-08T16:00:00",
        "result_type": "roundtable",
        "experts": ["commodities"],
        "rounds": 1,
        "transcript": [],
        "final_answer": "",
        "consensus_brief": {
            "governing_insight": "Favor structures with defined risk.",
            "executive_summary": ["Keep tail risk bounded."],
            "key_findings": [],
            "decision_implications": [
                {
                    "tradeoff": "Directional outrights vs. relative-value structures",
                    "detail": "Outright longs/shorts are exposed to ENSO-transition failure.",
                    "impact_on_execution": "Favor limited-risk structures like spreads.",
                }
            ],
            "recommendations": [],
            "limitations": [],
        },
    }

    html = build_executive_brief_html(result)

    assert "{'tradeoff':" not in html
    assert "Directional outrights vs. relative-value structures" in html
    assert "Favor limited-risk structures like spreads." in html


def test_title_case_query_handles_minor_words_and_edges() -> None:
    cased = _title_case_query(
        "what are the smart investments for summer 2026 commodity markets and why?"
    )
    assert cased == (
        "What Are the Smart Investments for Summer 2026 Commodity Markets and Why?"
    )


def test_title_case_query_capitalizes_trailing_minor_word() -> None:
    assert _title_case_query("what is it good for") == "What Is It Good For"


def test_title_case_query_preserves_punctuation() -> None:
    assert (
        _title_case_query("a farmer's guide to drought?")
        == "A Farmer's Guide to Drought?"
    )


def test_extract_headline_and_body_short_insight_passes_through() -> None:
    insight = "Pair irrigation monitoring with drought-tolerant varieties."
    headline, body = _extract_headline_and_body(insight)
    assert headline == insight
    assert body == []


def test_extract_headline_and_body_splits_long_insight() -> None:
    sentences = [
        "Drought resilience begins with visibility into soil moisture trends.",
        "Producers must invest in sensor networks before expanding acreage.",
        "Irrigation schedules need to be retuned as heat spikes grow more frequent.",
        "Crop genetics matter less than water discipline in the near term.",
        "Regional cooperatives can share instrumentation to reduce capex per farm.",
        "Trading desks should hedge water-exposed commodities ahead of summer.",
        "Financing partners want telemetry data before underwriting expansion loans.",
        "Insurance premiums reflect the gap between monitored and unmonitored farms.",
    ]
    long_insight = " ".join(sentences)
    assert len(long_insight) > 260

    headline, body = _extract_headline_and_body(long_insight)

    assert headline
    assert len(headline) <= 260
    assert headline.startswith(sentences[0])
    assert body, "expected remainder paragraphs for an over-long insight"
    assert all(paragraph.strip() for paragraph in body)
    # Every sentence after the headline should appear somewhere in the body.
    joined_body = " ".join(body)
    for sentence in sentences:
        if sentence not in headline:
            assert sentence in joined_body


def test_compose_executive_summary_skips_original_insight_duplicate() -> None:
    insight = "Protect water first, then expand into acreage only after telemetry is in place."

    summary = _compose_executive_summary(
        headline="Protect water first, then expand into acreage only after telemetry is in place.",
        remainder_paragraphs=[],
        existing_summary=[insight],
        original_insight=insight,
    )

    assert summary == []


def test_collapse_duplicate_consensus_sections_removes_legacy_repeat_block() -> None:
    duplicated = (
        "Executive Summary\n"
        "Consensus Answer - Smart Investments for Summer 2026\n"
        "Investment Area | What to Do | Why It Matters\n\n"
        "Consensus Answer - Smart Investments for Summer 2026\n"
        "Investment Area | What to Do | Why It Matters"
    )

    collapsed = _collapse_duplicate_consensus_sections(duplicated)

    assert collapsed.count("Consensus Answer - Smart Investments for Summer 2026") == 1
    assert collapsed.startswith("Executive Summary")


def test_roundtable_brief_breaks_wall_of_text_governing_insight() -> None:
    long_insight = (
        "Drought resilience begins with visibility into soil moisture trends across every field. "
        "Producers must invest in sensor networks before expanding acreage into marginal ground. "
        "Irrigation schedules need to be retuned as heat spikes grow more frequent each summer. "
        "Crop genetics matter less than water discipline in the near term for most operations. "
        "Regional cooperatives can share instrumentation to reduce capex per farm significantly. "
        "Trading desks should hedge water-exposed commodities ahead of every summer peak window. "
        "Financing partners want telemetry data before underwriting expansion loans going forward."
    )
    result = {
        "id": "longblob123",
        "query": "what should drought planning prioritize for summer 2026?",
        "timestamp": "2026-04-08T17:00:00",
        "result_type": "roundtable",
        "experts": ["agriculture", "climate"],
        "rounds": 2,
        "transcript": [],
        "final_answer": "",
        "consensus_brief": {
            "governing_insight": long_insight,
            "executive_summary": [long_insight],
            "key_findings": [],
            "decision_implications": [],
            "recommendations": [],
            "limitations": [],
        },
    }

    html = build_executive_brief_html(result)

    assert "What Should Drought Planning Prioritize for Summer 2026?" in html
    # The full wall should not be dumped verbatim into the governing insight card.
    assert long_insight not in html
    # But every sentence should still render somewhere in the brief body.
    for sentence in [
        "Drought resilience begins with visibility into soil moisture trends across every field.",
        "Financing partners want telemetry data before underwriting expansion loans going forward.",
    ]:
        assert sentence in html
    # And the body should not duplicate the same blob twice back-to-back.
    assert (
        html.count(
            "Drought resilience begins with visibility into soil moisture trends across every field."
        )
        == 1
    )


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
    assert (
        "Traditional varieties are increasingly mismatched to emerging climate baselines."
        in html
    )
