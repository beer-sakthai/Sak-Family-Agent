#!/usr/bin/env python3
"""Reject scalar GitHub Actions permission declarations.

Workflow-level permissions must be explicit mappings so new jobs do not inherit
an overly broad token scope by accident. Empty mappings are allowed when each
job declares the permissions it needs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"
FORBIDDEN_SCALAR_VALUES = frozenset({"read", "write", "read-all", "write-all"})


def _workflow_paths(workflows_dir: Path) -> list[Path]:
    """Return YAML workflow files in deterministic order."""
    return sorted({*workflows_dir.glob("*.yml"), *workflows_dir.glob("*.yaml")})


def _scalar_permission_nodes(node: Node) -> list[tuple[int, str]]:
    """Find forbidden scalar values in every ``permissions`` mapping key."""
    findings: list[tuple[int, str]] = []
    if isinstance(node, MappingNode):
        for key_node, value_node in node.value:
            if (
                isinstance(key_node, ScalarNode)
                and key_node.value == "permissions"
                and isinstance(value_node, ScalarNode)
                and value_node.value in FORBIDDEN_SCALAR_VALUES
            ):
                findings.append((key_node.start_mark.line + 1, value_node.value))
            findings.extend(_scalar_permission_nodes(key_node))
            findings.extend(_scalar_permission_nodes(value_node))
    elif isinstance(node, SequenceNode):
        for child in node.value:
            findings.extend(_scalar_permission_nodes(child))
    return findings


def find_scalar_permissions(workflows_dir: Path | None = None) -> list[tuple[Path, int, str]]:
    """Return scalar permission declarations as ``(path, line, value)`` tuples.

    PyYAML's node tree preserves source marks while understanding comments,
    quoted scalars, and block scalars. This prevents text inside comments or a
    multiline string from being mistaken for a workflow declaration.
    """
    findings: list[tuple[Path, int, str]] = []
    for workflow in _workflow_paths(workflows_dir or WORKFLOWS_DIR):
        document = yaml.compose(workflow.read_text(encoding="utf-8"))
        if document is None:
            continue
        findings.extend(
            (workflow, line_number, value)
            for line_number, value in _scalar_permission_nodes(document)
        )
    return findings


def main() -> int:
    try:
        findings = find_scalar_permissions()
    except yaml.YAMLError as error:
        print(f"Workflow permissions lint failed: invalid YAML: {error}", file=sys.stderr)
        return 1

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
