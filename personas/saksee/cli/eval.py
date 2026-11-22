"""CLI commands to summarize the local model eval/MLOps log and persona readiness."""

from __future__ import annotations

import contextlib
import json
import sys

import click
import yaml

from .. import config
from ..agent.eval import (
    evaluate_agents_md_trials,
    evaluate_all_personas,
    evaluate_extensions_trials,
    evaluate_persona_agents_md_alignment,
    evaluate_persona_audit,
    evaluate_persona_extensions_health,
    evaluate_persona_readiness,
    evaluate_persona_safety_compliance,
    evaluate_persona_skills_health,
    evaluate_persona_soul_alignment,
    evaluate_persona_tools_health,
    evaluate_skills_trials,
    evaluate_soul_trials,
    evaluate_tools_benchmark,
    evaluate_tools_trials,
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
@click.option(
    "--times",
    "-t",
    "times",
    default=1,
    type=click.IntRange(min=1),
    help="Number of evaluation trials to run (e.g. 10 or 100 for consistency benchmark).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the soul report as JSON.")
def eval_soul(persona: str | None, times: int, as_json: bool) -> None:
    """Evaluate persona intro line and behavioral soul alignment with SOUL.md."""
    if times > 1:
        bench = evaluate_soul_trials(persona=persona, trials=times)
        if as_json:
            click.echo(json.dumps(bench, indent=2, ensure_ascii=False))
            if not bench["all_trials_aligned"]:
                sys.exit(1)
            return

        click.echo(f"# Sak Family Soul Alignment Benchmark ({times} trials)")
        click.echo(
            f"  Consistency: {'100% Deterministic' if bench['consistent'] else 'Inconsistent'} | "
            f"Avg Latency: {bench['avg_latency_ms']:.2f}ms | Jitter: {bench['jitter_ms']:.2f}ms"
        )
        all_ok = bench["all_trials_aligned"]
        for p_name, res in bench["latest_report"].items():
            status = "ALIGNED" if res["aligned"] else "DIVERGENT"
            click.echo(
                f"  [{status}] {p_name:<10} score={res['soul_score']:.0%} "
                f"checks={res['checks_passed']}/{res['checks_total']} "
                f"trials={times}/{times} passed "
                f"intro={repr(res['intro_line'])}"
            )
            if res["diagnostics"]:
                for d in res["diagnostics"]:
                    click.echo(f"    - warning: {d}")
        if not all_ok:
            sys.exit(1)
        return

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
@click.option(
    "--times",
    "-t",
    "times",
    default=1,
    type=click.IntRange(min=1),
    help="Number of evaluation trials to run (e.g. 10 for consistency benchmark).",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Display 10-dimension rubric breakdown for each persona.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the skills report as JSON.")
def eval_skills(persona: str | None, times: int, detailed: bool, as_json: bool) -> None:
    """Evaluate persona skill fleet: 10-dimension rubric, schemas, and multi-run reliability."""
    if times > 1:
        trial_results = evaluate_skills_trials(persona=persona, trials=times)
        if as_json:
            click.echo(json.dumps(trial_results, indent=2, ensure_ascii=False))
            if not trial_results["all_trials_healthy"] or not trial_results["consistent"]:
                sys.exit(1)
            return

        click.echo(f"# Sak Family Skills Evaluation — {times} Trials Benchmark")
        target_str = persona if persona else "ALL PERSONAS (6 agents)"
        click.echo(f"  Target:       {target_str}")
        click.echo(f"  Trials:       {times} runs")
        consist_str = (
            "100% deterministic (0.0% variance)"
            if trial_results["consistent"]
            else "DRIFT DETECTED"
        )
        click.echo(f"  Consistency:  {consist_str}")
        click.echo(
            f"  Latency:      avg={trial_results['avg_latency_ms']:.2f}ms "
            f"(min={trial_results['min_latency_ms']:.2f}ms, "
            f"max={trial_results['max_latency_ms']:.2f}ms, "
            f"jitter={trial_results['jitter_ms']:.2f}ms)"
        )
        health_str = "HEALTHY" if trial_results["all_trials_healthy"] else "DEGRADED"
        click.echo(f"  Fleet Status: [{health_str}]")

        click.echo("\n  Trial Run Breakdown:")
        for t in trial_results["trial_history"]:
            status = "OK" if t["all_healthy"] else "FAIL"
            click.echo(
                f"    Trial #{t['trial']:<2} [{status}] "
                f"score={t['average_score']:.0%} "
                f"valid={t['valid_skills']}/{t['total_skills']} "
                f"10/10_pass={t['skills_passed_all_criteria']}/{t['total_skills']} "
                f"latency={t['latency_ms']:.2f}ms"
            )

        click.echo("\n# Final Scorecard")
        all_ok = True
        for p_name, res in trial_results["latest_report"].items():
            status = "HEALTHY" if res["healthy"] else "DEGRADED"
            if not res["healthy"]:
                all_ok = False
            pass10 = res.get("skills_passed_all_criteria", res["valid_skills"])
            click.echo(
                f"  [{status}] {p_name:<10} score={res['skills_score']:.0%} "
                f"valid={res['valid_skills']}/{res['total_skills']} "
                f"10/10_rubric={pass10}/{res['total_skills']} "
                f"primary={len(res['primary_skills'])}"
            )
            if detailed and res.get("dimensions_breakdown"):
                dims = res["dimensions_breakdown"]
                dim_str = " ".join(f"{k[:4]}={v}" for k, v in dims.items())
                click.echo(f"    - rubric: {dim_str}")
            if res["diagnostics"]:
                for d in res["diagnostics"]:
                    click.echo(f"    - warning: {d}")
        if not all_ok or not trial_results["consistent"]:
            sys.exit(1)
        return

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
        if detailed and res.get("dimensions_breakdown"):
            dims = res["dimensions_breakdown"]
            dim_str = " ".join(f"{k}={v}" for k, v in dims.items())
            click.echo(f"    - 10-factor rubric: {dim_str}")
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


@eval_cmd.command("tools")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Filter tool evaluation to a single persona.",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Show detailed 6-factor rubric breakdown and diagnostics.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the tools evaluation report as JSON.")
@click.option(
    "--times",
    "-t",
    "trials",
    default=1,
    type=click.IntRange(min=1, max=100),
    help="Number of evaluation trials to run (e.g. -t 10 for consistency benchmark).",
)
@click.option(
    "--bench",
    "-b",
    "bench",
    is_flag=True,
    help="Run dynamic tool evaluation benchmark suite and telemetry report.",
)
def eval_tools(
    persona: str | None,
    detailed: bool,
    as_json: bool,
    trials: int,
    bench: bool,
) -> None:
    """Evaluate built-in and persona tools: 6-factor rubric, schemas, validation, and repeatability."""
    if bench:
        bench_persona = persona or "sakthai"
        res = evaluate_tools_benchmark(persona=bench_persona)
        if as_json:
            click.echo(json.dumps(res, indent=2, ensure_ascii=False))
            if not res["healthy"]:
                sys.exit(1)
            return

        click.echo(res["report"])
        if not res["healthy"]:
            sys.exit(1)
        return

    if trials > 1:
        trial_res = evaluate_tools_trials(persona=persona, trials=trials)
        if as_json:
            click.echo(json.dumps(trial_res, indent=2, ensure_ascii=False))
            if not trial_res["all_healthy"] or not trial_res["deterministic"]:
                sys.exit(1)
            return

        click.echo(f"# Sak Family Tools Evaluation — {trials} Trials Benchmark")
        click.echo(f"  Target:       {trial_res['target']}")
        click.echo(f"  Trials:       {trial_res['trials']} runs")
        click.echo(
            f"  Consistency:  {trial_res['consistency']:.0%} "
            f"({'deterministic' if trial_res['deterministic'] else 'variance detected'})"
        )
        l_stats = trial_res["latency_stats"]
        click.echo(
            f"  Latency:      avg={l_stats['avg_ms']:.2f}ms "
            f"(min={l_stats['min_ms']:.2f}ms, max={l_stats['max_ms']:.2f}ms, jitter={l_stats['jitter_ms']:.2f}ms)"
        )
        click.echo(f"  Fleet Status: [{trial_res['status']}]")

        click.echo("\n  Final Scorecard:")
        for p_name, res in trial_res["latest_scorecard"].items():
            status = "HEALTHY" if res["healthy"] else "UNHEALTHY"
            click.echo(
                f"  [{status}] {p_name:<10} score={res['tools_score']:.0%} "
                f"valid={res['valid_tools']}/{res['total_tools']}"
            )
        if not trial_res["all_healthy"] or not trial_res["deterministic"]:
            sys.exit(1)
        return

    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_tools_health(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["healthy"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family Tool Health & Schema Evaluation")
    all_ok = True
    for p_name, res in results.items():
        status = "HEALTHY" if res["healthy"] else "UNHEALTHY"
        if not res["healthy"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} score={res['tools_score']:.0%} "
            f"valid={res['valid_tools']}/{res['total_tools']}"
        )
        if detailed and res.get("dimensions_breakdown"):
            dims = res["dimensions_breakdown"]
            dim_str = " ".join(f"{k}={v}" for k, v in dims.items())
            click.echo(f"    - 6-factor rubric: {dim_str}")
        if res["diagnostics"]:
            for d in res["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not all_ok:
        sys.exit(1)


@eval_cmd.command("agents")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate AGENTS.md requirement alignment for a single persona.",
)
@click.option(
    "--times",
    "-t",
    "times",
    default=1,
    type=click.IntRange(min=1),
    help="Number of evaluation trials to run (e.g. 10 for consistency benchmark).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the AGENTS.md report as JSON.")
def eval_agents(persona: str | None, times: int, as_json: bool) -> None:
    """Evaluate persona AGENTS.md alignment with workspace requirements, models, skills, and tools."""
    if times > 1:
        bench = evaluate_agents_md_trials(persona=persona, trials=times)
        if as_json:
            click.echo(json.dumps(bench, indent=2, ensure_ascii=False))
            if not bench["all_trials_aligned"] or not bench["consistent"]:
                sys.exit(1)
            return

        click.echo(f"# Sak Family AGENTS.md Requirements Benchmark ({times} trials)")
        click.echo(
            f"  Consistency: {'100% Deterministic' if bench['consistent'] else 'Inconsistent'} | "
            f"Avg Latency: {bench['avg_latency_ms']:.2f}ms | Jitter: {bench['jitter_ms']:.2f}ms"
        )
        all_ok = bench["all_trials_aligned"] and bench["consistent"]
        for p_name, res in bench["latest_report"].items():
            status = "MATCHED" if res["aligned"] else "DRIFTED"
            click.echo(
                f"  [{status}] {p_name:<10} score={res['agents_md_score']:.0%} "
                f"checks={res['checks_passed']}/{res['checks_total']} "
                f"skills={res['overlay_skills']}+{res['shared_skills']} "
                f"model={res['provider']}:{res['model']}"
            )
            if res["diagnostics"]:
                for d in res["diagnostics"]:
                    click.echo(f"    - warning: {d}")
        if not all_ok:
            sys.exit(1)
        return

    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_agents_md_alignment(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["aligned"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family AGENTS.md Requirements Alignment")
    all_ok = True
    for p_name, res in results.items():
        status = "MATCHED" if res["aligned"] else "DRIFTED"
        if not res["aligned"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} score={res['agents_md_score']:.0%} "
            f"checks={res['checks_passed']}/{res['checks_total']} "
            f"skills={res['overlay_skills']}+{res['shared_skills']} "
            f"primary={len(res['primary_skills'])} "
            f"tools={len(res['allowed_tools'])} "
            f"model={res['provider']}:{res['model']}"
        )
        if res["diagnostics"]:
            for d in res["diagnostics"]:
                click.echo(f"    - warning: {d}")
    if not all_ok:
        sys.exit(1)


@eval_cmd.command("extensions")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Evaluate extensions health for a single persona.",
)
@click.option(
    "--times",
    "-t",
    "times",
    default=1,
    type=click.IntRange(min=1),
    help="Number of evaluation trials to run (e.g. 10 for consistency benchmark).",
)
@click.option("--detailed", is_flag=True, help="Print detailed rubric breakdown for each persona.")
@click.option("--json", "as_json", is_flag=True, help="Emit the extensions report as JSON.")
def eval_extensions(
    persona: str | None,
    times: int,
    detailed: bool,
    as_json: bool,
) -> None:
    """Evaluate extensions health: 8-factor rubric across registry, containment, schema, and isolation."""
    if times > 1:
        bench = evaluate_extensions_trials(persona=persona, trials=times)
        if as_json:
            click.echo(json.dumps(bench, indent=2, ensure_ascii=False))
            if not bench["all_trials_healthy"] or not bench["consistent"]:
                sys.exit(1)
            return

        click.echo(f"# Sak Family Extensions Fleet Benchmark ({times} trials)")
        click.echo(
            f"  Consistency: {'100% Deterministic' if bench['consistent'] else 'Inconsistent'} | "
            f"Avg Latency: {bench['avg_latency_ms']:.2f}ms | Jitter: {bench['jitter_ms']:.2f}ms"
        )
        all_ok = bench["all_trials_healthy"] and bench["consistent"]
        for p_name, res in bench["latest_report"].items():
            status = "HEALTHY" if res["healthy"] else "UNHEALTHY"
            click.echo(
                f"  [{status}] {p_name:<10} score={res['extensions_score']:.0%} "
                f"checks={res['checks_passed']}/{res['checks_total']} "
                f"extensions={res['extensions_count']} "
                f"grade={res['grade']}"
            )
            if res["diagnostics"]:
                for d in res["diagnostics"]:
                    click.echo(f"    - warning: {d}")
        if not all_ok:
            sys.exit(1)
        return

    targets = [persona] if persona else sorted(PERSONA_NAMES)
    results = {p: evaluate_persona_extensions_health(p) for p in targets}
    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        if not all(r["healthy"] for r in results.values()):
            sys.exit(1)
        return

    click.echo("# Sak Family Extensions Fleet Health Audit")
    all_ok = True
    for p_name, res in results.items():
        status = "HEALTHY" if res["healthy"] else "UNHEALTHY"
        if not res["healthy"]:
            all_ok = False
        click.echo(
            f"  [{status}] {p_name:<10} grade={res['grade']:<4} score={res['extensions_score']:.0%} "
            f"checks={res['checks_passed']}/{res['checks_total']} "
            f"extensions={res['extensions_count']}"
        )
        if detailed:
            for criterion, passed in res["checks"].items():
                st = "PASS" if passed else "FAIL"
                click.echo(f"    - [{st}] {criterion}")
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
@click.option("--suite", default=None, help="Benchmark suite name or path.")
@click.option(
    "--persona",
    type=click.Choice(PERSONA_NAMES),
    default=None,
    help="Persona to evaluate (injects persona intro/soul context into generator).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit benchmark results as JSON.")
@click.option("--dry-run", is_flag=True, help="Print benchmark command without executing.")
@click.option("--legacy", is_flag=True, help="Run legacy benchmark via scripts/eval/run_bench.py.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def eval_bench(
    suite: str | None,
    persona: str | None,
    as_json: bool,
    dry_run: bool,
    legacy: bool,
    extra_args: tuple[str, ...],
) -> None:
    """Run benchmark evaluation suite or legacy model benchmark."""
    if legacy or dry_run or extra_args:
        argv = ["uv", "run", "python", "scripts/eval/run_bench.py"] + list(extra_args)
        code = run_repo_argv(argv, dry_run=dry_run)
        if code != 0:
            sys.exit(code)
        return

    if str(config.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(config.REPO_ROOT))

    from evaluation_tasks.graders import BenchmarkSuite, load_benchmark_tasks

    tasks = load_benchmark_tasks(suite)
    benchmark = BenchmarkSuite(tasks=tasks, persona=persona)
    result = benchmark.run()

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo(result.format_markdown())

    if result.total_tasks > 0 and result.passed_tasks == 0:
        sys.exit(1)
