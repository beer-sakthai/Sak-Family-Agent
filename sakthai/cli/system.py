"""System commands: ``doctor``, ``setup``, ``status``, ``tools``."""

from __future__ import annotations

import os
from pathlib import Path

import click

from ..config import check_env

_OK = "[+]"
_WARN = "[!]"
_ERR = "[x]"
_INFO = "[i]"


def _ok() -> str:
    return click.style(_OK, fg="green", bold=True)


def _warn() -> str:
    return click.style(_WARN, fg="yellow", bold=True)


def _err() -> str:
    return click.style(_ERR, fg="red", bold=True)


def _info() -> str:
    return click.style(_INFO, fg="cyan")


def _flag(ok: bool, *, optional: bool = False) -> str:
    if ok:
        return _ok()
    return _warn() if optional else _err()


@click.command()
def doctor() -> None:
    """Report environment, paths, memory, and credential status."""
    env = check_env()
    click.echo(click.style("\n── SakThai Doctor ──", bold=True))

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

    click.echo()
    if env["ready"]:
        click.echo(click.style("  ✓ SakThai is ready.", fg="green", bold=True))
    else:
        click.echo(click.style("  ✗ Core components missing — see above.", fg="red", bold=True))
    click.echo()


@click.command()
def setup() -> None:
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
            click.echo(
                click.style(f"      → export {var}=<value>  # {info['description']}", fg="yellow")
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
def status() -> None:
    """A high-level health summary of everything needed to start."""
    env = check_env()
    click.echo(click.style("\n── SakThai Status ──", bold=True))

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
    if env["ready"]:
        click.echo(
            click.style(
                '  ✓ Ready — try: sakthai run "what do you know about me?"', fg="green", bold=True
            )
        )
    else:
        click.echo(
            click.style(
                "  ✗ Not ready — run `sakthai setup` for a guided fix.", fg="red", bold=True
            )
        )
    click.echo()


@click.command()
def tools() -> None:
    """List the built-in agent/MCP tools."""
    from ..agent.tools import BUILTIN_TOOLS

    click.echo(
        click.style("\n── Built-in SakThai tools (via `sakthai run` and `sakthai mcp`)", bold=True)
    )
    for tool in BUILTIN_TOOLS:
        click.echo(f"  {_ok()} {tool.name:<22} {tool.description[:66]}")
    click.echo()
