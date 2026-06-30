"""Tests for skill module loading and parsing."""

from __future__ import annotations

from pathlib import Path

import dspy
import pytest
from evolution.skills.skill_module import SkillModule, find_skill, load_skill, reassemble_skill

SAMPLE_SKILL = """---
name: test-skill
description: A skill for testing things
version: 1.0.0
metadata:
  hermes:
    tags: [testing]
---

# Test Skill — Testing Things

## When to Use
Use this when you need to test things.

## Procedure
1. First, do the thing
2. Then, verify it worked
3. Report results

## Pitfalls
- Don't forget to check edge cases
"""


class TestLoadSkill:
    def test_parses_frontmatter(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)
        skill = load_skill(skill_file)

        assert skill["name"] == "test-skill"
        assert skill["description"] == "A skill for testing things"
        assert "version: 1.0.0" in skill["frontmatter"]

    def test_parses_body(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)
        skill = load_skill(skill_file)

        assert "# Test Skill" in skill["body"]
        assert "## Procedure" in skill["body"]
        assert "Don't forget" in skill["body"]

    def test_raw_contains_everything(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)
        skill = load_skill(skill_file)

        assert skill["raw"] == SAMPLE_SKILL

    def test_path_is_stored(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)
        skill = load_skill(skill_file)

        assert skill["path"] == skill_file


class TestReassembleSkill:
    def test_roundtrip(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)
        skill = load_skill(skill_file)

        reassembled = reassemble_skill(skill["frontmatter"], skill["body"])
        assert "---" in reassembled
        assert "name: test-skill" in reassembled
        assert "# Test Skill" in reassembled

    def test_preserves_frontmatter(self) -> None:
        frontmatter = "name: my-skill\ndescription: Does stuff"
        body = "# My Skill\nDo the thing."
        result = reassemble_skill(frontmatter, body)

        assert result.startswith("---\n")
        assert "name: my-skill" in result
        assert "# My Skill" in result

    def test_evolved_body_replaces_original(self) -> None:
        frontmatter = "name: my-skill\ndescription: Does stuff"
        evolved_body = "# EVOLVED\nNew and improved procedure."
        result = reassemble_skill(frontmatter, evolved_body)

        assert "EVOLVED" in result
        assert "New and improved" in result

    def test_exact_formatting(self) -> None:
        frontmatter = "name: test"
        body = "body text"
        result = reassemble_skill(frontmatter, body)
        # Expected: f"---\n{frontmatter}\n---\n\n{body}\n"
        expected = "---\nname: test\n---\n\nbody text\n"
        assert result == expected

    def test_empty_components(self) -> None:
        # Reassemble with empty strings should still follow the format
        result = reassemble_skill("", "")
        assert result == "---\n\n---\n\n\n"

    def test_reassemble_and_load_roundtrip(self, tmp_path: Path) -> None:
        frontmatter = "name: roundtrip\ndescription: testing load"
        body = "# Roundtrip Body"
        reassembled = reassemble_skill(frontmatter, body)

        skill_file = tmp_path / "ROUNDTRIP.md"
        skill_file.write_text(reassembled)

        reparsed = load_skill(skill_file)
        assert reparsed["name"] == "roundtrip"
        assert reparsed["description"] == "testing load"
        assert reparsed["body"] == body
        assert reparsed["frontmatter"] == frontmatter

class TestFindSkill:
    def test_returns_none_if_no_path(self) -> None:
        assert find_skill("test-skill", None) is None

    def test_returns_none_if_skills_dir_missing(self, tmp_path: Path) -> None:
        assert find_skill("test-skill", tmp_path) is None

    def test_direct_match(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skill_folder = skills_dir / "my-cool-skill"
        skill_folder.mkdir(parents=True)
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text("--- \nname: my-cool-skill\n---")

        found = find_skill("my-cool-skill", tmp_path)
        assert found == skill_file

    def test_fuzzy_match_frontmatter(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skill_folder = skills_dir / "random-folder"
        skill_folder.mkdir(parents=True)
        skill_file = skill_folder / "SKILL.md"
        # Name in frontmatter is different from folder name
        skill_file.write_text('---\nname: "fuzzy-skill"\n---')

        found = find_skill("fuzzy-skill", tmp_path)
        assert found == skill_file

    def test_fuzzy_match_unquoted(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skill_folder = skills_dir / "other-folder"
        skill_folder.mkdir(parents=True)
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text("---\nname: unquoted-skill\n---")

        found = find_skill("unquoted-skill", tmp_path)
        assert found == skill_file

    def test_missing_skill(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        assert find_skill("non-existent", tmp_path) is None

class TestSkillModule:
    def test_initialization(self) -> None:
        skill_text = "Instructions for the task."
        module = SkillModule(skill_text)

        # Check that the instructions were correctly seeded
        assert module.skill_text == skill_text

    def test_forward_basic(self) -> None:
        # Mock the predictor's call to avoid real LLM interaction
        skill_text = "Test skill body"
        module = SkillModule(skill_text)

        # We'll use a dummy output for the predictor
        dummy_output = "This is the mocked output"

        # DSPy predictors are callable. We can patch the predictor instance.
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.output = dummy_output
        module.predictor = MagicMock(return_value=mock_response)

        result = module.forward("Do something")
        assert result.output == dummy_output
        module.predictor.assert_called_once_with(task_input="Do something")
