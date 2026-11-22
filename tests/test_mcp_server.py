"""Tests for the MCP JSON-RPC request handler and stdio loop."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from sakthai.agent.tools import Tool
from sakthai.mcp.server import PROTOCOL_VERSION, handle_request, serve
from sakthai.memory.store import MemoryStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _raising_tool(name: str, exc: Exception) -> Tool:
    """Build a Tool whose handler always raises ``exc``."""

    def _handler(args: dict, store: MemoryStore) -> str:
        raise exc

    return Tool(
        name=name,
        description="a tool that always raises",
        input_schema={"type": "object", "properties": {}},
        handler=_handler,
    )


def test_initialize_echoes_protocol(store: MemoryStore) -> None:
    resp = handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "x"}},
        store,
    )
    assert resp["result"]["protocolVersion"] == "x"
    assert resp["result"]["serverInfo"]["name"] == "sakthai"


def test_initialize_default_protocol(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, store)
    assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION


def test_tools_list(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, store)
    names = {t["name"] for t in resp["result"]["tools"]}
    assert {"learn", "recall", "search", "forget"} <= names
    assert "inputSchema" in resp["result"]["tools"][0]


def test_tools_call_learn(store: MemoryStore) -> None:
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "hi"}},
        },
        store,
    )
    assert resp["result"]["isError"] is False
    assert "Stored fact" in resp["result"]["content"][0]["text"]


def test_tools_call_unknown_tool(store: MemoryStore) -> None:
    resp = handle_request(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope"}},
        store,
    )
    assert resp["result"]["isError"] is True


def test_invalid_jsonrpc(store: MemoryStore) -> None:
    resp = handle_request({"method": "x"}, store)
    assert resp["error"]["code"] == -32600


def test_unknown_method(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 9, "method": "bogus"}, store)
    assert resp["error"]["code"] == -32601


def test_notification_returns_none(store: MemoryStore) -> None:
    assert handle_request({"jsonrpc": "2.0", "method": "notifications/x"}, store) is None
    assert handle_request({"jsonrpc": "2.0", "method": "ping"}, store) is None


def test_serve_loop(store: MemoryStore) -> None:
    stdin = io.StringIO(
        '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n'
        "not json\n"
        '{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
    )
    stdout = io.StringIO()
    serve(store=store, stdin=stdin, stdout=stdout)
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert lines[0]["id"] == 1
    assert lines[1]["error"]["code"] == -32700  # parse error for "not json"
    assert lines[2]["id"] == 2


# ---------------------------------------------------------------------------
# Handler exception tests
# ---------------------------------------------------------------------------


def test_tools_call_value_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("bad_tool", ValueError("bad input"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "bad_tool", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "ValueError" in resp["result"]["content"][0]["text"]
    assert "bad input" in resp["result"]["content"][0]["text"]


def test_tools_call_permission_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("restricted_tool", PermissionError("access denied"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "restricted_tool", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "PermissionError" in resp["result"]["content"][0]["text"]
    assert "access denied" in resp["result"]["content"][0]["text"]


def test_tools_call_runtime_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("crasher", RuntimeError("unexpected failure"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "crasher", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "RuntimeError" in resp["result"]["content"][0]["text"]


def test_tools_call_handler_exception_response_is_valid_jsonrpc(store: MemoryStore) -> None:
    tool = _raising_tool("flakey", OSError("disk full"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "flakey", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    # The envelope must be a valid JSON-RPC 2.0 result, not an error frame.
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 13
    assert "result" in resp
    assert "error" not in resp
    assert resp["result"]["isError"] is True


def test_tools_call_handler_exception_does_not_propagate(store: MemoryStore) -> None:
    # handle_request must never let a handler exception bubble up to the caller.
    tool = _raising_tool("boom", Exception("internal boom"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {"name": "boom", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp is not None
    assert resp["result"]["isError"] is True


def test_tools_call_learn_invalid_value_returns_is_error(store: MemoryStore) -> None:
    # The built-in `learn` tool raises ValueError for blank input; verify this
    # surfaces as isError rather than a server crash.
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "   "}},
        },
        store,
    )
    assert resp["result"]["isError"] is True
    assert "ValueError" in resp["result"]["content"][0]["text"]


def test_tools_call_notification_with_handler_exception_returns_none(store: MemoryStore) -> None:
    # Notifications (no "id") must return None even when the handler would fail.
    tool = _raising_tool("noisy_notif", RuntimeError("boom"))
    result = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "noisy_notif", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert result is None


def test_notification_for_unknown_method_returns_none(store: MemoryStore) -> None:
    # A notification (no "id") with an unknown method (not ping, not tools/*,
    # not notifications/*) must return None — not an error frame.
    result = handle_request({"jsonrpc": "2.0", "method": "completely_unknown_method"}, store)
    assert result is None


def test_serve_skips_blank_lines(store: MemoryStore) -> None:
    """serve() must silently skip blank / whitespace-only input lines."""
    import io

    stdin = io.StringIO('\n   \n{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n\n')
    stdout = io.StringIO()
    serve(store=store, stdin=stdin, stdout=stdout)
    lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
    assert len(lines) == 1
    import json

    assert json.loads(lines[0])["id"] == 1


def test_serve_creates_and_closes_own_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no store is passed, serve() creates its own and closes it on exit."""
    import io

    from sakthai.config import memory_db_path

    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    stdin = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n')
    stdout = io.StringIO()
    serve(stdin=stdin, stdout=stdout)  # no store= argument → own_store=True
    # The DB should now exist (was opened and closed by serve)
    assert memory_db_path().exists()


