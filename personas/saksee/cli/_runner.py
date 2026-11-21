"""Safe subprocess runner helper for repository-wide tasks and subcommands.

Ensures commands always execute with ``shell=False`` list arguments, cwd
pinned relative to the repository root, and Bandit-audited invocations.
"""

from __future__ import annotations

import os
import shlex
import subprocess  # nosec B404
from collections.abc import Sequence
from pathlib import Path

import click

from .. import config


def resolve_repo_cwd(rel_or_abs: str | Path | None = None) -> Path:
    """Resolve a working directory path relative to the repository root."""
    root = config.REPO_ROOT
    if not rel_or_abs or rel_or_abs == ".":
        return root
    path = Path(rel_or_abs)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def run_repo_argv(
    argv: Sequence[str],
    *,
    cwd: str | Path | None = None,
    dry_run: bool = False,
    extra_env: dict[str, str] | None = None,
    echo: bool = True,
) -> int:
    """Run an argument list safely in the repository.

    Parameters
    ----------
    argv:
        Command line arguments (first argument is the executable).
    cwd:
        Working directory (resolved relative to `config.REPO_ROOT`).
    dry_run:
        If True, print what would be run and return 0 without executing.
    extra_env:
        Optional environment variables merged into os.environ.
    echo:
        If True, echo command execution details to the terminal.
    """
    if not argv:
        raise ValueError("argv cannot be empty")

    target_cwd = resolve_repo_cwd(cwd)
    cmd_str = " ".join(shlex.quote(str(arg)) for arg in argv)

    if dry_run:
        if echo:
            click.echo(f"[dry-run] (cwd: {target_cwd}) {cmd_str}")
        return 0

    if echo:
        click.echo(f"==> (cwd: {target_cwd.name}) {cmd_str}")

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    # Safe subprocess execution with shell=False and validated argv list
    proc = subprocess.run(  # nosec B603
        list(argv),
        cwd=str(target_cwd),
        env=env,
        check=False,
    )
    return proc.returncode
