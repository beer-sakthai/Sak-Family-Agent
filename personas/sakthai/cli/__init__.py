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
from .chat import chat as chat_cmd
from .client import client_cmd
from .cycle import cycle as cycle_cmd
from .dashboard import dashboard_cmd
from .eval import eval_cmd
from .extensions import extensions as extensions_cmd
from .gateway import gateway_cmd
from .hf import hf_cmd
from .lead import lead_cmd
from .memory import learn, recall
from .memory import memory as memory_cmd
from .platform import platform_cmd
from .quota import quota_cmd
from .repo import repo_cmd
from .sessions import sessions as sessions_cmd
from .skills import skills as skills_cmd
from .system import doctor, setup, status, tools, web
from .team import team_cmd
from .telegram import telegram_cmd
from .train import train_cmd
from .write import write_cmd

# Group commands are imported under ``*_cmd`` aliases on purpose: binding the
# group object under its own name here would shadow the same-named submodule as
# a package attribute (e.g. ``sakthai.cli.skills`` would resolve to the group,
# not the module), which breaks ``import sakthai.cli.skills`` for tests/tools.
# The same applies to any single command whose name matches its module (hence
# ``chat_cmd`` for the ``chat`` command in ``chat.py``).


def _is_interactive() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    prog = ctx.find_root().info_name or "sak"
    if prog not in ("sak", "sakthai"):
        prog = "sak"
    click.echo(f"{prog}, version {__version__}")
    ctx.exit()


class SakThaiGroup(click.Group):
    """Smart CLI group for Sak and Sak Family agents.

    Supports running like Claude Code / Gemini CLI / AGY:
    - When invoked without subcommands in an interactive terminal, launches the
      interactive agent chat directly.
    - When invoked with a task prompt or options that do not match a known subcommand,
      automatically dispatches them to `run`.
    - `sak --help` or `sak --version` display standard CLI info (with `sakthai` alias).
    - All existing subcommands (`status`, `doctor`, `mcp`, `gateway`, etc.) dispatch normally.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        has_help = any(a in ("--help", "-h") for a in args)
        has_version = any(a in ("--version", "-V") for a in args)
        if not has_help and not has_version and args and args[0] not in self.commands:
            args = ["run", *args]
        return super().parse_args(ctx, args)


@click.group(cls=SakThaiGroup, invoke_without_command=True)
@click.option(
    "--version",
    "-V",
    is_flag=True,
    callback=_version_callback,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Sak (House of Sak) — a personal learning agent and autonomous agent platform with persistent memory."""
    if ctx.invoked_subcommand is None:
        if _is_interactive():
            ctx.invoke(chat_cmd)
        else:
            click.echo(ctx.get_help())


# Memory
main.add_command(learn)
main.add_command(recall)
main.add_command(memory_cmd)

# System
main.add_command(doctor)
main.add_command(setup)
main.add_command(status)
main.add_command(tools)
main.add_command(web)

# Agent
main.add_command(run)
main.add_command(mcp)
main.add_command(chat_cmd, name="chat")

# Skills, cycle, extensions, sessions, hf, client, team
main.add_command(skills_cmd)
main.add_command(cycle_cmd)
main.add_command(extensions_cmd)
main.add_command(sessions_cmd)
main.add_command(hf_cmd)
main.add_command(eval_cmd, name="eval")
main.add_command(team_cmd)
main.add_command(client_cmd)
main.add_command(platform_cmd, name="platform")
main.add_command(quota_cmd)
main.add_command(lead_cmd, name="lead")
main.add_command(repo_cmd)
main.add_command(dashboard_cmd)
main.add_command(gateway_cmd)
main.add_command(telegram_cmd)
main.add_command(train_cmd)
main.add_command(write_cmd)

__all__ = ["main"]
