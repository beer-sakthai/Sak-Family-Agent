"""Tests for skill discovery and parsing logic in sakthai.skills."""

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

    with pytest.raises(SkillParseError, match="no YAML frontmatter found"):
        parse_skill(skill_md)


def test_parse_skill_invalid_yaml(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ninvalid: yaml: :\n---\nbody", encoding="utf-8")

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
from sakthai.skills import SkillParseError, collect_skills, parse_skill


def _write_skill(root: Path, name: str, body: str = "Body.", category: str | None = None) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    frontmatter = f"name: {name}\n"
    if category:
        frontmatter += f"category: {category}\n"
    frontmatter += "description: a skill\nversion: 1.0.0\n"

    md.write_text(
        f"---\n{frontmatter}---\n\n{body}\n",
        encoding="utf-8",
    )
    return md


def test_collect_skills_recursive(tmp_path: Path) -> None:
    # Flat structure
    _write_skill(tmp_path, "alpha")
    # Nested structure
    nested = tmp_path / "subdir"
    nested.mkdir()
    _write_skill(nested, "beta")

    found = collect_skills(tmp_path)
    assert len(found) == 2
    names = {s.name for s in found}
    assert names == {"alpha", "beta"}


def test_collect_skills_multiple_roots(tmp_path: Path) -> None:
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    root1.mkdir()
    root2.mkdir()

    _write_skill(root1, "alpha")
    _write_skill(root2, "beta")

    found = collect_skills(root1, root2)
    assert len(found) == 2
    assert {s.name for s in found} == {"alpha", "beta"}


def test_collect_skills_skips_non_directory(tmp_path: Path) -> None:
    fake_root = tmp_path / "not_a_dir"
    # Should not raise, just skip
    assert collect_skills(fake_root) == []


def test_collect_skills_duplicates_skipped(tmp_path: Path) -> None:
    # Same root passed twice
    _write_skill(tmp_path, "alpha")
    found = collect_skills(tmp_path, tmp_path)
    assert len(found) == 1


def test_collect_skills_skips_malformed(tmp_path: Path) -> None:
    _write_skill(tmp_path, "good")
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "SKILL.md").write_text("not a yaml frontmatter", encoding="utf-8")

    found = collect_skills(tmp_path)
    assert len(found) == 1
    assert found[0].name == "good"


def test_collect_skills_sorting(tmp_path: Path) -> None:
    _write_skill(tmp_path, "b")
    _write_skill(tmp_path, "A")
    _write_skill(tmp_path, "a")

    found = collect_skills(tmp_path)
    # Sorting is (name.lower(), str(path))
    names = [s.name for s in found]
    assert names[0].lower() == "a"
    assert names[1].lower() == "a"
    assert names[2].lower() == "b"


def test_collect_skills_sorting_by_path(tmp_path: Path) -> None:
    root1 = tmp_path / "z_root"
    root2 = tmp_path / "a_root"
    root1.mkdir()
    root2.mkdir()
    _write_skill(root1, "same")
    _write_skill(root2, "same")

    found = collect_skills(root1, root2)
    assert len(found) == 2
    assert found[0].name == "same"
    assert found[1].name == "same"
    # a_root/same/SKILL.md should come before z_root/same/SKILL.md
    assert "a_root" in str(found[0].path)
    assert "z_root" in str(found[1].path)


def test_collect_skills_category_assignment(tmp_path: Path) -> None:
    # Explicit category
    _write_skill(tmp_path, "explicit", category="web")

    # Nesting dir category (2 parts: tools/git/SKILL.md relative to root)
    # root is tmp_path
    tools = tmp_path / "tools"
    git = tools / "git"
    git.mkdir(parents=True)
    (git / "SKILL.md").write_text(
        "---\nname: git-commit\ndescription: d\n---\nBody", encoding="utf-8"
    )

    # Prefix category (sakthai-memory-test -> memory)
    _write_skill(tmp_path, "sakthai-memory-test")

    found = collect_skills(tmp_path)
    by_name = {s.name: s for s in found}

    assert by_name["explicit"].category == "web"
    assert by_name["git-commit"].category == "tools"
    assert by_name["sakthai-memory-test"].category == "memory"


def test_parse_skill_basic(tmp_path: Path) -> None:
    md = _write_skill(tmp_path, "test-skill", body="Content")
    skill = parse_skill(md)
    assert skill.name == "test-skill"
    assert skill.body == "Content"


def test_parse_skill_errors(tmp_path: Path) -> None:
    bad = tmp_path / "SKILL.md"

    # No frontmatter
    bad.write_text("No fence", encoding="utf-8")
    with pytest.raises(SkillParseError, match="no YAML frontmatter found"):
        parse_skill(bad)

    # Invalid YAML
    bad.write_text("---\nname: [\n---\nBody", encoding="utf-8")
    with pytest.raises(SkillParseError, match="invalid YAML"):
        parse_skill(bad)

    # Not a mapping
    bad.write_text("---\n- not\n- a\n- map\n---\nBody", encoding="utf-8")
    with pytest.raises(SkillParseError, match="empty or non-mapping frontmatter"):
        parse_skill(bad)

    # Missing name
    bad.write_text("---\ndescription: no name\n---\nBody", encoding="utf-8")
    with pytest.raises(SkillParseError, match="missing required field: name"):
        parse_skill(bad)
