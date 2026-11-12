# tests/test_agent_platform_customizations.py
from pathlib import Path

import pytest

from sakthai.agent_platform.customizations import CustomizationRegistry


def test_skill_discovery_progressive_disclosure(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills" / "demo-skill"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: demo-skill\ndescription: Demonstrates progressive skill disclosure\n---\n"
        "# Detailed Instructions\nStep 1: Execute demo\nStep 2: Verify outcome\n"
    )

    registry = CustomizationRegistry(workspace_root=tmp_path)
    summaries = registry.list_available_skills()
    assert len(summaries) == 1
    assert summaries[0].name == "demo-skill"
    assert summaries[0].description == "Demonstrates progressive skill disclosure"

    # Explicit on-demand activation loads full body
    full_content = registry.load_skill("demo-skill")
    assert "Detailed Instructions" in full_content
    assert "Step 1: Execute demo" in full_content


def test_hierarchical_rules_discovery(tmp_path: Path):
    root_rule = tmp_path / "AGENTS.md"
    root_rule.write_text("Enforce snake_case for all Python variables.")
    subdir = tmp_path / "src" / "sub"
    subdir.mkdir(parents=True)
    sub_rule = subdir / "AGENTS.md"
    sub_rule.write_text("All API models must use Pydantic V2.")

    registry = CustomizationRegistry(workspace_root=tmp_path)
    rules = registry.resolve_rules_for_path(subdir / "module.py")
    assert len(rules) == 2
    assert "Enforce snake_case" in rules[0].content
    assert "All API models must use Pydantic V2" in rules[1].content


def test_skill_fallback_description_and_missing_error(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills" / "plain-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("# Title\n\nThis is a fallback skill description.\n")

    registry = CustomizationRegistry(workspace_root=tmp_path)
    summaries = registry.list_available_skills()
    assert len(summaries) == 1
    assert summaries[0].description == "This is a fallback skill description."

    with pytest.raises(KeyError, match="not found in registry"):
        registry.load_skill("nonexistent-skill")


def test_resolve_rules_for_directory_path(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("Root directory rule.")
    subdir = tmp_path / "somedir"
    subdir.mkdir()

    registry = CustomizationRegistry(workspace_root=tmp_path)
    rules = registry.resolve_rules_for_path(subdir)
    assert len(rules) == 1
    assert "Root directory rule" in rules[0].content
