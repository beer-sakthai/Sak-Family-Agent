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
        {
            "role": "assistant",
            "content": "d" * 1000,
        },  # Part of last 2 messages (will not be truncated)
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


def test_summarization_filter_does_not_mutate_input() -> None:
    # The caller (sakthai chat) keeps holding the history it passes in, so the
    # filter must copy rather than rewrite the message dicts in place.
    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "assistant", "content": "b" * 1000},
        {"role": "user", "content": "c" * 10},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    assert messages[0]["content"] == "a" * 1000
    assert result[0]["content"] != messages[0]["content"]


def test_summarization_filter_compacts_tool_result_blocks() -> None:
    # Tool results (file reads, command output) are the largest turns in a
    # tool-using run and only ever appear as blocks, never as a bare string.
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tu_1",
                    "content": "x" * 1000,
                    "is_error": False,
                }
            ],
        },
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "next"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    block = result[0]["content"][0]
    assert block["content"] == "x" * 500 + "... [summarized]"
    # Sibling keys on the block survive the rewrite.
    assert block["tool_use_id"] == "tu_1"
    assert block["is_error"] is False


def test_summarization_filter_compacts_text_blocks() -> None:
    messages = [
        {"role": "assistant", "content": [{"type": "text", "text": "y" * 1000}]},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    assert result[0]["content"][0]["text"] == "y" * 500 + "... [summarized]"


def test_summarization_filter_compacts_nested_tool_result_blocks() -> None:
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tu_1",
                    "content": [{"type": "text", "text": "z" * 1000}],
                }
            ],
        },
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    assert result[0]["content"][0]["content"][0]["text"] == "z" * 500 + "... [summarized]"


def test_summarization_filter_leaves_non_dict_blocks_alone() -> None:
    # Provider `Block` objects on an assistant turn are still held by the
    # caller; rewriting them would mean mutating shared objects.
    class FakeBlock:
        type = "text"
        text = "q" * 1000

    block = FakeBlock()
    messages = [
        {"role": "assistant", "content": [block]},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    assert result[0]["content"][0] is block
    assert block.text == "q" * 1000


def test_summarization_filter_uses_summarizer_when_given() -> None:
    seen: list[str] = []

    def summarize(text: str) -> str:
        seen.append(text)
        return "SUMMARY"

    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500, summarizer=summarize)
    result = filt.filter(messages)

    assert result[0]["content"] == "SUMMARY"
    assert seen == ["a" * 1000]  # summarizer sees the full text, not a prefix


def test_summarization_filter_skips_summarizer_for_short_content() -> None:
    def summarize(text: str) -> str:  # pragma: no cover - must never be called
        raise AssertionError("summarizer called for short content")

    messages = [
        {"role": "user", "content": "short"},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500, summarizer=summarize)
    assert filt.filter(messages)[0]["content"] == "short"


def test_summarization_filter_falls_back_when_summarizer_raises() -> None:
    def summarize(text: str) -> str:
        raise RuntimeError("model unavailable")

    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500, summarizer=summarize)
    result = filt.filter(messages)

    assert result[0]["content"] == "a" * 500 + "... [summarized]"


def test_summarization_filter_falls_back_when_summary_is_not_shorter() -> None:
    # A summarizer that returns a non-string, or text no shorter than the
    # original, must not be allowed to grow the context.
    messages = [
        {"role": "user", "content": "a" * 1000},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    truncated = "a" * 500 + "... [summarized]"

    longer = TurnSummarizationFilter(max_length=500, summarizer=lambda text: "L" * 2000)
    assert longer.filter(messages)[0]["content"] == truncated

    not_a_string = TurnSummarizationFilter(max_length=500, summarizer=lambda text: None)  # type: ignore[arg-type,return-value]
    assert not_a_string.filter(messages)[0]["content"] == truncated


def test_summarization_filter_passes_through_unhandled_shapes() -> None:
    # Content and blocks the filter has no compaction rule for must survive
    # untouched rather than being dropped or raising.
    messages = [
        {"role": "user", "content": None},
        {
            "role": "assistant",
            "content": [
                # A block type with no compaction rule.
                {"type": "tool_use", "id": "tu_1", "name": "read_file", "input": {"path": "x"}},
                # A text block whose `text` is not a string.
                {"type": "text", "text": {"unexpected": "shape"}},
                # A tool_result short enough to leave alone.
                {"type": "tool_result", "tool_use_id": "tu_1", "content": "ok"},
            ],
        },
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    filt = TurnSummarizationFilter(max_length=500)
    result = filt.filter(messages)

    assert result == messages
    # Nothing changed, so the untouched turns are the very same objects.
    assert result[0] is messages[0]
    assert result[1] is messages[1]
