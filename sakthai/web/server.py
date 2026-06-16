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
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "0.0.0.0"
_DEFAULT_PORT = 3001
_STATIC_ROOT = (Path(__file__).resolve().parent.parent / "web").resolve()


def _dashboard_data(days: int = 30) -> dict[str, Any]:
    try:
        import sys

        sys.path.insert(0, str((Path(__file__).resolve().parent.parent).resolve()))
        from sakthai.dashboard.data import collect_dashboard_data

        return collect_dashboard_data(days=days)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Dashboard data unavailable (%s); returning demo stub.", exc)
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
        from datetime import datetime, UTC
        status["generated_at"] = datetime.now(UTC).isoformat()
    except Exception:
        pass
    return status


class _Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logger.debug(format, *args)

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
            except Exception:
                days = 30
            self._send_json(200, _dashboard_data(days=days))
            return

        if path == "/api/ecosystem":
            self._send_json(200, _ecosystem_status())
            return

        # Fallback: static files from `web/`
        relative = (Path(self.path.lstrip("/"))).resolve()
        try:
            relative.relative_to(_STATIC_ROOT)
        except ValueError:
            self.send_error(403, "Forbidden")
            return
        return super().do_GET()


def serve(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> HTTPServer:
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
