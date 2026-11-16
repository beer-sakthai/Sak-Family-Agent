"""CLI commands to summarize the local model eval/MLOps log and persona readiness."""

from __future__ import annotations

import json
import sys

import click

from ..agent.eval import evaluate_all_personas, evaluate_persona_readiness, summarize_evals
from ..config import PERSONA_NAMES


@click.group()
def eval_cmd() -> None:
    """Inspect local model evaluation / MLOps metrics and persona readiness."""


@eval_cmd.command("summary")
@click.option(
    "--limit",
    default=50,
    show_default=True,
    type=click.IntRange(min=1),
    help="Number of recent runs to summarize.",
)
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Filter summary to a single persona (reads root log + ~/.sakthai/<persona>/eval.jsonl).",
)
@click.option(
    "--all-personas",
    is_flag=True,
    help="Include all per-persona sharded logs (~/.sakthai/<persona>/eval.jsonl).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the raw summary as JSON.")
def eval_summary(limit: int, persona: str | None, all_personas: bool, as_json: bool) -> None:
    """Summarize latency, tokens, and error rate over recent agent runs."""
    data = summarize_evals(limit=limit, persona=persona, include_persona_shards=all_personas)
    if as_json:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if data["count"] == 0:
        click.echo('(no eval records yet — run `sakthai run "..."` first)')
        return

    click.echo("# Eval summary" + (f" ({persona})" if persona else ""))
    click.echo(f"  runs:          {data['count']}")
    click.echo(f"  error rate:    {data['error_rate']:.1%}")
    click.echo(f"  avg latency:   {data['avg_latency_s']:.2f}s")
    click.echo(f"  input tokens:  {data['total_input_tokens']}")
    click.echo(f"  output tokens: {data['total_output_tokens']}")

    if data.get("per_model"):
        click.echo("# Per-model")
        for model, stats in data["per_model"].items():
            click.echo(
                f"  {model:<24} runs={stats['count']:<4} "
                f"avg_latency={stats['avg_latency_s']:.2f}s "
                f"in={stats['input_tokens']} out={stats['output_tokens']}"
            )

    per_persona = data.get("per_persona")
    if per_persona and (all_personas or persona is not None or len(per_persona) > 1):
        click.echo("# Per-persona")
        for p_name, stats in per_persona.items():
            click.echo(
                f"  {p_name:<24} runs={stats['count']:<4} "
                f"err={stats['error_rate']:.1%} "
                f"avg_latency={stats['avg_latency_s']:.2f}s "
                f"in={stats['input_tokens']} out={stats['output_tokens']}"
            )


@eval_cmd.command("personas")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate a single persona instead of all six.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the persona evaluation report as JSON.")
def eval_personas(persona: str | None, as_json: bool) -> None:
    """Audit the 6 working files, v9 self-eval rubric, intro line, and skills for each persona."""
    if persona:
        report = {persona: evaluate_persona_readiness(persona)}
    else:
        report = evaluate_all_personas()
    if as_json:
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
        if not all(item["ready"] for item in report.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family 6-Persona Evaluation Readiness")
    all_ready = True
    for p_name, info in report.items():
        status = "READY" if info["ready"] else "INCOMPLETE"
        if not info["ready"]:
            all_ready = False
        wf_ok = sum(1 for v in info["working_files"].values() if v)
        has_rubric = info["has_v9_rubric_soul"] and info["has_v9_rubric_cycle"]
        rubric = "ok" if has_rubric else "missing"
        click.echo(
            f"  [{status}] {p_name:<10} "
            f"files={wf_ok}/6 "
            f"v9_rubric={rubric} "
            f"skills={info['skill_count']:<3} "
            f"model={info['provider']}:{info['model']}"
        )
    if not all_ready:
        sys.exit(1)
