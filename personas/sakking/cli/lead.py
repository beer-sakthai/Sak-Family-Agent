"""Commands for managing customer leads, pipeline, and recurring revenue."""

from __future__ import annotations

import json

import click

from ..lead import (
    VALID_LEAD_STATUSES,
    calculate_lead_revenue_metrics,
    capture_lead,
    get_lead_by_id,
    list_leads,
    update_lead_status,
)
from ..memory.store import MemoryStore


@click.group("lead")
def lead_cmd() -> None:
    """Manage customer leads, quoting status, and revenue tracking."""


@lead_cmd.command("list")
@click.option(
    "--status",
    type=click.Choice([s.lower() for s in VALID_LEAD_STATUSES], case_sensitive=False),
    help="Filter leads by status (new, quoted, won, lost).",
)
@click.option("--limit", default=50, show_default=True, type=int, help="Maximum leads to return.")
@click.option("--json", "as_json", is_flag=True, help="Output leads as JSON.")
def lead_list(status: str | None, limit: int, as_json: bool) -> None:
    """List customer leads stored in memory."""
    with MemoryStore() as store:
        leads = list_leads(status=status, store=store, limit=limit)

    if as_json:
        click.echo(json.dumps(leads, indent=2, ensure_ascii=False))
        return

    if not leads:
        msg = f"No leads found{f' with status {status.upper()}' if status else ''}."
        click.echo(msg)
        return

    click.echo(f"Found {len(leads)} lead(s):")
    for item in leads:
        lead_id = item.get("id")
        lead_status = item.get("status", "NEW")
        name = item.get("name") or "Anonymous"
        phone = item.get("phone") or "-"
        email = item.get("email") or "-"
        val = item.get("deal_value", 0.0)
        mrr = item.get("monthly_recurring_revenue", 0.0)
        query = item.get("query", "")
        click.echo(
            f"  [#{lead_id}] [{lead_status}] {name} (phone: {phone}, email: {email}) "
            f"| deal: ${val:,.2f} | MRR: ${mrr:,.2f}"
        )
        if query:
            preview = query[:80] + ("..." if len(query) > 80 else "")
            click.echo(f"       query: {preview}")


@lead_cmd.command("stats")
@click.option("--json", "as_json", is_flag=True, help="Output metrics as JSON.")
def lead_stats(as_json: bool) -> None:
    """Show lead conversion and revenue metrics (pipeline, won revenue, MRR)."""
    with MemoryStore() as store:
        metrics = calculate_lead_revenue_metrics(store=store)

    if as_json:
        click.echo(json.dumps(metrics.to_dict(), indent=2))
        return

    click.echo("================ Lead & Revenue Metrics ================")
    click.echo(f"  Total Leads:        {metrics.total_leads}")
    click.echo(
        f"  Status Breakdown:   {metrics.new_leads} NEW | {metrics.quoted_leads} QUOTED | "
        f"{metrics.won_leads} WON | {metrics.lost_leads} LOST"
    )
    click.echo(f"  Conversion Rate:    {metrics.conversion_rate:.1f}%")
    click.echo(f"  Pipeline Value:     ${metrics.total_pipeline_value:,.2f}")
    click.echo(f"  Total Won Revenue:  ${metrics.total_won_revenue:,.2f}")
    click.echo(f"  Monthly Recurring:  ${metrics.total_mrr:,.2f} MRR")
    click.echo(f"  Average Deal Size:  ${metrics.average_deal_size:,.2f}")
    click.echo("========================================================")


@lead_cmd.command("capture")
@click.option("--query", "-q", required=True, help="Customer request or service inquiry.")
@click.option("--name", "-n", help="Customer name.")
@click.option("--phone", "-p", help="Customer phone number.")
@click.option("--email", "-e", help="Customer email address.")
@click.option(
    "--status",
    default="NEW",
    type=click.Choice([s.lower() for s in VALID_LEAD_STATUSES], case_sensitive=False),
    help="Initial lead status.",
)
@click.option("--deal-value", type=float, default=0.0, help="Estimated deal value ($).")
@click.option("--mrr", type=float, default=0.0, help="Estimated monthly recurring revenue ($).")
@click.option("--notes", help="Internal lead notes.")
def lead_capture_cli(
    query: str,
    name: str | None,
    phone: str | None,
    email: str | None,
    status: str,
    deal_value: float,
    mrr: float,
    notes: str | None,
) -> None:
    """Capture a new customer lead."""
    try:
        with MemoryStore() as store:
            lead_id = capture_lead(
                name=name,
                phone=phone,
                email=email,
                query=query,
                status=status,
                deal_value=deal_value,
                monthly_recurring_revenue=mrr,
                notes=notes,
                store=store,
            )
        click.echo(f"Captured lead #{lead_id} ({status.upper()})")
    except ValueError as err:
        raise click.ClickException(str(err)) from err


@lead_cmd.command("update")
@click.argument("lead_id", type=int)
@click.option(
    "--status",
    type=click.Choice([s.lower() for s in VALID_LEAD_STATUSES], case_sensitive=False),
    help="New lead status (new, quoted, won, lost).",
)
@click.option("--deal-value", type=float, help="Updated deal value ($).")
@click.option("--mrr", type=float, help="Updated monthly recurring revenue ($).")
@click.option("--notes", help="Updated lead notes.")
def lead_update_cli(
    lead_id: int,
    status: str | None,
    deal_value: float | None,
    mrr: float | None,
    notes: str | None,
) -> None:
    """Update lead status, deal value, or MRR."""
    with MemoryStore() as store:
        lead = get_lead_by_id(lead_id, store=store)
        if lead is None:
            raise click.ClickException(f"Lead #{lead_id} not found.")

        target_status = status.upper() if status else lead.get("status", "NEW")
        updated = update_lead_status(
            lead_id,
            target_status,
            deal_value=deal_value,
            monthly_recurring_revenue=mrr,
            notes=notes,
            store=store,
        )

    if updated:
        click.echo(f"Updated lead #{lead_id} to status [{target_status}].")
    else:
        raise click.ClickException(f"Failed to update lead #{lead_id}.")
