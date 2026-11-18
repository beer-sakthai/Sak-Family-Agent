"""CLI commands to summarize the local model eval/MLOps log and persona readiness."""

from __future__ import annotations

import contextlib
import json
import sys

import click
import yaml

from .. import config
from ..agent.eval import evaluate_all_personas, evaluate_persona_readiness, summarize_evals
from ..config import PERSONA_NAMES
from ._runner import run_repo_argv


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


class _LmEvalYamlLoader(yaml.SafeLoader):  # type: ignore[misc]
    pass


_LmEvalYamlLoader.add_multi_constructor("", lambda loader, tag, node: None)


@eval_cmd.command("tasks")
@click.option("--json", "as_json", is_flag=True, help="Emit evaluation tasks as JSON.")
def eval_tasks(as_json: bool) -> None:
    """List registered lm-eval task definitions in evaluation_tasks/."""
    tasks_dir = config.REPO_ROOT / "evaluation_tasks"
    tasks: list[dict[str, object]] = []
    if tasks_dir.is_dir():
        for path in sorted(tasks_dir.glob("*.yaml")):
            try:
                data = (
                    yaml.load(path.read_text(encoding="utf-8"), Loader=_LmEvalYamlLoader)  # nosec B506
                    or {}
                )
            except Exception:
                data = {}
            task_name = data.get("task", path.stem)
            dataset_file = data.get("dataset_kwargs", {}).get("data_files")
            rows = 0
            if dataset_file:
                dpath = config.REPO_ROOT / str(dataset_file)
                if dpath.is_file():
                    with contextlib.suppress(OSError):
                        rows = sum(
                            1
                            for line in dpath.read_text(encoding="utf-8").splitlines()
                            if line.strip()
                        )
            tasks.append(
                {
                    "task": task_name,
                    "file": path.name,
                    "dataset_file": dataset_file or "",
                    "rows": rows,
                }
            )

    if as_json:
        click.echo(json.dumps(tasks, indent=2))
        return

    click.echo("# Registered lm-eval Tasks (evaluation_tasks/)")
    click.echo(f"  {'TASK NAME':<32} {'ROWS':<6} {'CONFIG FILE'}")
    click.echo("  " + "-" * 65)
    for t in tasks:
        click.echo(f"  {t['task']:<32} {t['rows']:<6} {t['file']}")
    click.echo(f"\nTotal tasks: {len(tasks)}. Run benchmark with `sakthai eval bench`.")


@eval_cmd.command("bench", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print benchmark command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def eval_bench(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Run model evaluation benchmark via scripts/eval/run_bench.py."""
    argv = ["uv", "run", "python", "scripts/eval/run_bench.py"] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)
