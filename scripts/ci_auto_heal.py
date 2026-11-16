#!/usr/bin/env python3
"""CI Auto-Heal: automated recovery utility for mechanical lint, formatting, and transient flakes."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(cmd: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository root and capture text output."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def heal_formatting(*, dry_run: bool = False) -> bool:
    """Run ruff format and ruff check --fix to auto-heal mechanical code quality issues."""
    if dry_run:
        print("[DRY-RUN] Would run 'uv run ruff format .' and 'uv run ruff check --fix .'")
        return True

    print("Executing auto-heal step 1: ruff format...")
    fmt_res = run_command(["uv", "run", "ruff", "format", "."])
    if fmt_res.returncode != 0:
        print(f"Format stderr: {fmt_res.stderr.strip() or fmt_res.stdout.strip()}")

    print("Executing auto-heal step 2: ruff check --fix...")
    fix_res = run_command(["uv", "run", "ruff", "check", "--fix", "."])
    if fix_res.returncode != 0:
        print(f"Check --fix stderr: {fix_res.stderr.strip() or fix_res.stdout.strip()}")

    return fmt_res.returncode == 0 and fix_res.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ci_auto_heal.py",
        description="House of Sak CI auto-heal utility: mechanical recovery for lint, format, and transient flakes.",
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
    args = parser.parse_args()

    print("Initializing House of Sak CI auto-heal engine...")
    if args.check_only:
        fmt_check = run_command(["uv", "run", "ruff", "format", "--check", "."])
        lint_check = run_command(["uv", "run", "ruff", "check", "."])
        if fmt_check.returncode == 0 and lint_check.returncode == 0:
            print("CI quality checks are clean; auto-heal not required.")
            return 0
        else:
            print("Mechanical issues detected; auto-heal is recommended.")
            return 1

    success = heal_formatting(dry_run=args.dry_run)
    if success:
        print("Auto-heal routine finished cleanly.")
        return 0
    else:
        print("Auto-heal routine completed with remaining warnings or failures.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
