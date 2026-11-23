"""Streamable HTTP transport for the inbound MCP server.

``mcp/server.handle_request`` is a pure function over one JSON-RPC message, so
the protocol itself is transport-agnostic — this module adds only what HTTP
needs on top: session identity, header validation, an ``Origin`` check, and the
mapping from a JSON-RPC reply to an HTTP status.

It is kept separate from the HTTP server that hosts it, and :func:`handle_http`
is likewise a pure function, for the same reason ``handle_request`` is: the
transport is testable without opening a socket.

**Why this is hosted on the gateway, not the web API.** ``web/server.py`` is a
single-threaded ``HTTPServer`` serving GET and HEAD only, and it is byte-parity
copied into all six personas. ``gateway/server.py`` is already a
``ThreadingHTTPServer`` with POST, DELETE and a working ``text/event-stream``
write path, and it is not copied. See ``docs/mcp-roadmap.md``.

**What is deliberately not implemented.** There is no GET stream, so the server
cannot initiate requests or notifications to the client — no sampling, no
elicitation, no server-side ``roots/list``. Nothing in ``BUILTIN_TOOLS`` needs
them, and offering a half-working stream is worse than offering none. Nor is
there SSE resumability (``Last-Event-ID``): a broken request is re-issued whole.
Both are recorded in ``docs/mcp-support-matrix.md``.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from ..agent.guardrails import DEFAULT_POLICY, GuardrailPolicy
from ..agent.tools import BUILTIN_TOOLS, Tool
from ..memory.store import MemoryStore
from . import protocol
from .server import handle_request

logger = logging.getLogger(__name__)

#: Header carrying the session identity, spelled as the spec spells it.
SESSION_HEADER = "Mcp-Session-Id"

#: Sessions idle longer than this are forgotten. A client that returns later
#: gets 404 and re-initializes, which is the spec's own recovery path.
SESSION_IDLE_SECONDS = 3600.0

#: Ceiling on concurrent sessions, so an unauthenticated flood (or a client
#: that re-initializes in a loop) cannot grow the map without bound.
MAX_SESSIONS = 256

_LOOPBACK_NAMES = {"localhost", "localhost.localdomain", ""}


def _is_loopback_host(host: str) -> bool:
    """True if ``host`` names only the local machine."""
    if host.lower() in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def allowed_origin_hosts() -> frozenset[str]:
    """Extra ``Origin`` hosts accepted beyond loopback.

    From ``SAKTHAI_MCP_HTTP_ORIGIN``, comma- or space-separated. Unset means
    loopback only, which is the right default for a loopback-bound server.
    """
    raw = os.environ.get("SAKTHAI_MCP_HTTP_ORIGIN", "")
    return frozenset(item.strip().lower() for item in raw.replace(",", " ").split() if item.strip())


def origin_is_allowed(origin: str | None) -> bool:
    """Whether a browser-supplied ``Origin`` may reach the MCP endpoint.

    The spec requires this check against DNS rebinding: a page on an attacker's
    domain can make the victim's browser resolve that domain to 127.0.0.1 and
    POST to a locally bound server, which then sees an ordinary same-machine
    request. The bearer token is the primary defence; this is the second one,
    because a token in a query string is the kind of thing that leaks.

    A *missing* ``Origin`` is allowed: non-browser clients — which is every MCP
    client — do not send one, and rejecting them would leave the transport
    usable only by the attacker's own case.
    """
    if origin is None or not origin.strip():
        return True
    host = (urlparse(origin).hostname or "").lower()
    if not host:
        return False
    return _is_loopback_host(host) or host in allowed_origin_hosts()


def confirmation_tools_allowed() -> bool:
    """Whether tools marked ``requires_confirmation`` are exposed over HTTP.

    Off by default, and that default is the point. Over stdio the server is a
    child of the host that launched it, and the host does the confirming — MCP
    advertises ``destructiveHint`` precisely so it can. Over HTTP there is no
    such parent: ``run_command``, ``write_file``, ``forget``,
    ``run_agent_loop`` and ``delegate_to_persona`` would be reachable by
    anything holding the bearer token, with nothing left to ask the operator.

    Set ``SAKTHAI_MCP_HTTP_WRITE_ALLOW`` to expose them anyway. Named to match
    ``SAKTHAI_WRITE_ALLOW``, which plays the same role inside the agent loop.
    """
    return bool(os.environ.get("SAKTHAI_MCP_HTTP_WRITE_ALLOW", "").strip())


def http_tools(tools: tuple[Tool, ...] = BUILTIN_TOOLS) -> tuple[Tool, ...]:
    """The tool set this transport exposes, after the confirmation filter."""
    if confirmation_tools_allowed():
        return tools
    return tuple(t for t in tools if not t.requires_confirmation)


@dataclass
class _Session:
    created_at: float
    last_seen: float
    protocol_version: str


class MCPSessionStore:
    """Thread-safe registry of live Streamable HTTP sessions.

    The gateway is a ``ThreadingHTTPServer``, so every method here can be
    entered concurrently; all state is guarded by one lock. Sessions hold no
    protocol state beyond the negotiated revision — the server is otherwise
    stateless, so losing one costs a client nothing but an ``initialize``.
    """

    def __init__(
        self,
        *,
        idle_seconds: float = SESSION_IDLE_SECONDS,
        max_sessions: int = MAX_SESSIONS,
    ) -> None:
        self._idle_seconds = idle_seconds
        self._max_sessions = max_sessions
        self._lock = threading.Lock()
        self._sessions: dict[str, _Session] = {}

    def create(self, protocol_version: str) -> str:
        """Mint a session id and return it."""
        now = time.monotonic()
        session_id = secrets.token_urlsafe(24)
        with self._lock:
            self._prune_locked(now)
            if len(self._sessions) >= self._max_sessions:
                # Drop the least recently used rather than refusing service.
                oldest = min(self._sessions, key=lambda k: self._sessions[k].last_seen)
                del self._sessions[oldest]
                logger.warning("MCP HTTP session limit reached; evicted the oldest session")
            self._sessions[session_id] = _Session(now, now, protocol_version)
        return session_id

    def touch(self, session_id: str) -> _Session | None:
        """Mark a session used and return it, or None if it is unknown."""
        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)
            session = self._sessions.get(session_id)
            if session is None:
                return None
            session.last_seen = now
            return session

    def terminate(self, session_id: str) -> bool:
        """Forget a session. True if it existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def __len__(self) -> int:
        with self._lock:
            self._prune_locked(time.monotonic())
            return len(self._sessions)

    def _prune_locked(self, now: float) -> None:
        stale = [
            key
            for key, session in self._sessions.items()
            if now - session.last_seen > self._idle_seconds
        ]
        for key in stale:
            del self._sessions[key]


