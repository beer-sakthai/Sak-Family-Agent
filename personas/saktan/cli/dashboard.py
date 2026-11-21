"""The ``dashboard`` command group: manage and build the Next.js agent dashboard."""

from __future__ import annotations

import shutil
import sys

import click

from ._runner import run_repo_argv

DASHBOARD_DIR = "apps/sak_agent_dashboard"


def _check_npm() -> None:
    if shutil.which("npm") is None:
        raise click.ClickException("'npm' executable not found on PATH. Node.js 22+ is required.")


@click.group(name="dashboard")
def dashboard_cmd() -> None:
    """Manage, test, build, and run the Next.js agent dashboard."""


@dashboard_cmd.command("dev")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def dashboard_dev(dry_run: bool) -> None:
    """Start the Next.js development server for the dashboard."""
    _check_npm()
    code = run_repo_argv(["npm", "run", "dev"], cwd=DASHBOARD_DIR, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@dashboard_cmd.command("build")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def dashboard_build(dry_run: bool) -> None:
    """Build the production Next.js dashboard bundle."""
    _check_npm()
    code = run_repo_argv(["npm", "run", "build"], cwd=DASHBOARD_DIR, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@dashboard_cmd.command("test")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def dashboard_test(dry_run: bool) -> None:
    """Run vitest and workflow tests in the dashboard."""
    _check_npm()
    code = run_repo_argv(["npm", "run", "test"], cwd=DASHBOARD_DIR, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@dashboard_cmd.command("install")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def dashboard_install(dry_run: bool) -> None:
    """Install Node.js dependencies for the dashboard."""
    _check_npm()
    code = run_repo_argv(["npm", "install"], cwd=DASHBOARD_DIR, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@dashboard_cmd.command("gen-types")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
def dashboard_gen_types(dry_run: bool) -> None:
    """Regenerate TypeScript data types from agent schemas."""
    code = run_repo_argv(["uv", "run", "python", "scripts/gen_dashboard_types.py"], dry_run=dry_run)
    if code != 0:
        sys.exit(code)
