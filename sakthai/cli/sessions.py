"""CLI commands to inspect and clean up past agent sessions."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import click

from ..config import sessions_dir


def parse_duration(val: str) -> float:
    """Parse duration string like '30d' or '12h' into seconds."""
    if not val:
        raise ValueError("Empty duration")
    unit = val[-1].lower()
    try:
        amount = float(val[:-1])
    except ValueError as exc:
        raise ValueError(f"Invalid duration format: '{val}'") from exc

    if unit == "d":
        return amount * 86400
    elif unit == "h":
        return amount * 3600
    elif unit == "m":
        return amount * 60
    elif unit == "s":
        return amount
    else:
        raise ValueError(f"Unknown duration unit '{unit}' (use d, h, m, s)")


@click.group()
def sessions() -> None:
    """Manage past agent sessions."""


@sessions.command("list")
@click.option(
    "--limit", default=20, show_default=True, help="Limit number of sessions shown."
)
def sessions_list(limit: int) -> None:
    """List past agent sessions."""
    dir_path = sessions_dir()
    if not dir_path.exists():
        click.echo("No sessions found.")
        return
    files = sorted(dir_path.glob("*.json"), key=lambda p: p.name, reverse=True)
    if not files:
        click.echo("No sessions found.")
        return

    click.secho(
        f"{'Session ID':<45} {'Date/Time':<19} {'Model':<18} {'Tokens':<10} {'Task':<50}",
        bold=True,
    )
    click.echo("-" * 140)

    count = 0
    for f in files:
        if count >= limit:
            break
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        ts = data.get("timestamp")
        dt_str = ""
        if ts:
            dt_str = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")

        session_id = f.stem
        task = data.get("task", "")
        if len(task) > 50:
            task = task[:47] + "..."

        model = data.get("model", "")
        if len(model) > 18:
            model = model[:15] + "..."

        usage = data.get("usage") or {}
        total_tokens = usage.get("total_tokens", 0)
        token_str = str(total_tokens) if total_tokens else "0"

        click.echo(
            f"{session_id:<45} {dt_str:<19} {model:<18} {token_str:<10} {task:<50}"
        )
        count += 1


@sessions.command("show")
@click.argument("session_id")
def sessions_show(session_id: str) -> None:
    """Show detailed log of a session by its ID."""
    dir_path = sessions_dir()
    target = dir_path / f"{session_id}.json"
    if not target.exists():
        raise click.ClickException(f"Session '{session_id}' not found.")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to read session file: {exc}") from exc

    ts = data.get("timestamp")
    dt_str = ""
    if ts:
        dt_str = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")

    click.secho("=== Session Summary ===", bold=True, fg="cyan")
    click.echo(f"ID:         {session_id}")
    click.echo(f"Date/Time:  {dt_str}")
    click.echo(f"Model:      {data.get('model', '')}")

    usage = data.get("usage") or {}
    click.echo(
        f"Tokens:     {usage.get('total_tokens', 0)} "
        f"(Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)})"
    )
    click.echo(f"Task:       {data.get('task', '')}")

    result = data.get("result") or {}
    click.echo()
    click.secho("=== Result ===", bold=True, fg="cyan")
    click.echo(f"Iterations:  {result.get('iterations', 0)}")
    click.echo(f"Stop Reason: {result.get('stop_reason', '')}")
    click.echo("Response:")
    click.echo(result.get("text", ""))

    click.echo()
    click.secho("=== Messages Trace ===", bold=True, fg="cyan")
    for msg in data.get("messages", []):
        role = msg.get("role")
        click.secho(
            f"\n=== {role.upper()} ===",
            fg="blue" if role == "user" else "green",
            bold=True,
        )
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                b_type = block.get("type")
                if b_type == "text":
                    click.echo(block.get("text", ""))
                elif b_type == "tool_use":
                    name = block.get("name", "")
                    args = block.get("input", {})
                    tool_id = block.get("id", "")
                    click.secho(
                        f"  Tool Use: {name}({args}) [id: {tool_id}]", fg="yellow"
                    )
                elif b_type == "tool_result":
                    tool_id = block.get("tool_use_id", "")
                    result_text = block.get("content", "")
                    is_error = block.get("is_error", False)
                    fg_color = "red" if is_error else "magenta"
                    click.secho(f"  Tool Result [id: {tool_id}]:", fg=fg_color)
                    click.echo(f"    {result_text}")
        else:
            click.echo(content)


@sessions.command("clean")
@click.option(
    "--older-than",
    default="30d",
    show_default=True,
    help="Clean sessions older than duration (e.g. 30d, 12h, 60m).",
)
@click.option("--yes", "-y", is_flag=True, help="Confirm deletion without prompting.")
def sessions_clean(older_than: str, yes: bool) -> None:
    """Delete old session log files."""
    try:
        cutoff_seconds = parse_duration(older_than)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    dir_path = sessions_dir()
    if not dir_path.exists():
        click.echo("No sessions directory found.")
        return

    now = time.time()
    cutoff_ts = now - cutoff_seconds

    files_to_delete = []
    for p in dir_path.glob("*.json"):
        try:
            ts_part = p.stem.split("_")[0]
            ts = float(ts_part)
        except Exception:
            ts = p.stat().st_mtime

        if ts < cutoff_ts:
            files_to_delete.append(p)

    if not files_to_delete:
        click.echo("No sessions matched the clean criteria.")
        return

    click.echo(f"Found {len(files_to_delete)} session(s) older than {older_than}.")
    if not yes and not click.confirm("Are you sure you want to delete them?"):
        click.echo("Aborted.")
        return

    deleted = 0
    for p in files_to_delete:
        try:
            p.unlink()
            deleted += 1
        except Exception as exc:
            click.echo(f"Failed to delete {p.name}: {exc}")

    click.echo(f"Successfully deleted {deleted} session log file(s).")
