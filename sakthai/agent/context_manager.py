"""
Manages the assembly of context for the agent's prompt.

This module provides a `ContextManager` class that is responsible for
intelligently constructing the system prompt and message history, applying
filtering and summarization to keep the context window efficient.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..memory.provider import SakThaiMemoryProvider
from ..skills import SkillInfo
from .context_filter import DEFAULT_CONTEXT_FILTER, ContextFilter
from .prompt_builder import (
    build_system_prompt,
    render_skills_prompt_block,
)


class ContextManager:
    """Assembles and manages the context for an agent run."""

    def __init__(
        self,
        memory_provider: SakThaiMemoryProvider,
        context_filter: ContextFilter = DEFAULT_CONTEXT_FILTER,
    ):
        self.memory_provider = memory_provider
        self.context_filter = context_filter

    def assemble_prompt(
        self,
        task: str,
        history: list[dict[str, Any]],
        skills: Sequence[SkillInfo] | None = None,
        system_prompt_prefix: str | None = None,
        caveman: str | None = None,
        fast: bool = False,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Assembles the final system prompt and message list.

        Args:
            task: The user's current task.
            history: The existing conversation history.
            skills: A list of active skills.
            system_prompt_prefix: A prefix for the system prompt (e.g., persona).
            caveman: The caveman mode for token compression.
            fast: Whether to use fast-track mode.

        Returns:
            A tuple of (system_prompt, messages).
        """
        memory_block = self.memory_provider.render_prompt_block()
        skills_block = render_skills_prompt_block(skills or [], caveman)
        system_prompt = build_system_prompt(memory_block, skills_block, system_prompt_prefix, fast)

        messages = self.context_filter.filter(history)
        messages.append({"role": "user", "content": task})

        return system_prompt, messages
