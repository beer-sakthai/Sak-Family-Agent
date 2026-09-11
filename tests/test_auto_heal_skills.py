from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_SCRIPT = Path(__file__).parents[1] / "scripts" / "auto_heal_skills.py"
_SPEC = spec_from_file_location("auto_heal_skills", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
discover_skill_files = _MODULE.discover_skill_files
heal_skill_file = _MODULE.heal_skill_file


def test_heal_preserves_existing_metadata_and_repairs_short_content(tmp_path: Path) -> None:
    skill = tmp_path / "demo" / "SKILL.md"
    skill.parent.mkdir()
    skill.write_text(
        "---\nname: demo\ndescription: short\nversion: 2\n---\n\n# Demo\n",
        encoding="utf-8",
    )

    assert heal_skill_file(skill) is True
    healed = skill.read_text(encoding="utf-8")
    assert "name: demo" in healed
    assert "version: 2" in healed
    assert "Comprehensive skill and execution procedures" in healed
    assert "## Execution Workflow" in healed


def test_heal_recovers_malformed_frontmatter_without_leaking_fences(tmp_path: Path) -> None:
    skill = tmp_path / "broken" / "SKILL.md"
    skill.parent.mkdir()
    skill.write_text("---\ndescription: bad: yaml\n---\n\n", encoding="utf-8")

    assert heal_skill_file(skill) is True
    healed = skill.read_text(encoding="utf-8")
    assert healed.startswith("---\nname: broken\n")
    assert "description: bad: yaml" not in healed
    assert healed.count("---") == 2


def test_dry_run_reports_change_without_writing(tmp_path: Path) -> None:
    skill = tmp_path / "demo" / "SKILL.md"
    skill.parent.mkdir()
    original = "# Demo\n"
    skill.write_text(original, encoding="utf-8")

    assert heal_skill_file(skill, write=False) is True
    assert skill.read_text(encoding="utf-8") == original


def test_discovery_skips_symlinks_and_ignored_directories(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    visible = root / "visible" / "SKILL.md"
    ignored = root / "node_modules" / "hidden" / "SKILL.md"
    visible.parent.mkdir(parents=True)
    ignored.parent.mkdir(parents=True)
    visible.write_text("# visible\n", encoding="utf-8")
    ignored.write_text("# hidden\n", encoding="utf-8")
    link = root / "linked"
    link.symlink_to(visible.parent, target_is_directory=True)

    assert discover_skill_files([root]) == [visible]
