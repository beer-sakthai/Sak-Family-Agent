"""Minimal HTTP API for SakThai dashboard endpoints.

Serves the static `web/` frontend and two JSON endpoints:
- `/api/stages` → dashboard data (live or demo)
- `/api/ecosystem` → basic ecosystem status (repos, cron, HF, Composio)

Run: `python scripts/serve_api.py`
Defaults to `http://localhost:3001/` with `web/` as static root.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import secrets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "127.0.0.1"
_BEARER_TOKEN: str | None = None


def _get_or_create_bearer_token() -> str:
    """Retrieve or create an opaque 32-character hex bearer token in MemoryStore."""
    global _BEARER_TOKEN
    if _BEARER_TOKEN is not None:
        return _BEARER_TOKEN

    try:
        from ..config import register_secret
        from ..memory.store import MemoryStore

        with MemoryStore() as store:
            fact = store.get_fact_by_key(kind="web_auth", key="bearer_token")
            if fact:
                _BEARER_TOKEN = fact.value
                register_secret(_BEARER_TOKEN)
                return _BEARER_TOKEN

            # Generate new token
            token = secrets.token_hex(16)
            store.delete_facts_by_key(kind="web_auth", key="bearer_token")
            store.add_fact(
                value=token,
                kind="web_auth",
                key="bearer_token",
                tags=["system", "no-export"],
            )
            register_secret(token)
            _BEARER_TOKEN = token
            return token
    except Exception as exc:
        logger.warning("Failed to get or create bearer token from MemoryStore: %s", exc)
        if _BEARER_TOKEN is None:
            _BEARER_TOKEN = secrets.token_hex(16)
        return _BEARER_TOKEN


_DEFAULT_PORT = 3001
_LOOPBACK_NAMES = frozenset({"localhost"})

#: The endpoints backing apps/sak_agent_dashboard. Kept separate from the
#: legacy /api/stages and /api/ecosystem, which stay as they were.
_DASHBOARD_ROUTES = frozenset(
    {
        "/api/personas",
        "/api/metrics",
        "/api/sessions",
        "/api/memory",
        "/api/audit",
        "/api/workflows",
    }
)


def _is_loopback_host(host: str) -> bool:
    """True if ``host`` is loopback-only (safe to bind without authentication)."""
    if host in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # A non-literal hostname (other than localhost) may resolve anywhere.
        return False


def _find_static_root(start: Path | None = None) -> Path:
    curr = (start or Path(__file__)).resolve().parent
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


def _load_api() -> Any:
    """Import the payload builders, working both as a package and standalone.

    ``server.py`` is also runnable directly (``python .../web/server.py``),
    where there is no parent package for a relative import to resolve against —
    the same reason ``_dashboard_data`` below does its own sys.path insertion.
    """
    try:
        from . import api

        return api
    except ImportError:  # pragma: no cover — only hit when run as a script
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from sakthai.web import api as api_mod

        return api_mod


def _cors_origin() -> str | None:
    """The single allowed cross-origin, or None (the default) for no CORS."""
    origin = os.environ.get("SAKTHAI_WEB_CORS_ORIGIN", "").strip()
    return origin or None


def _query_params(query: str) -> dict[str, str]:
    """Parse a query string, keeping the first value for each key."""
    return {key: values[0] for key, values in parse_qs(query, keep_blank_values=True).items()}


def _int_param(params: dict[str, str], name: str, default: int) -> int:
    """Read an int query param, falling back rather than 500-ing on garbage."""
    try:
        return int(params[name])
    except (KeyError, ValueError):
        return default


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
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Secure fallback: explicitly bind the static files directory to _STATIC_ROOT
        # to prevent fallback file serving from the process's working directory.
        super().__init__(*args, directory=str(_STATIC_ROOT), **kwargs)

    def address_string(self) -> str:
        return self.client_address[0]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logger.info(format, *args)

    def _has_auth_attempt(self) -> bool:
        """True if the request contains any authentication credentials."""
        if self.headers.get("Authorization"):
            return True
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            for item in query.split("&"):
                if "=" in item:
                    k, _ = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        return True
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, _ = item.strip().split("=", 1)
                    if k in ("token", "bearer_token"):
                        return True
        return False

    def _is_authenticated(self) -> bool:
        expected_token = _get_or_create_bearer_token()
        if not expected_token:
            return False

        # 1. Check Authorization header
        auth_header = self.headers.get("Authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if secrets.compare_digest(token, expected_token):
                return True

        # 2. Check query parameter 'token' or 'bearer_token'
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            for item in query.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            return True

        # 3. Check Cookie header
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            return True

        return False

    def _send_cors_headers(self) -> None:
        """Echo the one configured origin, and only when the request matches it.

        Off unless ``SAKTHAI_WEB_CORS_ORIGIN`` is set; it exists so ``next dev``
        on :3000 can call this server on :3001 in local development.

        Never ``*``, and ``Allow-Credentials`` is deliberately never sent: the
        bearer token travels in the ``Authorization`` header, so credentialed
        CORS buys nothing and would expose the cookie auth path cross-origin.
        """
        allowed = _cors_origin()
        if not allowed:
            return
        if self.headers.get("Origin") != allowed:
            return
        self.send_header("Access-Control-Allow-Origin", allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Vary", "Origin")

    def end_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self._send_cors_headers()
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        )
        # If authenticated via query param, set cookie so subsequent static asset requests load seamlessly
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            expected_token = _get_or_create_bearer_token()
            for item in query.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            self.send_header(
                                "Set-Cookie", f"token={val}; Path=/; HttpOnly; SameSite=Strict"
                            )
                            break
        super().end_headers()

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
        from ..config import redact_secrets

        raw_body = json.dumps(payload, indent=2, ensure_ascii=False)
        redacted_body = redact_secrets(raw_body)
        body = redacted_body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _dispatch_dashboard_api(self, path: str, query: str) -> bool:
        """Serve the dashboard endpoints. Returns True if the path was handled.

        Payloads come from :mod:`sakthai.web.api`, which reuses the package's
        existing parsers; this method only maps a URL onto a call. A payload
        builder that raises returns 500 with a generic message rather than
        leaking a traceback or a filesystem path to the client.
        """
        if path not in _DASHBOARD_ROUTES:
            return False

        _api = _load_api()
        params = _query_params(query)
        try:
            if path == "/api/personas":
                payload: Any = _api.personas_payload()
            elif path == "/api/metrics":
                payload = _api.metrics_payload(
                    limit=_int_param(params, "limit", _api.EVAL_WINDOW),
                    personas=_api.parse_personas(params.get("persona")),
                )
            elif path == "/api/sessions":
                payload = _api.sessions_payload(
                    search=params.get("search") or params.get("query"),
                    limit=_int_param(params, "limit", 20),
                    offset=_int_param(params, "offset", 0),
                    session_id=params.get("id"),
                    personas=_api.parse_personas(params.get("persona")),
                )
            elif path == "/api/memory":
                payload = _api.memory_payload(
                    query=params.get("query"),
                    limit=_int_param(params, "limit", 100),
                    personas=_api.parse_personas(params.get("persona")),
                )
            elif path == "/api/workflows":
                run_id = params.get("id")
                payload = (
                    _api.workflow_detail(run_id)
                    if run_id
                    else _api.workflows_payload(limit=_int_param(params, "limit", 100))
                )
            else:  # /api/audit
                payload = _api.audit_payload(
                    severity=params.get("severity"),
                    limit=_int_param(params, "limit", 200),
                    personas=_api.parse_personas(params.get("persona")),
                )
        except Exception:
            logger.warning("Dashboard API call failed for %s", path, exc_info=True)
            self._send_json(500, {"error": "InternalError", "message": "Failed to build payload"})
            return True

        self._send_json(200, dict(_api.envelope(payload)))
        return True

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Answer CORS preflight. No body, and no auth — a preflight carries none.

        Returns 204 only when CORS is configured; otherwise 405, so a
        default-configured server does not advertise cross-origin support.
        """
        if _cors_origin() is None:
            self.send_error(405, "Method Not Allowed")
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", "16")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return

        if path.startswith("/api/"):
            if not self._is_authenticated():
                auth_header = self.headers.get("Authorization", "")
                if auth_header and not auth_header.startswith("Bearer "):
                    self._send_json(
                        401,
                        {
                            "error": "Unauthorized",
                            "message": "Authorization header must be in 'Bearer <token>' format",
                        },
                    )
                    return

                if not self._has_auth_attempt():
                    self._send_json(
                        401, {"error": "Unauthorized", "message": "Missing Authorization header"}
                    )
                else:
                    self._send_json(403, {"error": "Forbidden", "message": "Invalid Bearer token"})
                return
        else:
            if not self._is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Unauthorized: Missing or invalid bearer token")
                return

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

        if self._dispatch_dashboard_api(path, parsed.query):
            return

        if path.startswith("/api/"):
            self.send_error(403, "Forbidden")
            return

        # Fallback: static files from the dashboard dist root. The stdlib
        # handler serves relative to the configured directory (explicitly set
        # to _STATIC_ROOT above), so canonicalise the request the same way and
        # confirm it stays within the static root before delegating.
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

        # Explicitly verify the static files directory exists before serving.
        if not _STATIC_ROOT.is_dir():
            self.send_error(404, "File not found")
            return

        return super().do_GET()


def serve(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> HTTPServer:
    # API endpoints require a Bearer token, but the loopback default is
    # defense-in-depth: personal memory should not be reachable off-host by
    # default. Require an explicit opt-in for any non-loopback bind.
    if not _is_loopback_host(host) and not os.environ.get("SAKTHAI_WEB_ALLOW_PUBLIC"):
        raise PermissionError(
            f"Refusing to bind the API to non-loopback host {host!r}. "
            "It serves personal memory; set SAKTHAI_WEB_ALLOW_PUBLIC=1 to "
            "override once you have placed authentication in front of it."
        )
    _get_or_create_bearer_token()  # Warm cache & register secret
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
