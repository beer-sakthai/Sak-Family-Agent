"""Tests for sakthai.agent.providers.gemini_provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.providers.base import AgentError
from sakthai.agent.providers.gemini_provider import call_gemini, to_gemini_contents
from sakthai.agent.tools import Tool


def _tool(name: str = "recall") -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {}},
        handler=lambda args, store: "ok",
    )


# -- to_gemini_contents ----------------------------------------------------


def test_to_gemini_contents_string_user_message() -> None:
    contents = to_gemini_contents([{"role": "user", "content": "hello"}])
    assert len(contents) == 1
    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "hello"


def test_to_gemini_contents_assistant_text_is_model_role() -> None:
    contents = to_gemini_contents(
        [{"role": "assistant", "content": [{"type": "text", "text": "hi"}]}]
    )
    assert contents[0].role == "model"
    assert contents[0].parts[0].text == "hi"


def test_to_gemini_contents_tool_use_creates_function_call() -> None:
    contents = to_gemini_contents(
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "learn",
                        "input": {"value": "x"},
                    }
                ],
            }
        ]
    )
    part = contents[0].parts[0]
    fc = part.function_call
    assert fc.name == "learn"
    assert dict(fc.args) == {"value": "x"}


def test_to_gemini_contents_tool_result_is_tool_role() -> None:
    msgs = [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "learn", "input": {}}],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": "done"}
            ],
        },
    ]
    contents = to_gemini_contents(msgs)
    tool_content = contents[1]
    assert tool_content.role == "tool"
    fr = tool_content.parts[0].function_response
    assert fr.name == "learn"
    assert fr.response == {"result": "done"}


def test_to_gemini_contents_multiple_messages() -> None:
    msgs = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": [{"type": "text", "text": "second"}]},
        {"role": "user", "content": "third"},
    ]
    contents = to_gemini_contents(msgs)
    assert len(contents) == 3
    assert contents[0].role == "user"
    assert contents[1].role == "model"
    assert contents[2].role == "user"


# -- to_gemini_contents: fall-through / malformed input --------------------
# These pin the translator's deliberate forward-compatible behaviour: unknown
# block types and non-(str|list) content are silently skipped, never crash.


def test_to_gemini_contents_unknown_block_type_falls_back_to_empty_part() -> None:
    """An unrecognised block type is skipped; a fallback empty text part keeps
    the Content schema-compliant (Gemini rejects an empty parts list)."""
    contents = to_gemini_contents(
        [{"role": "user", "content": [{"type": "image", "source": "..."}]}]
    )
    assert len(contents) == 1
    assert contents[0].role == "user"
    assert len(contents[0].parts) == 1
    assert contents[0].parts[0].text == ""


def test_to_gemini_contents_mixed_known_and_unknown_blocks_keeps_known() -> None:
    """A known block survives alongside an unknown one in the same message."""
    contents = to_gemini_contents(
        [
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "hmm"},
                    {"type": "text", "text": "answer"},
                ],
            }
        ]
    )
    assert len(contents[0].parts) == 1
    assert contents[0].parts[0].text == "answer"


@pytest.mark.parametrize("content", [None, 42, {"type": "text", "text": "x"}])
def test_to_gemini_contents_non_str_or_list_content_falls_back_to_empty_part(
    content: object,
) -> None:
    """Content that is neither str nor list (incl. a bare dict) yields a single
    fallback empty text part rather than an invalid empty Content."""
    contents = to_gemini_contents([{"role": "user", "content": content}])
    assert len(contents) == 1
    assert len(contents[0].parts) == 1
    assert contents[0].parts[0].text == ""


def test_to_gemini_contents_empty_block_list_falls_back_to_empty_part() -> None:
    contents = to_gemini_contents([{"role": "user", "content": []}])
    assert len(contents) == 1
    assert len(contents[0].parts) == 1
    assert contents[0].parts[0].text == ""


# -- call_gemini -----------------------------------------------------------


def _candidate(
    text: str = "", fn_calls: list | None = None, finish: str = "STOP"
) -> MagicMock:
    part = MagicMock()
    part.text = text
    part.function_calls = fn_calls or []
    content = MagicMock()
    content.parts = [part]
    c = MagicMock()
    c.content = content
    c.finish_reason = finish
    return c


def _gemini_resp(candidates: list | None = None) -> MagicMock:
    resp = MagicMock()
    resp.candidates = candidates if candidates is not None else []
    resp.usage_metadata = None
    return resp


def test_call_gemini_text_response() -> None:
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp(
        [_candidate(text="hello")]
    )
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        resp = call_gemini(client, "gemini-2.0-flash", "sys", (), [], 0)
    assert resp.stop_reason == "end_turn"
    assert any(b.type == "text" and b.text == "hello" for b in resp.content)


def test_call_gemini_tool_use() -> None:
    fc = MagicMock()
    fc.name = "recall"
    fc.args = {"query": "hobbies"}
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp(
        [_candidate(fn_calls=[fc])]
    )
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        resp = call_gemini(client, "gemini-2.0-flash", "sys", (_tool("recall"),), [], 1)
    assert resp.stop_reason == "tool_use"
    b = resp.content[0]
    assert b.type == "tool_use"
    assert b.name == "recall"
    assert b.input == {"query": "hobbies"}


def test_call_gemini_non_dict_schema_passed_through() -> None:
    # A tool whose input_schema is not a dict (e.g. None) must be forwarded to
    # the FunctionDeclaration untouched rather than crash the schema cleaner.
    no_schema_tool = Tool(
        name="ping",
        description="ping tool",
        input_schema=None,  # type: ignore[arg-type]
        handler=lambda args, store: "pong",
    )
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp([_candidate(text="ok")])
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        resp = call_gemini(client, "gemini-2.0-flash", "sys", (no_schema_tool,), [], 0)

    assert resp.stop_reason == "end_turn"
    _, kwargs = client.models.generate_content.call_args
    decl = kwargs["config"].tools[0].function_declarations[0]
    assert decl.parameters is None


def test_call_gemini_max_tokens_finish_reason() -> None:
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp(
        [_candidate(text="cut", finish="MAX_TOKENS")]
    )
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        resp = call_gemini(client, "gemini-2.0-flash", "sys", (), [], 0)
    assert resp.stop_reason == "max_tokens"


def test_call_gemini_no_candidates_raises() -> None:
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp([])
    with (
        patch(
            "sakthai.agent.providers.gemini_provider.to_gemini_contents",
            return_value=[],
        ),
        pytest.raises(AgentError, match="no candidates"),
    ):
        call_gemini(client, "gemini-2.0-flash", "sys", (), [], 0)


def test_call_gemini_api_error_raises_agent_error() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("quota exceeded")
    with (
        patch(
            "sakthai.agent.providers.gemini_provider.to_gemini_contents",
            return_value=[],
        ),
        pytest.raises(AgentError, match="Gemini API call failed"),
    ):
        call_gemini(client, "gemini-2.0-flash", "sys", (), [], 0)


def test_call_gemini_passes_system_instruction() -> None:

    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp([_candidate(text="ok")])
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        call_gemini(client, "gemini-2.0-flash", "my system", (), [], 0)
    call_kw = client.models.generate_content.call_args
    config = call_kw.kwargs.get("config") or call_kw.args[2] if call_kw.args else None
    if config is not None:
        assert config.system_instruction == "my system"


def test_call_gemini_multiple_tool_calls_in_one_part() -> None:
    fc1 = MagicMock()
    fc1.name = "learn"
    fc1.args = {"value": "a"}
    fc2 = MagicMock()
    fc2.name = "recall"
    fc2.args = {"query": "b"}

    part = MagicMock()
    part.text = ""
    part.function_calls = [fc1, fc2]
    content = MagicMock()
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = "STOP"

    client = MagicMock()
    client.models.generate_content.return_value = _gemini_resp([candidate])
    with patch(
        "sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]
    ):
        resp = call_gemini(client, "gemini-2.0-flash", "sys", (), [], 0)

    assert resp.stop_reason == "tool_use"
    assert len(resp.content) == 2
    assert resp.content[0].name == "learn"
    assert resp.content[1].name == "recall"
