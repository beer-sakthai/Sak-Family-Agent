"""Tests for skill discovery and parsing logic in sakthai.skills."""
"""Tests for the skills management module (sakthai/skills.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.skills import (
    SkillParseError,
    _as_str_list,
    collect_skills,
    find_skill,
    list_skills,
    parse_skill,
    validate_skills,
)


def test_as_str_list() -> None:
    assert _as_str_list(["a", 1, None]) == ["a", "1", "None"]
    assert _as_str_list("not a list") == []
    assert _as_str_list(None) == []
    assert _as_str_list([]) == []


def test_parse_skill_happy_path(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    content = """---
name: test-skill
category: testing
description: A test skill
version: 1.2.3
platforms: [linux, macos]
metadata:
  sakthai:
    tags: [test, unit]
    related_skills: [other-skill]
---

# Skill Body
This is the body of the skill.
"""
    skill_md.write_text(content, encoding="utf-8")

    info = parse_skill(skill_md)
    assert info.name == "test-skill"
    assert info.path == skill_md
    assert info.category == "testing"
    assert info.description == "A test skill"
    assert info.version == "1.2.3"
    assert info.platforms == ["linux", "macos"]
    assert info.tags == ["test", "unit"]
    assert info.related_skills == ["other-skill"]
    assert info.body == "# Skill Body\nThis is the body of the skill."


def test_parse_skill_minimal(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    content = """---
name: minimal
---
Body content
"""
    skill_md.write_text(content, encoding="utf-8")

    info = parse_skill(skill_md)
    assert info.name == "minimal"
    assert info.body == "Body content"
    assert info.category is None
    assert info.tags == []


def test_parse_skill_no_frontmatter(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("Just some text, no frontmatter delimiters.", encoding="utf-8")
from sakthai import skills

    with pytest.raises(SkillParseError, match="no YAML frontmatter found"):
        parse_skill(skill_md)


def test_parse_skill_invalid_yaml(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ninvalid: yaml: :\n---\nbody", encoding="utf-8")
def _write_skill(root: Path, name: str, category: str | None = None, body: str = "Body.") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    content = f"---\nname: {name}\n"
    if category:
        content += f"category: {category}\n"
    content += f"---\n\n{body}\n"
    md.write_text(content, encoding="utf-8")
    return md

    with pytest.raises(SkillParseError, match="invalid YAML"):
        parse_skill(skill_md)


def test_parse_skill_not_a_dict(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\n- just a list\n---\nbody", encoding="utf-8")

    with pytest.raises(SkillParseError, match="empty or non-mapping frontmatter"):
        parse_skill(skill_md)


def test_parse_skill_missing_name(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ncategory: oops\n---\nbody", encoding="utf-8")

    with pytest.raises(SkillParseError, match="missing required field: name"):
        parse_skill(skill_md)


def test_parse_skill_empty_name(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nname: ''\n---\nbody", encoding="utf-8")

    with pytest.raises(SkillParseError, match="missing required field: name"):
        parse_skill(skill_md)


def test_list_skills(tmp_path: Path) -> None:
    (tmp_path / "skill1").mkdir()
    (tmp_path / "skill1" / "SKILL.md").write_text("---\nname: s1\n---\nb1", encoding="utf-8")
    (tmp_path / "skill2").mkdir()
    (tmp_path / "skill2" / "SKILL.md").write_text("---\nname: s2\n---\nb2", encoding="utf-8")
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
    (tmp_path / "not-a-dir").write_text("just a file", encoding="utf-8")

    skills = list_skills(tmp_path)
    assert len(skills) == 2
    assert [s.name for s in skills] == ["s1", "s2"]


def test_validate_skills(tmp_path: Path) -> None:
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "SKILL.md").write_text("---\nname: good\n---\nbody", encoding="utf-8")
    (tmp_path / "missing").mkdir()
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "SKILL.md").write_text("---\nname: ''\n---\nbody", encoding="utf-8")

    errors = validate_skills(tmp_path)
    assert len(errors) == 2
    # Convert paths to relative for easier assertion
    err_map = {p.name: msg for p, msg in errors}
    assert err_map["missing"] == "missing SKILL.md"
    assert err_map["SKILL.md"] == "missing required field: name"


def test_collect_skills_recursive(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "cat1").mkdir()
    (root / "cat1" / "skill-a").mkdir()
    (root / "cat1" / "skill-a" / "SKILL.md").write_text(
        "---\nname: skill-a\n---\nbody", encoding="utf-8"
    )

    (root / "cat2").mkdir()
    (root / "cat2" / "sub").mkdir()
    (root / "cat2" / "sub" / "skill-b").mkdir()
    (root / "cat2" / "sub" / "skill-b" / "SKILL.md").write_text(
        "---\nname: skill-b\n---\nbody", encoding="utf-8"
    )

    # Prefix-based category
    (root / "sakthai-coding-test").mkdir()
    (root / "sakthai-coding-test" / "SKILL.md").write_text(
        "---\nname: sakthai-coding-test\n---\nbody", encoding="utf-8"
    )

    skills = collect_skills(root)
    assert len(skills) == 3

    s_map = {s.name: s for s in skills}
    assert s_map["skill-a"].category == "cat1"
    assert s_map["skill-b"].category == "cat2"
    assert s_map["sakthai-coding-test"].category == "coding"


def test_find_skill(tmp_path: Path) -> None:
    (tmp_path / "s1").mkdir()
    (tmp_path / "s1" / "SKILL.md").write_text("---\nname: found-me\n---\nbody", encoding="utf-8")

    assert find_skill("found-me", tmp_path) is not None
    assert find_skill("missing", tmp_path) is None
def test_collect_skills_recursive(tmp_path: Path) -> None:
    """Verify that skills are found recursively under a root."""
    # Flat
    _write_skill(tmp_path, "flat-skill")
    # Nested
    nested = tmp_path / "subdir"
    nested.mkdir()
    _write_skill(nested, "nested-skill")

    found = skills.collect_skills(tmp_path)
    names = [s.name for s in found]
    assert "flat-skill" in names
    assert "nested-skill" in names
    assert len(found) == 2


def test_collect_skills_multiple_roots(tmp_path: Path) -> None:
    """Verify that skills are collected from multiple root directories."""
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    root1.mkdir()
    root2.mkdir()

    _write_skill(root1, "skill1")
    _write_skill(root2, "skill2")

    found = skills.collect_skills(root1, root2)
    assert len(found) == 2
    assert {s.name for s in found} == {"skill1", "skill2"}


def test_collect_skills_ignores_non_dir(tmp_path: Path) -> None:
    """Verify that non-directory roots are ignored by collect_skills."""
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("hello")

    found = skills.collect_skills(not_a_dir)
    assert len(found) == 0


def test_collect_skills_skips_duplicates(tmp_path: Path) -> None:
    """Verify that duplicate SKILL.md paths are only parsed once."""
    _write_skill(tmp_path, "dupe")
    # Same root twice
    found = skills.collect_skills(tmp_path, tmp_path)
    assert len(found) == 1


def test_collect_skills_suppresses_parse_errors(tmp_path: Path) -> None:
    """Verify that malformed SKILL.md files do not halt collection."""
    _write_skill(tmp_path, "good")
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "SKILL.md").write_text("invalid yaml ---", encoding="utf-8")

    found = skills.collect_skills(tmp_path)
    assert len(found) == 1
    assert found[0].name == "good"


def test_collect_skills_sorting(tmp_path: Path) -> None:
    """Verify that collected skills are sorted by name (case-insensitive)."""
    _write_skill(tmp_path, "b-skill")
    _write_skill(tmp_path, "a-skill")
    _write_skill(tmp_path, "C-skill")

    found = skills.collect_skills(tmp_path)
    assert [s.name for s in found] == ["a-skill", "b-skill", "C-skill"]


def test_category_for_logic(tmp_path: Path) -> None:
    """Verify the heuristic hierarchy for skill category assignment."""
    # 1. Explicit category
    md1 = _write_skill(tmp_path, "explicit", category="web")
    skill1 = skills.parse_skill(md1)
    assert skills._category_for(skill1, md1, tmp_path) == "web"

    # 2. Nesting directory (rel.parts >= 2)
    # root/category/skill/SKILL.md
    cat_dir = tmp_path / "tools"
    skill_dir = cat_dir / "my-skill"
    skill_dir.mkdir(parents=True)
    md2 = skill_dir / "SKILL.md"
    md2.write_text("---\nname: my-skill\n---\n", encoding="utf-8")
    skill2 = skills.parse_skill(md2)
    assert skills._category_for(skill2, md2, tmp_path) == "tools"

    # 3. Name prefix (sakthai-XXX-...)
    md3 = _write_skill(tmp_path, "sakthai-memory-log")
    skill3 = skills.parse_skill(md3)
    assert skills._category_for(skill3, md3, tmp_path) == "memory"

    # 4. Default uncategorized (general)
    md4 = _write_skill(tmp_path, "plain")
    skill4 = skills.parse_skill(md4)
    assert skills._category_for(skill4, md4, tmp_path) == "general"


def test_category_for_value_error_fallback(tmp_path: Path) -> None:
    """Verify fallback behavior when a skill file is outside the search root."""
    md = tmp_path / "some-skill" / "SKILL.md"
    md.parent.mkdir(parents=True)
    md.write_text("---\nname: some-skill\n---\n", encoding="utf-8")
    skill = skills.parse_skill(md)

    # Passing a different root to trigger ValueError in relative_to
    other_root = tmp_path / "other-root"
    other_root.mkdir()

    # It should fallback to Path(skill.name) which has parts length 1 (if flat)
    assert skills._category_for(skill, md, other_root) == "general"

    # If name has parts (path-like name)
    skill.name = "some/nested/name"
    assert skills._category_for(skill, md, other_root) == "some"


def test_collect_skills_empty_root(tmp_path: Path) -> None:
    """Verify that an empty root directory returns an empty list."""
    root = tmp_path / "empty"
    root.mkdir()
    assert skills.collect_skills(root) == []
