"""Linter finding parser for Ruff, Mypy, and Bandit."""

from __future__ import annotations

import json
from typing import Any

from .finding import Finding


class LinterScanner:
    """Ingests findings from Ruff, Mypy, and Bandit."""

    @staticmethod
    def parse_ruff(output: list[dict[str, Any]] | str) -> list[Finding]:
        """Parse ruff check --output-format json output."""
        if isinstance(output, str):
            try:
                data = json.loads(output)
            except Exception:
                return []
        else:
            data = output

        findings: list[Finding] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            code = item.get("code", "RUFF")
            message = item.get("message", "Lint finding")
            filename = item.get("filename", "")
            location = item.get("location", {})
            row = location.get("row")

            findings.append(
                Finding(
                    id=f"ruff-{idx}-{code}",
                    source="linter",
                    file_path=filename,
                    line_number=row,
                    rule_id=code,
                    description=message,
                    severity="low",
                    raw_payload=item,
                )
            )
        return findings

    @staticmethod
    def parse_bandit(output: dict[str, Any] | str) -> list[Finding]:
        """Parse bandit -f json output."""
        if isinstance(output, str):
            try:
                data = json.loads(output)
            except Exception:
                return []
        else:
            data = output

        results = data.get("results", [])
        findings: list[Finding] = []
        for idx, item in enumerate(results):
            test_id = item.get("test_id", "B000")
            issue_text = item.get("issue_text", "")
            filename = item.get("filename", "")
            line_num = item.get("line_number")
            sev = str(item.get("issue_severity", "MEDIUM")).lower()
            valid_sev = sev if sev in ("critical", "high", "medium", "low") else "medium"

            findings.append(
                Finding(
                    id=f"bandit-{idx}-{test_id}",
                    source="linter",
                    file_path=filename,
                    line_number=line_num,
                    rule_id=test_id,
                    description=issue_text,
                    severity=valid_sev,  # type: ignore[arg-type]
                    raw_payload=item,
                )
            )
        return findings
