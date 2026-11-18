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
    has_expected = CONCURRENCY in text and MARKER in text
    if check:
        if not has_expected:
            raise SystemExit(f"{path} is missing the repository gh-aw concurrency patch")
        return 0

    if has_expected:
        return 0

    if "\npermissions: {}\n" not in text:
        raise SystemExit(f"cannot locate generated permissions boundary in {path}")

    patched = text.replace(
        "\npermissions: {}\n",
        f"\n{MARKER}{CONCURRENCY}\npermissions: {{}}\n",
        1,
    )
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