def test_mcp_tools_list_matches_builtin_tools(store: MemoryStore) -> None:
    """tools/list must expose exactly the same names as BUILTIN_TOOLS.

    This is a regression canary: if a tool is added to agent/tools.py but the
    MCP wiring breaks, this test fails immediately.
    """
    from sakthai.agent.tools import BUILTIN_TOOLS

    resp = handle_request({"jsonrpc": "2.0", "id": 99, "method": "tools/list"}, store)
    listed_names = {t["name"] for t in resp["result"]["tools"]}
    builtin_names = {t.name for t in BUILTIN_TOOLS}
    assert listed_names == builtin_names


def test_mcp_tools_list_schemas_have_required_fields(store: MemoryStore) -> None:
    """Every tool in tools/list must carry name, description, and inputSchema."""
    resp = handle_request({"jsonrpc": "2.0", "id": 100, "method": "tools/list"}, store)
    for tool in resp["result"]["tools"]:
        assert "name" in tool, f"tool missing 'name': {tool}"
        assert "description" in tool, f"tool {tool['name']!r} missing 'description'"
        assert "inputSchema" in tool, f"tool {tool['name']!r} missing 'inputSchema'"
        assert tool["inputSchema"]["type"] == "object"


def _listed_tools(store: MemoryStore) -> dict[str, dict]:
    resp = handle_request({"jsonrpc": "2.0", "id": 101, "method": "tools/list"}, store)
    return {t["name"]: t for t in resp["result"]["tools"]}


def test_every_builtin_tool_advertises_annotations(store: MemoryStore) -> None:
    """Clients gate approvals on these hints, so no built-in may omit them."""
    for name, tool in _listed_tools(store).items():
        annotations = tool.get("annotations")
        assert annotations is not None, f"{name} has no annotations"
        assert isinstance(annotations["readOnlyHint"], bool), name
        assert isinstance(annotations["openWorldHint"], bool), name
        if annotations["readOnlyHint"]:
            # destructive/idempotent hints are meaningless for read-only tools.
            assert "destructiveHint" not in annotations, name
            assert "idempotentHint" not in annotations, name
        else:
            assert isinstance(annotations["destructiveHint"], bool), name
            assert isinstance(annotations["idempotentHint"], bool), name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("recall", {"readOnlyHint": True, "openWorldHint": False}),
        ("read_file", {"readOnlyHint": True, "openWorldHint": False}),
        ("list_calendar_events", {"readOnlyHint": True, "openWorldHint": True}),
        (
            "forget",
            {
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        ),
        (
            "run_command",
            {
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": False,
                "openWorldHint": True,
            },
        ),
        (
            "send_outlook_mail",
            {
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": True,
            },
        ),
    ],
)
def test_tool_annotations_describe_real_behaviour(
    store: MemoryStore, name: str, expected: dict[str, bool]
) -> None:
    assert _listed_tools(store)[name]["annotations"] == expected


def test_tool_without_annotations_lists_without_the_key(store: MemoryStore) -> None:
    """Plugin tools predate annotations: they must list cleanly, not with a null."""
    bare = Tool(
        name="bare",
        description="no hints",
        input_schema={"type": "object", "properties": {}},
        handler=lambda _a, _s: "ok",
    )
    resp = handle_request(
        {"jsonrpc": "2.0", "id": 102, "method": "tools/list"}, store, tools=(bare,)
    )
    assert "annotations" not in resp["result"]["tools"][0]


