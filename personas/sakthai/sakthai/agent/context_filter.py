"""
Context filtering and summarization strategies.

This module provides mechanisms to reduce the token count of conversational
history by summarizing or pruning parts of it, helping to keep the overall
context window manageable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)

SUMMARY_MARKER = "... [summarized]"


class ContextFilter(Protocol):
    """A protocol for context filtering strategies."""

    def filter(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Applies a filtering strategy to the list of messages.

        Args:
            messages: The list of messages in the conversation history.

        Returns:
            A potentially modified list of messages.
        """
        ...


class TurnSummarizationFilter:
    """
    A context filter that compacts older conversational turns.

    Everything but the most recent two messages is compacted; the last turn is
    always left intact. Compaction has two modes:

    * With a ``summarizer`` — the injected seam for a smaller, faster model.
      It receives the full text and returns a summary. A summarizer that
      raises, returns a non-string, or fails to actually shorten the text
      falls back to truncation, so a flaky helper can never grow the context
      or break a run.
    * Without one — deterministic truncation to ``max_length`` characters
      followed by :data:`SUMMARY_MARKER`.

    Compaction reaches the places history actually accumulates: plain string
    content, ``text`` blocks, and ``tool_result`` blocks. The last of those
    matters most — file reads and command output are the largest turns in a
    tool-using run, and they only ever appear as blocks, never as a bare
    string.

    Content blocks that are not plain dicts (e.g. a provider's ``Block``
    objects on an assistant turn) are passed through untouched: rewriting them
    would mean mutating objects the caller still holds.

    Input messages are never mutated — a compacted turn is returned as a copy.
    """

    def __init__(
        self,
        max_length: int = 500,
        summarizer: Callable[[str], str] | None = None,
    ):
        self.max_length = max_length
        self.summarizer = summarizer

    def filter(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compacts long content in the older part of the history."""
        if len(messages) <= 2:  # Keep the last turn intact
            return messages

        filtered_messages: list[dict[str, Any]] = []
        for msg in messages[:-2]:
            content = msg.get("content")
            compacted = self._compact_content(content)
            # `_compact_content` returns the same object when nothing changed,
            # so an untouched message is appended as-is rather than copied.
            if compacted is content:
                filtered_messages.append(msg)
            else:
                filtered_messages.append({**msg, "content": compacted})

        filtered_messages.extend(messages[-2:])  # Add last turn back
        return filtered_messages

    def _compact_content(self, content: Any) -> Any:
        """Compacts a message's content, returning it unchanged if it is short."""
        if isinstance(content, str):
            return self._compact_text(content)
        if isinstance(content, list):
            blocks = [self._compact_block(block) for block in content]
            if all(new is old for new, old in zip(blocks, content, strict=True)):
                return content
            return blocks
        return content

    def _compact_block(self, block: Any) -> Any:
        """Compacts one content block, returning it unchanged if it is short."""
        if not isinstance(block, dict):
            return block

        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str):
                compacted = self._compact_text(text)
                if compacted is not text:
                    return {**block, "text": compacted}
        elif block_type == "tool_result":
            # A tool_result's payload is a string for the built-in tools, but
            # the protocol also allows a nested list of blocks.
            content = self._compact_content(block.get("content"))
            if content is not block.get("content"):
                return {**block, "content": content}
        return block

    def _compact_text(self, text: str) -> str:
        """Summarizes or truncates ``text``, returning it unchanged if short."""
        if len(text) <= self.max_length:
            return text
        if self.summarizer is not None:
            try:
                summary = self.summarizer(text)
            except Exception:  # noqa: BLE001 — a failed summary must not fail the run
                logger.warning("Context summarizer raised; truncating instead.", exc_info=True)
            else:
                if isinstance(summary, str) and len(summary) < len(text):
                    return summary
                logger.warning("Context summarizer did not shorten text; truncating instead.")
        return text[: self.max_length] + SUMMARY_MARKER


DEFAULT_CONTEXT_FILTER = TurnSummarizationFilter()
