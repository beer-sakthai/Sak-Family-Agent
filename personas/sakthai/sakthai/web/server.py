"""Minimal HTTP API for SakThai dashboard endpoints.

Serves the static `web/` frontend and two JSON endpoints:
- `/api/stages` → dashboard data (live or demo)
- `/api/ecosystem` → basic ecosystem status (repos, cron, HF, Composio)

Run: `python scripts/serve_api.py`
Defaults to `http://localhost:3001/` with `web/` as static root.
"""

from __future__ import annotations

import json
import logging
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 3001


def _find_static_root() -> Path:
    curr = Path(__file__).resolve().parent
    for parent in [curr] + list(curr.parents):
        candidate = parent / "dashboard" / "dist"
        if candidate.is_dir():
            return candidate.resolve()
    return (Path(__file__).resolve().parents[4] / "dashboard" / "dist").resolve()


_STATIC_ROOT = _find_static_root()


def _dashboard_data(days: int = 30) -> dict[str, Any]:
    try:
        import sys

        sys.path.insert(0, str((Path(__file__).resolve().parents[2]).resolve()))
        from sakthai.dashboard.data import collect_dashboard_data

        data: dict[str, Any] = collect_dashboard_data(days=days)
        return data
    except ImportError:
        logger.warning("Dashboard data module unavailable; returning demo stub.")
    except Exception:
        logger.warning("Dashboard data collection failed; returning demo stub.", exc_info=True)

    return {
        "generated_at": "demo",
        "source": "demo",
        "kpis": {
            "total_facts": 0,
            "total_facts_delta": 0,
            "total_observations": 0,
            "total_observations_delta": 0,
        },
        "growth": {"labels": [], "facts": [], "observations": []},
        "recent_facts": [],
        "top_observations": [],
        "categories": [],
    }


def _ecosystem_status() -> dict[str, Any]:
    composio_host = os.environ.get("COMPOSIO_API_KEY") is not None
    hf_user = os.environ.get("HUGGINGFACE_USERNAME")
    hf_token = os.environ.get("HF_TOKEN")
    status: dict[str, Any] = {
        "generated_at": "unknown",
        "composio_mcp": "configured" if composio_host else "not_configured",
        "huggingface": "ready" if (hf_user and hf_token) else "not_ready",
        "cron_jobs": [],
        "supermemory": "configured",
    }
    try:
        from datetime import UTC, datetime

        status["generated_at"] = datetime.now(UTC).isoformat()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to generate ecosystem timestamp: %s", exc)
    return status


class _Handler(SimpleHTTPRequestHandler):
    def address_string(self) -> str:
        return self.client_address[0]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logger.info(format, *args)

    def end_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        )
        super().end_headers()

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
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
            except (ValueError, KeyError, AttributeError):
                days = 30
            self._send_json(200, _dashboard_data(days=days))
            return

        if path == "/api/ecosystem":
            self._send_json(200, _ecosystem_status())
            return

        if path.startswith("/api/"):
            self.send_error(403, "Forbidden")
            return

        # Fallback: static files from the dashboard dist root. The stdlib
        # handler serves relative to the current working directory (which
        # `serve()` points at `_STATIC_ROOT`), so canonicalise the request the
        # same way and confirm it stays within the static root before
        # delegating.
        try:
            root = os.path.realpath(str(_STATIC_ROOT))
            requested = unquote(parsed.path).lstrip("/\\")
            candidate = os.path.realpath(os.path.join(root, requested))
            if candidate != root and not candidate.startswith(root + os.sep):
                self.send_error(403, "Forbidden")
                return
        except Exception:
            self.send_error(403, "Forbidden")
            return
        return super().do_GET()


def serve(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> HTTPServer:
    # The built dashboard (dashboard/dist) is optional: without it the API
    # endpoints still serve, and static requests fall through to 403/404.
    if _STATIC_ROOT.is_dir():
        os.chdir(str(_STATIC_ROOT))
    server = HTTPServer((host, port), _Handler)
    logger.info("SakThai API listening on http://%s:%d (static=%s)", host, port, _STATIC_ROOT)
    return server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srv = serve()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        raise SystemExit(0) from None
