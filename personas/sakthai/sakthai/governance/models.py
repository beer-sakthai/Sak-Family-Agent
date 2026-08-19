"""Domain models for Autonomous CI/CD Doctor & Mutation Governance."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class IssueSeverity(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DiagnosticIssue:
    code: str
    message: str
    severity: IssueSeverity
    file_path: str | None = None
    remediation_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class DiagnosticReport:
    health_score: int
    total_checks: int
    passed_checks: int
    issues: list[DiagnosticIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_score": self.health_score,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "issues": [i.to_dict() for i in self.issues],
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AutoHealResult:
    success: bool
    actions_taken: list[str] = field(default_factory=list)
    resolved_issues_count: int = 0
    remaining_issues_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "actions_taken": self.actions_taken,
            "resolved_issues_count": self.resolved_issues_count,
            "remaining_issues_count": self.remaining_issues_count,
            "timestamp": self.timestamp.isoformat(),
        }
