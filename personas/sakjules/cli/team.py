"""CLI commands for multi-agent team workflows and declarative pipelines."""

from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.table import Table

from ..team import (
    PipelineStep,
    StepResult,
    get_pipeline,
    list_builtin_pipelines,
)
from ..team import (
    run_pipeline as execute_pipeline,
)

console = Console()


@click.group(name="team")
def team_cmd() -> None:
    """Multi-agent team orchestration and declarative pipelines."""


@team_cmd.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_cmd(as_json: bool) -> None:
    """List available multi-agent team pipelines."""
    pipelines = list_builtin_pipelines()

    if as_json:
        payload = [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "step_count": len(p.steps),
                "personas": [s.persona for s in p.steps],
            }
            for p in pipelines.values()
        ]
        click.echo(json.dumps(payload, indent=2))
        return

    table = Table(title="Sak Family Team Pipelines", show_header=True, header_style="bold cyan")
    table.add_column("Pipeline", style="bold green")
    table.add_column("Description", style="white")
    table.add_column("Stages / Personas", style="cyan")

    for p in pipelines.values():
        flow = " ➔ ".join(f"[{s.persona.upper()}]" for s in p.steps)
        table.add_row(p.name, p.description, flow)

    console.print(table)


@team_cmd.command(name="show")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def show_cmd(name: str, as_json: bool) -> None:
    """Show details of a team workflow pipeline."""
    try:
        pipeline = get_pipeline(name)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        payload = {
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "steps": [
                {
                    "name": s.name,
                    "persona": s.persona,
                    "prompt_template": s.prompt_template,
                    "output_key": s.output_key,
                    "max_iterations": s.max_iterations,
                    "with_skills": list(s.with_skills),
                }
                for s in pipeline.steps
            ],
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold cyan]Pipeline:[/bold cyan] [bold green]{pipeline.name}[/bold green] (v{pipeline.version})"
    )
    console.print(f"[bold]Description:[/bold] {pipeline.description}\n")

    table = Table(
        title=f"Steps ({len(pipeline.steps)})", show_header=True, header_style="bold cyan"
    )
    table.add_column("#", style="dim")
    table.add_column("Step Name", style="bold")
    table.add_column("Persona", style="cyan")
    table.add_column("Output Key", style="yellow")
    table.add_column("Max Iter", style="magenta")

    for idx, s in enumerate(pipeline.steps, 1):
        table.add_row(
            str(idx), s.name, s.persona.upper(), s.output_key or "-", str(s.max_iterations)
        )

    console.print(table)
    console.print()


