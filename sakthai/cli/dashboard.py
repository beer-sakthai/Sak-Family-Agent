"""The ``dashboard`` command: serve the Streamlit UI or export a JSON snapshot."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.option("--port", "-p", default=8501, type=int, help="Port to serve on (default: 8501).")
@click.option(
    "--open/--no-open",
    "open_browser",
    default=True,
    help="Open the dashboard in a browser (default: yes).",
)
@click.option(
    "--export",
    "export_path",
    default=None,
    help="Write a JSON snapshot of dashboard data to PATH and exit (no streamlit needed).",
)
def dashboard(port: int, open_browser: bool, export_path: str | None) -> None:
    """Serve the SakThai dashboard, or export its data as JSON."""
    if export_path:
        from ..config import memory_db_path
        from ..dashboard.data import export_dashboard_json

        written = export_dashboard_json(Path(export_path), memory_db_path())
        click.echo(f"snapshot: {written}")
        return

    if not 1024 <= port <= 65535:
        raise click.BadParameter(
            f"{port} is not a valid port (must be 1024-65535).", param_hint="--port"
        )
    try:
        import streamlit  # noqa: F401
    except ImportError as exc:
        raise click.ClickException(
            "streamlit is not installed. Install the dashboard extra:\n"
            "    pip install -e '.[dashboard]'"
        ) from exc

    app_path = Path(__file__).parent.parent / "dashboard" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "false" if open_browser else "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    click.echo(f"dashboard: http://localhost:{port}  (Ctrl-C to stop)")
    try:
        sys.exit(subprocess.call(cmd))  # nosec B603 — fixed argv, no shell
    except KeyboardInterrupt:
        click.echo("\nstopped.")
