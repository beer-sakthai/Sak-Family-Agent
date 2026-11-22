"""CLI command group for Quota Sentinel status and telemetry."""

from __future__ import annotations

import json
import os
from typing import Any

import click

from ..agent.quota import (
    format_time_remaining,
    get_pacific_date_str,
    get_quota_sentinel,
    seconds_until_pacific_midnight,
)


def _render_meter(percentage: float, width: int = 10) -> str:
    """Render an ASCII progress meter for terminal gauges."""
    pct = max(0.0, min(100.0, percentage))
    filled = int(round((pct / 100.0) * width))
    unfilled = width - filled
    return f"[{'█' * filled}{'░' * unfilled}]"


def _format_compact(val: int) -> str:
    """Format large numbers with compact suffix (e.g., 250000 -> 250K)."""
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(val)


@click.group(name="quota")
def quota_cmd() -> None:
    """Google AI Studio Quota Sentinel & Adaptive Rate Limiter."""


@quota_cmd.command(name="status")
@click.option("--json", "as_json", is_flag=True, help="Output status telemetry as JSON.")
@click.option(
    "--date",
    "target_date",
    default=None,
    help="Optional date in YYYY-MM-DD format (defaults to current US/Pacific date).",
)
def status(as_json: bool, target_date: str | None) -> None:
    """Display real-time Free-Tier quota consumption, RPM/TPM meters, and reset countdown."""
    sentinel = get_quota_sentinel()
    pacific_date = target_date or get_pacific_date_str()
    reset_sec = seconds_until_pacific_midnight()
    reset_human = format_time_remaining(reset_sec)
    enabled = sentinel.is_enabled()
    project_id = (
        os.environ.get("GEMINI_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or "flutter-ai-playground-a63ab"
    )

    summaries = sentinel.get_status_summaries(date_str=pacific_date)

    if as_json:
        data: dict[str, Any] = {
            "project": project_id,
            "pacific_date": pacific_date,
            "reset_in_seconds": round(reset_sec, 1),
            "reset_in_human": reset_human,
            "sentinel_enabled": enabled,
            "models": [
                {
                    "model_id": s.model_id,
                    "category": s.category,
                    "rpd_used": s.rpd_used,
                    "rpd_limit": s.rpd_limit,
                    "rpd_percentage": s.rpd_percentage,
                    "rpm_used": s.rpm_used,
                    "rpm_limit": s.rpm_limit,
                    "tpm_used": s.tpm_used,
                    "tpm_limit": s.tpm_limit,
                    "status": s.status,
                }
                for s in summaries
            ],
        }
        click.echo(json.dumps(data, indent=2))
        return

    # Terminal ASCII rendering
    click.echo("=" * 80)
    click.echo(
        f"  Google AI Studio Quota Sentinel (Project: {project_id})\n"
        f"  Reset in: {reset_human} (Midnight Pacific / 08:00 UTC)"
    )
    click.echo("=" * 80)
    click.echo(
        f"{'Model':<23} {'RPD Used / Limit':<23} {'RPM (1m)':<11} {'TPM (1m)':<12} {'Status'}"
    )
    click.echo("-" * 80)

    for s in summaries:
        meter = _render_meter(s.rpd_percentage, width=10)
        rpd_limit_str = _format_compact(s.rpd_limit) if s.rpd_limit > 0 else "0"
        rpd_str = f"{s.rpd_used} / {rpd_limit_str} {meter}"
        rpm_str = f"{s.rpm_used} / {s.rpm_limit}"
        tpm_str = f"{_format_compact(s.tpm_used)} / {_format_compact(s.tpm_limit)}"
        click.echo(f"{s.model_id:<23} {rpd_str:<23} {rpm_str:<11} {tpm_str:<12} {s.status}")

    click.echo("-" * 80)
    mode_desc = "Free-Tier Auto-Cascading Enabled" if enabled else "Bypassed / Disabled"
    click.echo(f"Active Mode: {mode_desc}\n")
