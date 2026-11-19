"""CLI commands to summarize the local model eval/MLOps log and persona readiness."""

from __future__ import annotations

import contextlib
import json
import sys

import click
import yaml

from .. import config
from ..agent.eval import (
    evaluate_all_personas,
    evaluate_persona_audit,
    evaluate_persona_readiness,
    evaluate_persona_safety_compliance,
    evaluate_persona_skills_health,
    evaluate_persona_soul_alignment,
    summarize_evals,
    summarize_fleet_audit,
)
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
    if "success_rate" in data:
        click.echo(f"  success rate:  {data['success_rate']:.1%}")
    click.echo(f"  avg latency:   {data['avg_latency_s']:.2f}s")
    if "p50_latency_s" in data and "p95_latency_s" in data:
        click.echo(f"  p50 / p95:     {data['p50_latency_s']:.2f}s / {data['p95_latency_s']:.2f}s")
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
        score_val = info.get("readiness_score", 1.0)
        score_str = f"score={score_val:.0%}"
        mcp_str = f"mcp={len(info.get('mcp_servers', []))}" if info.get("mcp_ready") else "mcp=err"
        click.echo(
            f"  [{status}] {p_name:<10} "
            f"{score_str:<10} "
            f"files={wf_ok}/6 "
            f"v9_rubric={rubric} "
            f"{mcp_str:<8} "
            f"skills={info['skill_count']:<3} "
            f"model={info['provider']}:{info['model']}"
        )
        if not info["ready"] and info.get("diagnostics"):
            for diag in info["diagnostics"]:
                click.echo(f"    - warning: {diag}")
    if not all_ready:
        sys.exit(1)


@eval_cmd.command("audit")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Audit a single persona instead of all six.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the 5-pillar audit report as JSON.")
def eval_audit(persona: str | None, as_json: bool) -> None:
    """Execute deep 5-pillar evaluation audit (Readiness, Soul, Skills, Memory, Safety)."""
    if persona:
        card = evaluate_persona_audit(persona)
        if as_json:
            click.echo(json.dumps({persona: card}, indent=2, ensure_ascii=False))
            if not card["passed"]:
                sys.exit(1)
            return
        click.echo(f"# Sak Family Persona Audit: {persona} (Grade {card['grade']})")
        click.echo(f"  Composite Score: {card['composite_score']:.0%}")
        for pillar, details in card["pillars"].items():
            status = "PASS" if details["passed"] else "FAIL"
            click.echo(f"  [{status}] {pillar.upper():<10} score={details['score']:.0%}")
        if card["diagnostics"]:
            click.echo("\n  Diagnostics:")
            for diag in card["diagnostics"]:
                click.echo(f"    - {diag}")
        if not card["passed"]:
            sys.exit(1)
        return

    report = summarize_fleet_audit()
    if as_json:
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
        if not report["all_passed"]:
            sys.exit(1)
        return

    click.echo(
        f"# Sak Family 5-Pillar Fleet Audit — Grade: {report['fleet_grade']} "
        f"({report['fleet_average_score']:.0%})"
    )
    click.echo(
        f"  {'PERSONA':<10} {'GRADE':<6} {'SCORE':<7} "
        f"{'READINESS':<11} {'SOUL':<8} {'SKILLS':<8} {'MEMORY':<8} {'SAFETY':<8}"
    )
    click.echo("  " + "-" * 72)
    for p_name, card in report["scorecards"].items():
        pils = card["pillars"]
        click.echo(
            f"  {p_name:<10} {card['grade']:<6} {card['composite_score']:.0%}{'':<3} "
            f"{pils['readiness']['score']:.0%}{'':<7} "
            f"{pils['soul']['score']:.0%}{'':<4} "
            f"{pils['skills']['score']:.0%}{'':<4} "
            f"{pils['memory']['score']:.0%}{'':<4} "
            f"{pils['safety']['score']:.0%}"
        )
        if card["diagnostics"]:
            for d in card["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not report["all_passed"]:
        sys.exit(1)


@eval_cmd.command("soul")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate soul alignment for a single persona.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the soul report as JSON.")
def eval_soul(persona: str | None, as_json: bool) -> None:
    """Evaluate persona intro line and behavioral soul alignment with SOUL.md."""
    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_soul_alignment(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["aligned"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family Soul & Principles Alignment")
    all_ok = True
    for p_name, res in results.items():
        status = "ALIGNED" if res["aligned"] else "DIVERGENT"
        if not res["aligned"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} score={res['soul_score']:.0%} "
            f"checks={res['checks_passed']}/{res['checks_total']} "
            f"intro={repr(res['intro_line'])}"
        )
        if res["diagnostics"]:
            for d in res["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not all_ok:
        sys.exit(1)


@eval_cmd.command("skills")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate skills health for a single persona.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the skills report as JSON.")
def eval_skills(persona: str | None, as_json: bool) -> None:
    """Evaluate persona skill fleet frontmatter schemas, descriptions, and primary skills."""
    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_skills_health(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["healthy"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family Skills Health & Schema Validity")
    all_ok = True
    for p_name, res in results.items():
        status = "HEALTHY" if res["healthy"] else "DEGRADED"
        if not res["healthy"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} score={res['skills_score']:.0%} "
            f"valid={res['valid_skills']}/{res['total_skills']} "
            f"primary={len(res['primary_skills'])}"
        )
        if res["diagnostics"]:
            for d in res["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not all_ok:
        sys.exit(1)


@eval_cmd.command("safety")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate safety compliance for a single persona.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the safety report as JSON.")
def eval_safety(persona: str | None, as_json: bool) -> None:
    """Evaluate secret redaction, DLP rules, and guardrail compliance."""
    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_safety_compliance(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["compliant"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family Safety & Guardrail Compliance")
    all_ok = True
    for p_name, res in results.items():
        status = "COMPLIANT" if res["compliant"] else "NON-COMPLIANT"
        if not res["compliant"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} score={res['safety_score']:.0%} "
            f"checks={res['checks_passed']}/{res['checks_total']}"
        )
        if res["diagnostics"]:
            for d in res["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not all_ok:
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
