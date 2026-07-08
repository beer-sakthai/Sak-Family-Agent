"""Tests for prompt building logic (sakthai.agent.prompt_builder)."""

from __future__ import annotations

from unittest.mock import MagicMock

from sakthai.agent.prompt_builder import build_system_prompt, render_skills_prompt_block


def test_render_skills_prompt_block() -> None:
    # Set up mock skills
    skill1 = MagicMock()
    skill1.name = "skill-one"
    skill2 = MagicMock()
    skill2.name = "skill-two"

    # Render without caveman
    block = render_skills_prompt_block([skill1, skill2])
    # The actual _render_skills in sakthai.skills will look for these skills in library/skills dir,
    # but we can verify it contains or processes the input names/block correctly.
    assert isinstance(block, str)

    # Render with caveman
    block_caveman = render_skills_prompt_block([skill1, skill2], caveman="lite")
    assert "ACTIVE CAVEMAN LEVEL: lite" in block_caveman
    assert "Respond using the rules of lite level strictly." in block_caveman


def test_build_system_prompt_basic() -> None:
    prompt = build_system_prompt()
    # Should include base system instructions
    from sakthai.agent.loop import SYSTEM_BASE
    assert SYSTEM_BASE in prompt


def test_build_system_prompt_all_options() -> None:
    prefix = "Custom Prefix Here"
    memory_block = "User prefers Python."
    skills_block = "Active skills: git, grep"

    prompt = build_system_prompt(
        memory_block=memory_block,
        skills_block=skills_block,
        prefix=prefix,
        fast=True
    )

    # All components should be joined by double newlines
    assert prompt.startswith(prefix)
    assert "FAST-TRACK MODE" in prompt
    assert memory_block in prompt
    assert skills_block in prompt
