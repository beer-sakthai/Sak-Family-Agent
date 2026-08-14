"""Every tracked Python file must parse on the minimum supported interpreter.

`scripts/run_eval_loop.py` and its `sakthai-chat-cli` twin sat in the tree
unparseable on Python 3.11 — they used PEP 701 f-string syntax (a backslash
escape inside an expression part) that only became legal in 3.12, while
`pyproject.toml` declares `requires-python = ">=3.11"` and CI runs the suite on
3.11. Nothing caught it: `scripts/` is excluded from ruff, mypy covers only the
package, and pylint's `--fail-under` gate passes with a syntax error present
because an unparseable module is scored as a single error among hundreds of
files.

A file that cannot be parsed cannot be imported, linted, type-checked or run,
so this is the cheapest possible gate and it belongs on the whole tree rather
than the package alone.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _tracked_python_files() -> list[Path]:
    """Every `*.py` git knows about.

    `-z` matters: at least one tracked path in this repository contains a
    space in a directory name (`.../Copilot /...`), and splitting `git
    ls-files` output on whitespace silently mangles it into two nonexistent
    paths — which reads as a missing file rather than a quoting bug.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [REPO_ROOT / name for name in out.split("\0") if name]


TRACKED = _tracked_python_files()


def test_there_are_tracked_python_files() -> None:
    """Guard the guard: a broken listing would make every check below vacuous."""
    assert len(TRACKED) > 500, f"only found {len(TRACKED)} tracked .py files"


@pytest.mark.parametrize("path", TRACKED, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_file_parses(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:  # pragma: no cover - the failure being prevented
        pytest.fail(
            f"{path.relative_to(REPO_ROOT)}:{exc.lineno} does not parse on "
            f"this interpreter: {exc.msg}"
        )
