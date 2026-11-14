from pathlib import Path

import pytest

from app.agent_platform.customizations import (
    CustomizationRegistry,
)


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
    # Verify full instructions are not loaded during summary phase
    assert (
        not hasattr(summaries[0], "full_body") or summaries[0].description != skill_file.read_text()
    )

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


def test_gemini_skills_and_alphabetical_order(tmp_path: Path):
    agents_dir = tmp_path / ".agents" / "skills" / "z-skill"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text(
        "---\nname: z-skill\ndescription: Z skill description\n---\nBody"
    )

    gemini_dir = tmp_path / ".gemini" / "skills" / "a-skill"
    gemini_dir.mkdir(parents=True)
    (gemini_dir / "SKILL.md").write_text(
        "---\nname: a-skill\ndescription: A skill description\n---\nBody"
    )

    registry = CustomizationRegistry(workspace_root=tmp_path)
    summaries = registry.list_available_skills()
    assert len(summaries) == 2
    assert [s.name for s in summaries] == ["a-skill", "z-skill"]


def test_skill_description_fallback_and_missing_skill(tmp_path: Path):
    skill_dir = tmp_path / ".agents" / "skills" / "no-frontmatter"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Heading\n\nThis is a fallback summary line.\nMore body.")

    registry = CustomizationRegistry(workspace_root=tmp_path)
    summaries = registry.list_available_skills()
    assert len(summaries) == 1
    assert summaries[0].name == "no-frontmatter"
    assert summaries[0].description == "This is a fallback summary line."

    with pytest.raises(KeyError, match="not found in registry"):
        registry.load_skill("non-existent-skill")


def test_hierarchical_rules_gemini_and_scope(tmp_path: Path):
    root_agents = tmp_path / "AGENTS.md"
    root_agents.write_text("Global Agents Rule")
    root_gemini = tmp_path / "GEMINI.md"
    root_gemini.write_text("Global Gemini Rule")

    nested_dir = tmp_path / "services" / "payment"
    nested_dir.mkdir(parents=True)
    nested_gemini = nested_dir / "GEMINI.md"
    nested_gemini.write_text("Payment Gemini Rule")

    registry = CustomizationRegistry(workspace_root=tmp_path)
    rules = registry.resolve_rules_for_path(nested_dir)
    assert len(rules) == 3
    scopes = [r.scope for r in rules]
    assert scopes == ["AGENTS.md", "GEMINI.md", "services/payment/GEMINI.md"]
    assert rules[0].content == "Global Agents Rule"
    assert rules[1].content == "Global Gemini Rule"
    assert rules[2].content == "Payment Gemini Rule"


def test_resolve_rules_outside_workspace(tmp_path: Path):
    outside_dir = tmp_path.parent / "outside_dir"
    outside_dir.mkdir(exist_ok=True)
    registry = CustomizationRegistry(workspace_root=tmp_path)
    rules = registry.resolve_rules_for_path(outside_dir / "file.py")
    assert rules == []


def test_resolve_rules_with_dotted_directory(tmp_path: Path):
    dotted_dir = tmp_path / "src" / "v1.0"
    dotted_dir.mkdir(parents=True)
    rule_file = dotted_dir / "AGENTS.md"
    rule_file.write_text("Dotted dir rule")

    registry = CustomizationRegistry(workspace_root=tmp_path)

    # Resolving for directory directly
    rules_dir = registry.resolve_rules_for_path(dotted_dir)
    assert len(rules_dir) == 1
    assert rules_dir[0].scope == "src/v1.0/AGENTS.md"
    assert rules_dir[0].content == "Dotted dir rule"

    # Resolving for file inside dotted directory
    rules_file = registry.resolve_rules_for_path(dotted_dir / "api.py")
    assert len(rules_file) == 1
    assert rules_file[0].scope == "src/v1.0/AGENTS.md"
    assert rules_file[0].content == "Dotted dir rule"


def test_skill_description_bounded_to_frontmatter(tmp_path: Path):
    # Case 1: Frontmatter description takes precedence over description line in body
    skill1_dir = tmp_path / ".agents" / "skills" / "skill-fm-desc"
    skill1_dir.mkdir(parents=True)
    (skill1_dir / "SKILL.md").write_text(
        "---\nname: skill-fm-desc\ndescription: Proper frontmatter description\n---\n"
        "# Body\ndescription: Invalid body description\n"
    )

    # Case 2: Frontmatter without description; description in body should not be treated as frontmatter
    skill2_dir = tmp_path / ".agents" / "skills" / "skill-no-fm-desc"
    skill2_dir.mkdir(parents=True)
    (skill2_dir / "SKILL.md").write_text(
        "---\nname: skill-no-fm-desc\n---\n"
        "# Body Header\nThis is the actual fallback description.\ndescription: Something else in code block\n"
    )

    registry = CustomizationRegistry(workspace_root=tmp_path)
    skills = registry.list_available_skills()
    skill_map = {s.name: s.description for s in skills}

    assert skill_map["skill-fm-desc"] == "Proper frontmatter description"
    assert skill_map["skill-no-fm-desc"] == "This is the actual fallback description."
