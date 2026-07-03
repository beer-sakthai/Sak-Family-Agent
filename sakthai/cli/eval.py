"""CLI commands to summarize the local model eval/MLOps log."""

from __future__ import annotations

import json

import click

from ..agent.eval import summarize_evals


@click.group()
def eval_cmd() -> None:
    """Inspect local model evaluation / MLOps metrics."""


@eval_cmd.command("summary")
@click.option("--limit", default=50, show_default=True, help="Number of recent runs to summarize.")
@click.option("--json", "as_json", is_flag=True, help="Emit the raw summary as JSON.")
def eval_summary(limit: int, as_json: bool) -> None:
    """Summarize latency, tokens, and error rate over recent agent runs."""
    data = summarize_evals(limit=limit)
    if as_json:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if data["count"] == 0:
        click.echo("(no eval records yet — run `sakthai run \"...\"` first)")
        return

    click.echo("# Eval summary")
    click.echo(f"  runs:          {data['count']}")
    click.echo(f"  error rate:    {data['error_rate']:.1%}")
    click.echo(f"  avg latency:   {data['avg_latency_s']:.2f}s")
    click.echo(f"  input tokens:  {data['total_input_tokens']}")
    click.echo(f"  output tokens: {data['total_output_tokens']}")

    if data["per_model"]:
        click.echo("# Per-model")
        for model, stats in data["per_model"].items():
            click.echo(
                f"  {model:<24} runs={stats['count']:<4} "
                f"avg_latency={stats['avg_latency_s']:.2f}s "
                f"in={stats['input_tokens']} out={stats['output_tokens']}"
            )
