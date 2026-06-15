"""The ``sakthai`` CLI — a thin click frontend over the package layers."""

from __future__ import annotations

import click

from .. import __version__
from .agent import mcp, run
from .cycle import cycle
from .extensions import extensions
from .memory import learn, memory, recall
from .skills import skills
from .system import doctor, setup, status, tools


@click.group()
@click.version_option(__version__, prog_name="sakthai")
def main() -> None:
    """SakThai — a personal learning agent with persistent memory."""


# Memory
main.add_command(learn)
main.add_command(recall)
main.add_command(memory)

# System
main.add_command(doctor)
main.add_command(setup)
main.add_command(status)
main.add_command(tools)

# Agent
main.add_command(run)
main.add_command(mcp)

# Skills, cycle, extensions
main.add_command(skills)
main.add_command(cycle)
main.add_command(extensions)

__all__ = ["main"]
