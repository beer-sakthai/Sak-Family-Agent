"""The ``telegram`` command group: serve bot gateways and manage VM agents."""

from __future__ import annotations

import sys

import click

from ..config import telegram_bot_token
from ._runner import run_repo_argv


@click.group(name="telegram")
def telegram_cmd() -> None:
    """Manage Telegram bot gateways, message sending, and VM agents."""


@telegram_cmd.command("serve")
def telegram_serve() -> None:
    """Run the live Telegram bot gateway."""
    token = telegram_bot_token()
    if not token:
        raise click.ClickException(
            "TELEGRAM_BOT_TOKEN environment variable not set. "
            "Set it in your environment or .env file to start the bot."
        )
    from ..telegram.bot import main as bot_main

    bot_main()


@telegram_cmd.command("send")
@click.option("--text", "-m", required=True, help="Message text to send.")
@click.option("--chat-id", "-c", default=None, help="Target Telegram chat ID.")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def telegram_send(text: str, chat_id: str | None, dry_run: bool) -> None:
    """Send an ad-hoc message or alert through Telegram."""
    argv = ["uv", "run", "python", "scripts/telegram_send.py", "--message", text]
    if chat_id:
        argv.extend(["--chat-id", chat_id])
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@telegram_cmd.command("verify")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def telegram_verify(dry_run: bool) -> None:
    """Verify live status of background VM Telegram bot agents."""
    code = run_repo_argv(
        ["uv", "run", "python", "scripts/verify_vm_telegram_agents.py"],
        dry_run=dry_run,
    )
    if code != 0:
        sys.exit(code)


@telegram_cmd.command("setup-vm")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def telegram_setup_vm(dry_run: bool) -> None:
    """Provision systemd / background services for VM Telegram agents."""
    code = run_repo_argv(
        ["uv", "run", "python", "scripts/setup_vm_telegram_agents.py"],
        dry_run=dry_run,
    )
    if code != 0:
        sys.exit(code)
