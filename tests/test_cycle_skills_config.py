"""Tests for the cycle state machine, skill parsing, and config checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai import config, skills
from sakthai.cycle import Stage, advance_stage, get_current_stage, next_stage, set_stage
from sakthai.memory.store import MemoryStore

# -- cycle ---------------------------------------------------------------


def test_cycle_defaults_to_dream(store: MemoryStore) -> None:
    assert get_current_stage(store) == Stage.DREAM


def test_cycle_set_and_advance(store: MemoryStore) -> None:
    set_stage(store, Stage.CARE)
    assert get_current_stage(store) == Stage.CARE
    assert advance_stage(store) == Stage.JOY
    assert get_current_stage(store) == Stage.JOY


def test_next_stage_wraps() -> None:
    assert next_stage(Stage.GROWTH) == Stage.DREAM


def test_set_stage_overwrites_single_row(store: MemoryStore) -> None:
    set_stage(store, Stage.HOPE)
    set_stage(store, Stage.TRUST)
    assert get_current_stage(store) == Stage.TRUST
    assert sum(1 for f in store.list_facts() if f.kind == "cycle") == 1


# -- skills --------------------------------------------------------------


def _write_skill(root: Path, name: str, body: str = "Body.") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    md = skill_dir / "SKILL.md"
    md.write_text(
        f"---\nname: {name}\ndescription: a {name} skill\nversion: 1.0.0\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return md


def test_parse_and_list_skills(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha")
    _write_skill(tmp_path, "beta")
    found = skills.list_skills(tmp_path)
    assert [s.name for s in found] == ["alpha", "beta"]
    assert found[0].description == "a alpha skill"


def test_parse_skill_requires_frontmatter(tmp_path: Path) -> None:
    bad = tmp_path / "SKILL.md"
    bad.write_text("no frontmatter here", encoding="utf-8")
    with pytest.raises(skills.SkillParseError):
        skills.parse_skill(bad)


def test_build_catalog_and_find_skill(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha")
    catalog = skills.build_catalog(tmp_path)
    assert catalog[0]["count"] == 1
    assert skills.find_skill("alpha", tmp_path).name == "alpha"
    assert skills.find_skill("missing", tmp_path) is None


def test_validate_tree_flags_missing(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    errors = skills.validate_tree(tmp_path)
    assert any("missing SKILL.md" in msg for _, msg in errors)


# -- config --------------------------------------------------------------


def test_paths_honour_sakthai_home(sakthai_home: Path) -> None:
    assert config.sakthai_home() == sakthai_home
    assert config.memory_db_path() == sakthai_home / "memory.db"


def test_check_env_structure(sakthai_home: Path) -> None:
    report = config.check_env()
    assert set(report) >= {"paths", "env", "memory", "skills", "auth", "ready"}
    assert "ANTHROPIC_API_KEY" in report["env"]
    # No DB yet → still considered ready (created lazily on first use).
    assert report["ready"] is True
