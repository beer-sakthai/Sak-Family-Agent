"""The ``repo`` command group: discover and run tasks across the entire repository.

Provides unified CLI coverage for scripts/, training/, eval/, infra/,
services/, and evolution/ through declarative task definitions.
"""

from __future__ import annotations

import json
import sys

import click

from ._runner import run_repo_argv
from .repo_registry import (
    AREAS,
    get_repo_coverage_map,
    get_task,
    list_tasks,
)


@click.group(name="repo")
def repo_cmd() -> None:
    """Discover, inspect, and run repository-wide scripts and tasks."""


@repo_cmd.command("map")
@click.option("--json", "as_json", is_flag=True, help="Emit the repository map as JSON.")
def repo_map(as_json: bool) -> None:
    """Show top-level repository areas and CLI task coverage."""
    coverage = get_repo_coverage_map()
    if as_json:
        click.echo(json.dumps(coverage, indent=2))
        return

    click.echo("# Repository Coverage Map")
    click.echo(f"  {'AREA':<14} {'TASKS':<7} {'PATHS'}")
    click.echo("  " + "-" * 60)
    for area, info in coverage.items():
        click.echo(f"  {area:<14} {info['task_count']:<7} {info['path']}")
    click.echo("\nRun `sakthai repo list` to see all available tasks.")


@repo_cmd.command("list")
@click.option(
    "--area",
    type=click.Choice(list(AREAS.keys())),
    default=None,
    help="Filter tasks by repository area.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit task list as JSON.")
def repo_list(area: str | None, as_json: bool) -> None:
    """List registered repository scripts and tasks."""
    tasks = list_tasks(area=area)
    if as_json:
        tasks_data = [
            {
                "name": t.name,
                "area": t.area,
                "summary": t.summary,
                "argv": list(t.argv),
                "cwd": t.cwd,
                "requires": list(t.requires),
            }
            for t in tasks
        ]
        click.echo(json.dumps(tasks_data, indent=2))
        return

    title = f"# Repository Tasks ({area})" if area else "# Repository Tasks"
    click.echo(title)
    click.echo(f"  {'TASK NAME':<28} {'AREA':<12} {'SUMMARY'}")
    click.echo("  " + "-" * 75)
    for t in sorted(tasks, key=lambda x: (x.area, x.name)):
        click.echo(f"  {t.name:<28} {t.area:<12} {t.summary}")
    click.echo(f"\nTotal tasks: {len(tasks)}. Run with `sakthai repo run <name>`.")


@repo_cmd.command("run", context_settings={"ignore_unknown_options": True})
@click.argument("task_name")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def repo_run(task_name: str, dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Run a registered repository task by name."""
    task = get_task(task_name)
    if not task:
        all_names = ", ".join(t.name for t in list_tasks())
        raise click.ClickException(f"Unknown repo task '{task_name}'. Available tasks: {all_names}")

    missing_reqs = task.check_requirements()
    if missing_reqs:
        raise click.ClickException(
            f"Task '{task_name}' requires tools not found on PATH: {', '.join(missing_reqs)}"
        )

    if not task.check_target_file():
        raise click.ClickException(
            f"Target file for task '{task_name}' does not exist on disk: {task.file_path}"
        )

    full_argv = list(task.argv) + list(extra_args)
    code = run_repo_argv(full_argv, cwd=task.cwd, dry_run=dry_run)
    if code != 0:
        sys.exit(code)
