"""
Context filtering and summarization strategies.

This module provides mechanisms to reduce the token count of conversational
history by summarizing or pruning parts of it, helping to keep the overall
context window manageable.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Protocol

logger = logging.getLogger(__name__)


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
    A context filter that summarizes older conversational turns.

    This is a placeholder for a more sophisticated implementation that might
    use a smaller, faster model to summarize turns. For now, it demonstrates
    the principle by truncating long messages.
    """

    def __init__(self, max_length: int = 500):
        self.max_length = max_length

    def filter(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Truncates long messages in the history."""
        if len(messages) <= 2:  # Keep the last turn intact
            return messages

        filtered_messages = []
        for msg in messages[:-2]:
            # A real implementation would summarize with an LLM
            if isinstance(msg.get("content"), str) and len(msg["content"]) > self.max_length:
                msg["content"] = msg["content"][: self.max_length] + "... [summarized]"
            filtered_messages.append(msg)

        filtered_messages.extend(messages[-2:])  # Add last turn back
        return filtered_messages


DEFAULT_CONTEXT_FILTER = TurnSummarizationFilter()