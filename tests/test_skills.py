"""Tests for the skills management module (sakthai/skills.py)."""

from __future__ import annotations

from pathlib import Path

from sakthai import skills


def _write_skill(root: Path, name: str, category: str | None = None, body: str = "Body.") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    content = f"---\nname: {name}\n"
    if category:
        content += f"category: {category}\n"
    content += f"---\n\n{body}\n"
    md.write_text(content, encoding="utf-8")
import pytest

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
