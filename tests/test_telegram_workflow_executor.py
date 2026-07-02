"""Tests for the Telegram workflow executor bootstrap seam."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sakthai.telegram import workflow_executor


def test_get_available_workflows_uses_configured_skills_dir(
    tmp_path: Path, monkeypatch
) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "beta").mkdir()
    (skills_dir / "alpha").mkdir()
    (skills_dir / "ignored.txt").write_text("ignore me", encoding="utf-8")

    monkeypatch.setattr(workflow_executor, "SKILLS_DIR", skills_dir)

    assert workflow_executor.get_available_workflows() == ["alpha", "beta"]


def test_get_available_workflows_missing_dir_returns_empty(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(workflow_executor, "SKILLS_DIR", tmp_path / "missing-skills")

    assert workflow_executor.get_available_workflows() == []


def test_workflow_command_uses_current_interpreter() -> None:
    command = workflow_executor._workflow_command("alpha")
    assert command[0] == sys.executable
    assert command[1:4] == ["-m", "sakthai", "run"]
    assert command[-2:] == ["--fast", "--stateless"]


def test_run_workflow_executes_skill_with_current_interpreter(
    tmp_path: Path, monkeypatch
) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "alpha").mkdir()
    monkeypatch.setattr(workflow_executor, "SKILLS_DIR", skills_dir)

    captured: dict[str, object] = {}

    class _Process:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"workflow ok", b""

    async def _fake_subprocess_exec(*args: str, **kwargs: object) -> _Process:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _Process()

    monkeypatch.setattr(workflow_executor.asyncio, "create_subprocess_exec", _fake_subprocess_exec)

    result = asyncio.run(workflow_executor.run_workflow("alpha"))

    assert "executed successfully" in result
    assert captured["args"][0] == sys.executable
    assert "--stateless" in captured["args"]
