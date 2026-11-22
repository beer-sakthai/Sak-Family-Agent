"""Standalone agent loop and the tools it can call."""

from __future__ import annotations

from .tools import BUILTIN_TOOLS, Tool, tool_by_name
from .writing_assistant import (
    DEFAULT_WRITING_CONFIG_KEY,
    DEFAULT_WRITING_INSTRUCTIONS,
    WritingAssistantConfig,
    WritingAssistantResult,
    generate_writing,
    generate_writing_with_agentcontrol,
    get_writing_assistant_config,
    inspect_writing_config,
)

__all__ = [
    "BUILTIN_TOOLS",
    "DEFAULT_WRITING_CONFIG_KEY",
    "DEFAULT_WRITING_INSTRUCTIONS",
    "Tool",
    "WritingAssistantConfig",
    "WritingAssistantResult",
    "generate_writing",
    "generate_writing_with_agentcontrol",
    "get_writing_assistant_config",
    "inspect_writing_config",
    "tool_by_name",
]
