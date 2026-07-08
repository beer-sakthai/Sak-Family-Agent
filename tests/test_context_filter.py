"""Tests for context filtering logic (sakthai.agent.context_filter)."""

from __future__ import annotations

from sakthai.agent.context_filter import TurnSummarizationFilter


def test_summarization_filter_preserves_short_history() -> None:
    # History of 2 or fewer messages should not be altered, regardless of length
    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "assistant", "content": "b" * 1000},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)
    assert result == messages


def test_summarization_filter_truncates_old_messages() -> None:
    # History of >2 messages: older ones should be truncated, newer ones kept intact
    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "assistant", "content": "b" * 200},
        {"role": "user", "content": "c" * 1000},  # Part of last 2 messages (will not be truncated)
        {"role": "assistant", "content": "d" * 1000},  # Part of last 2 messages (will not be truncated)
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    # First message: was long, is in messages[:-2], should be truncated
    assert len(result[0]["content"]) == 500 + len("... [summarized]")
    assert result[0]["content"].endswith("... [summarized]")

    # Second message: was short, is in messages[:-2], should be untouched
    assert result[1]["content"] == "b" * 200

    # Third and fourth messages: in the last two messages, should be completely untouched
    assert result[2]["content"] == "c" * 1000
    assert result[3]["content"] == "d" * 1000


def test_summarization_filter_ignores_non_string_content() -> None:
    # Non-string content like block lists should be passed through without errors
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "foo"}]},
        {"role": "assistant", "content": "bar"},
        {"role": "user", "content": "baz"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)
    assert result == messages
