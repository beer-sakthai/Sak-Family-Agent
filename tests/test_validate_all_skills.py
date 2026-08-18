import importlib
import sys
from pathlib import Path

# Add script directory to sys.path
script_dir = (
    Path(__file__).parent.parent
    / "personas"
    / "sakking"
    / "skills"
    / "SakKing-plan-check-count"
    / "scripts"
)
sys.path.insert(0, str(script_dir))

validator = importlib.import_module("validate-all-skills")


def test_is_todo_false_alarm_positive() -> None:
    content = "--- \ntags: todo, devops\n---\n# My Skill\n"
    match_start = content.lower().find("todo")
    match_end = match_start + 4
    assert validator.is_todo_false_alarm(match_start, match_end, content) is True


def test_is_todo_false_alarm_negative() -> None:
    content = "# Skill Title\n\nTODO: implement feature X later.\n"
    match_start = content.find("TODO")
    match_end = match_start + 4
    assert validator.is_todo_false_alarm(match_start, match_end, content) is False


def test_check_stale_indicators_false_alarm_only() -> None:
    content = (
        "---\nname: my-skill\ntags: todo\nstatus: todo\n---\n"
        "# My Skill\n\nUses tool `todo` to manage tasks.\n"
    )
    stale = validator.check_stale_indicators(content)
    assert stale == []


def test_check_stale_indicators_true_positive() -> None:
    content = "---\nname: my-skill\n---\n# Title\n\nTODO: write implementation details.\n"
    stale = validator.check_stale_indicators(content)
    assert "TODO" in stale


def test_check_stale_indicators_mixed_case() -> None:
    """A file containing both a valid todo tag AND a real TODO marker must be flagged as STALE."""
    content = (
        "---\nname: my-skill\ntags: todo\n---\n# Title\n\nTODO: finish writing this section.\n"
    )
    stale = validator.check_stale_indicators(content)
    assert "TODO" in stale


def test_check_stale_indicators_other_patterns() -> None:
    content = "---\nname: my-skill\n---\n# Title\n\nFIXME: resolve memory leak.\n"
    stale = validator.check_stale_indicators(content)
    assert "FIXME" in stale


def test_validate_skill_content_empty() -> None:
    errors, warnings = validator.validate_skill_content("Short", "test/SKILL.md")
    assert any("EMPTY" in e for e in errors)


def test_validate_skill_content_no_fm() -> None:
    content = "# Title\n" + "A" * 60
    errors, warnings = validator.validate_skill_content(content, "test/SKILL.md")
    assert any("NO_FM" in e for e in errors)


def test_validate_skill_content_bad_fm() -> None:
    content = "---\n# Title without closing fm\n" + "A" * 60
    errors, warnings = validator.validate_skill_content(content, "test/SKILL.md")
    assert any("BAD_FM" in e for e in errors)


def test_validate_skill_content_valid() -> None:
    content = "---\nname: valid-skill\ndescription: A valid skill.\n---\n\n# Valid Skill\n\n" + (
        "Content lines.\n" * 5
    )
    errors, warnings = validator.validate_skill_content(content, "test/SKILL.md")
    assert errors == []
    assert warnings == []


def test_validate_skills_dir(tmp_path: Path) -> None:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: my-skill\n---\n\n# Title\n\n" + "Body text goes here.\n" * 5,
        encoding="utf-8",
    )

    ok_count, errors, warnings = validator.validate_skills_dir(str(tmp_path))
    assert ok_count == 1
    assert errors == []
    assert warnings == []


def test_main_cli(tmp_path: Path) -> None:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: my-skill\n---\n\n# Title\n\n" + "Body text goes here.\n" * 5,
        encoding="utf-8",
    )

    exit_code = validator.main([str(tmp_path)])
    assert exit_code == 0
