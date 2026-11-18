#!/usr/bin/env python3
"""Patch or validate the generated gh-aw centralized command router.

The gh-aw compiler currently generates agentic_commands.yml without a
workflow-level concurrency block and does not expose a project-config field
for that router. This script is the repository-owned post-compile boundary:
run it after `gh aw compile`, or use --check in CI to fail if regeneration
would remove the safety control.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CONCURRENCY = """concurrency:
  group: agentic-commands-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
"""
MARKER = "# repository patch: PR-scoped concurrency added after gh-aw compile\n"


def patch(path: Path, check: bool) -> int:
    text = path.read_text(encoding="utf-8")
    has_expected_concurrency = CONCURRENCY in text and MARKER in text
    has_expected_review_alias = '"review":' in text

    if check:
        if not has_expected_concurrency:
            raise SystemExit(f"{path} is missing the repository gh-aw concurrency patch")
        if not has_expected_review_alias:
            raise SystemExit(f"{path} is missing the /review slash command alias")
        return 0

    patched = text
    if not has_expected_concurrency:
        if "\npermissions: {}\n" not in patched:
            raise SystemExit(f"cannot locate generated permissions boundary in {path}")
        patched = patched.replace(
            "\npermissions: {}\n",
            f"\n{MARKER}{CONCURRENCY}\npermissions: {{}}\n",
            1,
        )

    if not has_expected_review_alias:
        import json
        import re

        m_routing = re.search(r"GH_AW_SLASH_ROUTING: '(.*?)'", patched)
        if m_routing:
            routing = json.loads(m_routing.group(1))
            if "review" not in routing and "skill-pr-reviewer" in routing:
                routing["review"] = routing["skill-pr-reviewer"]
                new_routing = json.dumps(routing, separators=(",", ":"))
                patched = patched.replace(m_routing.group(0), f"GH_AW_SLASH_ROUTING: '{new_routing}'")

        m_help = re.search(r"GH_AW_HELP_COMMANDS: '(.*?)'", patched)
        if m_help:
            helps = json.loads(m_help.group(1))
            if not any(h.get("command") == "review" for h in helps):
                helps.append({
                    "command": "review",
                    "description": "Review pull requests with installed expert skills",
                    "centralized": True,
                    "decentralized": False,
                    "source_file": "skill-pr-reviewer",
                })
                new_help = json.dumps(helps, separators=(",", ":"))
                patched = patched.replace(m_help.group(0), f"GH_AW_HELP_COMMANDS: '{new_help}'")

    if patched != text:
        path.write_text(patched, encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", default=".github/workflows/agentic_commands.yml")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return patch(Path(args.workflow), args.check)


if __name__ == "__main__":
    raise SystemExit(main())
