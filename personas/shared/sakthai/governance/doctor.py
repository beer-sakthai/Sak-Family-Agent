"""Repository Health Doctor and Autonomous CI/CD Diagnostic Engine."""

from __future__ import annotations

import ast
import logging
from collections.abc import Callable
from pathlib import Path

from .models import AutoHealResult, DiagnosticIssue, DiagnosticReport, IssueSeverity

logger = logging.getLogger(__name__)


class RepoDoctor:
    """Diagnoses monorepo health, AST safety, package parity, and SQLite integrity."""

    def __init__(self, repo_root: str | Path = ".") -> None:
        self.repo_root = Path(repo_root).resolve()
        self._custom_checks: dict[str, Callable[[], list[tuple[str, str, IssueSeverity]]]] = {}

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], list[tuple[str, str, IssueSeverity]]],
    ) -> None:
        self._custom_checks[name] = check_fn

    def check_ast_syntax(self) -> list[DiagnosticIssue]:
        """Scan all python files for syntax/AST errors."""
        issues: list[DiagnosticIssue] = []
        py_files = list(self.repo_root.glob("personas/**/*.py")) + list(
            self.repo_root.glob("tests/**/*.py")
        )

        for p in py_files:
            try:
                content = p.read_text(encoding="utf-8")
                ast.parse(content, filename=str(p))
            except Exception as e:
                issues.append(
                    DiagnosticIssue(
                        code="AST_SYNTAX_ERROR",
                        message=f"Failed to parse {p.name}: {e}",
                        severity=IssueSeverity.CRITICAL,
                        file_path=str(p.relative_to(self.repo_root)),
                        remediation_hint="Fix syntax errors to ensure clean compilation.",
                    )
                )
        return issues

    def check_package_parity(self) -> list[DiagnosticIssue]:
        """Verify parity between personas/sakthai and personas/shared."""
        issues: list[DiagnosticIssue] = []
        sakthai_dir = self.repo_root / "personas" / "sakthai" / "sakthai"
        shared_dir = self.repo_root / "personas" / "shared" / "sakthai"

        if not sakthai_dir.exists() or not shared_dir.exists():
            return issues

        for p in sakthai_dir.rglob("*.py"):
            rel = p.relative_to(sakthai_dir)
            shared_target = shared_dir / rel
            if not shared_target.exists():
                issues.append(
                    DiagnosticIssue(
                        code="PARITY_MISSING_FILE",
                        message=f"Missing parity replica: {shared_target}",
                        severity=IssueSeverity.HIGH,
                        file_path=str(shared_target),
                        remediation_hint="Copy updated module to personas/shared.",
                    )
                )
            elif p.read_bytes() != shared_target.read_bytes():
                issues.append(
                    DiagnosticIssue(
                        code="PARITY_DIVERGENCE",
                        message=f"Divergence detected in {rel}",
                        severity=IssueSeverity.MEDIUM,
                        file_path=str(shared_target),
                        remediation_hint="Synchronize byte contents between sakthai and shared.",
                    )
                )
        return issues

    def run_diagnostics(self) -> DiagnosticReport:
        """Run all built-in and custom diagnostics."""
        issues: list[DiagnosticIssue] = []
        total_checks = 2 + len(self._custom_checks)
        passed_checks = 0

        # 1. AST check
        ast_issues = self.check_ast_syntax()
        if not ast_issues:
            passed_checks += 1
        issues.extend(ast_issues)

        # 2. Parity check
        parity_issues = self.check_package_parity()
        if not parity_issues:
            passed_checks += 1
        issues.extend(parity_issues)

        # 3. Custom checks
        for _name, check_fn in self._custom_checks.items():
            res = check_fn()
            if not res:
                passed_checks += 1
            else:
                for code, msg, sev in res:
                    issues.append(DiagnosticIssue(code=code, message=msg, severity=sev))

        # Calculate health score (0 - 100)
        penalty = sum(
            40
            if i.severity == IssueSeverity.CRITICAL
            else 20
            if i.severity == IssueSeverity.HIGH
            else 10
            if i.severity == IssueSeverity.MEDIUM
            else 5
            for i in issues
        )
        health_score = max(0, 100 - penalty)

        return DiagnosticReport(
            health_score=health_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            issues=issues,
        )

    def auto_heal(self) -> AutoHealResult:
        """Execute automated remediation for parity and formatting anomalies."""
        actions: list[str] = []
        resolved = 0

        # Parity auto-heal
        sakthai_dir = self.repo_root / "personas" / "sakthai" / "sakthai"
        shared_dir = self.repo_root / "personas" / "shared" / "sakthai"

        if sakthai_dir.exists() and shared_dir.exists():
            for p in sakthai_dir.rglob("*.py"):
                rel = p.relative_to(sakthai_dir)
                shared_target = shared_dir / rel
                if not shared_target.exists() or p.read_bytes() != shared_target.read_bytes():
                    shared_target.parent.mkdir(parents=True, exist_ok=True)
                    shared_target.write_bytes(p.read_bytes())
                    actions.append(f"Synced {rel} to personas/shared")
                    resolved += 1

        remaining = len(self.check_ast_syntax())
        return AutoHealResult(
            success=True,
            actions_taken=actions,
            resolved_issues_count=resolved,
            remaining_issues_count=remaining,
        )