@dataclass
class HttpResult:
    """What the hosting HTTP server should send back."""

    status: int
    #: ``None`` for a 202 with no body, which is what a notification earns.
    payload: Any = None
    headers: dict[str, str] = field(default_factory=dict)


def _jsonrpc_error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_http(
    message: Any,
    store: MemoryStore,
    *,
    sessions: MCPSessionStore,
    session_id: str | None = None,
    protocol_version: str | None = None,
    origin: str | None = None,
    tools: tuple[Tool, ...] | None = None,
    policy: GuardrailPolicy = DEFAULT_POLICY,
) -> HttpResult:
    """Serve one POSTed JSON-RPC message over the Streamable HTTP transport.

    ``message`` is the already-parsed body: a single JSON-RPC object, or an
    array of them. Arrays are accepted because the earlier revisions in our
    supported range permit JSON-RPC batching (``2025-06-18`` removed it), and a
    client pinned to ``2024-11-05`` may legitimately send one.
    """
    if not origin_is_allowed(origin):
        return HttpResult(403, {"error": "forbidden", "message": "Origin not allowed."})

    if protocol_version is not None and not protocol.is_supported(protocol_version):
        return HttpResult(
            400,
            {
                "error": "unsupported_protocol_version",
                "message": (
                    f"{protocol.PROTOCOL_VERSION_HEADER}: {protocol_version!r} is not "
                    f"supported. Supported: {', '.join(protocol.SUPPORTED_PROTOCOL_VERSIONS)}."
                ),
            },
        )

    active = tools if tools is not None else http_tools()
    batch = message if isinstance(message, list) else [message]
    if not batch:
        return HttpResult(400, _jsonrpc_error(None, -32600, "Empty JSON-RPC batch."))

    # `initialize` is the one message that may arrive without a session, and the
    # one that mints one. Everything else must present a session we know, so a
    # stale client gets 404 and re-initializes — the spec's recovery path.
    is_initialize = any(isinstance(m, dict) and m.get("method") == "initialize" for m in batch)
    new_session_id: str | None = None
    if is_initialize:
        new_session_id = sessions.create(protocol_version or protocol.LATEST_PROTOCOL_VERSION)
    elif session_id is not None and sessions.touch(session_id) is None:
        return HttpResult(
            404,
            {"error": "session_not_found", "message": "Unknown or expired session."},
        )

    responses = [
        reply
        for raw in batch
        if (reply := handle_request(raw, store, tools=active, policy=policy)) is not None
    ]

    headers = {SESSION_HEADER: new_session_id} if new_session_id else {}

    if not responses:
        # Every message was a notification. 202 with no body, per the spec.
        return HttpResult(202, None, headers)

    payload: Any = responses if isinstance(message, list) else responses[0]
    return HttpResult(200, payload, headers)


def handle_http_delete(session_id: str | None, *, sessions: MCPSessionStore) -> HttpResult:
    """Terminate a session, as DELETE on the MCP endpoint.

    A DELETE with no session header is a client error rather than a no-op: it
    asks to end something it has not named.
    """
    if not session_id:
        return HttpResult(
            400,
            {"error": "missing_session", "message": f"{SESSION_HEADER} header is required."},
        )
    if not sessions.terminate(session_id):
        return HttpResult(
            404, {"error": "session_not_found", "message": "Unknown or expired session."}
        )
    return HttpResult(204, None)
