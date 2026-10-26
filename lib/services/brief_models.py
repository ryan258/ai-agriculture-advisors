"""Presentation data models shared by current rendering and legacy readers."""

from dataclasses import dataclass, field
from typing import Any


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
    workflow_handoff: dict[str, Any] = field(default_factory=dict)
    workflow_handoff_text: str = ""
    accessibility_handoff: dict[str, Any] = field(default_factory=dict)
    accessibility_handoff_text: str = ""
    supplied_sources: list[dict[str, str]] = field(default_factory=list)
    execution_receipts: list[dict[str, Any]] = field(default_factory=list)
    decision_analysis: dict[str, Any] = field(default_factory=dict)
