"""Tests for context management logic (sakthai.agent.context_manager)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from sakthai.agent.context_manager import ContextManager


def test_context_manager_assemble_prompt(sakthai_home: Path) -> None:
    # Plant a caveman skill so the caveman branch injects its body + directive
    skill_dir = sakthai_home.parent / "gemini" / "extensions" / "caveman" / "skills" / "caveman"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: caveman\ndescription: test caveman desc\n---\n\nRespond terse.\n",
        encoding="utf-8",
    )

    # Set up mock memory provider
    mock_memory_provider = MagicMock()
    mock_memory_provider.system_prompt_block.return_value = "Mocked Memory block"

    # Set up mock context filter
    mock_filter = MagicMock()
    mock_filter.filter.side_effect = lambda x: list(x)  # identity filter

    manager = ContextManager(memory_provider=mock_memory_provider, context_filter=mock_filter)

    task = "Do the task"
    history = [{"role": "user", "content": "hello"}]
    skills = [MagicMock(name="dummy")]

    system_prompt, messages = manager.assemble_prompt(
        task=task,
        history=history,
        skills=skills,
        system_prompt_prefix="My prefix",
        caveman="ultra",
        fast=True,
    )

    # Verify memory provider was called
    mock_memory_provider.system_prompt_block.assert_called_once()

    # Verify context filter was called
    mock_filter.filter.assert_called_once_with(history)

    # Verify system prompt components
    assert "My prefix" in system_prompt
    assert "Mocked Memory block" in system_prompt
    assert "Respond terse." in system_prompt
    assert "ACTIVE CAVEMAN LEVEL: ultra" in system_prompt
    assert "FAST-TRACK MODE" in system_prompt

    # Verify final messages list contains history + the task
    assert len(messages) == 2
    assert messages[0] == history[0]
    assert messages[1] == {"role": "user", "content": task}
