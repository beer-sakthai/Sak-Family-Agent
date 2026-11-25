"""Dependabot and CVE alert scanner."""

from __future__ import annotations

import json
from typing import Any

from .finding import Finding


class DependabotScanner:
    """Ingests and normalizes Dependabot alerts and CVE notifications."""

    @staticmethod
    def parse_alerts(payload: list[dict[str, Any]] | str) -> list[Finding]:
        """Parse raw GitHub Dependabot API responses or JSON dumps."""
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except Exception:
                return []
        else:
            data = payload

        findings: list[Finding] = []
        for idx, alert in enumerate(data):
            if not isinstance(alert, dict):
                continue

            security_advisory = alert.get("security_advisory", {})
            package = alert.get("dependency", {}).get("package", {})
            manifest_path = alert.get("dependency", {}).get("manifest_path", "pyproject.toml")

            ghsa_id = security_advisory.get("ghsa_id") or alert.get("number", f"DEP-{idx}")
            summary = security_advisory.get("summary") or alert.get(
                "summary", "Dependency vulnerability"
            )
            cve_id = security_advisory.get("cve_id", "")
            rule_id = f"{ghsa_id} ({cve_id})" if cve_id else str(ghsa_id)
            severity = str(security_advisory.get("severity", "medium")).lower()

            valid_severity = (
                severity if severity in ("critical", "high", "medium", "low") else "medium"
            )

            pkg_name = package.get("name", "unknown")
            desc = f"{pkg_name}: {summary}"

            findings.append(
                Finding(
                    id=f"dependabot-{ghsa_id}",
                    source="dependabot",
                    file_path=manifest_path,
                    rule_id=rule_id,
                    description=desc,
                    severity=valid_severity,  # type: ignore[arg-type]
                    raw_payload=alert,
                )
            )

        return findings