def test_memory_status_resource_counts_past_one_thousand_facts(store: MemoryStore) -> None:
    """fact_count used to come from list_facts(limit=1000) and silently capped there."""
    for i in range(1001):
        store.add_fact(f"fact {i}")
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 103,
            "method": "resources/read",
            "params": {"uri": "sakthai://memory/status"},
        },
        store,
    )
    stats = json.loads(resp["result"]["contents"][0]["text"])
    assert stats["fact_count"] == 1001


# ---------------------------------------------------------------------------
# Guardrail integration: pre- and post-execution DENY through the MCP surface
# ---------------------------------------------------------------------------


def test_tools_call_pre_execution_guardrail_denies(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_command without SAKTHAI_SHELL_ALLOW is denied before execution."""
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {"name": "run_command", "arguments": {"command": "ls"}},
        },
        store,
    )
    assert resp["result"]["isError"] is True
    assert "disabled" in resp["result"]["content"][0]["text"]


def test_tools_call_post_execution_guardrail_denies(store: MemoryStore) -> None:
    """A denying post-rule replaces the tool output with the denial reason."""
    from sakthai.agent.guardrails import GuardrailAction, GuardrailPolicy, GuardrailResult

    def deny_output(
        _tool: Tool, _args: dict, _output: str, _is_error: bool, _store: MemoryStore
    ) -> GuardrailResult:
        return GuardrailResult(GuardrailAction.DENY, reason="output blocked by policy")

    policy = GuardrailPolicy(post_rules=[deny_output])
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "hi"}},
        },
        store,
        policy=policy,
    )
    assert resp["result"]["isError"] is True
    assert resp["result"]["content"][0]["text"] == "output blocked by policy"


def test_tools_call_post_guardrail_default_reason(store: MemoryStore) -> None:
    """A reasonless post-rule denial falls back to the generic message."""
    from sakthai.agent.guardrails import GuardrailAction, GuardrailPolicy, GuardrailResult

    def deny_silently(
        _tool: Tool, _args: dict, _output: str, _is_error: bool, _store: MemoryStore
    ) -> GuardrailResult:
        return GuardrailResult(GuardrailAction.DENY)

    policy = GuardrailPolicy(post_rules=[deny_silently])
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "hi"}},
        },
        store,
        policy=policy,
    )
    assert resp["result"]["isError"] is True
    assert "denied by a guardrail" in resp["result"]["content"][0]["text"]


def test_resources_list_and_read(store: MemoryStore) -> None:
    # List resources
    resp = handle_request({"jsonrpc": "2.0", "id": 50, "method": "resources/list"}, store)
    assert "resources" in resp["result"]
    assert len(resp["result"]["resources"]) == 1
    uri = resp["result"]["resources"][0]["uri"]
    assert uri == "sakthai://memory/status"

    # Read existing resource
    read_resp = handle_request(
        {"jsonrpc": "2.0", "id": 51, "method": "resources/read", "params": {"uri": uri}},
        store,
    )
    assert "contents" in read_resp["result"]
    assert read_resp["result"]["contents"][0]["uri"] == uri

    # Read non-existent resource
    err_resp = handle_request(
        {"jsonrpc": "2.0", "id": 52, "method": "resources/read", "params": {"uri": "unknown"}},
        store,
    )
    assert "error" in err_resp


def test_prompts_list_and_get(store: MemoryStore) -> None:
    # List prompts
    resp = handle_request({"jsonrpc": "2.0", "id": 60, "method": "prompts/list"}, store)
    assert "prompts" in resp["result"]
    assert len(resp["result"]["prompts"]) == 1
    assert resp["result"]["prompts"][0]["name"] == "sakthai_prompt"

    # Get prompt with arguments
    get_resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 61,
            "method": "prompts/get",
            "params": {"name": "sakthai_prompt", "arguments": {"task": "fix bug"}},
        },
        store,
    )
    assert "messages" in get_resp["result"]
    assert "fix bug" in get_resp["result"]["messages"][0]["content"]["text"]

    # Get unknown prompt
    err_resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 62,
            "method": "prompts/get",
            "params": {"name": "nonexistent_prompt"},
        },
        store,
    )
    assert "error" in err_resp
