"""Tests for prompt building logic (sakthai.agent.prompt_builder)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

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


def test_render_skills_prompt_block_caveman_skill_body_injected(sakthai_home: Path) -> None:
    skill_dir = sakthai_home.parent / "gemini" / "extensions" / "caveman" / "skills" / "caveman"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: caveman\ndescription: test caveman desc\n---\n\nRespond terse.\n",
        encoding="utf-8",
    )

    block = render_skills_prompt_block([], caveman="ultra")

    assert "Respond terse." in block
    assert "ACTIVE CAVEMAN LEVEL: ultra" in block
    assert "Respond using the rules of ultra level strictly." in block


def test_render_skills_prompt_block_caveman_skill_missing_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import sakthai.agent.prompt_builder as pb

    monkeypatch.setattr(pb, "find_skill", lambda *_a: None)

    with caplog.at_level("WARNING", logger="sakthai.agent.prompt_builder"):
        block = render_skills_prompt_block([], caveman="full")

    assert "ACTIVE CAVEMAN LEVEL: full" in block
    assert any("Caveman skill not found" in rec.message for rec in caplog.records)


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
        memory_block=memory_block, skills_block=skills_block, prefix=prefix, fast=True
    )

    # All components should be joined by double newlines
    assert prompt.startswith(prefix)
    assert "FAST-TRACK MODE" in prompt
    assert memory_block in prompt
    assert skills_block in prompt
