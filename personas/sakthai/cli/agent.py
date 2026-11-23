"""Agent commands: ``run`` (the agent loop) and ``mcp`` (the stdio server)."""

from __future__ import annotations

import contextlib
import json
import os
import sys
from collections.abc import Callable, Iterator
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
        mcp_tools = stack.enter_context(connect_servers(persona=persona, include_builtins=True))
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


def _run_in_sandbox(
    task: str,
    model: str,
    max_tokens: int,
    max_iterations: int,
    max_seconds: float | None,
    provider: str | None,
    verbose: bool,
    no_mcp: bool,
    with_skills: tuple[str, ...],
    fast: bool,
    stateless: bool,
    caveman: str | None,
    dry_run: bool,
    stream: bool,
) -> None:
    from ..sandbox import SandboxError, run_in_sandbox

    try:
        click.echo("Building sandbox image (cached after first run)…", err=True)
        code = run_in_sandbox(
            task,
            model=model,
            max_tokens=max_tokens,
            max_iterations=max_iterations,
            max_seconds=max_seconds,
            provider=provider,
            verbose=verbose,
            no_mcp=no_mcp,
            with_skills=with_skills,
            fast=fast,
            stateless=stateless,
            caveman=caveman,
            dry_run=dry_run,
            stream=stream,
        )
    except SandboxError as e:
        raise click.ClickException(str(e)) from e
    sys.exit(code)


