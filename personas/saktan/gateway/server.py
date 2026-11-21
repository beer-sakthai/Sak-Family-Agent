"""Multi-threaded HTTP Server for the SakThai Runtime Gateway."""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..web.server import _is_loopback_host
from .config import GatewayConfig
from .router import GatewayRouter

logger = logging.getLogger(__name__)


def _token_matches(candidate: str, expected: str) -> bool:
    """Constant-time token comparison that is total over attacker input."""
    return secrets.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


class _GatewayHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer subclass holding a reference to RuntimeGatewayServer."""

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: type[BaseHTTPRequestHandler],
        gateway_instance: RuntimeGatewayServer,
    ) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.gateway_instance = gateway_instance


class GatewayRequestHandler(BaseHTTPRequestHandler):
    """Handles incoming HTTP requests for the Runtime Gateway."""

    server: _GatewayHTTPServer

    @property
    def gateway(self) -> RuntimeGatewayServer:
        return self.server.gateway_instance

    @property
    def gateway_config(self) -> GatewayConfig:
        return self.gateway.config

    @property
    def gateway_router(self) -> GatewayRouter:
        return self.gateway.router

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet default logging unless debug is enabled."""
        logger.debug(
            "%s - - [%s] %s",
            self.address_string(),
            self.log_date_time_string(),
            format % args,
        )

    def _send_cors_headers(self) -> None:
        origin = self.gateway_config.cors_origin or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Requested-With",
        )

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message, "status": "error"})

    def _check_auth(self) -> bool:
        expected = self.gateway_config.bearer_token
        if not expected:
            # Fail closed: with no token configured, nothing but /health is served.
            return False

        # Check Authorization header: Bearer <token>
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            candidate = auth_header[7:].strip()
            if _token_matches(candidate, expected):
                return True

        # Check query string: ?token=<token>
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return bool(
            "token" in params and params["token"] and _token_matches(params["token"][0], expected)
        )

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # Allow unauthenticated health check
        if path in ("/health", "/v1/health"):
            self._send_json(200, self.gateway_router.handle_health())
            return

        if not self._check_auth():
            self._send_error(401, "Unauthorized: Invalid or missing bearer token")
            return

        if path in ("/v1/models", "/models"):
            self._send_json(200, self.gateway_router.handle_models())
        elif path in ("/v1/personas", "/v1/agents", "/personas", "/agents"):
            self._send_json(200, self.gateway_router.handle_personas())
        elif path.startswith("/v1/personas/") and path.endswith("/memory"):
            parts = path.strip("/").split("/")
            if (
                len(parts) == 4
                and parts[0] == "v1"
                and parts[1] == "personas"
                and parts[3] == "memory"
            ):
                persona_name = parts[2]
                mem_data = self.gateway_router.handle_persona_memory(persona_name)
                self._send_json(200 if mem_data.get("ok") else 404, mem_data)
                return
        elif path.startswith("/v1/personas/") or path.startswith("/v1/agents/"):
            name = path.rsplit("/", 1)[-1]
            detail = self.gateway_router.handle_persona_detail(name)
            if detail is not None:
                self._send_json(200, detail)
            else:
                self._send_error(404, f"Persona '{name}' not found")
        elif path in ("/v1/tools", "/tools"):
            self._send_json(200, self.gateway_router.handle_tools())
        elif path in ("/v1/voice/profiles", "/voice/profiles"):
            self._send_json(200, self.gateway_router.handle_voice_profiles())
        elif path in ("/v1/team/pipelines", "/team/pipelines"):
            self._send_json(200, self.gateway_router.handle_team_pipelines())
        elif path == "/api/status":
            self._send_json(200, self.gateway_router.handle_status())
        elif path == "/api/saksee/status":
            self._send_json(200, self.gateway_router.handle_saksee_status())
        else:
            self._send_error(404, f"Endpoint '{path}' not found")

    def do_POST(self) -> None:
        """Handle POST endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not self._check_auth():
            self._send_error(401, "Unauthorized: Invalid or missing bearer token")
            return

        # Read JSON body
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as exc:
            self._send_error(400, f"Malformed JSON request: {exc}")
            return

        if path in ("/v1/chat/completions", "/chat/completions"):
            try:
                headers = {k.lower(): v for k, v in self.headers.items()}
                res, is_stream = self.gateway_router.handle_chat_completion(body, headers=headers)
            except ValueError as err:
                self._send_error(400, str(err))
                return
            except Exception as exc:
                logger.exception("Error in chat completion")
                self._send_error(500, f"Internal execution error: {exc}")
                return

            if is_stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self._send_cors_headers()
                self.end_headers()
                self.close_connection = True
                for chunk in res:
                    self.wfile.write(chunk.encode("utf-8"))
                    self.wfile.flush()
            else:
                self._send_json(200, res)  # type: ignore[arg-type]

        elif path in ("/v1/tools/execute", "/v1/runtime/execute", "/tools/execute"):
            res = self.gateway_router.handle_tools_execute(body)
            status_code = 200 if res.get("status") in ("success", "blocked") else 400
            self._send_json(status_code, res)

        elif path in ("/v1/chat/ws", "/v1/voice/duplex", "/chat/ws"):
            frames = self.gateway_router.handle_duplex_event(body)
            self._send_json(200, {"ok": True, "frames": frames})

        elif path in ("/v1/team/pipelines", "/v1/team/run", "/team/run"):
            res = self.gateway_router.handle_team_run(body)
            self._send_json(200 if res.get("ok") else 400, res)

        elif path in ("/v1/bench", "/bench"):
            res = self.gateway_router.handle_benchmark(body)
            self._send_json(200, res)

        elif path == "/api/model/chat":
            res = self.gateway_router.handle_model_chat(body)
            self._send_json(200, res)

        else:
            self._send_error(404, f"Endpoint '{path}' not found")


class RuntimeGatewayServer:
    """Runtime Gateway Server instance."""

    def __init__(
        self,
        config: GatewayConfig | None = None,
        router: GatewayRouter | None = None,
    ) -> None:
        self.config = config or GatewayConfig()
        self.router = router or GatewayRouter(config=self.config)
        self._httpd: _GatewayHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.is_running = False
        self.port = self.config.port
        self.host = self.config.host

    def start(self, background: bool = True) -> None:
        """Start the HTTP server."""
        if self.is_running:
            return

        if not _is_loopback_host(self.host) and not os.environ.get("SAKTHAI_GATEWAY_ALLOW_PUBLIC"):
            raise PermissionError(
                f"Refusing to bind the Runtime Gateway to non-loopback host {self.host!r}. "
                "Set SAKTHAI_GATEWAY_ALLOW_PUBLIC=1 to expose it beyond this machine."
            )

        # Bind server
        server_address = (self.host, self.port)
        httpd = _GatewayHTTPServer(server_address, GatewayRequestHandler, gateway_instance=self)

        self._httpd = httpd
        # Retrieve actual bound port if port was 0
        self.port = httpd.server_address[1]
        self.is_running = True

        logger.info("Runtime Gateway listening on http://%s:%d", self.host, self.port)

        if background:
            self._thread = threading.Thread(
                target=httpd.serve_forever,
                name=f"GatewayServer-{self.port}",
                daemon=True,
            )
            self._thread.start()
        else:
            try:
                httpd.serve_forever()
            finally:
                self.shutdown()

    def shutdown(self) -> None:
        """Stop the HTTP server."""
        if not self.is_running:
            return

        self.is_running = False
        if self._httpd is not None:
            if self._thread is not None:
                self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("Runtime Gateway shutdown complete.")

    def __enter__(self) -> RuntimeGatewayServer:
        self.start(background=True)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
