"""The ``sakthai`` CLI — a thin click frontend over the package layers."""

from __future__ import annotations

import sys

import click

# On Windows the default console encoding is often cp1252, which cannot
# represent the box-drawing and check-mark characters used by this CLI.
# Reconfigure stdout/stderr to UTF-8 with replacement so they never raise
# UnicodeEncodeError regardless of the user's terminal code-page setting.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

from .. import __version__
from .agent import mcp, run
from .cycle import cycle as cycle_cmd
from .eval import eval_cmd
from .extensions import extensions as extensions_cmd
from .hf import hf_cmd
from .memory import learn, recall
from .memory import memory as memory_cmd
from .sessions import sessions as sessions_cmd
from .skills import skills as skills_cmd
from .system import doctor, setup, status, tools

# Group commands are imported under ``*_cmd`` aliases on purpose: binding the
# group object under its own name here would shadow the same-named submodule as
# a package attribute (e.g. ``sakthai.cli.skills`` would resolve to the group,
# not the module), which breaks ``import sakthai.cli.skills`` for tests/tools.


@click.group()
@click.version_option(__version__, prog_name="sakthai")
def main() -> None:
    """SakThai — a personal learning agent with persistent memory."""


# Memory
main.add_command(learn)
main.add_command(recall)
main.add_command(memory_cmd)

# System
main.add_command(doctor)
main.add_command(setup)
main.add_command(status)
main.add_command(tools)

# Agent
main.add_command(run)
main.add_command(mcp)

# Skills, cycle, extensions, sessions, hf
main.add_command(skills_cmd)
main.add_command(cycle_cmd)
main.add_command(extensions_cmd)
main.add_command(sessions_cmd)
main.add_command(hf_cmd)
main.add_command(eval_cmd, name="eval")

__all__ = ["main"]
