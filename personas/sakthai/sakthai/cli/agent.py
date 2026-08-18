"""Agent commands: ``run`` (the agent loop) and ``mcp`` (the stdio server)."""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import click

from .. import config
from ..agent.chat import load_persona_soul
from ..agent.loop import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    AgentError,
    preflight,
    run_agent,
)
from ..agent.tools import BUILTIN_TOOLS, Tool
from ..memory.store import MemoryStore
from ..skills import resolve_skill_names


@contextlib.contextmanager
def _temp_env(key: str, value: str) -> Iterator[None]:
    """Temporarily set an environment variable, restoring its prior value on exit."""
    previous = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


@contextlib.contextmanager
def _tool_context(
    *, no_mcp: bool, verbose: bool, persona: str | None = None
) -> Iterator[tuple[Tool, ...]]:
    """Yield the tools for a run: built-ins plus any configured MCP servers.

    With no servers configured (or ``--no-mcp``) this is just the built-ins and
    spawns nothing. External servers come from ``~/.sakthai/mcp.json`` and
    installed extensions; one that fails to start is skipped, not fatal.
    ``persona``, when given and ``SAKTHAI_MCP_CONFIG`` isn't already set in the
    environment, temporarily points that env var at the persona's own
    ``mcp.json`` (if it exists) for the duration of this run — reuses the
    existing ``SAKTHAI_MCP_CONFIG``/``mcp_config_override()`` precedence chain
    in ``mcp/servers.py`` unchanged; an explicitly-set ``SAKTHAI_MCP_CONFIG``
    always wins.
    """
    if no_mcp:
        yield BUILTIN_TOOLS
        return
    from ..mcp.manager import connect_servers

    mcp_path = config.persona_mcp_config_path(persona) if persona else None
    override = (
        mcp_path
        if mcp_path is not None and mcp_path.is_file() and not os.environ.get("SAKTHAI_MCP_CONFIG")
        else None
    )
    with contextlib.ExitStack() as stack:
        if override is not None:
            stack.enter_context(_temp_env("SAKTHAI_MCP_CONFIG", str(override)))
        mcp_tools = stack.enter_context(connect_servers())
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
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway", "huggingface"]),
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
@click.option(
    "--persona",
    type=click.Choice(config.PERSONA_NAMES),
    default=None,
    help=(
        "Run as a specific Sak Family persona: uses that persona's own memory "
        "shard (~/.sakthai/<persona>/memory.db) and SOUL.md identity, matching "
        "how each persona already runs in production. Omit to use the default, "
        "unscoped memory.db (unchanged pre-existing behavior)."
    ),
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
    if opts.persona and opts.sandbox:
        raise click.UsageError(
            "--persona is not supported with --sandbox yet "
            "(the sandbox only bind-mounts the default, unscoped memory.db)."
        )
    if opts.persona:
        # Explicit --model/--provider always win; a persona's own config.yaml
        # (model.provider/model.default) only fills in when the caller left
        # them at their CLI defaults.
        default_provider, default_model = config.persona_model_defaults(opts.persona)
        if opts.provider is None and default_provider:
            opts.provider = default_provider
        if opts.model == DEFAULT_MODEL and default_model:
            opts.model = default_model
    if opts.sandbox:
        _run_in_sandbox(task, opts)

    if opts.dry_run:
        with _tool_context(no_mcp=opts.no_mcp, verbose=opts.verbose, persona=opts.persona) as tools:
            report = preflight(model=opts.model, provider=opts.provider, tools=tools)
        _print_preflight(report)
        resolved, missing = resolve_skill_names(list(opts.with_skills), persona=opts.persona)
        if resolved:
            click.echo(f"[dry-run] skills:      {len(resolved)} resolved ({', '.join(resolved)})")
        # Reported before the credentials check on purpose. An unresolved skill
        # name is a static error in the command itself, knowable without any
        # credentials — and validating skill names is a common reason to run
        # --dry-run somewhere that deliberately has none, such as CI. With the
        # order reversed, the credentials failure short-circuited first and the
        # unresolved name was never printed, which is how
        # continuous-security.yml kept passing a skill that does not exist.
        if missing:
            raise click.ClickException(f"Unresolved --with-skills name(s): {', '.join(missing)}")
        if not report["runnable"]:
            raise click.ClickException(
                f"Not runnable: no credentials found for provider {report['provider']!r}."
            )
        return
    if opts.with_skills:
        _, missing = resolve_skill_names(list(opts.with_skills), persona=opts.persona)
        if missing:
            click.echo(
                f"warning: skill(s) not found and will be skipped: {', '.join(missing)}",
                err=True,
            )
    streamed = False

    def _on_token(text: str) -> None:
        nonlocal streamed
        streamed = True
        click.echo(text, nl=False)

    # A --persona run gets its own memory shard and SOUL.md identity; without
    # --persona, behavior is unchanged from before this flag existed (no store
    # passed, run_agent() opens/closes its own default MemoryStore()).
    persona_store = (
        MemoryStore(config.persona_memory_db_path(opts.persona)) if opts.persona else None
    )
    system_prompt_prefix = load_persona_soul(opts.persona) if opts.persona else ""
    try:
        with _tool_context(no_mcp=opts.no_mcp, verbose=opts.verbose, persona=opts.persona) as tools:
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
                store=persona_store,
                system_prompt_prefix=system_prompt_prefix,
                persona=opts.persona,
            )
    except AgentError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        sys.exit(130)
    finally:
        if persona_store is not None:
            persona_store.close()
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
