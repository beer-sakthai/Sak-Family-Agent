"""Agent commands: ``run`` (the agent loop) and ``mcp`` (the stdio server)."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import click

from ..agent.loop import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    AgentError,
    run_agent,
)


def _event_emitter(verbose: bool) -> Callable[[str, dict[str, Any]], None]:
    def emit(kind: str, payload: dict[str, Any]) -> None:
        if not verbose:
            return
        if kind == "tool_call":
            tag = "tool!" if payload.get("is_error") else "tool"
            click.echo(f"[{tag}] {payload['name']} {payload['input']}", err=True)
        elif kind == "tool_error":
            click.echo(f"[tool?] unknown tool: {payload.get('name')}", err=True)
        elif kind == "iteration":
            click.echo(f"[iter {payload['n']}] stop={payload['stop_reason']}", err=True)

    return emit


@click.command()
@click.argument("task")
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Model identifier.")
@click.option("--max-tokens", default=DEFAULT_MAX_TOKENS, show_default=True, type=int)
@click.option(
    "--max-iterations",
    default=DEFAULT_MAX_ITERATIONS,
    show_default=True,
    type=int,
    help="Tool-use loop cap.",
)
@click.option(
    "--max-seconds",
    default=None,
    type=float,
    help="Wall-clock time budget in seconds (off by default).",
)
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "google"]),
    help="LLM provider backend.",
)
@click.option("-v", "--verbose", is_flag=True, help="Stream tool calls as they happen.")
def run(
    task: str,
    model: str,
    max_tokens: int,
    max_iterations: int,
    max_seconds: float | None,
    provider: str | None,
    verbose: bool,
) -> None:
    """Run TASK through the standalone SakThai agent."""
    try:
        result = run_agent(
            task,
            model=model,
            max_tokens=max_tokens,
            max_iterations=max_iterations,
            max_seconds=max_seconds,
            on_event=_event_emitter(verbose),
            provider=provider,
        )
    except AgentError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        sys.exit(130)
    click.echo(result.text)


@click.command()
def mcp() -> None:
    """Serve the memory tools over MCP (stdio JSON-RPC).

    Meant to be launched by an MCP client (an IDE, Claude Desktop, …): it reads
    requests on stdin and writes responses on stdout, exposing the same tools as
    ``sakthai run`` backed by the shared memory store.
    """
    from ..mcp import serve

    serve()
