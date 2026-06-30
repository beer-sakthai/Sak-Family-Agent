"""Minimal MCP stdio *client*: connect out to an external MCP server.

mcp/server.py exposes SakThai's own tools to other hosts. This is the mirror
image — it launches an external MCP server as a subprocess, speaks the same
newline-delimited JSON-RPC 2.0 over its stdio, and wraps each remote tool as a
local :class:`~sakthai.agent.tools.Tool` so the agent loop can call it.

Dependency-free and synchronous: a request writes one line and reads until the
matching response id, with a ``select``-based read timeout so a hung or dead
server fails loudly instead of blocking forever. (``select`` on pipes is POSIX;
this targets Linux, like the rest of the project.)
"""

from __future__ import annotations

import codecs
import contextlib
import json
import logging
import os
import select
import subprocess
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .. import config
from ..agent.tools import Tool
from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "sakthai-client"
# Backwards-compatible alias; the live default is resolved via config so that
# SAKTHAI_MCP_TIMEOUT is honoured at construction time.
DEFAULT_TIMEOUT = config.DEFAULT_MCP_TIMEOUT


class MCPClientError(RuntimeError):
    """The MCP server could not be started or did not answer correctly."""


class MCPToolError(RuntimeError):
    """A remote tool returned an error result."""


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
        # Line buffer for _readline. select() only reports bytes still in the OS
        # pipe, so we must never let a buffered reader pull *ahead* of select or
        # lines already drained from the pipe get stranded (the client would then
        # block on select until timeout). We do our own raw reads + line split and
        # keep the remainder here. An incremental decoder handles multi-byte UTF-8
        # sequences split across raw reads.
        self._read_buf = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")

    # -- lifecycle --------------------------------------------------------

    def start(self) -> StdioMCPClient:
        """Spawn the server, run the MCP handshake, and cache its tool list."""
        argv = [self._command, *self._args]
        full_env = {**os.environ, **(self._env or {})}
        try:
            self._proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=full_env,
                cwd=self._cwd,
                text=True,
                bufsize=1,  # line-buffered
            )
        except (OSError, ValueError) as exc:
            raise MCPClientError(f"could not start MCP server {self.name!r}: {exc}") from exc

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
            raise MCPClientError(f"{self.name}: initialize failed: {init['error']}")
        self._notify("notifications/initialized")

        listing = self._request("tools/list")
        result = listing.get("result") or {}
        tools = result.get("tools")
        self._remote_tools = (
            [t for t in tools if isinstance(t, dict)] if isinstance(tools, list) else []
        )
        logger.info("MCP server %r ready with %d tool(s)", self.name, len(self._remote_tools))
        return self

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return
        self._proc = None
        for stream in (proc.stdin, proc.stdout):
            if stream is not None:
                with contextlib.suppress(OSError):
                    stream.close()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def __enter__(self) -> StdioMCPClient:
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- tools ------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """The raw tool descriptors the server advertised at startup."""
        return list(self._remote_tools)

    def as_tools(self, *, prefix: str = "") -> list[Tool]:
        """Wrap each remote tool as a local Tool whose handler dispatches out.

        ``prefix`` namespaces the local tool names (e.g. ``"github_"``) while the
        bare remote name is used on the wire, so several servers can coexist.
        """
        wrapped: list[Tool] = []
        for desc in self._remote_tools:
            remote_name = desc.get("name")
            if not isinstance(remote_name, str):
                continue
            schema = desc.get("inputSchema")
            wrapped.append(
                Tool(
                    name=f"{prefix}{remote_name}",
                    description=str(desc.get("description") or ""),
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
        return self._read_response(req_id)

    def _read_response(self, req_id: int) -> dict[str, Any]:
        while True:
            line = self._readline()
            if line is None:
                raise MCPClientError(f"{self.name}: server closed before responding")
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
        proc = self._proc
        if proc is None or proc.stdout is None:
            raise MCPClientError(f"{self.name}: server is not running")
        # Serve a complete line straight from our buffer first: a previous raw
        # read may have pulled several lines (e.g. a burst of notifications)
        # off the pipe at once, and select() would not see them.
        while "\n" not in self._read_buf:
            ready, _, _ = select.select([proc.stdout], [], [], self._timeout)
            if not ready:
                raise MCPClientError(
                    f"{self.name}: timed out after {self._timeout}s waiting for reply"
                )
            chunk = os.read(proc.stdout.fileno(), 65536)
            if chunk == b"":
                # EOF: flush any decoder state and return a trailing partial line.
                self._read_buf += self._decoder.decode(b"", final=True)
                if self._read_buf:
                    line, self._read_buf = self._read_buf, ""
                    return line
                return None
            self._read_buf += self._decoder.decode(chunk)
        line, _, self._read_buf = self._read_buf.partition("\n")
        return line + "\n"
