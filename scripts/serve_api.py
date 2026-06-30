"""SakThai dashboard/API server.

Serves:
- `/` → `web/index.html`
- `/api/stages` → dashboard data
- `/api/ecosystem` → ecosystem status

Run:
    python scripts/serve_api.py
"""

from __future__ import annotations

import json
import logging
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

WEB_DIR = (Path(__file__).resolve().parent.parent / "dashboard" / "dist").resolve()
_HOST = "127.0.0.1"
_PORT = 3002


def _dashboard_data(days: int = 30) -> dict[str, Any]:
    try:
        import sys
        sys.path.insert(0, str((Path(__file__).resolve().parent.parent).resolve()))
        from sakthai.dashboard.data import collect_dashboard_data
        return collect_dashboard_data(days=days)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning("dashboard data failed: %s", exc)
        return {
            "generated_at": "demo",
            "source": "demo",
            "kpis": {"total_facts": 0, "total_facts_delta": 0, "total_observations": 0, "total_observations_delta": 0},
            "growth": {"labels": [], "facts": [], "observations": []},
            "recent_facts": [],
            "top_observations": [],
            "categories": [],
        }


def _ecosystem_status() -> dict[str, Any]:
    return {
        "generated_at": "unknown",
        "composio_mcp": "unknown",
        "huggingface": "unknown",
        "cron_jobs": [],
        "supermemory": "unknown",
    }


class _Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logging.getLogger(__name__).debug(format, *args)

    def end_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        )
        super().end_headers()

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/stages":
            try:
                qs = dict(item.split("=") for item in parsed.query.split("&") if "=" in item)
                days = int(qs.get("days", "30"))
            except Exception:
                days = 30
            self._json(200, _dashboard_data(days=days))
            return

        if path == "/api/ecosystem":
            self._json(200, _ecosystem_status())
            return

        # Serve static files from web/
        req_path = unquote(parsed.path)
        normalized = os.path.normpath(req_path).lstrip("/\\")
        rel = Path(normalized)
        if rel.is_absolute() or rel.drive or ".." in rel.parts:
            self.send_error(403, "Forbidden")
            return
        safe = (WEB_DIR / rel).resolve()
        try:
            safe.relative_to(WEB_DIR)
        except ValueError:
            self.send_error(403, "Forbidden")
            return

        if safe.is_dir():
            safe = safe / "index.html"

        if not safe.exists():
            self.send_error(404, "Not found")
            return

        self.send_response(200)
        ctype = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".png": "image/png",
            ".svg": "image/svg+xml",
        }.get(safe.suffix.lower(), "application/octet-stream")
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(safe.stat().st_size))
        self.end_headers()
        self.wfile.write(safe.read_bytes())


def serve(host: str = _HOST, port: int = _PORT) -> HTTPServer:
    os.chdir(str(WEB_DIR))
    srv = HTTPServer((host, port), _Handler)
    logging.getLogger(__name__).info("SakThai API on http://%s:%d  static=%s", host, port, WEB_DIR)
    return srv


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srv = serve()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        raise SystemExit(0) from None
