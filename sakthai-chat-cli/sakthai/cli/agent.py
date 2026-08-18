"""Agent commands: ``run`` (the agent loop) and ``mcp`` (the stdio server)."""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import click

from ..agent.loop import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    AgentError,
    preflight,
    run_agent,
)
from ..agent.tools import BUILTIN_TOOLS, Tool


@contextlib.contextmanager
def _tool_context(*, no_mcp: bool, verbose: bool) -> Iterator[tuple[Tool, ...]]:
    """Yield the tools for a run: built-ins plus any configured MCP servers.

    With no servers configured (or ``--no-mcp``) this is just the built-ins and
    spawns nothing. External servers come from ``~/.sakthai/mcp.json`` and
    installed extensions; one that fails to start is skipped, not fatal.
    """
    if no_mcp:
        yield BUILTIN_TOOLS
        return
    from ..mcp.manager import connect_servers

    with connect_servers() as mcp_tools:
        if mcp_tools and verbose:
            click.echo(f"[mcp] loaded {len(mcp_tools)} external tool(s)", err=True)
        yield (*BUILTIN_TOOLS, *mcp_tools)


def _print_preflight(report: dict[str, Any]) -> None:
    """Render a preflight report for ``sakthai run --dry-run``."""
    tools = report["tools"]
    preview = ", ".join(tools[:8]) + (", …" if len(tools) > 8 else "")
    click.echo(f"[dry-run] provider:    {report['provider']}")
    click.echo(f"[dry-run] model:       {report['model']}")
    click.echo(f"[dry-run] credentials: {report['credential_source'] or 'none'}")
    click.echo(f"[dry-run] tools:       {report['tool_count']} ({preview})")
    click.echo(f"[dry-run] runnable:    {'yes' if report['runnable'] else 'no'}")


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


@dataclass
class RunOptions:
    """Configuration options for the agent run command."""

    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    max_seconds: float | None = None
    provider: str | None = None
    verbose: bool = False
    no_mcp: bool = False
    with_skills: tuple[str, ...] = ()
    dry_run: bool = False
    stream: bool = False
    fast: bool = False
    stateless: bool = False
    caveman: str | None = None
    sandbox: bool = False
    persona: str | None = None


def _run_in_sandbox(task: str, opts: RunOptions) -> None:
    from ..sandbox import SandboxError, run_in_sandbox

    try:
        click.echo("Building sandbox image (cached after first run)…", err=True)
        code = run_in_sandbox(
            task,
            model=opts.model,
            max_tokens=opts.max_tokens,
            max_iterations=opts.max_iterations,
            max_seconds=opts.max_seconds,
            provider=opts.provider,
            verbose=opts.verbose,
            no_mcp=opts.no_mcp,
            with_skills=opts.with_skills,
            fast=opts.fast,
            stateless=opts.stateless,
            caveman=opts.caveman,
            dry_run=opts.dry_run,
            stream=opts.stream,
        )
    except SandboxError as e:
        raise click.ClickException(str(e)) from e
    sys.exit(code)


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
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway"]),
    help="LLM provider backend.",
)
@click.option("-v", "--verbose", is_flag=True, help="Stream tool calls as they happen.")
@click.option(
    "--no-mcp",
    is_flag=True,
    help="Don't load external MCP servers (from ~/.sakthai/mcp.json and extensions).",
)
@click.option(
    "--with-skills",
    "with_skills",
    multiple=True,
    help="Inject the named skill's instructions into the system prompt (repeatable).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate the run (provider, credentials, model, tools) without calling the API.",
)
@click.option(
    "--stream",
    is_flag=True,
    help="Stream the assistant's reply to stdout as it is generated.",
)
@click.option(
    "--fast",
    is_flag=True,
    help="Fast-track mode: bypass the 6-stage cycle for simple runs.",
)
@click.option(
    "--stateless",
    is_flag=True,
    help="Stateless mode: do not load or append persistent memory to the system prompt, saving tokens.",
)
@click.option(
    "--caveman",
    type=click.Choice(["lite", "full", "ultra", "wenyan-lite", "wenyan-full", "wenyan-ultra"]),
    help="Enable Caveman token compression at the specified intensity level.",
)
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run inside an isolated Docker container. Enables run_command safely — only memory.db is shared with the host.",
)
def run(task: str, **kwargs: Any) -> None:
    """Run TASK through the standalone SakThai agent.

    External MCP servers configured in ~/.sakthai/mcp.json (or installed
    extensions) are loaded automatically and their tools become available to the
    agent; pass --no-mcp to skip them. Pass --dry-run to check that the run is
    configured correctly (provider, credentials, model, tools) without spending
    any tokens.
    """
    opts = RunOptions(**kwargs)
    if opts.sandbox:
        _run_in_sandbox(task, opts)

    if opts.dry_run:
        with _tool_context(no_mcp=opts.no_mcp, verbose=opts.verbose) as tools:
            report = preflight(model=opts.model, provider=opts.provider, tools=tools)
        _print_preflight(report)
        if not report["runnable"]:
            raise click.ClickException(
                f"Not runnable: no credentials found for provider {report['provider']!r}."
            )
        return
    streamed = False

    def _on_token(text: str) -> None:
        nonlocal streamed
        streamed = True
        click.echo(text, nl=False)

    try:
        with _tool_context(no_mcp=opts.no_mcp, verbose=opts.verbose) as tools:
            result = run_agent(
                task,
                model=opts.model,
                max_tokens=opts.max_tokens,
                max_iterations=opts.max_iterations,
                max_seconds=opts.max_seconds,
                on_event=_event_emitter(opts.verbose),
                on_token=_on_token if opts.stream else None,
                provider=opts.provider,
                tools=tools,
                skills=list(opts.with_skills),
                fast=opts.fast,
                stateless=opts.stateless,
                caveman=opts.caveman,
            )
    except AgentError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        sys.exit(130)
    if streamed:
        click.echo("")  # terminate the streamed line
    else:
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
