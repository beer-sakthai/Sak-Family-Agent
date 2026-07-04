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
