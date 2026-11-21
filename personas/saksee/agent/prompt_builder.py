"""
Functions for building and rendering the agent's system prompt.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..skills import default_skill_roots, find_skill
from ..skills import render_skills_prompt_block as _render_skills

if TYPE_CHECKING:
    from ..skills import SkillInfo

logger = logging.getLogger(__name__)

# 5 Core Evolvable Prompt Sections
DEFAULT_AGENT_IDENTITY = (
    "You are SakThai, a personal agent that lives in the user's terminal. You have "
    "persistent memory (`learn`, `recall`, `search`, `forget`), read access to the "
    "local filesystem (`read_file`), and opt-in shell execution (`run_command`). "
    "Read existing facts before answering anything that may depend on them, and honor "
    "stated preferences silently. Prefer running CLI tasks yourself with `run_command` over "
    "asking the user to run commands."
)

MEMORY_GUIDANCE = (
    "Persistent Memory Guidance:\n"
    "- Read existing facts before answering questions that may depend on them.\n"
    "- Save new facts with `learn` only when the user shares durable preferences, project decisions, "
    "or environment constraints worth recalling in future sessions.\n"
    "- Never save transient conversation chatter or intermediate task outputs."
)

SESSION_SEARCH_GUIDANCE = (
    "Session Search Guidance:\n"
    "- When the user references previous conversations, past agreements, or uses phrases like "
    "'like last time', 'as we discussed earlier', or 'what did we do before', search past sessions "
    "using `search`.\n"
    "- Retrieve context before answering."
)

SKILLS_GUIDANCE = (
    "Skills Guidance:\n"
    "- Load and inspect relevant skills before starting complex workflows.\n"
    "- Follow the step-by-step procedures outlined in active skill instructions.\n"
    "- When recurring workflows are identified, formulate and save reusable procedures."
)

PLATFORM_HINTS = (
    "Platform Hints (Terminal):\n"
    "- Output clear, GitHub-flavored markdown with code fences for snippets.\n"
    "- Keep explanations concise and direct; favor working commands and concrete diffs over verbose exposition."
)


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
        caveman_skill = find_skill("caveman", *default_skill_roots())
        if caveman_skill:
            block += (
                f"\n\n{caveman_skill.body}\n\nACTIVE CAVEMAN LEVEL: {caveman}\n"
                f"Respond using the rules of {caveman} level strictly."
            )
        else:
            logger.warning("Caveman skill not found; compression mode disabled.")

    return block


def build_system_prompt(
    memory_block: str | None = None,
    skills_block: str | None = None,
    prefix: str | None = None,
    fast: bool = False,
    identity: str | None = None,
    memory_guidance: str | None = None,
    session_guidance: str | None = None,
    skills_guidance: str | None = None,
    platform_hints: str | None = None,
) -> str:
    """
    Assembles the final system prompt from various components.
    """
    from .loop import SYSTEM_BASE

    parts = []
    if prefix and prefix.strip():
        parts.append(prefix.strip())

    parts.append(identity.strip() if identity and identity.strip() else SYSTEM_BASE)

    if fast:
        parts.append(
            "FAST-TRACK MODE: Execute the user's task directly and quickly without enforcing the 6-stage cycle (Dream/Hope/Care/Joy/Trust/Growth)."
        )

    if memory_guidance and memory_guidance.strip():
        parts.append(memory_guidance.strip())

    if session_guidance and session_guidance.strip():
        parts.append(session_guidance.strip())

    if skills_guidance and skills_guidance.strip():
        parts.append(skills_guidance.strip())

    if platform_hints and platform_hints.strip():
        parts.append(platform_hints.strip())

    if memory_block and memory_block.strip():
        parts.append(memory_block.strip())

    if skills_block and skills_block.strip():
        parts.append(skills_block.strip())

    return "\n\n".join(parts)
