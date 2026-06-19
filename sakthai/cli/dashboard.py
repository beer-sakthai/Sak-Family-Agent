"""The dashboard command: serve the modern React dashboard or export a snapshot."""

from __future__ import annotations

import http.server
import json
import threading
import webbrowser
from functools import partial
from pathlib import Path
from typing import Any

import click

# Paths the dashboard polls for a fresh, live snapshot of the memory store.
_LIVE_PATHS = frozenset({"/data.json", "/api/data"})


def _get_dist_path() -> Path:
    return Path(__file__).parent.parent.parent / "dashboard" / "dist"


def _validate_port(ctx: click.Context, param: click.Parameter, value: int) -> int:
    if not (1024 <= value <= 65535):
        raise click.BadParameter("not a valid port (must be 1024-65535)")
    return value


class _DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Serve static dashboard files, but regenerate the snapshot live on each poll."""

    db_path: Path | None = None

    def do_GET(self) -> None:  # noqa: N802 (http.server API name)
        if self.path.split("?", 1)[0] in _LIVE_PATHS:
            self._send_live_snapshot()
            return
        super().do_GET()

    def _send_live_snapshot(self) -> None:
        from ..dashboard.data import collect_dashboard_data

        try:
            data = collect_dashboard_data(self.db_path)
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        except Exception:  # noqa: BLE001 - never crash the server on a bad read
            self.send_error(500, "could not read memory store")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: Any) -> None:  # noqa: N802
        # Stay quiet: the dashboard polls every few seconds.
        pass


def _make_server(port: int, dist_path: Path) -> http.server.ThreadingHTTPServer:
    """Build the dashboard server: static files + a live /data.json endpoint.

    ThreadingHTTPServer so a live snapshot query never blocks asset requests.
    """
    from ..config import memory_db_path

    _DashboardHandler.db_path = memory_db_path()
    handler = partial(_DashboardHandler, directory=str(dist_path))
    return http.server.ThreadingHTTPServer(("", port), handler)


def _serve_dashboard(port: int, open_browser: bool, dist_path: Path) -> None:
    """Serve the static dashboard with a live, always-current /data.json endpoint."""
    with _make_server(port, dist_path) as httpd:
        url = f"http://localhost:{port}"
        click.echo(f"dashboard: {url} (live · Ctrl-C to stop)")
        if open_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nstopped.")
            httpd.shutdown()


@click.command()
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
def dashboard(port: int, open_browser: bool, export_path: str | None) -> None:
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

    # The server's /data.json endpoint regenerates the snapshot live on every
    # request, so the dashboard reflects the memory store in real time.
    try:
        _serve_dashboard(port, open_browser, dist_path)
    except KeyboardInterrupt:
        click.echo("\nstopped.")