@click.command()
@click.argument("task", nargs=-1, required=True)
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Model identifier.")
@click.option(
    "--max-tokens", default=DEFAULT_MAX_TOKENS, show_default=True, type=click.IntRange(min=1)
)
@click.option(
    "--max-iterations",
    default=DEFAULT_MAX_ITERATIONS,
    show_default=True,
    type=click.IntRange(min=1),
    help="Tool-use loop cap.",
)
@click.option(
    "--max-seconds",
    default=None,
    type=click.FloatRange(min=0, min_open=True),
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
@click.option(
    "--optimize",
    is_flag=True,
    help="Run the iterative Evaluator-Optimizer loop to refine the solution.",
)
@click.option(
    "--criteria",
    default="",
    help="Optional evaluation criteria for the Evaluator-Optimizer loop.",
)
def run(
    task: str | tuple[str, ...],
    model: str,
    max_tokens: int,
    max_iterations: int,
    max_seconds: float | None,
    provider: str | None,
    verbose: bool,
    no_mcp: bool,
    with_skills: tuple[str, ...],
    dry_run: bool,
    stream: bool,
    fast: bool,
    stateless: bool,
    caveman: str | None,
    sandbox: bool,
    persona: str | None,
    optimize: bool = False,
    criteria: str = "",
) -> None:
    """Run TASK through the standalone SakThai agent.

    External MCP servers configured in ~/.sakthai/mcp.json (or installed
    extensions) are loaded automatically and their tools become available to the
    agent; pass --no-mcp to skip them. Pass --dry-run to check that the run is
    configured correctly (provider, credentials, model, tools) without spending
    any tokens.
    """
    task_str = " ".join(task) if isinstance(task, (tuple, list)) else str(task)
    if persona and sandbox:
        raise click.UsageError(
            "--persona is not supported with --sandbox yet "
            "(the sandbox only bind-mounts the default, unscoped memory.db)."
        )
    if persona:
        # Explicit --model/--provider always win; a persona's own config.yaml
        # (model.provider/model.default) only fills in when the caller left
        # them at their CLI defaults.
        default_provider, default_model = config.persona_model_defaults(persona)
        if provider is None and default_provider:
            provider = default_provider
        if model == DEFAULT_MODEL and default_model:
            model = default_model
    if sandbox:
        _run_in_sandbox(
            task=task_str,
            model=model,
            max_tokens=max_tokens,
            max_iterations=max_iterations,
            max_seconds=max_seconds,
            provider=provider,
            verbose=verbose,
            no_mcp=no_mcp,
            with_skills=with_skills,
            fast=fast,
            stateless=stateless,
            caveman=caveman,
            dry_run=dry_run,
            stream=stream,
        )

    if dry_run:
        with _tool_context(no_mcp=no_mcp, verbose=verbose, persona=persona) as tools:
            report = preflight(model=model, provider=provider, tools=tools)
        _print_preflight(report)
        resolved, missing = resolve_skill_names(list(with_skills), persona=persona)
        if resolved:
            click.echo(f"[dry-run] skills:      {len(resolved)} resolved ({', '.join(resolved)})")
        problems = []
        if not report["runnable"]:
            problems.append(
                f"Not runnable: no credentials found for provider {report['provider']!r}."
            )
        if missing:
            problems.append(f"Unresolved --with-skills name(s): {', '.join(missing)}")
        if problems:
            raise click.ClickException(" ".join(problems))
        return
    if with_skills:
        _, missing = resolve_skill_names(list(with_skills), persona=persona)
        if missing:
            click.echo(
                f"warning: skill(s) not found and will be skipped: {', '.join(missing)}",
                err=True,
            )
    if optimize:
        from ..agent.optimizer import optimize_solution

        opt_iterations = max_iterations if max_iterations != DEFAULT_MAX_ITERATIONS else 3
        try:
            opt_result = optimize_solution(
                task=task_str,
                criteria=criteria,
                max_iterations=opt_iterations,
                model=model,
                provider=provider,
            )
        except KeyboardInterrupt:
            click.echo("\nInterrupted.", err=True)
            sys.exit(130)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

        for it in opt_result.history:
            click.echo(f"\n--- Iteration {it.iteration} [{it.status}] ({it.latency_s:.2f}s) ---")
            if it.thoughts:
                click.echo(f"Thoughts:\n{it.thoughts}")
            click.echo(f"Candidate Solution:\n{it.response}")
            if it.feedback:
                click.echo(f"Feedback:\n{it.feedback}")

        click.echo(
            f"\n=== Final Solution [{opt_result.status}] "
            f"({opt_result.total_duration_s:.2f}s, {opt_result.iterations} iterations) ==="
        )
        click.echo(opt_result.final_response)
        return

    streamed = False

    def _on_token(text: str) -> None:
        nonlocal streamed
        streamed = True
        click.echo(text, nl=False)

    # A --persona run gets its own memory shard and SOUL.md identity; without
    # --persona, behavior is unchanged from before this flag existed (no store
    # passed, run_agent() opens/closes its own default MemoryStore()).
    persona_store = MemoryStore(config.persona_memory_db_path(persona)) if persona else None
    system_prompt_prefix = load_persona_soul(persona) if persona else ""
    try:
        with _tool_context(no_mcp=no_mcp, verbose=verbose, persona=persona) as tools:
            result = run_agent(
                task_str,
                model=model,
                max_tokens=max_tokens,
                max_iterations=max_iterations,
                max_seconds=max_seconds,
                on_event=_event_emitter(verbose),
                on_token=_on_token if stream else None,
                provider=provider,
                tools=tools,
                skills=list(with_skills),
                fast=fast,
                stateless=stateless,
                caveman=caveman,
                store=persona_store,
                system_prompt_prefix=system_prompt_prefix,
                persona=persona,
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


@click.group(invoke_without_command=True)
@click.pass_context
def mcp(ctx: click.Context) -> None:
    """Serve or inspect Model Context Protocol (MCP) integrations.

    Meant to be launched by an MCP client (an IDE, Claude Desktop, …): it reads
    requests on stdin and writes responses on stdout, exposing the same tools as
    ``sakthai run`` backed by the shared memory store.

    Run subcommands (`list`, `ping`, `tools`) to manage configured MCP servers.
    """
    if ctx.invoked_subcommand is None:
        from ..mcp import serve

        serve()


@mcp.command(name="serve")
def mcp_serve() -> None:
    """Serve the memory tools over MCP (stdio JSON-RPC)."""
    from ..mcp import serve

    serve()


@mcp.command(name="list")
@click.option("--persona", default=None, help="Inspect MCP servers for a specific persona.")
@click.option("--builtins/--no-builtins", default=False, help="Include built-in ecosystem servers.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def mcp_list(persona: str | None, builtins: bool, as_json: bool) -> None:
    """List configured external MCP servers."""
    from ..mcp import load_server_specs

    ctx_mgr = (
        _temp_env("SAKTHAI_MCP_CONFIG", str(config.persona_mcp_config_path(persona)))
        if (persona and config.persona_mcp_config_path(persona).is_file())
        else contextlib.nullcontext()
    )

    with ctx_mgr:
        specs = load_server_specs(persona=persona, include_builtins=builtins)

    if as_json:
        data = [
            {
                "name": s.name,
                "transport": s.transport,
                "command": s.command,
                "args": s.args,
                "url": s.url,
                "tools": s.tools,
            }
            for s in specs
        ]
        click.echo(json.dumps(data, indent=2))
        return

    if not specs:
        click.echo("No external MCP servers configured.")
        return

    click.echo(f"Configured MCP server(s) ({len(specs)}):")
    for s in specs:
        target = s.url if s.url else f"{s.command} {' '.join(s.args)}".strip()
        tools_str = f" [tools: {', '.join(s.tools)}]" if s.tools else ""
        click.echo(f"  • {click.style(s.name, bold=True)} ({s.transport}): {target}{tools_str}")


@mcp.command(name="ping")
@click.argument("name", required=False)
@click.option("--persona", default=None, help="Inspect MCP servers for a specific persona.")
@click.option("--builtins/--no-builtins", default=False, help="Include built-in ecosystem servers.")
def mcp_ping(name: str | None, persona: str | None, builtins: bool) -> None:
    """Ping configured MCP servers to verify responsiveness."""
    from ..mcp import RemoteMCPClient, StdioMCPClient, load_server_specs

    ctx_mgr = (
        _temp_env("SAKTHAI_MCP_CONFIG", str(config.persona_mcp_config_path(persona)))
        if (persona and config.persona_mcp_config_path(persona).is_file())
        else contextlib.nullcontext()
    )

    with ctx_mgr:
        specs = load_server_specs(persona=persona, include_builtins=builtins)

    if name:
        specs = [s for s in specs if s.name == name]
        if not specs:
            raise click.ClickException(f"No configured MCP server named {name!r}")

    if not specs:
        click.echo("No external MCP servers configured.")
        return

    for s in specs:
        client: StdioMCPClient | RemoteMCPClient
        if s.transport in ("sse", "http") or s.url:
            if not s.url:
                click.echo(f"  • {s.name}: FAIL (missing url)")
                continue
            client = RemoteMCPClient(s.url, name=s.name, timeout=5.0)
        else:
            if not s.command:
                click.echo(f"  • {s.name}: FAIL (missing command)")
                continue
            client = StdioMCPClient(
                s.command,
                s.args,
                env=s.env or None,
                cwd=s.cwd,
                name=s.name,
                timeout=5.0,
            )

        try:
            client.start()
            ok = client.ping()
            status = click.style("PONG", fg="green") if ok else click.style("NO PONG", fg="yellow")
            click.echo(f"  • {s.name}: {status}")
        except Exception as exc:
            click.echo(f"  • {s.name}: {click.style('ERROR', fg='red')} ({exc})")
        finally:
            client.close()


@mcp.command(name="tools")
@click.option("--persona", default=None, help="Inspect MCP servers for a specific persona.")
@click.option("--builtins/--no-builtins", default=False, help="Include built-in ecosystem servers.")
def mcp_tools(persona: str | None, builtins: bool) -> None:
    """List tools exposed by configured external MCP servers."""
    from ..mcp.manager import connect_servers

    ctx_mgr = (
        _temp_env("SAKTHAI_MCP_CONFIG", str(config.persona_mcp_config_path(persona)))
        if (persona and config.persona_mcp_config_path(persona).is_file())
        else contextlib.nullcontext()
    )

    with ctx_mgr, connect_servers(persona=persona, include_builtins=builtins) as tools:
        if not tools:
            click.echo("No external MCP tools available.")
            return
        click.echo(f"Available external MCP tool(s) ({len(tools)}):")
        for t in tools:
            click.echo(f"  • {click.style(t.name, bold=True)}: {t.description}")


@mcp.group(name="registry")
def mcp_registry() -> None:
    """Sync and search the MCP registry.

    The registry is the upstream catalogue of published MCP servers. Syncing it
    gives two things a hand-edited ``mcp.json`` cannot: a way to find a server
    by name, and the status the registry carries for each one — so a server
    withdrawn upstream for malware shows up in ``sakthai doctor`` instead of
    going on running. Point ``SAKTHAI_MCP_REGISTRY_URL`` at a private
    subregistry to curate what is discoverable.
    """


@mcp_registry.command(name="sync")
@click.option("--since", default=None, help="RFC 3339 timestamp; fetch only what changed since.")
@click.option("--url", default=None, help="Registry base URL (default: SAKTHAI_MCP_REGISTRY_URL).")
def mcp_registry_sync(since: str | None, url: str | None) -> None:
    """Fetch the registry listing into the local cache."""
    from ..mcp.registry import RegistryError, sync

    target = url or config.mcp_registry_url()
    click.echo(f"Syncing {target} …")
    try:
        count = sync(base_url=url, updated_since=since)
    except RegistryError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Cached {count} server(s) to {config.registry_cache_path()}")


@mcp_registry.command(name="search")
@click.argument("query", required=False, default="")
@click.option("--limit", default=20, show_default=True, help="Maximum results.")
@click.option("--all", "include_problems", is_flag=True, help="Include deprecated and deleted.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def mcp_registry_search(query: str, limit: int, include_problems: bool, as_json: bool) -> None:
    """Search the cached registry listing."""
    from ..mcp.registry import read_cache, search

    cached = read_cache()
    if not cached:
        raise click.ClickException("No registry cache. Run `sakthai mcp registry sync` first.")

    hits = search(query, servers=cached, limit=limit, include_problems=include_problems)
    if as_json:
        click.echo(json.dumps([s.to_json() for s in hits], indent=2))
        return
    if not hits:
        click.echo(f"No match for {query!r} in {len(cached)} cached server(s).")
        return

    click.echo(f"{len(hits)} of {len(cached)} cached server(s):")
    for s in hits:
        flag = "" if not s.is_problem else click.style(f" [{s.status}]", fg="red", bold=True)
        version = f" {s.version}" if s.version else ""
        click.echo(f"  • {click.style(s.name, bold=True)}{version}{flag}")
        if s.description:
            click.echo(f"      {s.description}")


@mcp_registry.command(name="check")
@click.option("--persona", default=None, help="Check the servers a specific persona configures.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def mcp_registry_check(persona: str | None, as_json: bool) -> None:
    """Report configured servers the registry marks deprecated or deleted.

    This is what a version pin cannot do. A pin stops an unreviewed new release
    from running; it says nothing about the release you already pinned being
    withdrawn for malware. Exits non-zero when something is found, so it can
    gate a deploy.
    """
    from ..mcp import load_server_specs
    from ..mcp.registry import check_configured_servers, read_cache

    cached = read_cache()
    if not cached:
        raise click.ClickException("No registry cache. Run `sakthai mcp registry sync` first.")

    ctx_mgr = (
        _temp_env("SAKTHAI_MCP_CONFIG", str(config.persona_mcp_config_path(persona)))
        if (persona and config.persona_mcp_config_path(persona).is_file())
        else contextlib.nullcontext()
    )
    with ctx_mgr:
        specs = load_server_specs()

    problems = check_configured_servers([s.name for s in specs], servers=cached)

    if as_json:
        click.echo(
            json.dumps(
                [
                    {"configured_as": name, "registry_name": e.name, "status": e.status}
                    for name, e in problems
                ],
                indent=2,
            )
        )
    elif not problems:
        click.echo(f"All {len(specs)} configured server(s) are active upstream.")
    else:
        click.echo(f"{len(problems)} configured server(s) withdrawn upstream:")
        for name, entry in problems:
            click.echo(
                f"  • {click.style(name, bold=True)} matches "
                f"{entry.name} — {click.style(entry.status, fg='red', bold=True)}"
            )
    if problems:
        raise SystemExit(1)
