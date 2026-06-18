"""Tests for sakthai.agent.providers.base — shared data types and retry policy."""

from __future__ import annotations

import httpx
import pytest

import sakthai.agent.providers.base as base_mod
from sakthai.agent.providers.base import (
    Block,
    Response,
    block_field,
    find_tool_name_by_id,
    is_retryable,
    with_retry,
)

# -- Block -----------------------------------------------------------------


def test_block_defaults() -> None:
    b = Block("text")
    assert b.type == "text"
    assert b.text == ""
    assert b.id == ""
    assert b.name == ""
    assert b.input == {}


def test_block_explicit_fields() -> None:
    b = Block("tool_use", id="t1", name="learn", input={"k": "v"}, text="hi")
    assert b.type == "tool_use"
    assert b.id == "t1"
    assert b.name == "learn"
    assert b.input == {"k": "v"}
    assert b.text == "hi"


def test_block_none_input_becomes_empty_dict() -> None:
    b = Block("text", input=None)
    assert b.input == {}


# -- Response --------------------------------------------------------------


def test_response_defaults() -> None:
    r = Response("end_turn", [])
    assert r.stop_reason == "end_turn"
    assert r.content == []
    assert r.usage["input_tokens"] == 0
    assert r.usage["output_tokens"] == 0


def test_response_custom_usage() -> None:
    r = Response("tool_use", [], usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})
    assert r.usage["input_tokens"] == 10
    assert r.usage["output_tokens"] == 5


def test_response_none_usage_becomes_zeros() -> None:
    r = Response("end_turn", [], usage=None)
    assert r.usage["input_tokens"] == 0
    assert r.usage["output_tokens"] == 0


# -- is_retryable ----------------------------------------------------------


@pytest.mark.parametrize("status", [408, 409, 429, 500, 502, 503, 504])
def test_is_retryable_status_codes(status: int) -> None:
    exc = RuntimeError()
    exc.status_code = status  # type: ignore[attr-defined]
    assert is_retryable(exc)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_not_retryable_status_codes(status: int) -> None:
    exc = RuntimeError()
    exc.status_code = status  # type: ignore[attr-defined]
    assert not is_retryable(exc)


def test_is_retryable_httpx_transport_error() -> None:
    assert is_retryable(httpx.ConnectError("refused"))


def test_is_retryable_oserror() -> None:
    assert is_retryable(OSError("broken pipe"))


def test_is_retryable_via_code_attribute() -> None:
    exc = RuntimeError()
    exc.code = 503  # type: ignore[attr-defined]
    assert is_retryable(exc)


def test_is_retryable_via_response_status_code() -> None:
    class _FakeResp:
        status_code = 502

    exc = RuntimeError()
    exc.response = _FakeResp()  # type: ignore[attr-defined]
    assert is_retryable(exc)


def test_not_retryable_plain_exception() -> None:
    assert not is_retryable(ValueError("bad input"))


def test_not_retryable_no_status_attribute() -> None:
    assert not is_retryable(RuntimeError("generic"))


# -- with_retry ------------------------------------------------------------


def _zero_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero out retry wait times so tests don't sleep."""
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MULTIPLIER", 0)
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MAX", 0)


def test_with_retry_succeeds_first_try(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    calls: list[int] = []

    def fn() -> str:
        calls.append(1)
        return "ok"

    assert with_retry(fn) == "ok"
    assert len(calls) == 1


def test_with_retry_retries_transient_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    monkeypatch.setattr(base_mod, "RETRY_ATTEMPTS", 3)
    calls: list[int] = []

    def fn() -> str:
        calls.append(1)
        if len(calls) < 2:
            raise OSError("transient")
        return "recovered"

    assert with_retry(fn) == "recovered"
    assert len(calls) == 2


def test_with_retry_exhausts_attempts_and_reraises(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    monkeypatch.setattr(base_mod, "RETRY_ATTEMPTS", 3)

    def fn() -> str:
        raise OSError("always fails")

    with pytest.raises(OSError, match="always fails"):
        with_retry(fn)


def test_with_retry_non_retryable_raises_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    calls: list[int] = []

    def fn() -> None:
        calls.append(1)
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        with_retry(fn)

    assert len(calls) == 1


def test_with_retry_passes_positional_and_keyword_args(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)

    def fn(x: int, y: int = 0) -> int:
        return x + y

    assert with_retry(fn, 3, y=4) == 7


# -- block_field -----------------------------------------------------------


def test_block_field_dict_present() -> None:
    assert block_field({"type": "text", "text": "hello"}, "text") == "hello"


def test_block_field_dict_missing_uses_default() -> None:
    assert block_field({"type": "text"}, "missing", "default") == "default"


def test_block_field_object_attribute() -> None:
    class Obj:
        type = "tool_use"
        name = "learn"

    assert block_field(Obj(), "name") == "learn"


def test_block_field_object_missing_uses_default() -> None:
    class Obj:
        pass

    assert block_field(Obj(), "no_attr", 42) == 42


# -- find_tool_name_by_id --------------------------------------------------


def test_find_tool_name_by_id_found() -> None:
    messages = [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "learn", "input": {}}],
        }
    ]
    assert find_tool_name_by_id(messages, "t1") == "learn"


def test_find_tool_name_by_id_not_found() -> None:
    messages = [{"role": "user", "content": "hi"}]
    assert find_tool_name_by_id(messages, "missing") == "unknown"


def test_find_tool_name_by_id_wrong_id() -> None:
    messages = [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "learn", "input": {}}],
        }
    ]
    assert find_tool_name_by_id(messages, "t999") == "unknown"


def test_find_tool_name_by_id_string_content_skipped() -> None:
    messages = [{"role": "user", "content": "hi"}]
    assert find_tool_name_by_id(messages, "t1") == "unknown"


def test_find_tool_name_by_id_multiple_messages() -> None:
    messages = [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "learn", "input": {}}],
        },
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t2", "name": "recall", "input": {}}],
        },
    ]
    assert find_tool_name_by_id(messages, "t2") == "recall"
