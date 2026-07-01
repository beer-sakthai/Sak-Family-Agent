"""The ``sakthai`` CLI — a thin click frontend over the package layers."""

from __future__ import annotations

import click

from .. import __version__
from .agent import mcp, run
from .cycle import cycle as cycle_cmd
from .dashboard import dashboard as dashboard_cmd
from .extensions import extensions as extensions_cmd
from .hf import hf_cmd
from .memory import learn
from .memory import memory as memory_cmd
from .memory import recall
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

# Skills, cycle, extensions, dashboard, sessions, hf
main.add_command(skills_cmd)
main.add_command(cycle_cmd)
main.add_command(extensions_cmd)
main.add_command(dashboard_cmd)
main.add_command(sessions_cmd)
main.add_command(hf_cmd)

__all__ = ["main"]
