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

from ..mcp.http import (
    SESSION_HEADER,
    MCPSessionStore,
    handle_http,
    handle_http_delete,
)
from ..mcp.protocol import PROTOCOL_VERSION_HEADER
from ..memory.store import MemoryStore
from ..web.server import _is_loopback_host
from .config import GatewayConfig
from .router import GatewayRouter

logger = logging.getLogger(__name__)

#: Paths serving the inbound MCP Streamable HTTP transport.
MCP_ENDPOINTS = ("/v1/mcp", "/mcp")


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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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
        elif path in ("/v1/team/pipelines/stream", "/team/pipelines/stream"):
            parsed = urlparse(self.path)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self._send_cors_headers()
            self.end_headers()
            self.close_connection = True
            for chunk in self.gateway_router.handle_team_stream(params):
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
            return
        elif path in (
            "/v1/team/github-subagents/maintenance",
            "/team/github-subagents/maintenance",
        ):
            parsed = urlparse(self.path)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            self._send_json(200, self.gateway_router.handle_github_maintenance(params))
        elif path in ("/v1/team/github-subagents/audit", "/team/github-subagents/audit"):
            self._send_json(200, self.gateway_router.handle_github_audit())
        elif path in ("/v1/team/github-subagents/security", "/team/github-subagents/security"):
            self._send_json(200, self.gateway_router.handle_github_security())
        elif path in ("/v1/memory/shards", "/memory/shards"):
            self._send_json(200, self.gateway_router.handle_memory_shards())
        elif path in ("/v1/memory/facts", "/memory/facts"):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            persona = qs.get("persona", ["sakthai"])[0]
            kind = qs.get("kind", [None])[0]
            tag = qs.get("tag", [None])[0]
            try:
                limit = int(qs.get("limit", ["100"])[0])
            except (ValueError, TypeError):
                limit = 100
            self._send_json(
                200,
                self.gateway_router.handle_memory_facts(persona, kind=kind, tag=tag, limit=limit),
            )
        elif path == "/api/status":
            self._send_json(200, self.gateway_router.handle_status())
        elif path == "/api/saksee/status":
            self._send_json(200, self.gateway_router.handle_saksee_status())
        else:
            self._send_error(404, f"Endpoint '{path}' not found")

    def _send_mcp_result(self, result: Any) -> None:
        """Write an :class:`~sakthai.mcp.http.HttpResult` to the wire."""
        if result.payload is None:
            self.send_response(result.status)
            for key, value in result.headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", "0")
            self._send_cors_headers()
            self.end_headers()
            return

        payload = json.dumps(result.payload, ensure_ascii=False).encode("utf-8")
        self.send_response(result.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        for key, value in result.headers.items():
            self.send_header(key, value)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _handle_mcp_post(self, body: Any) -> None:
        """Serve one JSON-RPC message on the MCP Streamable HTTP endpoint.

        The store is opened per request, inside this handler thread, matching
        ``GatewayRouter.handle_tools_execute``. A SQLite connection belongs to
        the thread that opened it, and this is a ``ThreadingHTTPServer`` — a
        single long-lived store shared across handler threads raises
        ``ProgrammingError`` as soon as two requests land on different threads.
        WAL makes the repeated opens cheap and concurrent readers safe.
        """
        with MemoryStore() as store:
            result = handle_http(
                body,
                store,
                sessions=self.gateway.mcp_sessions,
                session_id=self.headers.get(SESSION_HEADER),
                protocol_version=self.headers.get(PROTOCOL_VERSION_HEADER),
                origin=self.headers.get("Origin"),
            )
        self._send_mcp_result(result)

    def do_POST(self) -> None:
        """Handle POST endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Webhook endpoints authenticate via X-Webhook-Secret rather than the Gateway bearer token
        if path in ("/v1/webhooks/huggingface", "/webhooks/huggingface"):
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except Exception as exc:
                self._send_error(400, f"Malformed JSON request: {exc}")
                return

            headers = {k: v for k, v in self.headers.items()}
            status_code, webhook_res = self.gateway_router.handle_webhook_huggingface(
                body, headers=headers
            )
            self._send_json(status_code, webhook_res)
            return

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

        if path in MCP_ENDPOINTS:
            self._handle_mcp_post(body)
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

        elif path in ("/v1/team/pipelines/stream", "/team/pipelines/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self._send_cors_headers()
            self.end_headers()
            self.close_connection = True
            for chunk in self.gateway_router.handle_team_stream(body):
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
            return

        elif path in ("/v1/team/pipelines", "/v1/team/run", "/team/run"):
            res = self.gateway_router.handle_team_run(body)
            self._send_json(200 if res.get("ok") else 400, res)

        elif path in (
            "/v1/team/github-subagents/maintenance",
            "/team/github-subagents/maintenance",
        ):
            self._send_json(200, self.gateway_router.handle_github_maintenance(body))

        elif path in ("/v1/team/github-subagents/audit", "/team/github-subagents/audit"):
            self._send_json(200, self.gateway_router.handle_github_audit())

        elif path in ("/v1/team/github-subagents/security", "/team/github-subagents/security"):
            self._send_json(200, self.gateway_router.handle_github_security())

        elif path in ("/v1/memory/facts", "/memory/facts"):
            res = self.gateway_router.handle_memory_add_fact(body)
            status_code = 200 if res.get("ok") else 400
            self._send_json(status_code, res)

        elif path in ("/v1/memory/facts/delete", "/memory/facts/delete"):
            res = self.gateway_router.handle_memory_delete_fact(body)
            status_code = (
                200 if res.get("ok") else (404 if res.get("status") == "not_found" else 400)
            )
            self._send_json(status_code, res)

        elif path in ("/v1/memory/preview", "/memory/preview"):
            res = self.gateway_router.handle_memory_preview(body)
            self._send_json(200, res)

        elif path in ("/v1/bench", "/bench"):
            res = self.gateway_router.handle_benchmark(body)
            self._send_json(200, res)

        elif path == "/api/model/chat":
            res = self.gateway_router.handle_model_chat(body)
            self._send_json(200, res)

        else:
            self._send_error(404, f"Endpoint '{path}' not found")

    def do_DELETE(self) -> None:
        """Handle DELETE endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not self._check_auth():
            self._send_error(401, "Unauthorized: Invalid or missing bearer token")
            return

        if path in MCP_ENDPOINTS:
            self._send_mcp_result(
                handle_http_delete(
                    self.headers.get(SESSION_HEADER), sessions=self.gateway.mcp_sessions
                )
            )
            return

        if path.startswith("/v1/memory/facts/") or path.startswith("/memory/facts/"):
            fact_id_str = path.rsplit("/", 1)[-1]
            qs = parse_qs(parsed.query)
            persona = qs.get("persona", ["sakthai"])[0]
            confirm_val = qs.get("confirmed", qs.get("confirm", ["false"]))[0]
            confirmed = confirm_val.lower() in ("true", "1", "yes")
            res = self.gateway_router.handle_memory_delete_fact(
                {"id": fact_id_str, "persona": persona, "confirmed": confirmed}
            )
            status_code = (
                200 if res.get("ok") else (404 if res.get("status") == "not_found" else 400)
            )
            self._send_json(status_code, res)
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
        #: Live sessions on the MCP Streamable HTTP endpoint. One per server
        #: instance, shared across handler threads — which is safe because
        #: MCPSessionStore guards its own state with a lock. The *memory store*
        #: deliberately is not shared; see ``_handle_mcp_post``.
        self.mcp_sessions = MCPSessionStore()

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
