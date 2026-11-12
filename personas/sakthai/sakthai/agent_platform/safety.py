import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyCheckResult:
    is_destructive: bool
    reason: str
    impact: str
    blocked: bool


class DataLossGuardrail:
    DESTRUCTIVE_SHELL_PATTERNS = [
        (
            re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(.+)"),
            "Destructive file deletion",
        ),
        (
            re.compile(r"\bgsutil\s+rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(.+)"),
            "Cloud Storage bucket/object deletion",
        ),
        (
            re.compile(r"\bbq\s+rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(.+)"),
            "BigQuery table/dataset deletion",
        ),
        (
            re.compile(r"\bgit\s+reset\s+--hard\b"),
            "Destructive git worktree/commit reset",
        ),
        (
            re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*\s*(.*)"),
            "Destructive git untracked file removal",
        ),
        (
            re.compile(r"\bmkfs(?:\.\w+)?\s+(.+)"),
            "Destructive filesystem format operation",
        ),
        (
            re.compile(r"\bdd\s+.*of=/dev/(.+)"),
            "Destructive direct disk/device write",
        ),
        (
            re.compile(r"\bterraform\s+destroy\b"),
            "Infrastructure destruction (terraform destroy)",
        ),
        (
            re.compile(r"\bkubectl\s+delete\s+(?:namespace|ns|all)\b"),
            "Destructive Kubernetes cluster resource deletion",
        ),
    ]

    DESTRUCTIVE_SQL_PATTERNS = [
        (
            re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
            "Destructive database operation (DROP)",
        ),
        (
            re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
            "Destructive database operation (TRUNCATE)",
        ),
        (
            re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", re.IGNORECASE),
            "Unbounded DELETE operation without WHERE clause",
        ),
    ]

    def generate_approval_token(self, command: str) -> str:
        cleaned = command.strip()
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]
        return f"APPROVE_{digest}"

    def inspect(self, command: str) -> SafetyCheckResult:
        cleaned = command.strip()
        for pattern, desc in self.DESTRUCTIVE_SHELL_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    impact_target = groups[1]
                elif len(groups) >= 1 and groups[0]:
                    impact_target = groups[0]
                else:
                    impact_target = cleaned
                return SafetyCheckResult(
                    is_destructive=True,
                    reason=desc,
                    impact=f"Potential data loss on target: {impact_target.strip()}",
                    blocked=True,
                )

        for pattern, desc in self.DESTRUCTIVE_SQL_PATTERNS:
            if pattern.search(cleaned):
                return SafetyCheckResult(
                    is_destructive=True,
                    reason=desc,
                    impact=f"Irreversible modification of database entity: {cleaned}",
                    blocked=True,
                )

        return SafetyCheckResult(
            is_destructive=False,
            reason="Command verified safe",
            impact="None",
            blocked=False,
        )

    def verify_or_halt(self, command: str, approval_token: str | None = None) -> SafetyCheckResult:
        check = self.inspect(command)
        if not check.is_destructive:
            return check

        expected_token = self.generate_approval_token(command)
        if approval_token == expected_token:
            return SafetyCheckResult(
                is_destructive=True,
                reason=f"{check.reason} (Explicitly authorized)",
                impact=check.impact,
                blocked=False,
            )

        return check
