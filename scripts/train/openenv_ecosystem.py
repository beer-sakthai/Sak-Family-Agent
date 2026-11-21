#!/usr/bin/env python3
"""Standalone runner for the OpenEnv RL Training ecosystem bridge.

Delegates to ``sakthai.cli.train.openenv_cmd`` so repository tasks and external
automation can invoke OpenEnv RL contract verification, test suites, baseline
competitions, and evaluation benchmarks directly.

Usage:
    python scripts/train/openenv_ecosystem.py status [--json]
    python scripts/train/openenv_ecosystem.py verify [--dry-run]
    python scripts/train/openenv_ecosystem.py test [--workspace all] [--dry-run]
    python scripts/train/openenv_ecosystem.py baselines [--dry-run]
    python scripts/train/openenv_ecosystem.py benchmark [--json] [--dry-run]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Explicit canonical package path insertion as required by monorepo guidelines
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.cli.train import openenv_cmd  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["status"]
    try:
        openenv_cmd.main(args=args, prog_name="openenv_ecosystem.py", standalone_mode=False)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
