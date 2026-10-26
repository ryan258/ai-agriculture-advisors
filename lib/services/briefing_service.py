"""Build executive brief HTML from saved advisory results."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from lib.experts.response_format import collect_decision_checks, extract_compact_ending

from ._text_utils import clean_string_list as _clean_string_list
from ._text_utils import coerce_to_string as _coerce_to_string
from .record_export import fenced
from .brief_models import BriefDocument, BriefMetric, BriefFinding, BriefRecommendation
from .brief_compat import (
    _build_key_findings_from_agreements,
    _build_decision_implications_from_perspectives,
    _build_recommendations_from_conclusions,
    _apply_recommendation_defaults,
    _build_key_findings_from_consensus_matrix,
    _build_decision_implications_from_consensus_matrix,
    _build_recommendations_from_consensus_matrix,
    _parse_markdown_sections,
    _without_decision_check,
    _parse_list_items,
    _parse_markdown_table,
    _parse_markdown_table_row,
    _parse_inline_consensus_matrix,
    _extract_consensus_title,
    _collapse_duplicate_consensus_sections,
    _normalize_whitespace,
    _clean_cell_text,
    _extract_cell_points,
    _join_cell_points,
    _title_case_query,
    _split_into_sentences,
    _chunk_sentences_into_paragraphs,
    _break_long_text_into_paragraphs,
    _extract_headline_and_body,
    _compose_executive_summary,
    _split_labeled_text,
    _normalize_heading_key,
    _extract_bold_only_text,
    _dedupe_preserve_order,
    _format_timestamp,
    _extract_evidence_points,
    _extract_summary,
    _extract_list_points,
    _split_blocks,
    _block_to_point,
    _clean_markdown_text,
    _clean_markdown_line,
    _join_point_parts,
    _remove_label_prefix,
    _looks_like_heading,
    _looks_like_list_line,
    _looks_like_continuation_line,
    _first_non_empty,
    _compact_metrics,
)

_ORGANIZATION = "AI Advisors"
_HEADER_LABEL = "AI Advisory"
_PUBLICATION_LABEL = "Executive Brief"
_SERVICE_TEMPLATE_DIR = Path(__file__).resolve().with_name("templates")


@lru_cache(maxsize=1)
def _get_template_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_SERVICE_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build_executive_brief_html(result: dict[str, Any]) -> str:
    """Render a saved query or roundtable result as executive-brief HTML."""
    template = _get_template_environment().get_template("brief.html")
    return template.render(brief=_build_brief_payload(result))


def build_executive_brief_markdown(result: dict[str, Any]) -> str:
    """Render a saved query or roundtable result as report markdown."""
    return _render_brief_markdown(_build_brief_payload(result))


def _build_brief_payload(result: dict[str, Any]) -> BriefDocument:
    if result.get("result_type") == "roundtable":
        brief = _build_roundtable_brief(result)
    else:
        brief = _build_query_evidence(result)
    if result.get("result_type") == "roundtable" and result.get("synthesis_error"):
        failure = result["synthesis_error"]
        message = (
            failure.get("message", "Synthesis has not completed.")
            if isinstance(failure, dict)
            else "Synthesis has not completed."
        )
        brief = replace(brief, limitations=[*brief.limitations, message])
    if result.get("result_type") == "roundtable":
        transcript = result.get("transcript", [])
        completed = sum(
            entry.get("status") == "success"
            or (
                "status" not in entry
                and not str(entry.get("text", "")).startswith("Error:")
            )
            for entry in transcript
        )
        if completed < len(transcript):
            brief = replace(
                brief,
                limitations=[
                    *brief.limitations,
                    f"{completed} of {len(transcript)} advisor contributions completed; missing responses are excluded from synthesis.",
                ],
                metrics=[
                    (
                        replace(metric, value=str(completed))
                        if metric.label == "Contributions"
                        else metric
                    )
                    for metric in brief.metrics
                ],
            )
        if result.get("synthesis_stale"):
            brief = replace(
                brief,
                limitations=[
                    *brief.limitations,
                    "The synthesis predates recovered responses and has not been refreshed.",
                ],
            )
    structured = result.get("consensus_brief") or {}
    brief = replace(
        brief,
        decision_checks=collect_decision_checks(result),
        supplied_sources=result.get("sources", []),
        execution_receipts=result.get("execution_receipts", []),
        decision_analysis={
            key: structured.get(key, [])
            for key in ("claims", "options", "disagreements")
        },
        limitations=[
            *brief.limitations,
            "AI-generated analysis is not independent verification. Participant names identify generated inputs, not source citations. This is an abridged presentation; use Complete record for exact original content.",
        ],
    )
    context = result.get("advisor_context")
    if isinstance(context, dict) and context:
        return replace(brief, advisor_context=context)
    return replace(
        brief,
        limitations=[
            *brief.limitations,
            "Advisor definitions were not captured for this saved result.",
        ],
    )


def _build_query_evidence(result: dict[str, Any]) -> BriefDocument:
    responses = result.get("responses", [])
    successful = [item for item in responses if item.get("response")]
    failures = [item for item in responses if item.get("error")]

    governing_insight = _first_non_empty(
        _extract_summary(item.get("response", "")) for item in successful
    )
    if not governing_insight:
        governing_insight = (
            "No successful advisor responses were available for synthesis."
        )

    findings = [
        BriefFinding(
            title=item.get("label", item.get("role", "Advisor")),
            claim=_extract_summary(item.get("response", "")),
            evidence_points=_extract_evidence_points(item.get("response", "")),
            implication=(
                f"Use the {item.get('label', item.get('role', 'advisor'))} perspective "
                "to pressure-test the final recommendation."
            ),
            confidence="directional",
        )
        for item in successful
        if _extract_summary(item.get("response", ""))
    ]

    if failures:
        findings.append(
            BriefFinding(
                title="Delivery gaps",
                claim=(
                    f"{len(failures)} advisor response(s) failed and were excluded from the brief."
                ),
                evidence_points=[
                    f"{item.get('label', item.get('role', 'Advisor'))}: {item.get('error', 'Unknown error')}"
                    for item in failures[:3]
                ],
                implication=(
                    "Rerun the query or inspect logs before treating the synthesis as complete."
                ),
                confidence="low",
            )
        )

    query = result.get("query", "Advisor query")
    headline, remainder_paragraphs = _extract_headline_and_body(governing_insight)
    display_insight = headline or governing_insight
    composed_summary = _compose_executive_summary(
        display_insight, remainder_paragraphs, [], original_insight=governing_insight
    )
    if not composed_summary:
        composed_summary = [display_insight] if display_insight else []
    return BriefDocument(
        brief_id=result.get("id", ""),
        title=_title_case_query(query),
        subtitle="Expert Query Synthesis",
        organization=_ORGANIZATION,
        publication_label=_PUBLICATION_LABEL,
        header_label=_HEADER_LABEL,
        date_label=_format_timestamp(result.get("timestamp")),
        governing_question=query,
        governing_insight=display_insight,
        executive_summary=composed_summary,
        metrics=_compact_metrics(
            [
                BriefMetric(
                    label="Experts Consulted",
                    value=str(len(result.get("experts", []))),
                ),
                BriefMetric(
                    label="Successful Responses",
                    value=str(len(successful)),
                ),
                (
                    BriefMetric(
                        label="Failed Responses",
                        value=str(len(failures)),
                    )
                    if failures
                    else None
                ),
            ]
        ),
        findings=findings,
        methodology=[
            "Built from saved expert responses in AI Advisors.",
            "Rendered into a decision-ready brief without re-querying the LLM providers.",
        ],
        limitations=[
            "This brief is a structural synthesis of stored advisor outputs.",
            "Conflicting expert recommendations still require user judgment.",
        ],
        sources=[item.get("label", item.get("role", "Advisor")) for item in successful],
    )


def _build_roundtable_brief(result: dict[str, Any]) -> BriefDocument:
    transcript = result.get("transcript", [])
    structured_consensus = result.get("consensus_brief")
    if isinstance(structured_consensus, dict) and structured_consensus:
        return _build_roundtable_brief_from_structured(
            result,
            transcript,
            structured_consensus,
        )

    # Legacy fallback for older saved results that only contain free-form consensus text.
    final_answer = str(result.get("final_answer", "")).strip() or (
        "No consensus answer was available from the saved roundtable."
    )
    normalized_final_answer = _collapse_duplicate_consensus_sections(final_answer)
    intro, sections = _parse_markdown_sections(normalized_final_answer)
    workflow_handoff_text = ""
    accessibility_handoff_text = ""
    context = result.get("advisor_context")
    panel = context.get("panel") if isinstance(context, dict) else None
    if isinstance(panel, dict):
        if panel.get("id") == "ai_workflow":
            workflow_handoff_text = _without_decision_check(normalized_final_answer)
        elif panel.get("id") == "accessibility_effort":
            accessibility_handoff_text = _without_decision_check(
                normalized_final_answer
            )
    agreement_lines = sections.get("key points of agreement", [])
    perspective_lines = sections.get("important differences in perspective", [])
    conclusions_lines = sections.get("actionable conclusions", [])

    key_findings = _build_key_findings_from_agreements(agreement_lines)
    decision_implications = _build_decision_implications_from_perspectives(
        perspective_lines
    )
    recommendations, bottom_line = _build_recommendations_from_conclusions(
        conclusions_lines
    )
    inline_title, inline_rows = _parse_inline_consensus_matrix(normalized_final_answer)
    if inline_title:
        intro = inline_title
    if inline_rows:
        if not key_findings:
            key_findings = _build_key_findings_from_consensus_matrix(inline_rows)
        if not decision_implications:
            decision_implications = _build_decision_implications_from_consensus_matrix(
                inline_rows
            )
        if not recommendations:
            recommendations = _build_recommendations_from_consensus_matrix(inline_rows)
    recommendations = _apply_recommendation_defaults(recommendations)

    if workflow_handoff_text or accessibility_handoff_text:
        if accessibility_handoff_text:
            governing_insight = "Reusable voice-friendly starter with a checkpoint and dictation fallback."
        else:
            first_packet_line = _first_non_empty(
                _clean_markdown_line(line) for line in sections.get("task packet", [])
            )
            label, separator, objective = first_packet_line.partition(":")
            governing_insight = (
                (
                    objective.strip()
                    if separator and label.strip().casefold() == "goal"
                    else first_packet_line
                )
                or "See the saved workflow handoff for the task packet and review checks."
            )
        executive_summary = []
        key_findings = []
        decision_implications = []
        recommendations = []
    else:
        governing_insight = (
            bottom_line
            or intro
            or _first_non_empty(finding.claim for finding in key_findings)
            or _clean_markdown_text(normalized_final_answer)
        )

        executive_summary = [item for item in [intro, bottom_line] if item]
        if not executive_summary:
            executive_summary = [governing_insight]

        if not key_findings:
            fallback_summary = _extract_summary(normalized_final_answer)
            if fallback_summary:
                key_findings = [
                    BriefFinding(
                        title="Consensus",
                        claim=fallback_summary,
                        confidence="directional",
                    )
                ]

    limitations = [
        "Built from a saved multi-expert roundtable consensus without re-running the discussion.",
    ]
    error_entries = [
        entry for entry in transcript if str(entry.get("text", "")).startswith("Error:")
    ]
    if error_entries:
        affected_speakers = _dedupe_preserve_order(
            [
                str(entry.get("speaker", "Advisor")).strip() or "Advisor"
                for entry in error_entries
            ]
        )
        limitations.append(
            f"{len(error_entries)} participant contribution(s) failed during the saved roundtable."
        )
        limitations.append(
            f"Affected participants: {', '.join(affected_speakers[:4])}."
        )

    sources = _dedupe_preserve_order(
        [
            str(entry.get("speaker", "")).strip()
            for entry in transcript
            if str(entry.get("speaker", "")).strip()
        ]
    ) or [str(expert) for expert in result.get("experts", []) if str(expert).strip()]

    headline, remainder_paragraphs = _extract_headline_and_body(governing_insight)
    display_insight = headline or governing_insight
    composed_summary = _compose_executive_summary(
        display_insight,
        remainder_paragraphs,
        executive_summary,
        original_insight=governing_insight,
    )
    if (
        not composed_summary
        and not workflow_handoff_text
        and not accessibility_handoff_text
    ):
        composed_summary = executive_summary or (
            [display_insight] if display_insight else []
        )

    query = result.get("query", "Advisor roundtable")
    return BriefDocument(
        brief_id=result.get("id", ""),
        title=_title_case_query(query),
        subtitle="Roundtable Consensus",
        organization=_ORGANIZATION,
        publication_label=_PUBLICATION_LABEL,
        header_label=_HEADER_LABEL,
        date_label=_format_timestamp(result.get("timestamp")),
        governing_question=query,
        governing_insight=display_insight,
        executive_summary=composed_summary,
        metrics=_compact_metrics(
            [
                BriefMetric(
                    label="Participants", value=str(len(result.get("experts", [])))
                ),
                BriefMetric(label="Rounds", value=str(result.get("rounds", 0))),
                BriefMetric(label="Contributions", value=str(len(transcript))),
            ]
        ),
        findings=key_findings,
        decision_implications=decision_implications,
        recommendations=recommendations,
        methodology=[
            "Built from a saved multi-expert roundtable transcript.",
            "Consensus text came from the moderator synthesis stored with the result.",
        ],
        limitations=limitations,
        sources=sources,
        workflow_handoff_text=workflow_handoff_text,
        accessibility_handoff_text=accessibility_handoff_text,
    )


def _build_roundtable_brief_from_structured(
    result: dict[str, Any],
    transcript: list[dict[str, Any]],
    consensus_brief: dict[str, Any],
) -> BriefDocument:
    governing_insight = str(consensus_brief.get("governing_insight", "")).strip()
    if consensus_brief.get("synthesis_format") == "workflow_handoff":
        task_packet = str(consensus_brief.get("task_packet", "")).strip()
        first_line = task_packet.splitlines()[0] if task_packet else ""
        label, separator, objective = first_line.partition(":")
        governing_insight = (
            objective.strip()
            if separator and label.strip().casefold() == "goal"
            else first_line
        )
    if consensus_brief.get("synthesis_format") == "accessibility_handoff":
        governing_insight = (
            "Reusable voice-friendly starter with a checkpoint and dictation fallback."
        )
    executive_summary = _clean_string_list(consensus_brief.get("executive_summary", []))
    findings = [
        BriefFinding(
            title=str(item.get("title", "")).strip() or "Consensus finding",
            claim=str(item.get("claim", "")).strip() or governing_insight,
            evidence_points=_clean_string_list(item.get("evidence_points", [])),
            implication=str(item.get("implication", "")).strip(),
            confidence="directional",
        )
        for item in consensus_brief.get("key_findings", [])
        if isinstance(item, dict)
    ]
    recommendations = [
        BriefRecommendation(
            owner=str(item.get("owner", "")).strip(),
            action=str(item.get("action", "")).strip(),
            expected_impact=str(item.get("expected_impact", "")).strip(),
            key_risk=str(item.get("key_risk", "")).strip(),
        )
        for item in consensus_brief.get("recommendations", [])
        if isinstance(item, dict) and str(item.get("action", "")).strip()
    ]
    recommendations = _apply_recommendation_defaults(recommendations)
    limitations = [
        "Built from a saved multi-expert roundtable consensus without re-running the discussion.",
    ]
    limitations.extend(_clean_string_list(consensus_brief.get("limitations", [])))
    error_entries = [
        entry for entry in transcript if str(entry.get("text", "")).startswith("Error:")
    ]
    if error_entries:
        affected_speakers = _dedupe_preserve_order(
            [
                str(entry.get("speaker", "Advisor")).strip() or "Advisor"
                for entry in error_entries
            ]
        )
        limitations.append(
            f"{len(error_entries)} participant contribution(s) failed during the saved roundtable."
        )
        limitations.append(
            f"Affected participants: {', '.join(affected_speakers[:4])}."
        )

    sources = _dedupe_preserve_order(
        [
            str(entry.get("speaker", "")).strip()
            for entry in transcript
            if str(entry.get("speaker", "")).strip()
        ]
    ) or [str(expert) for expert in result.get("experts", []) if str(expert).strip()]

    workflow_handoff = (
        consensus_brief
        if consensus_brief.get("synthesis_format") == "workflow_handoff"
        else {}
    )
    accessibility_handoff = (
        consensus_brief
        if consensus_brief.get("synthesis_format") == "accessibility_handoff"
        else {}
    )
    # Split over-long insights into a readable headline + body, and dedupe against the
    # executive_summary field (LLMs frequently dump the same blob into both).
    headline, remainder_paragraphs = _extract_headline_and_body(governing_insight)
    display_governing_insight = (
        headline
        or _first_non_empty(executive_summary)
        or "No consensus answer was available from the saved roundtable."
    )
    composed_summary = _compose_executive_summary(
        display_governing_insight,
        remainder_paragraphs,
        executive_summary,
        original_insight=governing_insight,
    )

    if not composed_summary and not workflow_handoff and not accessibility_handoff:
        composed_summary = executive_summary or (
            [display_governing_insight] if display_governing_insight else []
        )
    query = result.get("query", "Advisor roundtable")
    return BriefDocument(
        brief_id=result.get("id", ""),
        title=_title_case_query(query),
        subtitle="Roundtable Consensus",
        organization=_ORGANIZATION,
        publication_label=_PUBLICATION_LABEL,
        header_label=_HEADER_LABEL,
        date_label=_format_timestamp(result.get("timestamp")),
        governing_question=query,
        governing_insight=display_governing_insight,
        executive_summary=composed_summary,
        metrics=_compact_metrics(
            [
                BriefMetric(
                    label="Participants", value=str(len(result.get("experts", [])))
                ),
                BriefMetric(label="Rounds", value=str(result.get("rounds", 0))),
                BriefMetric(label="Contributions", value=str(len(transcript))),
            ]
        ),
        findings=findings,
        decision_implications=_clean_string_list(
            consensus_brief.get("decision_implications", [])
        ),
        recommendations=recommendations,
        methodology=[
            "Built from a saved multi-expert roundtable transcript.",
            "Consensus sections came from the structured moderator synthesis stored with the result.",
        ],
        limitations=limitations,
        sources=sources,
        workflow_handoff=workflow_handoff,
        accessibility_handoff=accessibility_handoff,
    )


def _render_brief_markdown(brief: BriefDocument) -> str:
    lines = [
        f"# {brief.title}",
        "",
        f"*{brief.subtitle}*",
        "",
        f"**Organization:** {brief.organization}",
    ]
    if brief.date_label:
        lines.append(f"**Date:** {brief.date_label}")
    lines.extend(["", "## Original question", "", fenced(brief.governing_question), ""])
    lines.extend(
        [
            "",
            "## Governing Insight",
            "",
            brief.governing_insight,
            "",
        ]
    )

    if brief.executive_summary:
        lines.extend(["## Executive Summary", ""])
        for paragraph in brief.executive_summary:
            lines.extend([paragraph, ""])

    if brief.workflow_handoff:
        handoff = brief.workflow_handoff
        lines.extend(
            [
                "## Task Packet",
                "",
                handoff["task_packet"],
                "",
                "## Review Checklist",
                "",
            ]
        )
        lines.extend(
            f"- [ ] {item['check']} **Evidence:** {item['evidence_target']}"
            for item in handoff["review_checklist"]
        )
        lines.extend(
            [
                "",
                "## Resume Checkpoint",
                "",
                handoff["resume_checkpoint"],
            ]
        )
        lines.extend(
            [
                "",
                "## Success Measure",
                "",
                handoff["success_measure"],
                "",
            ]
        )

    if brief.accessibility_handoff:
        handoff = brief.accessibility_handoff
        for key, heading in (
            ("starter_template", "Reusable Starter"),
            ("resume_checkpoint", "Resume Checkpoint"),
            ("dictation_fallback", "Dictation Fallback"),
            ("first_trial", "First Trial"),
        ):
            lines.extend([f"## {heading}", "", handoff[key], ""])

    if brief.workflow_handoff_text:
        lines.extend(
            ["## Saved Plain-Text Handoff", "", brief.workflow_handoff_text, ""]
        )

    if brief.accessibility_handoff_text:
        lines.extend(
            [
                "## Saved Accessibility Handoff",
                "",
                brief.accessibility_handoff_text,
                "",
            ]
        )

    if brief.metrics:
        lines.extend(["## Metrics", ""])
        for metric in brief.metrics:
            lines.append(f"- **{metric.label}:** {metric.value}")
        lines.append("")

    if brief.findings:
        lines.extend(["## Key Findings", ""])
        for finding in brief.findings:
            lines.extend([f"### {finding.title}", "", finding.claim, ""])
            for point in finding.evidence_points:
                lines.append(f"- {point}")
            if finding.implication:
                lines.extend(["", f"**Implication:** {finding.implication}"])
            lines.append("")

    if brief.recommendations:
        lines.extend(["## Recommendations", ""])
        for recommendation in brief.recommendations:
            lines.extend([f"### {recommendation.owner}", ""])
            lines.append(f"- **Action:** {recommendation.action}")
            if recommendation.expected_impact:
                lines.append(f"- **Expected Impact:** {recommendation.expected_impact}")
            if recommendation.key_risk:
                lines.append(f"- **Key Risk:** {recommendation.key_risk}")
            lines.append("")

    if brief.decision_implications:
        lines.extend(["## Decision Implications", ""])
        for implication in brief.decision_implications:
            lines.append(f"- {implication}")
        lines.append("")

    if brief.methodology:
        lines.extend(["## Methodology", ""])
        for item in brief.methodology:
            lines.append(f"- {item}")
        lines.append("")

    if brief.limitations:
        lines.extend(["## Limitations", ""])
        for item in brief.limitations:
            lines.append(f"- {item}")
        lines.append("")

    if brief.sources:
        lines.extend(["## AI Participants (generated inputs)", ""])
        for source in brief.sources:
            lines.append(f"- {source}")
        lines.append("")

    for source in brief.supplied_sources:
        lines.extend(
            [
                f"## Supplied source [{source['id']}] — {source['label']}",
                "",
                f"Reference: {source['reference']} · Date: {source['date'] or 'Unknown'}",
                "",
                fenced(source["passage"]),
                "",
            ]
        )
    if brief.execution_receipts:
        lines.extend(
            [
                "## Captured execution receipts",
                "",
                fenced(brief.execution_receipts, "json"),
                "",
            ]
        )
    if any(brief.decision_analysis.values()):
        lines.extend(
            [
                "## Captured options, claims, and disagreement",
                "",
                fenced(brief.decision_analysis, "json"),
                "",
            ]
        )

    if brief.advisor_context:
        context = brief.advisor_context
        lines.extend(
            [
                "## Advisor Definitions Used",
                "",
                f"**Panel:** {context['panel']['label']} ({context['panel']['id']})",
                "",
            ]
        )
        for advisor in context["advisors"]:
            lines.extend(
                [
                    f"### {advisor['label']} ({advisor['role']})",
                    "",
                    advisor["system_prompt"],
                    "",
                ]
            )

    for check in brief.decision_checks:
        lines.extend([f"## Decision Check — {check['label']}", ""])
        lines.extend(
            f"- **{point['label']}:** {point['text']}" for point in check["points"]
        )
        lines.append("")

    return "\n".join(lines).strip()
