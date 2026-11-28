"""System commands: ``doctor``, ``setup``, ``status``, ``tools``."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import click

from ..config import check_env
from ._output import EXIT_NOT_READY, EXIT_OK, OutputContext, output_options

_OK = "[+]"
_WARN = "[!]"
_ERR = "[x]"
_INFO = "[i]"


def _ok() -> str:
    return str(click.style(_OK, fg="green", bold=True))


def _warn() -> str:
    return str(click.style(_WARN, fg="yellow", bold=True))


def _err() -> str:
    return str(click.style(_ERR, fg="red", bold=True))


def _info() -> str:
    return str(click.style(_INFO, fg="cyan"))


def _flag(ok: bool, *, optional: bool = False) -> str:
    if ok:
        return _ok()
    return _warn() if optional else _err()


def _emit_json_report(report: dict[str, object]) -> None:
    """Write a deterministic, secret-free environment report for automation."""
    click.echo(json.dumps(report, sort_keys=True))


def _has_provider_credentials(auth: dict[str, object]) -> bool:
    """True when any model provider's credentials were detected.

    ``ready`` only covers memory (``learn``/``recall``/``mcp`` need no key), so
    this is what decides whether ``run``/``chat`` can reach a model. A local
    Ollama at the default address needs no env var and is not detected here.
    """
    keys = ("anthropic_ok", "openai_ok", "gateway_ok", "huggingface_ok", "gemini_ok")
    return any(bool(auth.get(k)) for k in keys) or bool(auth.get("gemini_cli_oauth"))


_NO_PROVIDER_HINT = (
    "  ! No model provider credentials found — `run`/`chat` need one "
    "(e.g. ANTHROPIC_API_KEY, GEMINI_API_KEY, HF_TOKEN);\n"
    "    `--provider ollama` and SakTan need none if Ollama runs at 127.0.0.1:11434 "
    "(or OLLAMA_HOST);\n"
    "    memory commands (`learn`, `recall`, `mcp`) work now."
)


def _exit_if_not_ready(report: dict[str, object]) -> None:
    """Return success only when the core components are usable."""
    if not report.get("ready"):
        click.get_current_context().exit(EXIT_NOT_READY)


@click.command()
@output_options
def doctor(out: OutputContext | None = None, **_kwargs: Any) -> None:
    """Report environment, paths, memory, and credential status."""
    if out is None:
        out = OutputContext()
    env = check_env()
    exit_code = EXIT_OK if env.get("ready") else EXIT_NOT_READY

    if out.json:
        out.emit(env, exit_code=exit_code)
        return

    if out.quiet:
        if exit_code != EXIT_OK:
            out.error("Core components missing", code="NOT_READY", exit_code=exit_code)
        return

    out.rainbow_header("SakThai Doctor", persona="sakthai")
    out.rainbow_rule(width=60)

    paths = env["paths"]
    click.echo(click.style("\n  Paths", bold=True))
    click.echo(f"  {_flag(paths['sakthai_home_exists'])} sakthai home : {paths['sakthai_home']}")
    click.echo(
        f"  {_flag(paths['memory_db_exists'], optional=True)} memory db    : {paths['memory_db']}"
    )
    click.echo(
        f"  {_flag(paths['skills_dir_exists'], optional=True)} skills dir   : {paths['skills_dir']}"
    )

    mem = env["memory"]
    click.echo(click.style("\n  Memory database", bold=True))
    click.echo(f"  {_flag(mem['db_exists'], optional=True)} exists  : {mem['db_exists']}")
    click.echo(f"  {_flag(mem['db_writable'], optional=True)} writable: {mem['db_writable']}")
    if mem["db_exists"] and mem["error"] is None:
        click.echo(
            f"  {_ok()} facts: {mem['fact_count']}  observations: {mem['observation_count']}"
        )
    if mem["error"]:
        click.echo(f"  {_err()} error: {mem['error']}")

    auth = env["auth"]
    click.echo(click.style("\n  Credentials", bold=True))
    label = {
        "api_key": "ANTHROPIC_API_KEY env var",
        "auth_token": "ANTHROPIC_AUTH_TOKEN env var",  # nosec B105 — UI label
        "claude_cli": "Claude CLI (~/.claude/.credentials.json)",
    }.get(auth.get("anthropic_source") or "")
    if label:
        click.echo(f"  {_ok()} Anthropic    : {label}")
    else:
        click.echo(f"  {_err()} Anthropic    : none found")
        click.echo(click.style("      → set ANTHROPIC_API_KEY or run `claude login`", fg="yellow"))
    gemini = auth.get("gemini_cli_oauth", False)
    click.echo(
        f"  {_flag(gemini, optional=True)} Gemini CLI   : "
        f"{'active' if gemini else 'not found (optional — `gemini auth login`)'}"
    )

    _report_mcp_supply_chain()

    click.echo()
    if env["ready"] and not _has_provider_credentials(env["auth"]):
        click.echo(click.style("  ✓ Memory is ready.", fg="green", bold=True))
        click.echo(click.style(_NO_PROVIDER_HINT, fg="yellow"))
    elif env["ready"]:
        ready_text = out.rainbow_text("  ✓ SakThai is ready.", style="bold")
        out.console.print(ready_text)
    else:
        click.echo(click.style("  ✗ Core components missing — see above.", fg="red", bold=True))
    click.echo()


def _report_mcp_supply_chain() -> None:
    """Warn about configured MCP servers the registry has withdrawn.

    An exact version pin stops an unreviewed *new* release from running. It
    says nothing about the release already pinned being pulled upstream for
    malware, which is what the registry's ``deleted`` status records. Silent
    when no registry cache exists, because syncing is an explicit choice and a
    nag for an unused feature is noise.
    """
    from ..mcp.registry import check_configured_servers, read_cache

    try:
        cached = read_cache()
        if not cached:
            return
        from ..mcp import load_server_specs

        specs = load_server_specs()
        problems = check_configured_servers([s.name for s in specs], servers=cached)
    except Exception as exc:  # noqa: BLE001 — diagnostics must never fail doctor
        click.echo(click.style("\n  MCP supply chain", bold=True))
        click.echo(f"  {_err()} could not check the registry cache: {exc}")
        return

    click.echo(click.style("\n  MCP supply chain", bold=True))
    if not problems:
        click.echo(f"  {_ok()} all {len(specs)} configured server(s) active upstream")
        return
    for name, entry in problems:
        click.echo(f"  {_err()} {name} → {entry.name} is {entry.status} upstream")
    click.echo(click.style("      → review it, then remove it from mcp.json", fg="yellow"))


@click.command()
@click.option("--interactive/--no-interactive", default=False, help="Prompt to fix issues.")
def setup(interactive: bool) -> None:
    """Check the .env file, env vars, memory DB, and virtualenv."""
    env = check_env()
    click.echo(click.style("\n── SakThai Setup Check ──", bold=True))
    issues: list[str] = []

    click.echo(click.style("\n  1. .env file", bold=True))
    env_file = Path(".env")
    if env_file.exists():
        click.echo(f"  {_ok()} found at {env_file.resolve()}")
    else:
        click.echo(f"  {_err()} not found")
        example = Path(".env.example")
        if interactive and example.exists():
            if click.confirm(
                click.style("      → .env.example exists. Create .env now?", fg="yellow"),
                default=True,
            ):
                env_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
                click.echo(f"  {_ok()} created .env from .env.example")
            else:
                issues.append(".env file missing")
        else:
            click.echo(
                click.style("      → cp .env.example .env  # then fill in your keys", fg="yellow")
            )
            issues.append(".env file missing")

    click.echo(click.style("\n  2. Required environment variables", bold=True))
    anthropic_ok = env["auth"]["anthropic_ok"]
    for var, info in env["env"].items():
        if not info["required"]:
            continue
        if info["set"] or (var == "ANTHROPIC_API_KEY" and anthropic_ok):
            click.echo(f"  {_ok()} {var}")
        else:
            click.echo(f"  {_err()} {var} is NOT set")
            if interactive and var == "ANTHROPIC_API_KEY" and env_file.exists():
                val = str(
                    click.prompt(
                        click.style(f"      → Enter your {var}", fg="yellow"),
                        hide_input=True,
                        default="",
                        show_default=False,
                    )
                )
                if val:
                    content = env_file.read_text(encoding="utf-8")
                    pattern = rf"^{var}=.*$"
                    replacement = f"{var}={val}"
                    if re.search(pattern, content, re.MULTILINE):
                        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    else:
                        new_content = content.rstrip() + f"\n{replacement}\n"
                    env_file.write_text(new_content, encoding="utf-8")
                    click.echo(f"  {_ok()} saved {var} to .env")
                    # Update local env for subsequent checks in this run
                    os.environ[var] = val
                else:
                    issues.append(f"{var} not set")
            else:
                click.echo(
                    click.style(
                        f"      → export {var}=<value>  # {info['description']}", fg="yellow"
                    )
                )
                issues.append(f"{var} not set")

    click.echo(click.style("\n  3. Memory database", bold=True))
    mem = env["memory"]
    if mem["db_exists"] and mem["db_writable"]:
        click.echo(
            f"  {_ok()} writable — {mem['fact_count']} facts, {mem['observation_count']} observations"
        )
    elif not mem["db_exists"]:
        click.echo(f"  {_info()} not yet created (created on first use)")
    else:
        click.echo(f"  {_err()} exists but is not writable")
        issues.append("memory.db not writable")

    click.echo(click.style("\n  4. Python environment", bold=True))
    venv = os.environ.get("VIRTUAL_ENV")
    click.echo(
        f"  {_ok()} virtualenv active: {venv}"
        if venv
        else f"  {_info()} no virtualenv detected — consider: source .venv/bin/activate"
    )

    click.echo()
    if not issues:
        click.echo(
            click.style('  ✓ All checks passed. Try `sakthai run "hello"`.', fg="green", bold=True)
        )
    else:
        click.echo(click.style(f"  ✗ {len(issues)} issue(s):", fg="red", bold=True))
        for issue in issues:
            click.echo(f"    • {issue}")
    click.echo()


@click.command()
@output_options
def status(out: OutputContext | None = None, **_kwargs: Any) -> None:
    """A high-level health summary of everything needed to start."""
    if out is None:
        out = OutputContext()
    env = check_env()
    exit_code = EXIT_OK if env.get("ready") else EXIT_NOT_READY

    if out.json:
        out.emit(env, exit_code=exit_code)
        return

    if out.quiet:
        if exit_code != EXIT_OK:
            out.error("Environment not ready", code="NOT_READY", exit_code=exit_code)
        return

    out.rainbow_header("SakThai Status", persona="sakthai")
    out.rainbow_rule(width=60)

    mem = env["memory"]
    if mem["db_exists"] and mem["db_writable"]:
        click.echo(
            f"  {_ok()} Memory DB        : writable ({mem['fact_count']} facts, {mem['observation_count']} obs)"
        )
    elif not mem["db_exists"]:
        click.echo(f"  {_info()} Memory DB        : not yet created")
    else:
        click.echo(f"  {_err()} Memory DB        : exists but NOT writable")

    missing = [v for v, info in env["env"].items() if info["required"] and not info["set"]]
    if missing and not env["auth"]["anthropic_ok"]:
        for var in missing:
            click.echo(f"  {_err()} {var:<16}: NOT SET")
    else:
        click.echo(f"  {_ok()} Credentials      : present")

    skills = env["skills"]
    if skills["dir_exists"]:
        click.echo(
            f"  {_ok()} Skills dir       : {env['paths']['skills_dir']} ({skills['skill_count']})"
        )
    else:
        click.echo(f"  {_info()} Skills dir       : none ({env['paths']['skills_dir']})")

    click.echo()
    if env["ready"] and not _has_provider_credentials(env["auth"]):
        click.echo(
            click.style("  ✓ Memory ready — try: sakthai learn / recall", fg="green", bold=True)
        )
        click.echo(click.style(_NO_PROVIDER_HINT, fg="yellow"))
    elif env["ready"]:
        ready_text = out.rainbow_text(
            '  ✓ Ready — try: sakthai run "what do you know about me?"', style="bold"
        )
        out.console.print(ready_text)
    else:
        click.echo(
            click.style(
                "  ✗ Not ready — run `sakthai setup` for a guided fix.", fg="red", bold=True
            )
        )
    click.echo()


@click.command()
@output_options
def tools(out: OutputContext | None = None, **_kwargs: Any) -> None:
    """List the built-in agent/MCP tools."""
    from ..agent.tools import BUILTIN_TOOLS

    if out is None:
        out = OutputContext()

    if out.json:
        tools_data = [
            {"name": tool.name, "description": tool.description} for tool in BUILTIN_TOOLS
        ]
        out.emit(tools_data)
        return

    if out.quiet:
        for tool in BUILTIN_TOOLS:
            click.echo(tool.name)
        return

    out.rainbow_header("Built-in SakThai Tools", persona="sakthai")
    out.rainbow_rule(width=72)
    for tool in BUILTIN_TOOLS:
        name_styled = click.style(f"{tool.name:<24}", bold=True, fg="cyan")
        click.echo(f"  {_ok()} {name_styled} {tool.description[:64]}")
    click.echo()


@click.group()
def web() -> None:
    """Web server commands."""


@web.command("setup")
def web_setup() -> None:
    """Initialize web API authentication and display the token."""
    from ..web.server import _get_or_create_bearer_token

    token = _get_or_create_bearer_token()
    click.echo(click.style("\n── SakThai Web API Setup ──", bold=True))
    click.echo(f"  {_ok()} Web API bearer token is configured.")
    click.echo(f"  Token: {click.style(token, fg='green', bold=True)}")
    click.echo("  Use it in your request headers as:")
    click.echo(click.style(f"    Authorization: Bearer {token}", fg="cyan"))
    click.echo(
        click.style(
            "\n  Keep this token secret. You can regenerate it anytime using `sakthai web regen-token`.",
            fg="yellow",
        )
    )
    click.echo()


@web.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True, help="Interface to bind.")
@click.option(
    "--port",
    default=3001,
    show_default=True,
    type=click.IntRange(0, 65535),
    help="Port to listen on.",
)
def web_serve(host: str, port: int) -> None:
    """Serve the read-only web API.

    Loopback-only unless ``SAKTHAI_WEB_ALLOW_PUBLIC`` is set; every path except
    ``/health`` needs the bearer token from ``sakthai web setup``.
    """
    from ..web.server import serve

    try:
        server = serve(host=host, port=port)
    except OSError as exc:  # PermissionError (public bind refused), port in use, bad host
        raise click.ClickException(str(exc)) from exc

    click.echo(click.style(f"\n  SakThai web API on http://{host}:{port}", bold=True))
    click.echo("  Get a token with `sakthai web setup`. Ctrl-C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\n  Stopped.")
    finally:
        server.server_close()


@web.command("regen-token")
@click.confirmation_option(
    prompt="Are you sure you want to regenerate the Web API bearer token? All existing clients will stop working."
)
def web_regen_token() -> None:
    """Regenerate the Web API bearer token."""
    import secrets

    from ..config import register_secret
    from ..memory.store import MemoryStore

    new_token = secrets.token_hex(16)
    try:
        with MemoryStore() as store:
            store.delete_facts_by_key(kind="web_auth", key="bearer_token")
            store.add_fact(
                value=new_token, kind="web_auth", key="bearer_token", tags=["system", "no-export"]
            )
        # Best-effort update of any in-process server cache. Any failure here
        # only means the running server keeps the old token in memory until
        # restart; the DB write above is the source of truth.
        try:
            import sys

            for mod_name in list(sys.modules.keys()):
                if mod_name.endswith(".web.server") or mod_name.endswith(".server"):
                    mod = sys.modules[mod_name]
                    if hasattr(mod, "_BEARER_TOKEN"):
                        setattr(mod, "_BEARER_TOKEN", new_token)  # noqa: B010
        except Exception as cache_exc:  # noqa: BLE001
            click.echo(f"{_warn()} Could not refresh in-process token cache: {cache_exc}", err=True)
        register_secret(new_token)
        click.echo(click.style("\n── Web API Token Regenerated ──", bold=True))
        click.echo(f"  {_ok()} New bearer token: {click.style(new_token, fg='green', bold=True)}")
        click.echo("  Update your clients with this new token.")
        click.echo()
    except Exception as exc:
        raise click.ClickException(f"Failed to regenerate token: {exc}") from exc