@team_cmd.command(name="run")
@click.argument("pipeline_name")
@click.argument("task")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose log output.")
@click.option("--json", "as_json", is_flag=True, help="Output consolidated result as JSON.")
def run_cmd(pipeline_name: str, task: str, verbose: bool, as_json: bool) -> None:
    """Execute a team workflow pipeline on a task."""
    try:
        pipeline = get_pipeline(pipeline_name)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not as_json:
        console.print(
            f"\n[bold cyan]🚀 Launching Team Workflow:[/bold cyan] [bold green]{pipeline.name}[/bold green]"
        )
        console.print(f"[bold]Task:[/bold] {task}\n")

    def on_step_start(step: PipelineStep, idx: int, total: int) -> None:
        if not as_json:
            console.print(
                f"[cyan]▶ [{idx}/{total}][/cyan] Running step [bold]{step.name}[/bold] with persona [bold yellow]{step.persona.upper()}[/bold yellow]..."
            )

    def on_step_complete(step_res: StepResult, idx: int, total: int) -> None:
        if not as_json:
            if step_res.is_error:
                console.print(
                    f"  [red]✗ Failed ({step_res.duration_seconds:.2f}s): {step_res.error_message}[/red]"
                )
            else:
                tokens = step_res.usage.get("total_tokens", 0)
                console.print(
                    f"  [green]✓ Done[/green] in {step_res.duration_seconds:.2f}s ({step_res.iterations} iters, {tokens:,} tokens)"
                )

    result = execute_pipeline(
        pipeline,
        task,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
        verbose=verbose,
    )

    if as_json:
        payload = {
            "pipeline": result.pipeline_name,
            "task": result.task,
            "success": result.success,
            "total_duration_seconds": result.total_duration_seconds,
            "total_tokens": result.total_tokens,
            "steps": [
                {
                    "name": s.step_name,
                    "persona": s.persona,
                    "output": s.output,
                    "iterations": s.iterations,
                    "tokens": s.usage.get("total_tokens", 0),
                    "duration_s": s.duration_seconds,
                    "is_error": s.is_error,
                    "error": s.error_message,
                }
                for s in result.steps
            ],
            "context": result.context,
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        console.print("\n" + "=" * 60)
        console.print(result.summary)
        console.print("=" * 60 + "\n")

    if not result.success:
        sys.exit(1)


@team_cmd.group(name="gh")
def gh_cmd() -> None:
    """GitHub CLI dynamic subagents and workflow automation."""


@gh_cmd.command(name="maintenance")
@click.option(
    "--vacuum", is_flag=True, default=False, help="Vacuum and check SQLite memory stores."
)
@click.option(
    "--audit", is_flag=True, default=False, help="Run fleet audit alongside backlog sync."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit output as JSON.")
def gh_maintenance_cmd(vacuum: bool, audit: bool, as_json: bool) -> None:
    """Run weekly maintenance and backlog sync pipeline via GitHub subagent."""
    from ..team.github_subagents import run_github_maintenance_pipeline

    report = asyncio.run(run_github_maintenance_pipeline(vacuum=vacuum, run_audit=audit))
    if as_json:
        payload = {
            "workflow_id": report.workflow_id,
            "phases_completed": report.phases_completed,
            "open_prs_audited": report.open_prs_audited,
            "details": report.details,
            "auto_merge_blocked": report.auto_merge_blocked,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold green]✓ Weekly Maintenance Pipeline Completed:[/bold green] {report.workflow_id}"
    )
    console.print(f"[bold]Phases:[/bold] {' ➔ '.join(report.phases_completed)}")
    console.print(f"[bold]Open PRs Audited:[/bold] {report.open_prs_audited}")
    console.print(f"[bold]Auto-Merge Blocked:[/bold] {report.auto_merge_blocked}\n")


@gh_cmd.command(name="audit")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit output as JSON.")
def gh_audit_cmd(as_json: bool) -> None:
    """Run pull request and workflow audit pipeline via GitHub subagent."""
    from ..team.github_subagents import run_github_audit_pipeline

    report = asyncio.run(run_github_audit_pipeline())
    if as_json:
        payload = {
            "workflow_id": report.workflow_id,
            "phases_completed": report.phases_completed,
            "open_prs_audited": report.open_prs_audited,
            "high_risk_detected": report.high_risk_detected,
            "boost_triggered": report.boost_triggered,
            "details": report.details,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold green]✓ GitHub Audit Pipeline Completed:[/bold green] {report.workflow_id}"
    )
    console.print(f"[bold]Phases:[/bold] {' ➔ '.join(report.phases_completed)}")
    console.print(f"[bold]Open PRs Audited:[/bold] {report.open_prs_audited}")
    console.print(f"[bold]High Risk Detected:[/bold] {report.high_risk_detected}")
    console.print(f"[bold]Deep Reasoning Boost:[/bold] {report.boost_triggered}\n")


@gh_cmd.command(name="security")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit output as JSON.")
def gh_security_cmd(as_json: bool) -> None:
    """Run repository security and governance audit via GitHub subagent."""
    from ..team.github_subagents import run_github_security_pipeline

    report = asyncio.run(run_github_security_pipeline())
    if as_json:
        payload = {
            "workflow_id": report.workflow_id,
            "phases_completed": report.phases_completed,
            "details": report.details,
            "auto_merge_blocked": report.auto_merge_blocked,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold green]✓ Repository Security Audit Completed:[/bold green] {report.workflow_id}"
    )
    console.print(f"[bold]Phases:[/bold] {' ➔ '.join(report.phases_completed)}")
    for d in report.details:
        phase = d.get("phase")
        if phase == "branch_protection":
            console.print(
                f"  • Branch Protection: {'Enabled' if d.get('protected') else 'Disabled / Unconfigured'}"
            )
        elif phase == "action_pinning":
            console.print(f"  • Unpinned Action References: {d.get('unpinned_count', 0)}")
        elif phase == "credential_hygiene":
            console.print(f"  • Credential Hygiene: {d.get('status', 'unknown').upper()}")
    console.print(f"[bold]Auto-Merge Blocked:[/bold] {report.auto_merge_blocked}\n")
