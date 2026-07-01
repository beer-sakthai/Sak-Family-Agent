"""The dashboard command: serve the modern React dashboard or export a snapshot."""

from __future__ import annotations

import http.server
import os
import socketserver
import threading
import webbrowser
from pathlib import Path

import click


def _get_dist_path() -> Path:
    return Path(__file__).parent.parent.parent / "dashboard" / "dist"


def _validate_port(ctx: click.Context, param: click.Parameter, value: int) -> int:
    if not (1024 <= value <= 65535):
        raise click.BadParameter("not a valid port (must be 1024-65535)")
    return value


class _SecurityHandler(http.server.SimpleHTTPRequestHandler):
    """Enforce defensive security headers for the dashboard."""

    def end_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        )
        super().end_headers()


def _serve_dashboard(host: str, port: int, open_browser: bool, dist_path: Path) -> None:
    """Simple HTTP server to serve the static dashboard files."""
    os.chdir(dist_path)
    Handler = _SecurityHandler

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(
        (host, port), Handler
    ) as httpd:  # nosec B104 — default is local
        url = (
            f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"  # nosec B104
        )
        click.echo(f"dashboard: {url} (Ctrl-C to stop)")
        if open_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nstopped.")
            httpd.shutdown()


@click.command()
@click.option(
    "--host",
    "-H",
    default="127.0.0.1",
    help="Host to bind the dashboard to (default: 127.0.0.1).",
)
@click.option(
    "--port",
    "-p",
    default=3000,
    type=int,
    callback=_validate_port,
    help="Port to serve on (default: 3000).",
)
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
def dashboard(
    host: str, port: int, open_browser: bool, export_path: str | None
) -> None:
    """Serve the modern SakThai dashboard, or export its data as JSON."""
    from ..config import memory_db_path
    from ..dashboard.data import export_dashboard_json

    if export_path:
        written = export_dashboard_json(Path(export_path), memory_db_path())
        click.echo(f"snapshot: {written}")
        return

    dist_path = _get_dist_path()
    if not dist_path.exists():
        raise click.ClickException(
            "Dashboard build artifacts not found. Please run 'npm run build' in the dashboard directory."
        )

    # Export live data to the dist folder so the dashboard can fetch it
    export_dashboard_json(dist_path / "data.json", memory_db_path())

    try:
        _serve_dashboard(host, port, open_browser, dist_path)
    except KeyboardInterrupt:
        click.echo("\nstopped.")
