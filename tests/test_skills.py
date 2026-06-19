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
    render_skills_prompt_block,
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


def test_render_skills_prompt_block_empty() -> None:

    assert render_skills_prompt_block([]) == ""


def test_render_skills_prompt_block_missing(tmp_path: Path) -> None:

    assert render_skills_prompt_block(["missing"], roots=[tmp_path]) == ""


def test_render_skills_prompt_block_success(tmp_path: Path) -> None:

    (tmp_path / "skill1").mkdir()
    (tmp_path / "skill1" / "SKILL.md").write_text(
        "---\nname: skill1\ndescription: Desc 1\n---\nBody 1", encoding="utf-8"
    )
    (tmp_path / "skill2").mkdir()
    (tmp_path / "skill2" / "SKILL.md").write_text(
        "---\nname: skill2\n---\nBody 2", encoding="utf-8"
    )
    (tmp_path / "skill3").mkdir()
    (tmp_path / "skill3" / "SKILL.md").write_text(
        "---\nname: skill3\ndescription: Desc 3\n---\n", encoding="utf-8"
    )

    rendered = render_skills_prompt_block(
        ["skill1", "skill2", "skill3", "missing"], roots=[tmp_path]
    )

    expected = (
        "## Active skills\n\n"
        "### skill1 — Desc 1\n\n"
        "Body 1\n\n"
        "### skill2\n\n"
        "Body 2\n\n"
        "### skill3 — Desc 3"
    )
    assert rendered == expected


def test_default_skill_roots(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.skills import LIBRARY_DIR, SKILLS_DIR, default_skill_roots

    # Ensure GEMINI_HOME is NOT set for the first part
    monkeypatch.delenv("GEMINI_HOME", raising=False)

    roots = default_skill_roots()
    assert SKILLS_DIR in roots
    assert LIBRARY_DIR in roots
    assert (sakthai_home / "extensions") in roots

    # Test with GEMINI_HOME
    gemini_home = sakthai_home.parent / "gemini_home"
    gemini_ext = gemini_home / "extensions"
    gemini_ext.mkdir(parents=True)
    monkeypatch.setenv("GEMINI_HOME", str(gemini_home))

    roots = default_skill_roots()
    assert gemini_ext in roots


def test_render_skills_prompt_block_default_roots(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # extensions dir in sakthai_home is one of the default roots
    ext_dir = sakthai_home / "extensions"
    ext_dir.mkdir()
    skill_dir = ext_dir / "myskill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: myskill\n---\nHello", encoding="utf-8")

    # render_skills_prompt_block with roots=None should find it
    rendered = render_skills_prompt_block(["myskill"], roots=None)
    assert "### myskill" in rendered
    assert "Hello" in rendered


def test_build_catalog(tmp_path: Path) -> None:
    from sakthai.skills import build_catalog

    root = tmp_path / "root"
    root.mkdir()
    (root / "cat1").mkdir()
    (root / "cat1" / "s1").mkdir()
    (root / "cat1" / "s1" / "SKILL.md").write_text(
        "---\nname: s1\nversion: 1.0\ndescription: d1\n---\nbody1", encoding="utf-8"
    )

    catalog = build_catalog(root)
    assert len(catalog) == 1
    assert catalog[0]["category"] == "cat1"
    assert catalog[0]["count"] == 1
    assert catalog[0]["skills"][0]["name"] == "s1"
    assert catalog[0]["skills"][0]["source"] == "root"


def test_validate_tree(tmp_path: Path) -> None:
    from sakthai.skills import validate_tree

    root = tmp_path / "root"
    root.mkdir()

    # Valid skill
    (root / "good").mkdir()
    (root / "good" / "SKILL.md").write_text("---\nname: good\n---\nbody", encoding="utf-8")

    # Missing SKILL.md in a folder
    (root / "empty_folder").mkdir()

    # Hidden folder (should be skipped)
    (root / ".hidden").mkdir()

    # Malformed SKILL.md
    (root / "bad").mkdir()
    (root / "bad" / "SKILL.md").write_text("---\nname: \n---\nbody", encoding="utf-8")

    errors = validate_tree(root, tmp_path / "not_a_dir")
    err_map = {str(p.relative_to(root)) if root in p.parents else str(p): msg for p, msg in errors}

    assert "empty_folder" in err_map
    assert err_map["empty_folder"] == "missing SKILL.md"
    assert ".hidden" not in err_map
    assert "bad/SKILL.md" in err_map
    assert "missing required field: name" in err_map["bad/SKILL.md"]


def test_source_for(tmp_path: Path) -> None:
    from sakthai.skills import _source_for

    root1 = tmp_path / "root1"
    root1.mkdir()
    root2 = tmp_path / "root2"
    root2.mkdir()

    skill_md = root1 / "s1" / "SKILL.md"
    skill_md.parent.mkdir()
    skill_md.touch()

    assert _source_for(skill_md, (root1, root2)) == "root1"
    assert _source_for(skill_md, (root2,)) == ""


def test_category_for_precedence(tmp_path: Path) -> None:
    from sakthai.skills import SkillInfo, _category_for

    root = tmp_path / "root"
    root.mkdir()
    skill_md = root / "some" / "path" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)

    skill = SkillInfo(name="test", path=skill_md, category="explicit")
    assert _category_for(skill, skill_md, root) == "explicit"


def test_category_for_fallback(tmp_path: Path) -> None:
    from sakthai.skills import SkillInfo, _category_for

    # Test ValueError branch in _category_for (when skill_md is not under root)
    root = tmp_path / "root"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    skill_md = other / "skill" / "SKILL.md"
    skill_md.parent.mkdir()

    skill = SkillInfo(name="fallback-name", path=skill_md)
    # It should use Path(skill.name) which is "fallback-name"
    assert _category_for(skill, skill_md, root) == "general"

    # Test with sakthai- prefix
    skill2 = SkillInfo(name="sakthai-coding-foo", path=skill_md)
    assert _category_for(skill2, skill_md, root) == "coding"


def test_collect_skills_edge_cases(tmp_path: Path) -> None:
    # Non-directory root
    not_a_dir = tmp_path / "not_a_dir"
    not_a_dir.touch()
    assert collect_skills(not_a_dir) == []

    # Duplicate prevention (seen set)
    root = tmp_path / "root"
    root.mkdir()
    (root / "s1").mkdir()
    skill_md = root / "s1" / "SKILL.md"
    skill_md.write_text("---\nname: s1\n---\nbody", encoding="utf-8")

    # Pass the same root twice
    skills = collect_skills(root, root)
    assert len(skills) == 1


def test_validate_skills_non_dir(tmp_path: Path) -> None:
    from sakthai.skills import validate_skills

    (tmp_path / "not-a-dir").write_text("file")
    errors = validate_skills(tmp_path)
    # Should skip the file, so no errors
    assert errors == []


def test_validate_tree_duplicates(tmp_path: Path) -> None:
    from sakthai.skills import validate_tree

    root = tmp_path / "root"
    root.mkdir()
    (root / "s1").mkdir()
    skill_md = root / "s1" / "SKILL.md"
    skill_md.write_text("---\nname: s1\n---\nbody", encoding="utf-8")

    # Pass the same root twice; line 234 "continue" should be hit
    errors = validate_tree(root, root)
    assert errors == []
