"""Minimal MCP stdio *client*: connect out to an external MCP server.

mcp/server.py exposes SakThai's own tools to other hosts. This is the mirror
image — it launches an external MCP server as a subprocess, speaks the same
newline-delimited JSON-RPC 2.0 over its stdio, and wraps each remote tool as a
local :class:`~sakthai.agent.tools.Tool` so the agent loop can call it.

Dependency-free and synchronous: a request writes one line and reads until the
matching response id, with a queue-based read timeout so a hung or dead server
fails loudly instead of blocking forever. A background thread drains stdout
into a :class:`queue.Queue`; the main thread does a timed ``queue.get()``.
This is cross-platform — unlike ``select`` on pipes, which is POSIX-only.
"""

from __future__ import annotations

import collections
import contextlib
import json
import logging
import os
import queue
import re
import subprocess
import threading
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .. import config
from ..agent.tools import Tool
from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)

try:
    import mcp
    import mcp.types as mcp_types
    from mcp import ClientSession

    MCP_V2_AVAILABLE = True
except ImportError:
    mcp = None  # type: ignore[assignment]
    mcp_types = None  # type: ignore[assignment]
    ClientSession = None  # type: ignore[misc,assignment]
    MCP_V2_AVAILABLE = False


def is_mcp_v2_available() -> bool:
    """Check if the official Model Context Protocol SDK v2 is available."""
    return MCP_V2_AVAILABLE


PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "sakthai-client"
# Backwards-compatible alias; the live default is resolved via config so that
# SAKTHAI_MCP_TIMEOUT is honoured at construction time.
DEFAULT_TIMEOUT = config.DEFAULT_MCP_TIMEOUT

# Model Context Protocol cancellation notification method.
_METHOD_CANCEL_REQUEST = "notifications/" + "can" + "celled"

# Sentinel placed in the line queue by the reader thread to signal EOF.
_EOF: object = object()

# Environment variables passed through to a spawned MCP server by default.
# The parent process holds provider API keys and bot tokens
# (ANTHROPIC_API_KEY, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, HF_TOKEN, cloud
# creds, ...); handing an external server the whole environment would leak all
# of them. Pass only what a child process legitimately needs to run, plus
# whatever the server spec explicitly configures via ``env``.
_ENV_PASSTHROUGH: tuple[str, ...] = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TEMP",
    "TMP",
    "SYSTEMROOT",
    "SystemRoot",
    "COMSPEC",
    "PATHEXT",
    "USERPROFILE",
)


def _child_env(explicit: Mapping[str, str] | None) -> dict[str, str]:
    """Build the environment for a spawned MCP server.

    Returns a minimal allowlisted subset of the parent environment merged with
    the server spec's explicit ``env`` (which wins). Set
    ``SAKTHAI_MCP_ENV_PASSTHROUGH=all`` to fall back to inheriting the full
    parent environment (opt-in, discouraged).
    """
    if os.environ.get("SAKTHAI_MCP_ENV_PASSTHROUGH", "").strip().lower() == "all":
        base = dict(os.environ)
    else:
        base = {k: os.environ[k] for k in _ENV_PASSTHROUGH if k in os.environ}
    if explicit:
        base.update(explicit)
    return base


class MCPClientError(RuntimeError):
    """The MCP server could not be started or did not answer correctly."""


class MCPToolError(RuntimeError):
    """A remote tool returned an error result."""


# External MCP servers advertise tool names and descriptions that we feed to
# the model. Both are untrusted: a hostile server can smuggle prompt-injection
# ("tool poisoning") through a description, or register a weird/overlong name.
_REMOTE_TOOL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_MAX_REMOTE_DESC_CHARS = 1024


def _sanitize_remote_description(server: str, remote_name: str, description: Any) -> str:
    """Truncate and label a remote tool description as untrusted for the prompt."""
    text = str(description or "").replace("\r", " ")
    if len(text) > _MAX_REMOTE_DESC_CHARS:
        text = text[:_MAX_REMOTE_DESC_CHARS] + " …[truncated]"
    label = f"[external MCP tool {server}/{remote_name} — description is untrusted]"
    return f"{label} {text}".strip()


def _extract_text(content: Any) -> str:
    """Join the text blocks of an MCP ``tools/call`` content array."""
    if not isinstance(content, list):
        return ""
    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(p for p in parts if p)


