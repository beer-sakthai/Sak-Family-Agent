"""The dashboard command: serve the modern React dashboard or export a snapshot."""

from __future__ import annotations

import http.server
import os
import socketserver
import threading
import webbrowser
from pathlib import Path

import click


def _serve_dashboard(port: int, open_browser: bool, dist_path: Path) -> None:
    """Simple HTTP server to serve the static dashboard files."""
    os.chdir(dist_path)
    Handler = http.server.SimpleHTTPRequestHandler

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}"
        click.echo(f"dashboard: {url} (Ctrl-C to stop)")
        if open_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nstopped.")
            httpd.shutdown()


@click.command()
@click.option("--port", "-p", default=3000, type=int, help="Port to serve on (default: 3000).")
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
    help="Write a JSON snapshot of dashboard data to PATH and exit.",
)
def dashboard(port: int, open_browser: bool, export_path: str | None) -> None:
    """Serve the modern SakThai dashboard, or export its data as JSON."""
    from ..config import memory_db_path
    from ..dashboard.data import export_dashboard_json

    if export_path:
        written = export_dashboard_json(Path(export_path), memory_db_path())
        click.echo(f"snapshot: {written}")
        return

    dist_path = Path(__file__).parent.parent.parent / "dashboard" / "dist"
    if not dist_path.exists():
        raise click.ClickException(
            "Dashboard build artifacts not found. Please run 'npm run build' in the dashboard directory."
        )

    # Export live data to the dist folder so the dashboard can fetch it
    export_dashboard_json(dist_path / "data.json", memory_db_path())

    _serve_dashboard(port, open_browser, dist_path)
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
