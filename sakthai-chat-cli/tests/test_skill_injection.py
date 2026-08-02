"""Tests for skill injection: render_skills_prompt_block + default_skill_roots."""

from __future__ import annotations

from pathlib import Path

from sakthai import skills as skills_mod
from sakthai.skills import default_skill_roots, render_skills_prompt_block


def _write_skill(root: Path, name: str, body: str, *, description: str = "d") -> None:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\nversion: 1.0.0\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_render_selected_skill_bodies(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", "ALPHA INSTRUCTIONS")
    _write_skill(tmp_path, "beta", "BETA INSTRUCTIONS")
    block = render_skills_prompt_block(["alpha"], roots=[tmp_path])
    assert "## Active skills" in block
    assert "### alpha" in block
    assert "ALPHA INSTRUCTIONS" in block
    assert "BETA INSTRUCTIONS" not in block  # only the selected skill


def test_render_skips_unknown_names(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", "A")
    block = render_skills_prompt_block(["alpha", "ghost"], roots=[tmp_path])
    assert "### alpha" in block
    assert "ghost" not in block


def test_render_empty_when_no_names_or_no_match(tmp_path: Path) -> None:
    assert render_skills_prompt_block([], roots=[tmp_path]) == ""
    assert render_skills_prompt_block(["nope"], roots=[tmp_path]) == ""


def test_default_skill_roots_includes_extensions(sakthai_home: Path) -> None:
    roots = default_skill_roots()
    assert skills_mod.SKILLS_DIR in roots
    assert sakthai_home / "extensions" in roots