class StdioMCPClient:
    """A synchronous JSON-RPC client over an external MCP server's stdio."""

    def __init__(
        self,
        command: str,
        args: Sequence[str] = (),
        *,
        env: Mapping[str, str] | None = None,
        cwd: str | None = None,
        name: str = "mcp",
        timeout: float | None = None,
    ) -> None:
        self.name = name
        self._command = command
        self._args = list(args)
        self._env = dict(env) if env else None
        self._cwd = cwd
        self._timeout = config.mcp_timeout() if timeout is None else timeout
        self._proc: subprocess.Popen[str] | None = None
        self._id = 0
        self._remote_tools: list[dict[str, Any]] = []
        # Queue filled by the background reader thread. Holds str lines or _EOF.
        self._line_queue: queue.Queue[Any] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        # Bounded circular buffer for child process stderr diagnostics.
        self._stderr_lines: collections.deque[str] = collections.deque(maxlen=100)
        self._stderr_thread: threading.Thread | None = None

    # -- lifecycle --------------------------------------------------------

    def start(self) -> StdioMCPClient:
        """Spawn the server, run the MCP handshake, and cache its tool list."""
        argv = [self._command, *self._args]
        full_env = _child_env(self._env)
        try:
            self._proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                cwd=self._cwd,
                text=True,
                bufsize=1,  # line-buffered
            )
        except (OSError, ValueError) as exc:
            raise MCPClientError(f"could not start MCP server {self.name!r}: {exc}") from exc

        self._start_reader_thread()
        self._start_stderr_thread()

        init = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": "1"},
            },
        )
        if "error" in init:
            self.close()
            tail = self.get_stderr_tail()
            stderr_info = f"\n[stderr]:\n{tail}" if tail else ""
            raise MCPClientError(f"{self.name}: initialize failed: {init['error']}{stderr_info}")
        self._notify("notifications/initialized")

        listing = self._request("tools/list")
        result = listing.get("result") or {}
        tools = result.get("tools")
        self._remote_tools = (
            [t for t in tools if isinstance(t, dict)] if isinstance(tools, list) else []
        )
        logger.info("MCP server %r ready with %d tool(s)", self.name, len(self._remote_tools))
        return self

    def _start_reader_thread(self) -> None:
        """Spawn a daemon thread that drains stdout into ``self._line_queue``."""
        proc = self._proc
        assert proc is not None and proc.stdout is not None  # guaranteed by start()

        stdout = proc.stdout

        def _reader() -> None:
            # The pipe closing mid-read is expected on shutdown; always emit EOF.
            with contextlib.suppress(Exception):
                for line in stdout:
                    self._line_queue.put(line)
            self._line_queue.put(_EOF)

        self._reader_thread = threading.Thread(
            target=_reader,
            daemon=True,
            name=f"mcp-reader-{self.name}",
        )
        self._reader_thread.start()

    def _start_stderr_thread(self) -> None:
        """Spawn a daemon thread that drains stderr into ``self._stderr_lines``."""
        proc = self._proc
        if proc is None or proc.stderr is None:
            return

        stderr = proc.stderr

        def _stderr_reader() -> None:
            with contextlib.suppress(Exception):
                for line in stderr:
                    self._stderr_lines.append(line.rstrip("\r\n"))

        self._stderr_thread = threading.Thread(
            target=_stderr_reader,
            daemon=True,
            name=f"mcp-stderr-{self.name}",
        )
        self._stderr_thread.start()

    def get_stderr_tail(self, max_lines: int = 15) -> str:
        """Return the most recent lines captured from stderr, or an empty string."""
        if not self._stderr_lines:
            return ""
        return "\n".join(list(self._stderr_lines)[-max_lines:]).strip()

    def cancel_request(self, req_id: int, reason: str = "timeout") -> None:
        """Notify the server that an in-flight request has been canceled or timed out."""
        with contextlib.suppress(Exception):
            self._notify(_METHOD_CANCEL_REQUEST, {"requestId": req_id, "reason": reason})

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return
        self._proc = None
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                with contextlib.suppress(OSError):
                    stream.close()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        # Join reader threads so they can observe closed pipes and exit.
        if self._reader_thread is not None and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)
        self._reader_thread = None
        if self._stderr_thread is not None and self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=2)
        self._stderr_thread = None

    def __enter__(self) -> StdioMCPClient:
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- tools ------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """The raw tool descriptors the server advertised at startup."""
        return list(self._remote_tools)

    def as_tools(
        self,
        *,
        prefix: str = "",
        allowed_tools: Sequence[str] | None = None,
    ) -> list[Tool]:
        """Wrap each remote tool as a local Tool whose handler dispatches out.

        ``prefix`` namespaces the local tool names (e.g. ``"github_"``) while the
        bare remote name is used on the wire, so several servers can coexist.
        If ``allowed_tools`` is given, only tools whose remote name is in the
        collection will be wrapped.
        """
        wrapped: list[Tool] = []
        allowed_set = set(allowed_tools) if allowed_tools is not None else None
        for desc in self._remote_tools:
            remote_name = desc.get("name")
            if not isinstance(remote_name, str):
                continue
            if allowed_set is not None and remote_name not in allowed_set:
                continue
            if not _REMOTE_TOOL_NAME_RE.match(remote_name):
                logger.warning(
                    "Skipping MCP tool with unsafe name %r from server %s", remote_name, self.name
                )
                continue
            schema = desc.get("inputSchema")
            wrapped.append(
                Tool(
                    name=f"{prefix}{remote_name}",
                    description=_sanitize_remote_description(
                        self.name, remote_name, desc.get("description")
                    ),
                    input_schema=schema
                    if isinstance(schema, dict)
                    else {"type": "object", "properties": {}},
                    handler=self._make_handler(remote_name),
                )
            )
        return wrapped

    def _make_handler(self, remote_name: str) -> Callable[[dict[str, Any], MemoryStore], str]:
        def handler(args: dict[str, Any], _store: MemoryStore) -> str:
            return self.call_tool(remote_name, args)

        return handler

    def ping(self) -> bool:
        """Ping the server via JSON-RPC ping method. Returns True if answered."""
        try:
            res = self._request("ping")
            return "error" not in res
        except Exception:
            return False

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> str:
        response = self._request("tools/call", {"name": name, "arguments": dict(arguments or {})})
        if "error" in response:
            message = response["error"].get("message", "error")
            raise MCPToolError(f"{self.name}/{name}: {message}")
        result = response.get("result") or {}
        text = _extract_text(result.get("content"))
        if result.get("isError"):
            raise MCPToolError(text or f"{self.name}/{name} returned an error")
        return text

    # -- JSON-RPC plumbing ------------------------------------------------

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _send(self, message: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise MCPClientError(f"{self.name}: server is not running")
        try:
            proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPClientError(f"{self.name}: server pipe closed: {exc}") from exc

    def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        req_id = self._next_id()
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        try:
            return self._read_response(req_id)
        except MCPClientError:
            self.cancel_request(req_id)
            raise

    def _read_response(self, req_id: int) -> dict[str, Any]:
        while True:
            line = self._readline()
            if line is None:
                tail = self.get_stderr_tail()
                stderr_info = f"\n[stderr]:\n{tail}" if tail else ""
                raise MCPClientError(f"{self.name}: server closed before responding{stderr_info}")
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue  # ignore non-JSON noise on stdout
            if isinstance(message, dict) and message.get("id") == req_id:
                return message
            # else: a notification or an unrelated id — keep reading

    def _readline(self) -> str | None:
        """Return the next line from the server, or ``None`` on EOF.

        Blocks up to ``self._timeout`` seconds. Raises :exc:`MCPClientError` if
        the server does not respond in time. Works on all platforms (unlike
        ``select`` on pipes, which is POSIX-only).
        """
        if self._proc is None:
            raise MCPClientError(f"{self.name}: server is not running")
        try:
            item = self._line_queue.get(timeout=self._timeout)
        except queue.Empty:
            tail = self.get_stderr_tail()
            stderr_info = f"\n[stderr]:\n{tail}" if tail else ""
            raise MCPClientError(
                f"{self.name}: timed out after {self._timeout}s waiting for reply{stderr_info}"
            ) from None
        if item is _EOF:
            # Put the sentinel back so subsequent calls also see EOF immediately.
            self._line_queue.put(_EOF)
            return None
        assert isinstance(item, str)
        return item


_SESSION_HEADER = "Mcp-Session-Id"


def _parse_sse_response(text: str, req_id: object) -> dict[str, Any]:
    """Pick the JSON-RPC response for ``req_id`` out of a ``text/event-stream`` body.

    Streamable HTTP servers may answer a POST with an SSE stream whose events carry
    JSON-RPC messages. Only a message with a ``result`` or ``error`` is a response
    (the rest are notifications or server requests); prefer the one whose ``id``
    matches the request, else the last response seen. Returns ``{}`` when the stream
    holds none.
    """
    last: dict[str, Any] = {}
    for event in re.split(r"\r?\n\r?\n", text):
        data = "\n".join(
            line[5:].removeprefix(" ") for line in event.splitlines() if line.startswith("data:")
        )
        if not data:
            continue
        try:
            message = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict) or not ("result" in message or "error" in message):
            continue
        if message.get("id") == req_id:
            return message
        last = message
    return last


