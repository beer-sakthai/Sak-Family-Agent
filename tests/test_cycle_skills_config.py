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


# -- cycle fallback on corrupt stored value ------------------------------


def test_get_stage_falls_back_on_invalid_stored_value(store: MemoryStore) -> None:
    # Simulate an invalid stage name written to the DB (e.g. from a future
    # version that adds a new stage, or plain DB corruption).
    store.add_fact("NOT_A_VALID_STAGE", kind="cycle", key="current_stage")
    assert get_current_stage(store) == Stage.DREAM


def test_parse_skill_invalid_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "SKILL.md"
    bad.write_text("---\nname: alpha\ninvalid: [unclosed\n---\nBody.", encoding="utf-8")
    with pytest.raises(skills.SkillParseError) as exc:
        skills.parse_skill(bad)
    assert "invalid YAML" in str(exc.value)


def test_parse_skill_non_mapping_frontmatter(tmp_path: Path) -> None:
    bad = tmp_path / "SKILL.md"
    bad.write_text("---\n- item1\n- item2\n---\nBody.", encoding="utf-8")
    with pytest.raises(skills.SkillParseError) as exc:
        skills.parse_skill(bad)
    assert "non-mapping frontmatter" in str(exc.value)


def test_parse_skill_missing_name(tmp_path: Path) -> None:
    bad = tmp_path / "SKILL.md"
    bad.write_text("---\ndescription: missing name\n---\nBody.", encoding="utf-8")
    with pytest.raises(skills.SkillParseError) as exc:
        skills.parse_skill(bad)
    assert "missing required field: name" in str(exc.value)


def test_validate_skills(tmp_path: Path) -> None:
    # 1. Valid skill
    _write_skill(tmp_path, "valid")

    # 2. Folder with missing SKILL.md
    (tmp_path / "missing-skill").mkdir()

    # 3. Broken skill (bad frontmatter)
    broken_dir = tmp_path / "broken"
    broken_dir.mkdir()
    broken_md = broken_dir / "SKILL.md"
    broken_md.write_text("bad text", encoding="utf-8")

    # 4. Non-directory file to trigger line 85 skip
    (tmp_path / "regular_file.txt").write_text("not a dir", encoding="utf-8")

    errors = skills.validate_skills(tmp_path)
    assert len(errors) == 2
    paths = [p for p, _ in errors]
    assert tmp_path / "missing-skill" in paths
    assert broken_md in paths


def test_category_for_edge_cases(tmp_path: Path) -> None:
    # Rel path has < 2 parts and prefix-based category mapping
    skill = skills.SkillInfo(
        name="sakthai-memory-test", path=tmp_path / "sakthai-memory-test" / "SKILL.md"
    )
    cat = skills._category_for(skill, skill.path, tmp_path)
    assert cat == "memory"

    # Prefix not matching pattern
    skill_misc = skills.SkillInfo(name="nonstandard", path=tmp_path / "nonstandard" / "SKILL.md")
    assert skills._category_for(skill_misc, skill_misc.path, tmp_path) == "general"

    # Trigger ValueError in relative_to and check fallback category (lines 103-104)
    skill_outside = skills.SkillInfo(name="sakthai-outside-test", path=Path("/other/path/SKILL.md"))
    cat_outside = skills._category_for(skill_outside, skill_outside.path, tmp_path)
    assert cat_outside == "outside"


def test_collect_skills_duplicates(tmp_path: Path) -> None:
    # Ensure duplicates are skipped when collecting from multiple overlapping roots
    _write_skill(tmp_path, "dupe")
    found = skills.collect_skills(tmp_path, tmp_path)
    assert len(found) == 1
    assert found[0].name == "dupe"


def test_source_for(tmp_path: Path) -> None:
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    root1.mkdir()
    root2.mkdir()

    s1 = _write_skill(root1, "skill1")
    s2 = _write_skill(root2, "skill2")

    assert skills._source_for(s1, (root1, root2)) == "root1"
    assert skills._source_for(s2, (root1, root2)) == "root2"
    assert skills._source_for(tmp_path / "outside" / "SKILL.md", (root1, root2)) == ""


def test_validate_tree_corrupt_and_ignored(tmp_path: Path) -> None:
    # 1. Ignored dot directory
    (tmp_path / ".ignored").mkdir()

    # 2. Corrupt YAML error caught in validate_tree
    bad_dir = tmp_path / "bad-skill"
    bad_dir.mkdir()
    bad_md = bad_dir / "SKILL.md"
    bad_md.write_text("bad text", encoding="utf-8")

    # 3. Test non-existent root directory (line 217 skip)
    errors_non_existent = skills.validate_tree(tmp_path / "non-existent")
    assert len(errors_non_existent) == 0

    # 4. Duplicate SKILL.md paths skip (line 225 skip)
    _write_skill(tmp_path, "unique-skill")
    errors = skills.validate_tree(tmp_path, tmp_path)
    # The errors list still contains only the bad-skill (from the first root parsing)
    assert len(errors) == 1
    assert errors[0][0] == bad_md
    assert "no YAML frontmatter found" in errors[0][1]
