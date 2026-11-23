"""A dependency-free MCP server over stdio for the memory tools.

The MCP stdio transport is newline-delimited JSON-RPC 2.0: one request object
per line on stdin, one response per line on stdout. We implement the methods a
client needs to discover and call tools — ``initialize``, ``tools/list``,
``tools/call``, ``ping`` — reusing :data:`BUILTIN_TOOLS` so behavior matches
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
from ..config import redact_secrets, sakthai_experimental
from ..memory.store import MemoryStore
from . import resources as resources_mod
from .protocol import (
    LATEST_PROTOCOL_VERSION,
    negotiate_protocol_version,
)

logger = logging.getLogger(__name__)

#: The revision advertised when a client states no preference. Negotiation for
#: a client that does state one goes through ``negotiate_protocol_version``;
#: see ``mcp/protocol.py`` for why echoing the client's value was wrong.
PROTOCOL_VERSION = LATEST_PROTOCOL_VERSION
SERVER_NAME = "sakthai"

# JSON-RPC 2.0 error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
#: Resource-not-found, per the targeted revisions. ``resources/read`` answered
#: with ``-32602`` (invalid params); the spec reserves a distinct code so a
#: client can tell "no such resource" from "malformed request". It only becomes
#: ``-32602`` in ``2026-07-28``, which this package does not target.
RESOURCE_NOT_FOUND = -32002


def _result(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_descriptor(tool: Tool) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.input_schema,
    }
    if tool.annotations is not None:
        descriptor["annotations"] = dict(tool.annotations)
    # The MCP Apps link, when the extension is enabled and this tool has a
    # view. Resolved per request rather than baked into BUILTIN_TOOLS, because
    # the gate is an environment variable read at request time while the tool
    # table is built at import.
    meta = resources_mod.tool_view_meta(tool.name)
    if meta:
        descriptor["_meta"] = meta
    return descriptor


def _server_capabilities() -> dict[str, Any]:
    """What this server tells a client it can do.

    ``extensions`` is the 2026-07-28 mechanism for declaring support for a
    named extension, and is accepted earlier as an unknown key. Keys are
    reverse-DNS with a mandatory prefix; anything whose second label is
    ``modelcontextprotocol`` or ``mcp`` is reserved for the specification, so
    ``io.modelcontextprotocol/ui`` is theirs, not ours to invent.
    """
    capabilities: dict[str, Any] = {
        "tools": {"listChanged": False},
        "resources": {"subscribe": False, "listChanged": False},
        "prompts": {"listChanged": False},
    }
    if sakthai_experimental():
        capabilities["extensions"] = {resources_mod.UI_EXTENSION: {}}
    return capabilities


def _tool_list(tools: tuple[Tool, ...]) -> dict[str, Any]:
    return {"tools": [_tool_descriptor(t) for t in tools]}


def _text_content(text: str, *, is_error: bool) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _tool_call(
    params: dict[str, Any],
    store: MemoryStore,
    tools: tuple[Tool, ...],
    policy: GuardrailPolicy,
) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    tool = next((t for t in tools if t.name == name), None)
    if tool is None:
        return _text_content(f"Unknown tool: {name}", is_error=True)

    # 1. Pre-execution guardrails
    pre_check = policy.check_pre_execution(tool, dict(arguments), store)
    if pre_check.action == GuardrailAction.DENY:
        reason = pre_check.reason or f"Tool '{name}' was denied by a pre-execution guardrail."
        return _text_content(reason, is_error=True)

    final_args = pre_check.modified_args if pre_check.modified_args is not None else dict(arguments)

    # 2. Validated execution, with the same redaction fail-safe the agent loop
    #    gets. Calling ``tool.handler`` directly skipped ``Tool.validate_args``,
    #    which made MCP the one transport where a schema violation — a missing
    #    required field, a string where an integer belongs — reached a handler
    #    unexamined. ``safe_call`` validates, executes and redacts, and reports
    #    a failure the same way for either cause.
    redacted_output, is_error = tool.safe_call(final_args, store)

    # 3. Post-execution guardrails
    post_check = policy.check_post_execution(tool, final_args, redacted_output, is_error, store)
    if post_check.action == GuardrailAction.DENY:
        reason = post_check.reason or f"Output from tool '{name}' was denied by a guardrail."
        return _text_content(reason, is_error=True)

    return _text_content(redacted_output, is_error=is_error)


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
        # Echo the id when the request carried one. Returning id=null for a
        # request that supplied an id leaves the client unable to match the
        # error to what it sent; JSON-RPC only allows null when the id could
        # not be determined.
        bad_id = request.get("id") if isinstance(request, dict) else None
        return _error(bad_id, INVALID_REQUEST, "Invalid JSON-RPC 2.0 request.")

    method = request.get("method")
    req_id = request.get("id")
    is_notification = "id" not in request
    params = request.get("params")
    if not isinstance(params, dict):
        params = {}

    if method == "initialize":
        # Guarded like every other method: `initialize` is a request, so an
        # `initialize` with no id is malformed and must not draw a reply. It
        # used to be handled above the notification check and answered with
        # `"id": null`.
        if is_notification:
            return None
        return _result(
            req_id,
            {
                "protocolVersion": negotiate_protocol_version(params.get("protocolVersion")),
                "capabilities": _server_capabilities(),
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
            None
            if is_notification
            else _result(
                req_id,
                _tool_call(params, store, tools, policy),
            )
        )

    if method == "resources/list":
        return (
            None
            if is_notification
            else _result(
                req_id,
                {"resources": [r.descriptor() for r in resources_mod.available()]},
            )
        )

    if method == "resources/read":
        uri = params.get("uri")
        resource = resources_mod.by_uri(uri)
        if resource is None:
            return (
                None
                if is_notification
                else _error(req_id, RESOURCE_NOT_FOUND, f"Resource not found: {uri}")
            )
        if is_notification:
            return None
        return _result(
            req_id,
            {
                "contents": [
                    {
                        "uri": resource.uri,
                        "mimeType": resource.mime_type,
                        # Same fail-safe tool output gets: resource bodies leave
                        # the process over the same transport and deserve the
                        # same filter.
                        "text": redact_secrets(resource.reader(store)),
                    }
                ]
            },
        )

    if method == "prompts/list":
        return (
            None
            if is_notification
            else _result(
                req_id,
                {
                    "prompts": [
                        {
                            "name": "sakthai_prompt",
                            "description": "Standard SakThai agent prompt template",
                            "arguments": [
                                {
                                    "name": "task",
                                    "description": "The user task or objective",
                                    "required": True,
                                }
                            ],
                        }
                    ]
                },
            )
        )

    if method == "prompts/get":
        name = params.get("name")
        if name == "sakthai_prompt":
            task_arg = (params.get("arguments") or {}).get("task", "")
            return (
                None
                if is_notification
                else _result(
                    req_id,
                    {
                        "description": "SakThai agent prompt template",
                        "messages": [
                            {
                                "role": "user",
                                "content": {
                                    "type": "text",
                                    "text": f"Task: {task_arg}"
                                    if task_arg
                                    else "Please provide a task.",
                                },
                            }
                        ],
                    },
                )
            )
        return (
            None if is_notification else _error(req_id, INVALID_PARAMS, f"Prompt not found: {name}")
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
