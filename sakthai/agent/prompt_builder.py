"""
Functions for building and rendering the agent's system prompt.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..skills import render_skills_prompt_block as _render_skills

if TYPE_CHECKING:
    from ..skills import SkillInfo

logger = logging.getLogger(__name__)


def render_skills_prompt_block(skills: Sequence[SkillInfo], caveman: str | None = None) -> str:
    """
    Renders the skills section of the system prompt.

    Args:
        skills: A sequence of SkillInfo objects.
        caveman: Optional caveman mode level.

    Returns:
        A string representing the skills block.
    """
    names = [s.name for s in skills]
    block = _render_skills(names)

    if caveman:
        # In a real implementation, this might load the caveman skill
        # and append its instructions. For now, we'll just add a placeholder
        # or simplified version if the caveman skill isn't easily accessible.
        block += f"\n\nACTIVE CAVEMAN LEVEL: {caveman}\nRespond using the rules of {caveman} level strictly."

    return block


def build_system_prompt(
    memory_block: str | None = None,
    skills_block: str | None = None,
    prefix: str | None = None,
    fast: bool = False,
) -> str:
    """
    Assembles the final system prompt from various components.
    """
    from .loop import SYSTEM_BASE

    parts = []
    if prefix and prefix.strip():
        parts.append(prefix.strip())
from __future__ import annotations

from typing import Any

from ..skills import render_skills_prompt_block as _render


def build_system_prompt(
    memory_block: str,
    skills_block: str,
    system_prompt_prefix: str | None = None,
    fast: bool = False,
) -> str:
    """Assemble the system prompt from various blocks."""
    from .loop import SYSTEM_BASE

    parts = []
    if system_prompt_prefix and system_prompt_prefix.strip():
        parts.append(system_prompt_prefix.strip())

    parts.append(SYSTEM_BASE)

    if fast:
        parts.append(
            "FAST-TRACK MODE: Execute the user's task directly and quickly without enforcing the 6-stage cycle (Dream/Hope/Care/Joy/Trust/Growth)."
        )

    if memory_block and memory_block.strip():
        parts.append(memory_block.strip())

    if skills_block and skills_block.strip():
        parts.append(skills_block.strip())

    return "\n\n".join(parts)
    if memory_block:
        parts.append(memory_block)

    if skills_block:
        parts.append(skills_block)

    return "\n\n".join(p for p in parts if p)


def render_skills_prompt_block(skills: Any, caveman: str | None = None) -> str:
    """Proxy to the actual skills renderer, handling both names and SkillInfo."""
    from ..skills import SkillInfo

    names: list[str] = []
    for s in skills or []:
        if isinstance(s, str):
            names.append(s)
        elif isinstance(s, SkillInfo):
            names.append(s.name)
        else:
            names.append(str(s))

    # Note: the caveman arg is currently ignored by the base renderer in skills.py
    # but we keep the signature for compatibility with context_manager.py
    return _render(names)


def build_skills_prompt_block(skills: Any) -> str:
    """Another alias used by some parts of the system."""
    return render_skills_prompt_block(skills)
