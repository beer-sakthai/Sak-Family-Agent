#!/usr/bin/env python3
"""CI Auto-Heal: automated recovery utility for lint, formatting, parity drift, and transient CI flakes.

Supports:
- Local multi-stage remediation (Ruff formatting & fixes, persona package parity sync, targeted pytest loops).
- GitHub Actions failure log parsing, automated classification, and family memory logging.
"""

from __future__ import annotations

import argparse
import enum
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class FailureCategory(str, enum.Enum):
    LINT_FORMAT = "lint/format"
    TYPE_CHECK = "type"
    UNIT_TEST_FAILURE = "test"
    FLAKY_NETWORK_TIMEOUT = "network/timeout"
    SECURITY_BANDIT = "security"
    UNKNOWN = "unknown"


@dataclass
class HealResult:
    success: bool
    format_passed: bool = True
    lint_passed: bool = True
    parity_passed: bool = True
    tests_passed: bool = True
    details: list[str] = field(default_factory=list)


def run_command(cmd: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository root and capture text output."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def classify_ci_failure(log_text: str) -> tuple[FailureCategory, str]:
    """Analyze failed CI logs and classify the root failure category."""
    # 1. Flaky network / timeout
    if re.search(r"Connection timed out|ReadTimeout|HTTPSConnectionPool|timed out after", log_text, re.IGNORECASE):
        match = re.search(r"(Connection timed out[^\n]*|ReadTimeout[^\n]*|timed out after[^\n]*)", log_text)
        return FailureCategory.FLAKY_NETWORK_TIMEOUT, match.group(1).strip() if match else "Network connection timed out"

    # 2. Security / Bandit AST scan
    if re.search(r"Run bandit|Issue:\s*\[B\d+:", log_text):
        match = re.search(r"Issue:\s*\[(B\d+:[^\]]+)\]", log_text)
        issue_name = match.group(1) if match else "Bandit security finding"
        return FailureCategory.SECURITY_BANDIT, f"Bandit AST check: {issue_name}"

    # 3. Type-check (mypy)
    if re.search(r"error:.*\[[a-z-]+\]|checked \d+ source files.*Found \d+ error", log_text):
        match = re.search(r"([^:\n]+:\d+:\s*error:[^\n]+)", log_text)
        error_line = match.group(1) if match else "mypy type checking failure"
        return FailureCategory.TYPE_CHECK, f"mypy: {error_line}"

    # 4. Lint / format (Ruff)
    if re.search(r"ruff check|ruff format|Found \d+ error|E\d{3}|F\d{3}|I\d{3}|B\d{3}", log_text):
        match = re.search(r"([^:\n]+:\d+:\d+:\s*[A-Z]\d{3}[^\n]+)", log_text)
        error_line = match.group(1) if match else "Ruff lint or formatting violation"
        return FailureCategory.LINT_FORMAT, f"Ruff: {error_line}"

    # 5. Unit test failure (pytest)
    if re.search(r"FAILED\s+tests/|=== FAILURES ===|AssertionError", log_text):
        match = re.search(r"FAILED\s+(tests/[^\s]+)", log_text)
        failed_test = match.group(1) if match else "pytest test failure"
        return FailureCategory.UNIT_TEST_FAILURE, f"pytest failure: {failed_test}"

    return FailureCategory.UNKNOWN, "Unknown failure signature in CI log"


def parse_failed_log(log_path: Path) -> tuple[FailureCategory, str]:
    """Read and classify a log file from disk."""
    if not log_path.is_file():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    content = log_path.read_text(encoding="utf-8", errors="replace")
    return classify_ci_failure(content)


def fetch_gh_run_failed_log(run_id: str) -> str:
    """Fetch failed job logs from a remote GitHub Actions run via gh CLI."""
    res = run_command(["gh", "run", "view", run_id, "--log-failed"])
    if res.returncode != 0:
        raise RuntimeError(f"Failed to retrieve logs for run {run_id}: {res.stderr.strip() or res.stdout.strip()}")
    return res.stdout


def format_ci_failure_memory(
    *,
    task: str,
    run_id: str,
    failure_type: str,
    root_cause: str,
    fix_applied: str,
    attempt: int,
    timestamp: str | None = None,
) -> str:
    """Format a CI failure record conforming to SakJules SOUL.md protocol."""
    iso_time = timestamp or datetime.now(timezone.utc).isoformat()
    return (
        f"CI FAILURE: sakjules | task: {task} | run-id: {run_id} | "
        f"failure-type: {failure_type} | root-cause: {root_cause} | "
        f"fix-applied: {fix_applied} | attempt: {attempt} | timestamp: {iso_time}"
    )


def format_ci_stalled_memory(
    *,
    task: str,
    run_id: str,
    attempts: int = 3,
    timestamp: str | None = None,
) -> str:
    """Format a CI stalled alert conforming to SakJules SOUL.md protocol."""
    iso_time = timestamp or datetime.now(timezone.utc).isoformat()
    return (
        f"CI STALLED: sakjules | task: {task} | run-id: {run_id} | "
        f"attempts: {attempts} | reason: 3 consecutive CI failures | timestamp: {iso_time}"
    )


def find_affected_tests(changed_files: list[str]) -> list[str]:
    """Map modified source and test files to targeted pytest test files."""
    affected: set[str] = set()
    for f in changed_files:
        p = Path(f)
        if not p.is_file() and not (REPO_ROOT / f).is_file():
            continue
        rel = f.replace("\\", "/")
        if rel.startswith("tests/") and rel.endswith(".py"):
            affected.add(rel)
        elif rel.startswith("personas/sakthai/"):
            stem = p.stem
            candidates = [
                f"tests/test_{stem}.py",
                f"tests/test_agent_{stem}.py",
                f"tests/test_cli_{stem}.py",
                f"tests/test_memory_{stem}.py",
                f"tests/test_mcp_{stem}.py",
            ]
            for cand in candidates:
                if (REPO_ROOT / cand).is_file():
                    affected.add(cand)

    return sorted(affected)


def heal_local_pipeline(
    *,
    run_tests: bool = False,
    sync_parity: bool = True,
    dry_run: bool = False,
) -> HealResult:
    """Execute local multi-stage healing sequence."""
    result = HealResult(success=True)

    if dry_run:
        print("[DRY-RUN] Would run: ruff format, ruff check --fix, parity sync, and affected tests.")
        return result

    # Stage 1: Ruff format
    print("Executing auto-heal step 1: ruff format...")
    fmt_res = run_command(["uv", "run", "ruff", "format", "."])
    if fmt_res.returncode != 0:
        result.format_passed = False
        result.success = False
        result.details.append(f"Format stderr: {fmt_res.stderr.strip() or fmt_res.stdout.strip()}")

    # Stage 2: Ruff check --fix
    print("Executing auto-heal step 2: ruff check --fix...")
    fix_res = run_command(["uv", "run", "ruff", "check", "--fix", "."])
    if fix_res.returncode != 0:
        result.lint_passed = False
        result.success = False
        result.details.append(f"Check --fix stderr: {fix_res.stderr.strip() or fix_res.stdout.strip()}")

    # Stage 3: Persona package parity sync
    if sync_parity:
        print("Executing auto-heal step 3: syncing persona package parity...")
        sync_res = run_command(["python3", "scripts/sync_personas.py"])
        if sync_res.returncode != 0:
            result.parity_passed = False
            result.success = False
            result.details.append(f"Parity sync stderr: {sync_res.stderr.strip() or sync_res.stdout.strip()}")

    # Stage 4: Targeted test run
    if run_tests:
        print("Executing auto-heal step 4: running targeted test verification...")
        diff_res = run_command(["git", "diff", "--name-only", "HEAD~1"])
        changed = diff_res.stdout.splitlines() if diff_res.returncode == 0 else []
        tests_to_run = find_affected_tests(changed)

        if not tests_to_run:
            tests_to_run = ["tests/test_persona_package_parity.py", "tests/test_skills_organization_parity.py"]

        test_cmd = ["uv", "run", "pytest", "-q"] + tests_to_run
        print(f"Running: {' '.join(test_cmd)}")
        test_res = run_command(test_cmd)
        if test_res.returncode != 0:
            result.tests_passed = False
            result.success = False
            result.details.append(f"Targeted test failures: {test_res.stdout.strip()}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ci_auto_heal.py",
        description="House of Sak CI Auto-Heal Engine: multi-stage recovery for formatting, lint, parity drift, and CI log diagnostics.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate auto-heal actions without writing file modifications.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check whether auto-heal is needed without applying fixes.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run targeted pytest suites on files affected by recent changes.",
    )
    parser.add_argument(
        "--no-sync-parity",
        action="store_true",
        help="Skip syncing canonical package code to persona copies.",
    )
    parser.add_argument(
        "--parse-log",
        type=Path,
        help="Path to a CI failure log file to analyze and classify.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="GitHub Actions run ID to fetch and analyze failed logs for.",
    )
    parser.add_argument(
        "--task-name",
        type=str,
        default="ci-maintenance",
        help="Task name when formatting memory records.",
    )

    args = parser.parse_args()

    # Log analysis mode
    if args.parse_log or args.run_id:
        print("Analyzing CI failure log...")
        if args.parse_log:
            category, cause = parse_failed_log(args.parse_log)
        else:
            raw_log = fetch_gh_run_failed_log(args.run_id)
            category, cause = classify_ci_failure(raw_log)

        print(f"Classification: {category.value.upper()}")
        print(f"Root Cause:     {cause}")
        mem = format_ci_failure_memory(
            task=args.task_name,
            run_id=args.run_id or "local",
            failure_type=category.value,
            root_cause=cause,
            fix_applied="auto-heal evaluation",
            attempt=1,
        )
        print(f"\nRecommended Memory Tag:\n{mem}")
        return 0

    if args.check_only:
        fmt_check = run_command(["uv", "run", "ruff", "format", "--check", "."])
        lint_check = run_command(["uv", "run", "ruff", "check", "."])
        if fmt_check.returncode == 0 and lint_check.returncode == 0:
            print("CI quality checks are clean; auto-heal not required.")
            return 0
        else:
            print("Mechanical issues detected; auto-heal is recommended.")
            return 1

    heal_res = heal_local_pipeline(
        run_tests=args.run_tests,
        sync_parity=not args.no_sync_parity,
        dry_run=args.dry_run,
    )

    if heal_res.success:
        print("Auto-heal routine finished cleanly.")
        return 0
    else:
        print("Auto-heal routine completed with remaining warnings or failures:")
        for det in heal_res.details:
            print(f"  - {det}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