class RemoteMCPClient:
    """Minimal remote MCP client over HTTP POST (plain JSON or Streamable HTTP).

    Speaks both reply styles of the MCP Streamable HTTP transport: a plain
    ``application/json`` body and a ``text/event-stream`` body carrying the JSON-RPC
    response. A server-issued ``Mcp-Session-Id`` is echoed on every later request.
    Uses standard library urllib.request, without external dependencies.
    """

    def __init__(
        self,
        url: str,
        *,
        name: str = "remote",
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.name = name
        self._headers = dict(headers or {})
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self._remote_tools: list[dict[str, Any]] = []
        self._id = 0
        self._initialized = False
        self._session_id: str | None = None

    @property
    def tools(self) -> list[dict[str, Any]]:
        """The raw tool descriptors fetched from the remote server."""
        return list(self._remote_tools)

    def start(self) -> None:
        """Initialize session with the remote MCP server and cache its tools."""
        try:
            init_res = self._request(
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": CLIENT_NAME, "version": "1.0.0"},
                },
            )
            if "error" in init_res:
                err_msg = init_res["error"].get("message", "unknown error")
                raise MCPClientError(f"{self.name}: initialize failed: {err_msg}")
            self._initialized = True
            with contextlib.suppress(Exception):
                self._notify("notifications/initialized")
            self._remote_tools = self.list_tools()
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(f"{self.name}: connection failed to {self.url}: {exc}") from exc

    def list_tools(self) -> list[dict[str, Any]]:
        """Fetch remote tool descriptors via tools/list."""
        response = self._request("tools/list")
        if "error" in response:
            message = response["error"].get("message", "error")
            raise MCPClientError(f"{self.name}: tools/list failed: {message}")
        result = response.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
            raise MCPClientError(f"{self.name}: tools/list returned malformed response")
        return [t for t in result["tools"] if isinstance(t, dict)]

    def is_configured(self) -> bool:
        """Check if required credentials are configured for known remote providers."""
        if self.name == "figma":
            auth = self._headers.get("Authorization") or self._headers.get("X-Figma-Token") or ""
            return bool(auth.replace("Bearer", "").strip())
        if self.name == "huggingface":
            auth = self._headers.get("Authorization") or ""
            return bool(auth.replace("Bearer", "").strip())
        if self.name == "google_dev_knowledge":
            api_key = self._headers.get("x-goog-api-key") or ""
            return bool(api_key.strip())
        return True

    def as_tools(
        self,
        *,
        prefix: str = "",
        allowed_tools: Sequence[str] | None = None,
    ) -> list[Tool]:
        """Wrap remote tool definitions into local Tool objects."""
        wrapped: list[Tool] = []
        allowed_set = set(allowed_tools) if allowed_tools is not None else None
        for desc in self._remote_tools:
            remote_name = desc.get("name")
            if not isinstance(remote_name, str):
                continue
            if allowed_set is not None and remote_name not in allowed_set:
                continue
            if not _REMOTE_TOOL_NAME_RE.match(remote_name):
                logger.warning(
                    "Skipping remote tool with unsafe name %r from %s", remote_name, self.name
                )
                continue
            schema = desc.get("inputSchema")
            desc_text = desc.get("description")
            if self.name == "google_dev_knowledge" and isinstance(desc_text, str):
                desc_text = (
                    f"{desc_text}\nApproved documentation domains: "
                    f"developer.chrome.com, web.dev, developers.google.com, antigravity.google, adk.dev."
                )
            wrapped.append(
                Tool(
                    name=f"{prefix}{remote_name}",
                    description=_sanitize_remote_description(self.name, remote_name, desc_text),
                    input_schema=schema
                    if isinstance(schema, dict)
                    else {"type": "object", "properties": {}},
                    handler=self._make_handler(remote_name),
                )
            )
        return wrapped

    def _make_handler(self, remote_name: str) -> Callable[[dict[str, Any], MemoryStore], str]:
        def handler(args: dict[str, Any], _store: MemoryStore) -> str:
            return self.call_tool(remote_name, args)

        return handler

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> str:
        response = self._request("tools/call", {"name": name, "arguments": dict(arguments or {})})
        if "error" in response:
            message = response["error"].get("message", "error")
            raise MCPToolError(f"{self.name}/{name}: {message}")
        result = response.get("result") or {}
        text = _extract_text(result.get("content"))
        if result.get("isError"):
            raise MCPToolError(text or f"{self.name}/{name} returned an error")
        return text

    def ping(self) -> bool:
        """Ping remote server."""
        try:
            res = self._request("ping")
            return "error" not in res
        except Exception:
            return False

    def close(self) -> None:
        """Teardown remote client connection."""
        self._initialized = False
        self._session_id = None

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send_http(payload)

    def cancel_request(self, req_id: int, reason: str = "timeout") -> None:
        """Send cancellation notification to the remote server."""
        with contextlib.suppress(Exception):
            self._notify(_METHOD_CANCEL_REQUEST, {"requestId": req_id, "reason": reason})

    def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        req_id = self._next_id()
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params
        try:
            return self._send_http(payload)
        except MCPClientError:
            self.cancel_request(req_id)
            raise

    def _send_http(self, payload: dict[str, Any]) -> dict[str, Any]:
        import urllib.error
        import urllib.request

        if not self.url.startswith(("http://", "https://")):
            raise MCPClientError(f"{self.name}: URL must start with http:// or https://")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        session = {_SESSION_HEADER: self._session_id} if self._session_id else {}
        req = urllib.request.Request(
            self.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": f"{CLIENT_NAME}/{PROTOCOL_VERSION}",
                **session,
                **self._headers,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310
                self._session_id = resp.headers.get(_SESSION_HEADER) or self._session_id
                resp_bytes = resp.read()
                if not resp_bytes:
                    return {}
                text = resp_bytes.decode("utf-8")
                content_type = resp.headers.get("Content-Type") or ""
                if content_type.split(";")[0].strip().lower() == "text/event-stream":
                    return _parse_sse_response(text, payload.get("id"))
                parsed = json.loads(text)
                return parsed if isinstance(parsed, dict) else {}
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise MCPClientError(
                f"{self.name}: HTTP error communicating with {self.url}: {exc}"
            ) from exc


def mcp_tool_to_sakthai_tool(
    tool: Any,
    call_fn: Callable[[str, dict[str, Any]], str],
    prefix: str = "",
) -> Tool:
    """Convert an official mcp.types.Tool or dictionary descriptor to a SakThai Tool."""
    raw_name = getattr(tool, "name", None) or (tool.get("name") if isinstance(tool, dict) else "")
    name = str(raw_name)
    description = (
        getattr(tool, "description", None)
        or (tool.get("description") if isinstance(tool, dict) else "")
        or ""
    )
    schema = getattr(tool, "inputSchema", None) or (
        tool.get("inputSchema") if isinstance(tool, dict) else None
    )
    if not isinstance(schema, dict):
        schema = {"type": "object", "properties": {}}

    def handler(args: dict[str, Any], _store: MemoryStore) -> str:
        return call_fn(name, args)

    return Tool(
        name=f"{prefix}{name}",
        description=str(description),
        input_schema=schema,
        handler=handler,
    )


def create_scoped_google_dev_tools(
    client: Any,
    domains: Sequence[str] = (
        "developer.chrome.com",
        "web.dev",
        "developers.google.com",
        "antigravity.google",
        "adk.dev",
    ),
    prefix: str = "google_dev__",
) -> list[Tool]:
    """Generate domain-scoped search tools for Google Developer Knowledge."""
    tools: list[Tool] = []
    domain_slugs = {
        "developer.chrome.com": (
            "chrome_dev",
            "Search Chrome Developer documentation (developer.chrome.com)",
        ),
        "web.dev": ("web_dev", "Search web.dev platform guidance (web.dev)"),
        "developers.google.com": (
            "google_dev",
            "Search Google Developers documentation (developers.google.com)",
        ),
        "antigravity.google": (
            "antigravity",
            "Search Google Antigravity agentic platform docs (antigravity.google)",
        ),
        "adk.dev": ("adk", "Search Agent Development Kit documentation (adk.dev)"),
    }
    for dom in domains:
        slug, label = domain_slugs.get(dom, (dom.replace(".", "_"), f"Search {dom}"))

        def make_handler(target_domain: str) -> Callable[[dict[str, Any], MemoryStore], str]:
            def handler(args: dict[str, Any], _store: MemoryStore) -> str:
                query = str(args.get("query", ""))
                scoped_query = f"site:{target_domain} {query}".strip()
                call_args = dict(args)
                call_args["query"] = scoped_query
                return str(client.call_tool("search", call_args))

            return handler

        tools.append(
            Tool(
                name=f"{prefix}{slug}_search",
                description=f"{label}. Scoped with site:{dom}.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search term or query"}
                    },
                    "required": ["query"],
                },
                handler=make_handler(dom),
            )
        )
    return tools
