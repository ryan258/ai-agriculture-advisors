"""Compatibility parsing and display cleanup; no provider calls or storage effects."""

from __future__ import annotations
import re
from datetime import datetime
from typing import Any
from lib.experts.response_format import extract_compact_ending
from ._text_utils import (
    clean_string_list as _clean_string_list,
    coerce_to_string as _coerce_to_string,
)
from .brief_models import BriefFinding, BriefRecommendation, BriefMetric

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


def _without_decision_check(text: str) -> str:
    """Keep a plain-text handoff intact while leaving its ending to the saved check."""
    source = str(text).replace("\r\n", "\n")
    if not extract_compact_ending(source):
        return source.strip()
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^[ \t]*[-*][ \t]+(?:\*\*)?Recommended next step:", line):
            source = "\n".join(lines[:index])
            break

    lines: list[str] = []
    skipping = False
    for line in source.splitlines():
        heading = _HEADING_RE.match(line.strip())
        if heading:
            skipping = (
                _normalize_heading_key(_clean_markdown_line(heading.group(1)))
                == "decision check"
            )
        if not skipping:
            lines.append(line)
    return "\n".join(lines).strip()


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
