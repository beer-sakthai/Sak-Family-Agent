"""A dependency-free MCP server over stdio for the memory tools.

The MCP stdio transport is newline-delimited JSON-RPC 2.0: one request object
per line on stdin, one response per line on stdout. We implement the methods a
client needs to discover and call tools — ``initialize``, ``tools/list``,
``tools/call``, ``ping`` — reusing :data:`BUILTIN_TOOLS` so behaviour matches
``sakthai run`` exactly.

:func:`handle_request` is a pure function over a single request dict, so the
protocol is unit-testable without spawning a process. :func:`serve` is the thin
stdin/stdout loop built on top of it.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, TextIO

from .. import __version__
from ..agent.guardrails import DEFAULT_POLICY, GuardrailAction, GuardrailPolicy
from ..agent.tools import BUILTIN_TOOLS, Tool
from ..config import redact_secrets
from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)

# Advertised when the client does not pin a version; we echo the client's value
# back when it sends one.
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "sakthai"

# JSON-RPC 2.0 error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601


def _result(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_list(tools: tuple[Tool, ...]) -> dict[str, Any]:
    return {
        "tools": [
            {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
            for t in tools
        ]
    }


def _text_content(text: str, *, is_error: bool) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _tool_call(
    params: dict[str, Any],
    store: MemoryStore,
    tools: tuple[Tool, ...],
    policy: GuardrailPolicy = DEFAULT_POLICY,
) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    tool = next((t for t in tools if t.name == name), None)
    if tool is None:
        return _text_content(f"Unknown tool: {name}", is_error=True)

    # Pre-execution guardrail check
    pre_check = policy.check_pre_execution(tool, arguments, store)
    if pre_check.action == GuardrailAction.DENY:
        return _text_content(
            pre_check.reason or f"Tool '{name}' was denied by a pre-execution guardrail.",
            is_error=True,
        )

    final_args = pre_check.modified_args or arguments

    try:
        output = tool.handler(dict(final_args), store)
        is_error = False
    except Exception as exc:  # noqa: BLE001 — reported to the client as isError
        logger.debug("MCP tool %r raised %s: %s", name, type(exc).__name__, exc)
        output = f"{type(exc).__name__}: {exc}"
        is_error = True

    # Post-execution guardrail check
    post_check = policy.check_post_execution(tool, final_args, output, is_error, store)
    if post_check.action == GuardrailAction.DENY:
        return _text_content(
            post_check.reason
            or f"Output from tool '{name}' was denied by a post-execution guardrail.",
            is_error=True,
        )

    return _text_content(redact_secrets(output), is_error=is_error)


def handle_request(
    request: Any,
    store: MemoryStore,
    *,
    tools: tuple[Tool, ...] = BUILTIN_TOOLS,
    policy: GuardrailPolicy = DEFAULT_POLICY,
) -> dict[str, Any] | None:
    """Handle one JSON-RPC request.

    Returns the response dict to write, or ``None`` for notifications (no ``id``)
    and for methods that need no reply.
    """
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        return _error(None, INVALID_REQUEST, "Invalid JSON-RPC 2.0 request.")

    method = request.get("method")
    req_id = request.get("id")
    is_notification = "id" not in request
    params = request.get("params")
    if not isinstance(params, dict):
        params = {}

    if method == "initialize":
        return _result(
            req_id,
            {
                "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
            },
        )

    if isinstance(method, str) and method.startswith("notifications/"):
        return None

    if method == "ping":
        return None if is_notification else _result(req_id, {})

    if method == "tools/list":
        return None if is_notification else _result(req_id, _tool_list(tools))

    if method == "tools/call":
        return (
            None if is_notification else _result(req_id, _tool_call(params, store, tools, policy))
        )

    if is_notification:
        return None
    return _error(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")


def _write(stream: TextIO, message: dict[str, Any]) -> None:
    stream.write(json.dumps(message, ensure_ascii=False) + "\n")
    stream.flush()


def serve(
    *,
    store: MemoryStore | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    tools: tuple[Tool, ...] = BUILTIN_TOOLS,
    policy: GuardrailPolicy = DEFAULT_POLICY,
) -> None:
    """Run the stdio loop until EOF. Streams and store are injectable for tests."""
    in_stream = stdin if stdin is not None else sys.stdin
    out_stream = stdout if stdout is not None else sys.stdout
    own_store = store is None
    store = store if store is not None else MemoryStore()
    logger.debug("SakThai MCP server started (db=%s)", store.db_path)
    try:
        for raw in in_stream:
            line = raw.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                _write(out_stream, _error(None, PARSE_ERROR, "Parse error."))
                continue
            response = handle_request(request, store, tools=tools, policy=policy)
            if response is not None:
                _write(out_stream, response)
    finally:
        if own_store:
            store.close()
        logger.debug("SakThai MCP server stopped")
