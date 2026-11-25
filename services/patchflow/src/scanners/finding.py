"""Common finding representation across all vulnerability and error sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class Finding:
    """Standardized finding extracted from security scans, linters, or test suites."""

    id: str
    source: Literal["dependabot", "linter", "test_failure"]
    file_path: str
    line_number: int | None = None
    rule_id: str = ""
    description: str = ""
    severity: Literal["critical", "high", "medium", "low", "info"] = "medium"
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation."""
        return asdict(self)
