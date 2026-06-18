from __future__ import annotations

from pathlib import Path
import pytest
from sakthai.skills import (
    SkillInfo,
    SkillParseError,
    parse_skill,
    list_skills,
    validate_skills,
    collect_skills,
    build_catalog,
    find_skill,
    validate_tree,
    _category_for
)

def write_skill(root: Path, folder: str, name: str, frontmatter: str = "", body: str = "body") -> Path:
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    skill_md = d / "SKILL.md"
    if not frontmatter:
        frontmatter = f"name: {name}\nversion: 1.0.0"
    skill_md.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")
    return skill_md

def test_parse_skill_valid(tmp_path: Path):
    path = write_skill(tmp_path, "skill1", "test-skill", "name: test-skill\nversion: 1.1.0\ndescription: desc\ncategory: cat\nplatforms: [linux]\nmetadata:\n  sakthai:\n    tags: [tag1]\n    related_skills: [other]")
    skill = parse_skill(path)
    assert skill.name == "test-skill"
    assert skill.version == "1.1.0"
    assert skill.description == "desc"
    assert skill.category == "cat"
    assert skill.platforms == ["linux"]
    assert skill.tags == ["tag1"]
    assert skill.related_skills == ["other"]
    assert skill.body == "body"

def test_parse_skill_invalid_yaml(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nname: : invalid\n---", encoding="utf-8")
    with pytest.raises(SkillParseError, match="invalid YAML"):
        parse_skill(skill_md)

def test_parse_skill_no_frontmatter(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("just text", encoding="utf-8")
    with pytest.raises(SkillParseError, match="no YAML frontmatter found"):
        parse_skill(skill_md)

def test_parse_skill_missing_name(tmp_path: Path):
    path = write_skill(tmp_path, "skill", "none", "version: 1.0.0")
    with pytest.raises(SkillParseError, match="missing required field: name"):
        parse_skill(path)

def test_list_skills(tmp_path: Path):
    write_skill(tmp_path, "beta", "beta")
    write_skill(tmp_path, "alpha", "alpha")
    # Invalid skill
    write_skill(tmp_path, "invalid", "none", "version: 1.0.0") # missing name
    # Not a skill dir
    (tmp_path / "not-a-dir").write_text("file")
    (tmp_path / "empty-dir").mkdir()

    skills = list_skills(tmp_path)
    assert len(skills) == 2
    assert skills[0].name == "alpha"
    assert skills[1].name == "beta"

def test_validate_skills(tmp_path: Path):
    write_skill(tmp_path, "valid", "valid")
    write_skill(tmp_path, "invalid", "none", "version: 1.0.0") # invalid
    (tmp_path / "missing").mkdir() # missing SKILL.md

    errors = validate_skills(tmp_path)
    # sorted by entry name
    assert len(errors) == 2
    assert "invalid/SKILL.md" in str(errors[0][0])
    assert "missing required field: name" in errors[0][1]
    assert "missing" in str(errors[1][0])
    assert "missing SKILL.md" in errors[1][1]

def test_category_resolution(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    # 1. Explicit category
    s1_path = write_skill(root, "dir/skill1", "skill1", "name: skill1\ncategory: explicit")
    s1 = parse_skill(s1_path)
    assert _category_for(s1, s1_path, root) == "explicit"

    # 2. Nesting dir
    s2_path = write_skill(root, "coding/skill2", "skill2")
    s2 = parse_skill(s2_path)
    assert _category_for(s2, s2_path, root) == "coding"

    # 3. Name prefix
    s3_path = write_skill(root, "skill3", "sakthai-memory-test")
    s3 = parse_skill(s3_path)
    assert _category_for(s3, s3_path, root) == "memory"

    # 4. General
    s4_path = write_skill(root, "skill4", "just-a-skill")
    s4 = parse_skill(s4_path)
    assert _category_for(s4, s4_path, root) == "general"

def test_collect_skills_recursive(tmp_path: Path):
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    write_skill(root1, "cat1/s1", "s1")
    write_skill(root2, "cat2/s2", "s2")

    skills = collect_skills(root1, root2)
    assert len(skills) == 2
    assert skills[0].name == "s1"
    assert skills[0].category == "cat1"
    assert skills[1].name == "s2"
    assert skills[1].category == "cat2"

def test_build_catalog(tmp_path: Path):
    root = tmp_path / "library"
    root.mkdir()
    write_skill(root, "coding/test", "test-skill", "name: test-skill\ndescription: d")

    catalog = build_catalog(root)
    assert len(catalog) == 1
    assert catalog[0]["category"] == "coding"
    assert catalog[0]["count"] == 1
    assert catalog[0]["skills"][0]["name"] == "test-skill"
    assert catalog[0]["skills"][0]["source"] == "library"

def test_find_skill(tmp_path: Path):
    root = tmp_path / "root"
    write_skill(root, "s1", "found-me")
    write_skill(root, "s2", "other")

    skill = find_skill("found-me", root)
    assert skill is not None
    assert skill.name == "found-me"

    assert find_skill("ghost", root) is None

def test_validate_tree(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    # 1. Valid skill
    write_skill(root, "valid", "valid")
    # 2. Folder with no SKILL.md
    (root / "empty-folder").mkdir()
    # 3. Invalid SKILL.md
    write_skill(root, "invalid", "none", "version: 1.0.0") # missing name

    errors = validate_tree(root)
    assert len(errors) == 2
    # Verify that both types of errors are present
    reasons = [e[1] for e in errors]
    assert "missing SKILL.md" in reasons
    assert "missing required field: name" in reasons
