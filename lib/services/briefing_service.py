"""Build executive brief HTML from saved advisory results."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from lib.experts.response_format import collect_decision_checks

from ._text_utils import clean_string_list as _clean_string_list
from ._text_utils import coerce_to_string as _coerce_to_string

_ORGANIZATION = "AI Advisors"
_HEADER_LABEL = "AI Advisory"
_PUBLICATION_LABEL = "Executive Brief"
_SERVICE_TEMPLATE_DIR = Path(__file__).resolve().with_name("templates")
_DEFAULT_RECOMMENDATION_OWNER = "Shared"
_DEFAULT_RECOMMENDATION_IMPACT = "Directional upside; validate locally."
_DEFAULT_RECOMMENDATION_RISK = "Execution quality and timing."
_HORIZONTAL_RULE_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*$")
_ORDERED_PREFIX_RE = re.compile(r"^\s*\d+[.)]\s*")
_UNORDERED_PREFIX_RE = re.compile(r"^\s*[-+*•▪◦]\s*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_DECORATIVE_PREFIX_RE = re.compile(r"^[^\w(]+")
_LABEL_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 /&()'’+-]{1,40}:\s*")
_BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")
_BOLD_PREFIX_RE = re.compile(r"^\*\*(.+?)\*\*:\s*(.+)$")
_CONSENSUS_TITLE_RE = re.compile(r"Consensus Answer\s*[–—:-]\s*(.+)$", re.IGNORECASE)
_CONSENSUS_SECTION_START_RE = re.compile(
    r"^Consensus Answer\s*[–—:-]\s*.+$",
    re.IGNORECASE | re.MULTILINE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'“‘])")
_HEADLINE_MAX_CHARS = 260
_SUMMARY_SENTENCES_PER_PARAGRAPH = 3
_TITLE_MINOR_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "from",
        "in",
        "nor",
        "of",
        "on",
        "or",
        "the",
        "to",
        "up",
        "via",
        "with",
    }
)


@dataclass(frozen=True)
class BriefMetric:
    label: str
    value: str


@dataclass(frozen=True)
class BriefFinding:
    title: str
    claim: str
    evidence_points: list[str] = field(default_factory=list)
    implication: str = ""
    confidence: str = "directional"


@dataclass(frozen=True)
class BriefRecommendation:
    action: str
    owner: str = ""
    expected_impact: str = ""
    key_risk: str = ""


@dataclass(frozen=True)
class BriefDocument:
    brief_id: str
    title: str
    subtitle: str
    organization: str
    publication_label: str
    header_label: str
    date_label: str
    governing_question: str
    governing_insight: str
    executive_summary: list[str] = field(default_factory=list)
    metrics: list[BriefMetric] = field(default_factory=list)
    findings: list[BriefFinding] = field(default_factory=list)
    decision_implications: list[str] = field(default_factory=list)
    recommendations: list[BriefRecommendation] = field(default_factory=list)
    methodology: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    advisor_context: dict[str, Any] = field(default_factory=dict)
    decision_checks: list[dict[str, Any]] = field(default_factory=list)


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
    brief = replace(brief, decision_checks=collect_decision_checks(result))
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
    if not composed_summary:
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
    )


def _build_roundtable_brief_from_structured(
    result: dict[str, Any],
    transcript: list[dict[str, Any]],
    consensus_brief: dict[str, Any],
) -> BriefDocument:
    governing_insight = str(consensus_brief.get("governing_insight", "")).strip()
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
    )


def _build_key_findings_from_agreements(lines: list[str]) -> list[BriefFinding]:
    findings: list[BriefFinding] = []
    for item in _parse_list_items(lines):
        title, body = _split_labeled_text(item)
        if not body:
            body = title
            title = "Consensus finding"
        findings.append(
            BriefFinding(
                title=title,
                claim=body,
                confidence="directional",
            )
        )
    return findings


def _build_decision_implications_from_perspectives(lines: list[str]) -> list[str]:
    implications: list[str] = []
    for row in _parse_markdown_table(lines):
        lens = row.get("Lens", "")
        focus = row.get("Primary Focus", "")
        tension = row.get("Divergence/Tension", "")
        parts = [part for part in [focus, tension] if part]
        if not parts:
            continue
        implication = ": ".join([lens, " ".join(parts)]) if lens else " ".join(parts)
        implications.append(implication)
    return implications


def _build_recommendations_from_conclusions(
    lines: list[str],
) -> tuple[list[BriefRecommendation], str]:
    recommendations: list[BriefRecommendation] = []
    owner = ""
    bottom_line = ""
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue

        subsection = _extract_bold_only_text(stripped)
        if subsection:
            owner = subsection
            index += 1
            continue

        bottom_match = _BOLD_PREFIX_RE.match(stripped)
        if (
            bottom_match
            and _clean_markdown_line(bottom_match.group(1)).lower() == "bottom line"
        ):
            bottom_line = _clean_markdown_line(bottom_match.group(2))
            index += 1
            continue

        if _looks_like_list_line(raw_line):
            current = [_clean_markdown_line(raw_line)]
            index += 1
            while index < len(lines) and _looks_like_continuation_line(lines[index]):
                current.append(_clean_markdown_line(lines[index]))
                index += 1
            action = _join_point_parts(current)
            if action:
                recommendations.append(BriefRecommendation(action=action, owner=owner))
            continue

        index += 1

    return recommendations, bottom_line


def _apply_recommendation_defaults(
    recommendations: list[BriefRecommendation],
) -> list[BriefRecommendation]:
    normalized: list[BriefRecommendation] = []
    for recommendation in recommendations:
        normalized.append(
            BriefRecommendation(
                action=recommendation.action,
                owner=recommendation.owner or _DEFAULT_RECOMMENDATION_OWNER,
                expected_impact=(
                    recommendation.expected_impact or _DEFAULT_RECOMMENDATION_IMPACT
                ),
                key_risk=recommendation.key_risk or _DEFAULT_RECOMMENDATION_RISK,
            )
        )
    return normalized


def _build_key_findings_from_consensus_matrix(
    rows: list[dict[str, str]],
) -> list[BriefFinding]:
    findings: list[BriefFinding] = []
    for row in rows:
        title = row.get("Investment Area", "")
        rationale_points = _extract_cell_points(
            row.get("Why It Is Smart for Summer 2026", "")
        )
        enabler_points = _extract_cell_points(
            row.get("Key Enablers / Risk-Mitigations", "")
        )
        claim = rationale_points[0] if rationale_points else title
        evidence_points = rationale_points[1:]
        implication = _join_cell_points(enabler_points)
        findings.append(
            BriefFinding(
                title=title or "Consensus finding",
                claim=claim,
                evidence_points=evidence_points,
                implication=implication,
                confidence="directional",
            )
        )
    return findings


def _build_decision_implications_from_consensus_matrix(
    rows: list[dict[str, str]],
) -> list[str]:
    implications: list[str] = []
    for row in rows:
        area = row.get("Investment Area", "")
        enablers = _join_cell_points(
            _extract_cell_points(row.get("Key Enablers / Risk-Mitigations", ""))
        )
        if not enablers:
            continue
        implications.append(f"{area}: {enablers}" if area else enablers)
    return implications


def _build_recommendations_from_consensus_matrix(
    rows: list[dict[str, str]],
) -> list[BriefRecommendation]:
    recommendations: list[BriefRecommendation] = []
    for row in rows:
        action = _join_cell_points(
            _extract_cell_points(row.get("What to Do (2025-2026)", ""))
        )
        if not action:
            continue
        recommendations.append(
            BriefRecommendation(
                action=action,
                owner=row.get("Investment Area", ""),
                expected_impact=_join_cell_points(
                    _extract_cell_points(row.get("Why It Is Smart for Summer 2026", ""))
                ),
            )
        )
    return recommendations


def _parse_markdown_sections(text: str) -> tuple[str, dict[str, list[str]]]:
    intro_lines: list[str] = []
    current_heading = ""
    current_lines: list[str] = []
    sections: dict[str, list[str]] = {}

    for raw_line in str(text).replace("\r\n", "\n").splitlines():
        stripped = raw_line.strip()
        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            if current_heading:
                sections[current_heading] = current_lines
            current_heading = _normalize_heading_key(
                _clean_markdown_line(heading_match.group(1))
            )
            current_lines = []
            continue

        if current_heading:
            current_lines.append(raw_line)
        else:
            intro_lines.append(raw_line)

    if current_heading:
        sections[current_heading] = current_lines

    return _clean_markdown_text("\n".join(intro_lines)), sections


def _parse_list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        if not _looks_like_list_line(raw_line):
            index += 1
            continue

        current = [_clean_markdown_line(raw_line)]
        index += 1
        while index < len(lines) and _looks_like_continuation_line(lines[index]):
            current.append(_clean_markdown_line(lines[index]))
            index += 1

        item = _join_point_parts(current)
        if item:
            items.append(item)
    return items


def _parse_markdown_table(lines: list[str]) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []

    headers = _parse_markdown_table_row(table_lines[0])
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = _parse_markdown_table_row(line)
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def _parse_markdown_table_row(line: str) -> list[str]:
    raw_cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return [_clean_markdown_line(cell) for cell in raw_cells]


def _parse_inline_consensus_matrix(text: str) -> tuple[str, list[dict[str, str]]]:
    # Legacy fallback for pre-structured roundtable summaries that flattened a matrix into
    # a single prose block. New roundtables should use `consensus_brief` instead.
    marker = "Investment Area |"
    if marker not in text:
        return "", []

    prefix, _, remainder = str(text).partition(marker)
    title = _extract_consensus_title(prefix)
    raw_cells = [cell.strip() for cell in f"{marker}{remainder}".split("|")]
    cells = [cell for cell in raw_cells if cell.strip()]
    if len(cells) < 8:
        return title, []

    headers = [_clean_markdown_text(cell) for cell in cells[:4]]
    if headers[0].lower() != "investment area":
        return title, []

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    row_cells = cells[4:]
    for index in range(0, len(row_cells) - 3, 4):
        chunk = row_cells[index : index + 4]
        first_cell = _clean_cell_text(chunk[0])
        if first_cell.lower().startswith("consensus answer"):
            break

        values: tuple[str, ...] = tuple(_clean_cell_text(cell) for cell in chunk)
        if not values[0] or values in seen:
            continue
        seen.add(values)
        rows.append(dict(zip(headers, values)))

    return title, rows


def _extract_consensus_title(text: str) -> str:
    flattened = " ".join(str(text).split())
    match = _CONSENSUS_TITLE_RE.search(flattened)
    if match:
        return _clean_markdown_line(match.group(1))
    cleaned = _clean_markdown_text(text)
    if cleaned.lower() in {"executive summary", "governing insight"}:
        return ""
    return cleaned


def _collapse_duplicate_consensus_sections(text: str) -> str:
    normalized = str(text).replace("\r\n", "\n").strip()
    matches = list(_CONSENSUS_SECTION_START_RE.finditer(normalized))
    if len(matches) < 2:
        return normalized

    first_start = matches[0].start()
    second_start = matches[1].start()
    first_block = normalized[first_start:second_start].strip()
    second_block = normalized[second_start:].strip()
    if _normalize_whitespace(first_block) != _normalize_whitespace(second_block):
        return normalized

    prefix = normalized[:first_start].strip()
    if not prefix:
        return first_block
    return f"{prefix}\n{first_block}"


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _clean_cell_text(text: str) -> str:
    lines = [_clean_markdown_line(line) for line in str(text).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extract_cell_points(text: str) -> list[str]:
    points = [_clean_markdown_line(line) for line in str(text).splitlines()]
    return [point for point in points if point]


def _join_cell_points(points: list[str]) -> str:
    cleaned = [point.strip() for point in points if point.strip()]
    return "; ".join(cleaned)


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
        lines.extend(["## Sources", ""])
        for source in brief.sources:
            lines.append(f"- {source}")
        lines.append("")

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


def _title_case_query(text: str) -> str:
    """Title-case a user query for display as a brief title (AP-style minor words)."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    words = cleaned.split()
    last = len(words) - 1
    result: list[str] = []
    for index, word in enumerate(words):
        core = word.strip("?!.,;:\"'()[]“”‘’")
        if not core:
            result.append(word)
            continue
        is_edge = index == 0 or index == last
        is_minor = core.lower() in _TITLE_MINOR_WORDS
        cased_core = (
            core.lower()
            if is_minor and not is_edge
            else (core[0].upper() + core[1:].lower() if len(core) > 1 else core.upper())
        )
        result.append(word.replace(core, cased_core, 1))
    return " ".join(result)


