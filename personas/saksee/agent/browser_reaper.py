"""Chromium and browser automation lifecycle manager, reaper, and timeout supervisor.

Enforces memory-safety launch arguments (--disable-dev-shm-usage, --no-sandbox),
reaps orphaned/zombie browser processes, purges temporary profile directories,
and enforces bounded execution timeouts.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import logging
import os
import shutil
import subprocess
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BrowserTimeoutError(TimeoutError):
    """Raised when browser automation exceeds its allocated execution timeout."""


def enforce_browser_launch_args(args: list[str]) -> list[str]:
    """Ensure mandatory memory-safety and sandbox isolation flags are present."""
    result = list(args)
    if "--disable-dev-shm-usage" not in result:
        result.append("--disable-dev-shm-usage")
    if "--no-sandbox" not in result:
        result.append("--no-sandbox")
    return result


def reap_orphaned_browser_processes(dry_run: bool = False) -> int:
    """Find and terminate orphaned chromium / playwright processes."""
    reaped = 0
    try:
        # Use pgrep to safely identify zombie/orphaned chromium or playwright helper processes
        proc = subprocess.run(  # nosec B603, B607
            ["pgrep", "-f", "chromium|chrome-headless-shell|playwright"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode != 0:
            return 0

        pids = [int(p) for p in proc.stdout.strip().splitlines() if p.isdigit()]
        my_pid = os.getpid()

        for pid in pids:
            if pid == my_pid:
                continue
            reaped += 1
            if not dry_run:
                with contextlib.suppress(OSError, ProcessLookupError):
                    os.kill(pid, 15)  # SIGTERM
    except Exception as exc:  # noqa: BLE001
        logger.debug("Browser process reaper check encountered error: %s", exc)

    return reaped


def cleanup_temp_browser_profiles(temp_dirs: list[str] | None = None) -> list[str]:
    """Safely delete ephemeral browser user data directories."""
    cleaned: list[str] = []
    dirs_to_clean = list(temp_dirs or [])

    for d in dirs_to_clean:
        if not d or not isinstance(d, str):
            continue
        clean_path = os.path.abspath(d)
        if os.path.isdir(clean_path):
            try:
                shutil.rmtree(clean_path, ignore_errors=True)
                if not os.path.exists(clean_path):
                    cleaned.append(d)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed cleaning ephemeral profile %s: %s", clean_path, exc)

    return cleaned


def run_browser_task_with_timeout(
    fn: Callable[..., T],
    timeout_seconds: float = 15.0,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute a browser automation function under a strict execution timeout."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            reap_orphaned_browser_processes()
            raise BrowserTimeoutError(
                f"Browser task timed out after {timeout_seconds} seconds"
            ) from exc
