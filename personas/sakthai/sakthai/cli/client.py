"""CLI commands for ServiceQuoteBot client provisioning, management, and verification."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from ..client.manager import (
    get_client_dir,
    list_clients,
    load_client,
    onboard_client,
)
from ..client.models import ClientConfig
from ..client.verifier import run_client_verification

console = Console()


@click.group(name="client")
def client_cmd() -> None:
    """ServiceQuoteBot client provisioning, management, and verification."""


@client_cmd.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_cmd(as_json: bool) -> None:
    """List all provisioned ServiceQuoteBot clients."""
    clients = list_clients()

    if as_json:
        payload = [c.mask_sensitive() for c in clients]
        click.echo(json.dumps(payload, indent=2))
        return

    if not clients:
        console.print(
            "[yellow]No clients provisioned yet. Run 'sakthai client onboard' to provision one.[/yellow]"
        )
        return

    table = Table(
        title="Provisioned ServiceQuoteBot Clients", show_header=True, header_style="bold cyan"
    )
    table.add_column("Client ID", style="bold green")
    table.add_column("Company Name", style="white")
    table.add_column("Currency", style="cyan")
    table.add_column("Model / Provider", style="magenta")
    table.add_column("Port", style="yellow")
    table.add_column("Created", style="dim")

    for c in clients:
        model_str = f"{c.provider}:{c.model}"
        created_str = c.created_at[:10] if len(c.created_at) >= 10 else c.created_at
        table.add_row(c.client_id, c.company_name, c.currency, model_str, str(c.port), created_str)

    console.print(table)


@client_cmd.command(name="show")
@click.argument("client_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def show_cmd(client_id: str, as_json: bool) -> None:
    """Show details and paths for a provisioned client."""
    try:
        cfg = load_client(client_id)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    client_dir = get_client_dir(cfg.client_id)

    if as_json:
        payload = cfg.mask_sensitive()
        payload["workspace_dir"] = str(client_dir)
        payload["memory_db"] = str(client_dir / "data" / "memory.db")
        payload["env_file"] = str(client_dir / "client.env")
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold cyan]Client Workspace:[/bold cyan] [bold green]{cfg.client_id}[/bold green]"
    )
    console.print(f"[bold]Company Name:[/bold] {cfg.company_name}")
    console.print(f"[bold]Currency:[/bold] {cfg.currency}")
    console.print(f"[bold]Model / Provider:[/bold] {cfg.model} ({cfg.provider})")
    console.print(f"[bold]Port:[/bold] {cfg.port}")
    console.print(f"[bold]Price Book Source:[/bold] {cfg.price_book_path or '(None)'}")
    console.print(f"[bold]Workspace Dir:[/bold] {client_dir}")
    console.print(f"[bold]Memory Database:[/bold] {client_dir / 'data' / 'memory.db'}")
    console.print(f"[bold]Env File:[/bold] {client_dir / 'client.env'}\n")


@client_cmd.command(name="onboard")
@click.option("--client-id", help="Unique client slug identifier.")
@click.option("--company", "company_name", help="Company or business display name.")
@click.option(
    "--currency", default="USD", show_default=True, help="Currency code (USD, EUR, etc.)."
)
@click.option("--price-book", "price_book_path", help="Path to Markdown or CSV price book.")
@click.option("--telegram-token", default="", help="Telegram bot token.")
@click.option("--allowed-users", default="", help="Comma-separated Telegram user IDs.")
@click.option(
    "--model", default="anthropic/claude-3-5-sonnet", show_default=True, help="LLM model."
)
@click.option("--provider", default="anthropic", show_default=True, help="LLM provider.")
@click.option("--port", default=8080, type=int, show_default=True, help="Container/webhook port.")
@click.option("--json", "as_json", is_flag=True, help="Output result as JSON.")
def onboard_cmd(
    client_id: str | None,
    company_name: str | None,
    currency: str,
    price_book_path: str | None,
    telegram_token: str,
    allowed_users: str,
    model: str,
    provider: str,
    port: int,
    as_json: bool,
) -> None:
    """Provision a new client workspace and ingest their price book."""
    # Interactive fallback if required fields are missing
    if not client_id:
        client_id = click.prompt("Client ID (slug, e.g. acme-plumbing)", type=str)
    if not company_name:
        company_name = click.prompt("Company Display Name", type=str)

    user_ids: tuple[int, ...] = ()
    if allowed_users.strip():
        try:
            user_ids = tuple(int(uid.strip()) for uid in allowed_users.split(",") if uid.strip())
        except ValueError:
            click.echo("Error: allowed-users must be a comma-separated list of integers.", err=True)
            sys.exit(1)

    try:
        config = ClientConfig(
            client_id=client_id,
            company_name=company_name,
            currency=currency,
            price_book_path=price_book_path or "",
            telegram_bot_token=telegram_token,
            telegram_allowed_user_ids=user_ids,
            model=model,
            provider=provider,
            port=port,
        )
        res = onboard_client(config)
    except Exception as exc:
        click.echo(f"Error onboarding client: {exc}", err=True)
        sys.exit(1)

    if as_json:
        payload: dict[str, Any] = {
            "client_id": res.client_id,
            "workspace_dir": res.workspace_dir,
            "env_file": res.env_file,
            "memory_db": res.memory_db,
            "ingested_facts_count": res.ingested_facts_count,
            "service_file": res.service_file,
            "compose_file": res.compose_file,
            "success": res.success,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold green]✅ Successfully Onboarded Client:[/bold green] [bold cyan]{res.client_id}[/bold cyan]"
    )
    console.print(f"  • [bold]Workspace:[/bold] {res.workspace_dir}")
    console.print(f"  • [bold]Memory DB:[/bold] {res.memory_db}")
    console.print(f"  • [bold]Price Facts Ingested:[/bold] {res.ingested_facts_count}")
    console.print(f"  • [bold]Systemd Unit:[/bold] {res.service_file}")
    console.print(f"  • [bold]Docker Compose:[/bold] {res.compose_file}\n")


@client_cmd.command(name="test")
@click.argument("client_id")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging during testing.")
@click.option("--json", "as_json", is_flag=True, help="Output results as JSON.")
def test_cmd(client_id: str, verbose: bool, as_json: bool) -> None:
    """Run pre-flight verification tests for a provisioned client."""
    try:
        cfg = load_client(client_id)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not as_json:
        console.print(
            f"\n[bold cyan]🧪 Running Pre-Flight Verification for:[/bold cyan] [bold green]{cfg.company_name}[/bold green] (`{cfg.client_id}`)..."
        )

    result = run_client_verification(client_id, verbose=verbose)

    if as_json:
        payload = {
            "client_id": result.client_id,
            "all_passed": result.all_passed,
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "details": r.details,
                    "response": r.response_text,
                }
                for r in result.results
            ],
            "summary": result.summary,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print("\n" + "=" * 60)
    console.print(result.summary)
    console.print("=" * 60 + "\n")

    if not result.all_passed:
        sys.exit(1)
