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
            re.compile(r"\bgsutil\s+rm\s+((?:-[a-zA-Z-]+\s+)*)(.+)"),
            "Cloud Storage bucket/object deletion",
        ),
        (re.compile(r"\bbq\s+rm\s+((?:-[a-zA-Z-]+\s+)*)(.+)"), "BigQuery table/dataset deletion"),
        (
            re.compile(
                r"(?:^|[;&|]\s*)\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(.+)"
            ),
            "Destructive file deletion",
        ),
    ]

    DESTRUCTIVE_SQL_PATTERNS = [
        (
            re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
            "Destructive database operation (DROP)",
        ),
        (
            re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?", re.IGNORECASE),
            "Destructive database operation (TRUNCATE)",
        ),
        (
            re.compile(r"\bDELETE\s+FROM\s+[`\"'\w-]+(?:[\.`\"'\w-]+)*\s*(?:;|$)", re.IGNORECASE),
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
                impact_target = (
                    match.group(2) if len(match.groups()) >= 2 and match.group(2) else cleaned
                )
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
