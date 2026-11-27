"""Multi-pass editorial evaluation and Generative Engine Optimization (GEO) scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

HYPE_PATTERNS = [
    r"\brevolutionary\b",
    r"\bgame-changing\b",
    r"\bdestroys\s+all\b",
    r"\bunprecedented\b",
    r"\bmiracle[s]?\b",
    r"\bflawless\b",
    r"\b10x\s+better\b",
]
_HYPE_RE = re.compile("|".join(HYPE_PATTERNS), re.IGNORECASE)

# Pattern detecting suspicious unflagged raw percentages or high user claims
_RAW_METRIC_RE = re.compile(
    r"\b(?:99\.\d+%|\d{2,3}(?:,\d{3})+\s+(?:users|downloads|requests)|\b\d+%\s+uptime\b)",
    re.IGNORECASE,
)


@dataclass
class EditorialEvalResult:
    voice_score: float
    precision_score: float
    geo_score: float
    total_score: float
    grade: str
    findings: list[str] = field(default_factory=list)
    is_publishable: bool = False


def _calculate_grade(score: float) -> str:
    if score >= 90.0:
        return "S"
    if score >= 80.0:
        return "A"
    if score >= 70.0:
        return "B"
    if score >= 60.0:
        return "C"
    if score >= 50.0:
        return "D"
    return "F"


def evaluate_editorial_quality(
    content: str, verified_facts: dict[str, Any] | None = None
) -> EditorialEvalResult:
    """Evaluate content for Beer's authentic voice, technical precision, and GEO citation readiness."""
    findings: list[str] = []

    # 1. Voice & Authenticity Score (Max 35)
    voice_score = 35.0
    hype_matches = _HYPE_RE.findall(content)
    if hype_matches:
        deduction = min(len(hype_matches) * 12.0, 30.0)
        voice_score = max(0.0, voice_score - deduction)
        findings.append(
            f"Detected excessive hype/buzzwords: {', '.join(set(hype_matches))}. Voice must remain humble and grounded."
        )

    # 2. Technical Precision Score (Max 35)
    precision_score = 35.0
    # Check for raw metrics that are not flagged as pending and not in verified_facts
    has_pending_flag = "[PENDING VERIFICATION" in content
    raw_metric_matches = _RAW_METRIC_RE.findall(content)
    if raw_metric_matches and not has_pending_flag and not verified_facts:
        precision_score = max(10.0, precision_score - 15.0)
        findings.append(
            f"Detected raw unverified metrics ({', '.join(raw_metric_matches)}) without [PENDING VERIFICATION] flags."
        )

    # 3. GEO & AI Citation Readiness Score (Max 30)
    geo_score = 15.0
    if re.search(r"^#{1,4}\s+", content, re.MULTILINE):
        geo_score += 5.0
    if re.search(r"^\s*[-*]\s+", content, re.MULTILINE):
        geo_score += 5.0
    if "```" in content or re.search(
        r"\b(?:according to|metrics|definition)\b", content, re.IGNORECASE
    ):
        geo_score += 5.0
    geo_score = min(30.0, geo_score)

    total = round(voice_score + precision_score + geo_score, 1)
    grade = _calculate_grade(total)
    is_pub = total >= 70.0 and voice_score >= 25.0 and precision_score >= 25.0

    return EditorialEvalResult(
        voice_score=voice_score,
        precision_score=precision_score,
        geo_score=geo_score,
        total_score=total,
        grade=grade,
        findings=findings,
        is_publishable=is_pub,
    )
