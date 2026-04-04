"""Build executive brief HTML from saved advisory results."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from executive_reporting import (
    BriefMetadataItem,
    BriefFinding,
    BriefRecommendation,
    EvidenceMetric,
    EvidenceObservation,
    EvidencePackage,
    ExecutiveBrief,
    ExecutiveBriefingComponent,
    StrategicAnalysisPlugin,
)


_ORGANIZATION = "AI Agriculture Advisors"
_HEADER_LABEL = "Agricultural Advisory"
_PUBLICATION_LABEL = "Executive Brief"
_HORIZONTAL_RULE_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*$")
_ORDERED_PREFIX_RE = re.compile(r"^\s*\d+[.)]\s*")
_UNORDERED_PREFIX_RE = re.compile(r"^\s*[-+*•▪◦]\s*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_DECORATIVE_PREFIX_RE = re.compile(r"^[^\w(]+")
_LABEL_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 /&()'’+-]{1,40}:\s*")
_BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")
_BOLD_PREFIX_RE = re.compile(r"^\*\*(.+?)\*\*:\s*(.+)$")


def build_executive_brief_html(result: dict[str, Any]) -> str:
    """Render a saved query or roundtable result as executive-brief HTML."""
    component = ExecutiveBriefingComponent(
        plugin=StrategicAnalysisPlugin(
            organization=_ORGANIZATION,
            header_label=_HEADER_LABEL,
            publication_label=_PUBLICATION_LABEL,
        )
    )
    return component.render_html(_build_brief_payload(result))


def _build_brief_payload(result: dict[str, Any]) -> EvidencePackage | ExecutiveBrief:
    if result.get("result_type") == "roundtable":
        return _build_roundtable_brief(result)
    return _build_query_evidence(result)


def _build_query_evidence(result: dict[str, Any]) -> EvidencePackage:
    responses = result.get("responses", [])
    successful = [item for item in responses if item.get("response")]
    failures = [item for item in responses if item.get("error")]

    governing_insight = _first_non_empty(
        _extract_summary(item.get("response", "")) for item in successful
    )
    if not governing_insight:
        governing_insight = "No successful advisor responses were available for synthesis."

    observations = [
        EvidenceObservation(
            title=item.get("label", item.get("role", "Advisor")),
            summary=_extract_summary(item.get("response", "")),
            evidence_points=_extract_evidence_points(item.get("response", "")),
            significance=(
                f"Use the {item.get('label', item.get('role', 'advisor'))} perspective "
                "to pressure-test the final recommendation."
            ),
            confidence="directional",
            source_refs=[item.get("role", "")],
        )
        for item in successful
        if _extract_summary(item.get("response", ""))
    ]

    if failures:
        observations.append(
            EvidenceObservation(
                title="Delivery gaps",
                summary=(
                    f"{len(failures)} advisor response(s) failed and were excluded from the brief."
                ),
                evidence_points=[
                    f"{item.get('label', item.get('role', 'Advisor'))}: {item.get('error', 'Unknown error')}"
                    for item in failures[:3]
                ],
                significance=(
                    "Rerun the query or inspect logs before treating the synthesis as complete."
                ),
                confidence="low",
            )
        )

    query = result.get("query", "Agricultural advisory query")
    return EvidencePackage(
        package_id=result.get("id", ""),
        subject=query,
        governing_question=query,
        governing_insight=governing_insight,
        summary_metrics=_compact_metrics(
            [
                EvidenceMetric(
                    label="Experts Consulted",
                    value=str(len(result.get("experts", []))),
                ),
                EvidenceMetric(
                    label="Successful Responses",
                    value=str(len(successful)),
                ),
                EvidenceMetric(
                    label="Failed Responses",
                    value=str(len(failures)),
                )
                if failures
                else None,
            ]
        ),
        observations=observations,
        methodology=[
            "Built from saved expert responses in AI Agriculture Advisors.",
            "Rendered into a decision-ready brief without re-querying the LLM providers.",
        ],
        limitations=[
            "This brief is a structural synthesis of stored advisor outputs.",
            "Conflicting expert recommendations still require user judgment.",
        ],
        sources=[
            item.get("label", item.get("role", "Advisor"))
            for item in successful
        ],
        metadata=_build_metadata(
            result,
            subtitle="Expert Query Synthesis",
            headline=governing_insight,
        ),
    )


def _build_roundtable_brief(result: dict[str, Any]) -> ExecutiveBrief:
    transcript = result.get("transcript", [])
    final_answer = str(result.get("final_answer", "")).strip() or (
        "No consensus answer was available from the saved roundtable."
    )
    intro, sections = _parse_markdown_sections(final_answer)
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

    governing_insight = (
        bottom_line
        or _first_non_empty(
            finding.claim for finding in key_findings
        )
        or intro
        or _clean_markdown_text(final_answer)
    )

    executive_summary = [item for item in [intro, bottom_line] if item]
    if not executive_summary:
        executive_summary = [governing_insight]

    if not key_findings:
        fallback_summary = _extract_summary(final_answer)
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

    query = result.get("query", "Agricultural advisory roundtable")
    return ExecutiveBrief(
        brief_id=result.get("id", ""),
        title=query,
        subtitle="Roundtable Consensus",
        kicker=_HEADER_LABEL,
        organization=_ORGANIZATION,
        publication_label=_PUBLICATION_LABEL,
        date_label=_format_timestamp(result.get("timestamp")),
        headline=governing_insight,
        governing_question=query,
        governing_insight=governing_insight,
        executive_summary=executive_summary,
        top_metrics=_compact_metrics(
            [
                EvidenceMetric(label="Participants", value=str(len(result.get("experts", [])))),
                EvidenceMetric(label="Rounds", value=str(result.get("rounds", 0))),
                EvidenceMetric(label="Contributions", value=str(len(transcript))),
            ]
        ),
        key_findings=key_findings,
        decision_implications=decision_implications,
        recommendations=recommendations,
        methodology=[
            "Built from a saved multi-expert roundtable transcript.",
            "Consensus text came from the moderator synthesis stored with the result.",
        ],
        limitations=limitations,
        sources=sources,
    )


def _build_metadata(
    result: dict[str, Any],
    *,
    subtitle: str,
    headline: str,
) -> list[BriefMetadataItem]:
    return [
        BriefMetadataItem(label="organization", value=_ORGANIZATION),
        BriefMetadataItem(label="publication", value=_PUBLICATION_LABEL),
        BriefMetadataItem(label="date", value=_format_timestamp(result.get("timestamp"))),
        BriefMetadataItem(label="subtitle", value=subtitle),
        BriefMetadataItem(label="headline", value=headline),
    ]


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
        if bottom_match and _clean_markdown_line(bottom_match.group(1)).lower() == "bottom line":
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
            current_heading = _normalize_heading_key(_clean_markdown_line(heading_match.group(1)))
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
    cleaned_lines = [_clean_markdown_line(line) for line in block if _clean_markdown_line(line)]
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
    return bool(_UNORDERED_PREFIX_RE.match(stripped) or _ORDERED_PREFIX_RE.match(stripped))


def _looks_like_continuation_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _looks_like_list_line(stripped) or _looks_like_heading(stripped) or _HORIZONTAL_RULE_RE.match(stripped):
        return False
    return True


def _first_non_empty(values: Any) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return ""


def _compact_metrics(
    metrics: list[EvidenceMetric | None],
) -> list[EvidenceMetric]:
    return [metric for metric in metrics if metric is not None]
