#!/usr/bin/env python3
"""Repair lightweight metadata problems in SKILL.md files.

The utility is intentionally conservative: it only scans explicitly supplied
roots, skips symlinks and ignored directories, preserves valid frontmatter
keys, and writes a file only when its normalized content changes.
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ROOTS = ("personas", ".claude/skills", ".agents/skills")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<header>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL)
_MIN_DESCRIPTION_LENGTH = 15
_MIN_BODY_LENGTH = 30
_IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__"}


def _default_description(name: str) -> str:
    return f"Comprehensive skill and execution procedures for {name} agent operations."


def _fallback_body(name: str) -> str:
    return (
        f"# {name}\n\n"
        "## Overview\n"
        f"This skill provides automated runbooks, tools, and operational workflows for `{name}`.\n\n"
        "## Execution Workflow\n"
        "1. Initialize project and environmental context.\n"
        "2. Execute procedures according to task specifications.\n"
        "3. Validate outputs with automated quality gates.\n"
    )


def _parse_content(content: str) -> tuple[dict[str, Any], str]:
    """Return frontmatter data and body, recovering from malformed YAML."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    try:
        parsed = yaml.safe_load(match.group("header"))
    except yaml.YAMLError:
        parsed = {}
    metadata = dict(parsed) if isinstance(parsed, dict) else {}
    return metadata, match.group("body")


def _serialize(metadata: dict[str, Any], body: str) -> str:
    header = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{header}\n---\n\n{body.rstrip()}\n"


def heal_skill_file(path: Path, *, write: bool = True) -> bool:
    """Heal one regular SKILL.md file and return whether it needs changing."""
    if not path.is_file() or path.is_symlink() or path.name != "SKILL.md":
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False

    metadata, body = _parse_content(content)
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        name = path.parent.name
        metadata["name"] = name
    else:
        name = name.strip()

    description = metadata.get("description")
    if not isinstance(description, str) or len(description.strip()) < _MIN_DESCRIPTION_LENGTH:
        metadata["description"] = _default_description(name)

    if len(body.strip()) < _MIN_BODY_LENGTH:
        body = _fallback_body(name)

    healed = _serialize(metadata, body)
    if healed == content or not write:
        return healed != content

    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as temporary:
            temporary.write(healed)
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    except OSError:
        with suppress(OSError, UnboundLocalError):
            Path(temporary_name).unlink(missing_ok=True)
        return False
    return True


def discover_skill_files(roots: list[Path]) -> list[Path]:
    """Discover regular SKILL.md files below explicit roots without symlink traversal."""
    found: set[Path] = set()
    for root in roots:
        if not root.exists() or root.is_symlink():
            continue
        for directory, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _IGNORED_DIRS]
            candidate = Path(directory) / "SKILL.md"
            if "SKILL.md" in filenames and not candidate.is_symlink():
                found.add(candidate)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots", nargs="*", type=Path, help="roots to scan (default: repository skill roots)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report changes without writing files"
    )
    args = parser.parse_args()

    roots = args.roots or [Path(root) for root in DEFAULT_ROOTS]
    changed = sum(
        heal_skill_file(path, write=not args.dry_run) for path in discover_skill_files(roots)
    )
    action = "would auto-heal" if args.dry_run else "auto-healed"
    print(f"Auto-healed {changed} SKILL.md files (or {action} in dry-run mode).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
