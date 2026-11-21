"""Unit tests for the Runtime Gateway router and request dispatching."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.gateway.router import GatewayRouter


def test_router_handle_models() -> None:
    router = GatewayRouter()
    res = router.handle_models()
    assert res["object"] == "list"
    models = res["data"]
    ids = {m["id"] for m in models}

    # Verify all 6 personas exist
    for p in ("sakthai", "sakking", "saksee", "sakjules", "saksit", "saktan"):
        assert p in ids

    # Verify model presets exist
    assert "gemini-2.5-flash" in ids
    assert "gemini-3.7-flash" in ids


def test_router_handle_personas() -> None:
    router = GatewayRouter()
    res = router.handle_personas()
    assert res["count"] == 6
    assert "sakjules" in res["personas"]
    assert res["personas"]["sakjules"]["role"] == "GitHub, CI/CD & Automation"


def test_router_handle_persona_detail() -> None:
    router = GatewayRouter()
    detail = router.handle_persona_detail("saksee")
    assert detail is not None
    assert detail["name"] == "SakSee"
    assert detail["handle"] == "@saksee_agent_bot"

    # Case insensitive
    assert router.handle_persona_detail("SAKKING") is not None

    # Unknown persona
    assert router.handle_persona_detail("nonexistent") is None


def test_router_handle_tools() -> None:
    router = GatewayRouter()
    res = router.handle_tools()
    assert "tools" in res
    tools = res["tools"]
    names = {t["function"]["name"] for t in tools}
    assert "learn" in names
    assert "recall" in names
    assert "search" in names


def test_router_handle_tools_execute_missing_fields() -> None:
    router = GatewayRouter()
    res = router.handle_tools_execute({})
    assert res["status"] == "error"
    assert "Missing required field" in res["error"]

    res2 = router.handle_tools_execute({"tool": "recall", "arguments": "not-a-dict"})
    assert res2["status"] == "error"
    assert "must be a dictionary" in res2["error"]

    res3 = router.handle_tools_execute({"tool": "nonexistent_tool"})
    assert res3["status"] == "error"
    assert "Unknown tool" in res3["error"]


def test_router_handle_tools_execute_guardrail_block() -> None:
    router = GatewayRouter()
    # Attempt destructive SQL drop table
    res = router.handle_tools_execute({"tool": "run_command", "arguments": {"command": "rm -rf /"}})
    assert res["status"] == "blocked"
    assert "approval_token_required" in res


def test_router_handle_chat_completion_validation() -> None:
    router = GatewayRouter()
    with pytest.raises(ValueError, match="Field 'messages' is required"):
        router.handle_chat_completion({})

    with pytest.raises(ValueError, match="Field 'messages' is required"):
        router.handle_chat_completion({"messages": []})


def test_router_handle_chat_completion_non_streaming() -> None:
    router = GatewayRouter()
    res, is_stream = router.handle_chat_completion(
        {
            "model": "sakking",
            "messages": [{"role": "user", "content": "How do you do TDD?"}],
            "stream": False,
        }
    )
    assert not is_stream
    assert isinstance(res, dict)
    assert res["object"] == "chat.completion"
    assert res["model"] == "sakking"
    assert len(res["choices"]) == 1
    content = res["choices"][0]["message"]["content"]
    assert "SakKing" in content
    assert "How do you do TDD?" in content
    assert res["usage"]["total_tokens"] > 0


def test_router_handle_chat_completion_streaming() -> None:
    router = GatewayRouter()
    res, is_stream = router.handle_chat_completion(
        {
            "model": "gateway/sakjules",
            "messages": [{"role": "user", "content": "Build the release pipeline"}],
            "stream": True,
        }
    )
    assert is_stream
    chunks = list(res)
    assert len(chunks) > 2
    assert chunks[-1] == "data: [DONE]\n\n"
    # Ensure chunk payloads are valid JSON
    first_payload = chunks[0].strip()[6:]
    assert "chat.completion.chunk" in first_payload


def test_router_handle_chat_completion_with_custom_executor() -> None:
    def dummy_executor(prompt: str, persona: str, **kwargs: Any) -> str:
        return f"Echo from {persona}: {prompt}"

    router = GatewayRouter(chat_executor=dummy_executor)
    res, is_stream = router.handle_chat_completion(
        {
            "model": "saksee",
            "messages": [{"role": "user", "content": "Scrape site"}],
            "stream": False,
        }
    )
    assert not is_stream
    assert isinstance(res, dict)
    assert res["choices"][0]["message"]["content"] == "Echo from saksee: Scrape site"


def test_router_handle_health_and_status() -> None:
    router = GatewayRouter()
    health = router.handle_health()
    assert health["status"] == "healthy"
    assert health["gateway"] == "running"
    assert "personas" in health

    status = router.handle_status()
    assert status["status"] == "ok"
    assert status["gateway"] == "running"

    saksee = router.handle_saksee_status()
    assert saksee["gateway"] == "running"
    assert saksee["telegram"] == "connected"

    chat_out = router.handle_model_chat({"prompt": "Hello"})
    assert "[SakSee]" in chat_out["response"]


def test_router_handle_tools_execute_success(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello Gateway", encoding="utf-8")
    router = GatewayRouter()
    res = router.handle_tools_execute({"tool": "read_file", "arguments": {"path": str(test_file)}})
    assert res["status"] == "success"
    assert "Hello Gateway" in res["output"]


def test_router_handle_tools_execute_handler_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    router = GatewayRouter()
    from sakthai.agent.tools import Tool

    def failing_handler(args: Any, store: Any) -> str:
        raise RuntimeError("Handler failure")

    tool = Tool(name="failing_tool", description="Fails", input_schema={}, handler=failing_handler)
    monkeypatch.setattr("sakthai.gateway.router.BUILTIN_TOOLS", (tool,))

    res = router.handle_tools_execute({"tool": "failing_tool", "arguments": {}})
    assert res["status"] == "error"
    assert "Handler failure" in res["error"]


def test_router_handle_tools_execute_output_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    router = GatewayRouter()
    from sakthai.agent.tools import Tool

    tool = Tool(
        name="dangerous_output_tool",
        description="Emits drop table",
        input_schema={},
        handler=lambda args, store: "DROP TABLE users;",
    )
    monkeypatch.setattr("sakthai.gateway.router.BUILTIN_TOOLS", (tool,))

    res = router.handle_tools_execute({"tool": "dangerous_output_tool", "arguments": {}})
    assert res["status"] == "blocked"
    assert "approval_token_required" in res


def test_router_handle_chat_completion_streaming_with_generator_executor() -> None:
    def streaming_executor(**kwargs: Any) -> Any:
        def _gen():
            yield "part1 "
            yield "part2"

        return _gen()

    router = GatewayRouter(chat_executor=streaming_executor)
    res, is_stream = router.handle_chat_completion(
        {"messages": [{"role": "user", "content": "hi"}], "stream": True}
    )
    assert is_stream
    chunks = list(res)
    assert len(chunks) == 4  # part1, part2, stop, [DONE]


def test_router_handle_chat_completion_system_and_assistant_messages() -> None:
    router = GatewayRouter()
    res, is_stream = router.handle_chat_completion(
        {
            "messages": [
                {"role": "system", "content": "You are a test agent."},
                {"role": "assistant", "content": "Previous assistant turn."},
            ],
            "stream": False,
        }
    )
    assert not is_stream
    assert isinstance(res, dict)


def test_router_handle_tools_execute_non_string_arguments(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))
    test_file = tmp_path / "hello_int.txt"
    test_file.write_text("Integer arg test", encoding="utf-8")
    router = GatewayRouter()
    # Path is string, but timeout is int (exercises non-string argument branch in safety check)
    res = router.handle_tools_execute(
        {
            "tool": "read_file",
            "arguments": {"path": str(test_file), "offset": 0},
        }
    )
    assert res["status"] == "success"


def test_router_handle_chat_completion_non_dict_message_fallback() -> None:
    router = GatewayRouter()
    # Messages list containing non-dict items
    res, is_stream = router.handle_chat_completion(
        {
            "messages": ["not-a-dict", 123],  # type: ignore[list-item]
            "stream": False,
        }
    )
    assert not is_stream
    assert isinstance(res, dict)
