"""SakThai Agent command-line interface."""

from __future__ import annotations

import json

import click

from . import __version__
from .config import check_env


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="sakthai")
def cli() -> None:
    """
    SakThai Agent: a multi-modal, multi-provider AI agent with a shared memory
    and a focus on local-first execution and extensibility.
    """


@cli.command()
def check() -> None:
    """Display a comprehensive environment and configuration report.

    This command checks for required and optional environment variables, verifies
    the existence and writability of the memory database, lists available
    credentials for AI providers, and confirms that core components are ready.

    The output is a JSON object detailing the status of each component, which is
    useful for diagnosing setup issues.
    """
    report = check_env()
    click.echo(json.dumps(report, indent=2))


# --- Placeholder for existing commands ---
# You can move your existing 'run' and 'mcp' command implementations here.


@cli.command()
@click.argument("task", required=False)
def run(task: str | None) -> None:
    """(Placeholder) Run the agent loop with a given task."""
    click.echo("Placeholder for 'run' command.")
    click.echo(f"Task: {task}")


@cli.command()
def mcp() -> None:
    """(Placeholder) Run as a long-lived MCP server."""
    click.echo("Placeholder for 'mcp' command.")


if __name__ == "__main__":
    cli()