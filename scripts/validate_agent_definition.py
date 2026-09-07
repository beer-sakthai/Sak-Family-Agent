#!/usr/bin/env python3
"""Validate a Claude-style agent definition used by this repository's CI."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VALID_COLORS = {"blue", "cyan", "green", "yellow", "magenta", "red"}
VALID_MODELS = {"inherit", "sonnet", "opus", "haiku"}
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
REQUIRED_FIELDS = ("name", "description", "model", "color")


def parse_agent(path: Path) -> tuple[dict[str, str], str, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    if not lines or lines[0].strip() != "---":
        return {}, "", ["file must start with YAML frontmatter (---)"]

    try:
        closing = lines.index("---", 1)
    except ValueError:
        return {}, "", ["frontmatter is not closed with a second ---"]

    frontmatter: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"line {line_number}: frontmatter entry must contain ':'")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"line {line_number}: frontmatter key is empty")
        elif key in frontmatter:
            errors.append(f"line {line_number}: duplicate frontmatter field {key!r}")
        else:
            frontmatter[key] = value

    body = "\n".join(lines[closing + 1 :]).strip()
    return frontmatter, body, errors


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"file does not exist: {path}"]

    frontmatter, body, errors = parse_agent(path)
    for field in REQUIRED_FIELDS:
        if not frontmatter.get(field):
            errors.append(f"missing required frontmatter field: {field}")

    name = frontmatter.get("name", "")
    if name and (not NAME_RE.fullmatch(name) or not 3 <= len(name) <= 50):
        errors.append("name must be 3-50 characters of lowercase letters, digits, and hyphens")

    description = frontmatter.get("description", "")
    if description:
        if not 10 <= len(description) <= 5000:
            errors.append("description must be 10-5000 characters")
        if "Use this agent when" not in description:
            errors.append("description must state when to use the agent")
        if description.count("<example>") < 2:
            errors.append("description must include at least two <example> trigger markers")
        if 'See "When to invoke"' not in description:
            errors.append('description must point to the body section "When to invoke"')

    model = frontmatter.get("model", "")
    if model and model not in VALID_MODELS:
        errors.append(f"model must be one of: {', '.join(sorted(VALID_MODELS))}")

    color = frontmatter.get("color", "")
    if color and color not in VALID_COLORS:
        errors.append(f"color must be one of: {', '.join(sorted(VALID_COLORS))}")

    if not 20 <= len(body) <= 10000:
        errors.append("system prompt body must be 20-10000 characters")
    required_sections = {
        "When to invoke": "When to invoke",
        "Core Responsibilities": "responsibilities",
        "Process": "process",
        "Output Format": "output",
        "Quality Standards": "quality",
        "Edge Cases": "edge cases",
    }
    for label, needle in required_sections.items():
        if needle.lower() not in body.lower():
            errors.append(f"system prompt is missing a {label} section")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent_file", type=Path)
    args = parser.parse_args(argv)
    errors = validate(args.agent_file)
    if errors:
        print(f"Invalid agent definition: {args.agent_file}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Valid agent definition: {args.agent_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
