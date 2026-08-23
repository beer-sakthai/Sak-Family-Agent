"""Tests for the self-healing one-shot completion adapter."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.selfheal import completion as completion_module
from sakthai.selfheal.completion import _extract_text, build_completion


class _Block:
    def __init__(self, block_type: str, text: str = "") -> None:
        self.type = block_type
        self.text = text


class _Response:
    def __init__(self, content: list[Any]) -> None:
        self.content = content


def test_extract_text_joins_text_blocks_and_ignores_the_rest() -> None:
    blocks = [_Block("text", "first"), _Block("tool_use"), _Block("text", "second")]

    assert _extract_text(blocks) == "first\nsecond"


def test_extract_text_reads_dict_shaped_blocks() -> None:
    assert _extract_text([{"type": "text", "text": "hello"}]) == "hello"


def test_extract_text_of_nothing_is_empty() -> None:
    assert _extract_text([]) == ""
    assert _extract_text(None) == ""


def test_google_model_routes_to_the_gemini_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_gemini(client, model, system, tools, messages, iteration, on_token=None):
        seen.update(model=model, system=system, messages=messages, tools=tools)
        return _Response([_Block("text", "gemini says hi")])

    monkeypatch.setattr(completion_module, "call_gemini", fake_gemini)

    complete = build_completion(model="gemini-3.1-flash-lite", client=object())

    assert complete("SYS", "USER") == "gemini says hi"
    assert seen["system"] == "SYS"
    assert seen["messages"] == [{"role": "user", "content": "USER"}]
    assert seen["tools"] == (), "the diagnosis call must not expose any tools"


def test_anthropic_model_routes_to_the_anthropic_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_anthropic(client, model, max_tokens, system, tool_schemas, messages, on_token=None):
        seen.update(max_tokens=max_tokens, tool_schemas=tool_schemas)
        return _Response([_Block("text", "claude says hi")])

    monkeypatch.setattr(completion_module, "call_anthropic", fake_anthropic)

    complete = build_completion(provider="anthropic", model="claude-opus-4-8", client=object())

    assert complete("SYS", "USER") == "claude says hi"
    assert seen["tool_schemas"] == []
    assert seen["max_tokens"] == completion_module.DEFAULT_MAX_TOKENS


def test_openai_compatible_model_routes_to_the_openai_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai(client, model, system, tools, messages, iteration, on_token=None):
        return _Response([_Block("text", "gpt says hi")])

    monkeypatch.setattr(completion_module, "call_openai_compat", fake_openai)

    complete = build_completion(provider="openai", model="gpt-4o", client=object())

    assert complete("SYS", "USER") == "gpt says hi"


def test_an_explicit_provider_overrides_model_name_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A gemini-named model served through a gateway must use the gateway path."""

    def fake_openai(client, model, system, tools, messages, iteration, on_token=None):
        return _Response([_Block("text", "via gateway")])

    monkeypatch.setattr(completion_module, "call_openai_compat", fake_openai)

    complete = build_completion(provider="gateway", model="gemini-3.1-flash-lite", client=object())

    assert complete("SYS", "USER") == "via gateway"


def test_max_tokens_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_anthropic(client, model, max_tokens, system, tool_schemas, messages, on_token=None):
        seen["max_tokens"] = max_tokens
        return _Response([])

    monkeypatch.setattr(completion_module, "call_anthropic", fake_anthropic)

    build_completion(provider="anthropic", model="m", client=object(), max_tokens=99)("s", "u")

    assert seen["max_tokens"] == 99
