#!/usr/bin/env python3
"""Reject scalar GitHub Actions permission declarations.

Workflow-level permissions must be explicit mappings so new jobs do not inherit
an overly broad token scope by accident. Empty mappings are allowed when each
job declares the permissions it needs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"
SCALAR_PERMISSION = re.compile(
    r"^(?P<indent>\s*)permissions:\s*(?P<value>read-all|write-all|read|write)\s*(?:#.*)?$"
)


def find_scalar_permissions(workflows_dir: Path = WORKFLOWS_DIR) -> list[tuple[Path, int, str]]:
    """Return scalar permission declarations as ``(path, line, value)`` tuples."""
    findings: list[tuple[Path, int, str]] = []
    for workflow in sorted(workflows_dir.glob("*.yml")):
        for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            match = SCALAR_PERMISSION.match(line)
            if match:
                findings.append((workflow, line_number, match.group("value")))
    return findings


def main() -> int:
    findings = find_scalar_permissions()
    if not findings:
        print("Workflow permissions lint passed: no scalar permission declarations found.")
        return 0

    print("Workflow permissions lint failed:", file=sys.stderr)
    for path, line_number, value in findings:
        print(f"  {path}:{line_number}: permissions: {value}", file=sys.stderr)
    print(
        "Use an explicit mapping such as 'permissions: {}' or list only the required scopes.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