def _split_into_sentences(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    return [
        piece.strip() for piece in _SENTENCE_SPLIT_RE.split(cleaned) if piece.strip()
    ]


def _chunk_sentences_into_paragraphs(
    sentences: list[str],
    sentences_per_paragraph: int = _SUMMARY_SENTENCES_PER_PARAGRAPH,
) -> list[str]:
    paragraphs: list[str] = []
    for start in range(0, len(sentences), sentences_per_paragraph):
        chunk = " ".join(sentences[start : start + sentences_per_paragraph]).strip()
        if chunk:
            paragraphs.append(chunk)
    return paragraphs


def _break_long_text_into_paragraphs(
    text: str,
    sentences_per_paragraph: int = _SUMMARY_SENTENCES_PER_PARAGRAPH,
) -> list[str]:
    """Return the input as one paragraph per ~N sentences, preserving short text as-is."""
    sentences = _split_into_sentences(text)
    if len(sentences) <= sentences_per_paragraph:
        return [text.strip()] if text.strip() else []
    return _chunk_sentences_into_paragraphs(sentences, sentences_per_paragraph)


def _extract_headline_and_body(
    insight: str,
    max_headline_chars: int = _HEADLINE_MAX_CHARS,
) -> tuple[str, list[str]]:
    """Split an over-long governing insight into a short headline plus body paragraphs."""
    cleaned = insight.strip()
    if not cleaned or len(cleaned) <= max_headline_chars:
        return cleaned, []

    sentences = _split_into_sentences(cleaned)
    if len(sentences) <= 1:
        return cleaned, []

    headline_sentences: list[str] = []
    headline_len = 0
    for sentence in sentences:
        if headline_sentences and headline_len + len(sentence) + 1 > max_headline_chars:
            break
        headline_sentences.append(sentence)
        headline_len += len(sentence) + 1

    headline = " ".join(headline_sentences).strip()
    remainder = sentences[len(headline_sentences) :]
    body_paragraphs = _chunk_sentences_into_paragraphs(remainder)
    return headline, body_paragraphs


def _compose_executive_summary(
    headline: str,
    remainder_paragraphs: list[str],
    existing_summary: list[str],
    original_insight: str = "",
) -> list[str]:
    """Combine extracted body with LLM-provided summary, deduping against the headline."""
    headline_key = _normalize_whitespace(headline)
    original_key = _normalize_whitespace(original_insight)
    seen: set[str] = set()
    if headline_key:
        seen.add(headline_key)
    if original_key:
        seen.add(original_key)
    paragraphs: list[str] = []

    def _add(text: str) -> None:
        key = _normalize_whitespace(text)
        if not key or key in seen:
            return
        seen.add(key)
        paragraphs.append(text)

    for paragraph in remainder_paragraphs:
        cleaned = (
            paragraph.strip()
            if isinstance(paragraph, str)
            else _coerce_to_string(paragraph)
        )
        if cleaned:
            _add(cleaned)

    for entry in existing_summary:
        cleaned = entry.strip() if isinstance(entry, str) else _coerce_to_string(entry)
        if not cleaned:
            continue
        cleaned_key = _normalize_whitespace(cleaned)
        if cleaned_key in seen:
            continue
        # If the entry restates the original insight wholesale, skip it entirely
        # rather than letting its sentence-chunked version leak back in.
        if original_key and cleaned_key == original_key:
            continue
        for chunk in _break_long_text_into_paragraphs(cleaned):
            _add(chunk)

    return paragraphs


def _split_labeled_text(text: str) -> tuple[str, str]:
    if ":" not in text:
        return text, ""
    label, body = text.split(":", 1)
    cleaned_label = label.strip()
    cleaned_body = body.strip()
    if 0 < len(cleaned_label.split()) <= 8 and cleaned_body:
        return cleaned_label, cleaned_body
    return text, ""


def _normalize_heading_key(text: str) -> str:
    return _clean_markdown_line(text).lower()


def _extract_bold_only_text(text: str) -> str:
    match = _BOLD_ONLY_RE.match(text)
    if not match:
        return ""
    return _clean_markdown_line(match.group(1))


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _format_timestamp(raw_value: Any) -> str:
    text = str(raw_value or "").strip()
    if not text:
        return ""

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return text
    return parsed.strftime("%B %d, %Y %H:%M")


def _extract_evidence_points(text: str) -> list[str]:
    blocks = _split_blocks(text)
    if not blocks:
        return []

    summary = _extract_summary(text)
    section_points: list[str] = []
    for block in blocks[1:]:
        point = _block_to_point(block)
        if point and point != summary and point not in section_points:
            section_points.append(point)
        if len(section_points) >= 3:
            return section_points

    if section_points:
        return section_points

    list_points = _extract_list_points(text, summary)
    return list_points[:3]


def _extract_summary(text: str) -> str:
    blocks = _split_blocks(text)
    if not blocks:
        return ""
    return _clean_markdown_text(" ".join(blocks[0]))


def _extract_list_points(text: str, summary: str) -> list[str]:
    points: list[str] = []
    lines = [line.rstrip() for line in text.splitlines()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _looks_like_list_line(line):
            index += 1
            continue

        current = [_clean_markdown_line(line)]
        index += 1
        while index < len(lines) and _looks_like_continuation_line(lines[index]):
            current.append(_clean_markdown_line(lines[index]))
            index += 1

        point = _join_point_parts(current)
        if point and point != summary and point not in points:
            points.append(point)
        if len(points) >= 3:
            break
    return points


def _split_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in str(text).replace("\r\n", "\n").splitlines():
        line = raw_line.rstrip()
        if _HORIZONTAL_RULE_RE.match(line):
            if current:
                blocks.append(current)
                current = []
            continue
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _block_to_point(block: list[str]) -> str:
    cleaned_lines = [
        _clean_markdown_line(line) for line in block if _clean_markdown_line(line)
    ]
    if not cleaned_lines:
        return ""

    heading = ""
    details: list[str] = []
    for raw_line in block:
        cleaned = _clean_markdown_line(raw_line)
        if not cleaned:
            continue
        if not heading and _looks_like_heading(raw_line):
            heading = _remove_label_prefix(cleaned)
            continue
        detail = _remove_label_prefix(cleaned)
        if detail and detail != heading:
            details.append(detail)

    if heading and details:
        return _join_point_parts([heading, details[0]])
    if heading:
        return heading
    return cleaned_lines[0]


def _clean_markdown_text(text: str) -> str:
    parts = [_clean_markdown_line(line) for line in str(text).splitlines()]
    return " ".join(part for part in parts if part).strip()


def _clean_markdown_line(text: str) -> str:
    line = str(text).strip()
    if not line or _HORIZONTAL_RULE_RE.match(line):
        return ""

    line = _LINK_RE.sub(r"\1", line)
    line = _HEADING_RE.sub(r"\1", line)
    line = _DECORATIVE_PREFIX_RE.sub("", line)
    line = _UNORDERED_PREFIX_RE.sub("", line)
    line = _ORDERED_PREFIX_RE.sub("", line)
    line = line.replace("**", "").replace("__", "").replace("*", "").replace("`", "")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def _join_point_parts(parts: list[str]) -> str:
    cleaned = [part.strip(" :-") for part in parts if part.strip(" :-")]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return f"{cleaned[0]}: {cleaned[1]}"


def _remove_label_prefix(text: str) -> str:
    return _LABEL_PREFIX_RE.sub("", text).strip()


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if _HEADING_RE.match(stripped):
        return True
    return bool(re.match(r"^[•▪◦🔹🔸]?\s*\d+[.)]\s+", stripped))


def _looks_like_list_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(
        _UNORDERED_PREFIX_RE.match(stripped) or _ORDERED_PREFIX_RE.match(stripped)
    )


def _looks_like_continuation_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if (
        _looks_like_list_line(stripped)
        or _looks_like_heading(stripped)
        or _HORIZONTAL_RULE_RE.match(stripped)
    ):
        return False
    return True


def _first_non_empty(values: Any) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return ""


def _compact_metrics(
    metrics: list[BriefMetric | None],
) -> list[BriefMetric]:
    return [metric for metric in metrics if metric is not None]
