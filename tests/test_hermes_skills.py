"""Tests for importing Hermes-learned skills into the repo skills/ tree."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.hermes_skills import (
    _MAX_DESC,
    _category_for,
    _collect_paragraph,
    _derive_description,
    _derive_title,
    _first_sentence,
    bundled_slugs,
    discover_learned_skills,
    sync_hermes_skills,
)
from sakthai.skills import parse_skill, validate_tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _hermes_root(tmp_path: Path) -> Path:
    """Build a fake ~/.hermes/skills tree: bundled + learned + internal."""
    root = tmp_path / "hermes" / "skills"
    _write(root / ".bundled_manifest", "github:aaa\nairtable:bbb\napple-notes:ccc\n")

    # Bundled (in manifest) — must be ignored.
    _write(root / "github" / "SKILL.md", "---\nname: github\ndescription: bundled\n---\nx")
    _write(root / "apple" / "apple-notes" / "SKILL.md", "---\nname: apple-notes\n---\nx")

    # Learned, no frontmatter, with a ## Purpose section.
    _write(
        root / "cron-watchdog" / "SKILL.md",
        "# Cron Watchdog\n\n## Purpose\n\nHeal the cron fleet automatically. More text.\n",
    )
    # Learned, with frontmatter, nested under a category dir.
    _write(
        root / "devops" / "deploy-helper" / "SKILL.md",
        "---\nname: deploy-helper\ndescription: Ship it safely\nversion: 2.1\n"
        "platforms:\n  - linux\nmetadata:\n  sakthai:\n    tags:\n      - ci\n---\n\nBody here.\n",
    )
    # Hermes-internal — excluded by default prefix.
    _write(root / "hermes-operations" / "SKILL.md", "# Hermes Ops\n\nInternal stuff.\n")
    # Already sakthai-prefixed learned skill — keep its name as-is.
    _write(root / "sakthai-special" / "SKILL.md", "# Special\n\nDo special things.\n")
    return root


def test_bundled_slugs_parses_manifest(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    assert bundled_slugs(root) == {"github", "airtable", "apple-notes"}


def test_bundled_slugs_missing_manifest_is_empty(tmp_path: Path) -> None:
    assert bundled_slugs(tmp_path) == set()


def test_discover_selects_only_learned(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    slugs = {s.target_slug for s in discover_learned_skills(root)}
    assert slugs == {"sakthai-cron-watchdog", "sakthai-deploy-helper", "sakthai-special"}


def test_discover_can_include_internal_via_empty_excludes(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    slugs = {s.target_slug for s in discover_learned_skills(root, exclude_prefixes=())}
    assert "sakthai-hermes-operations" in slugs


def test_category_from_nesting_and_defaults(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    by_slug = {s.target_slug: s for s in discover_learned_skills(root)}
    assert by_slug["sakthai-deploy-helper"].category == "devops"
    assert by_slug["sakthai-cron-watchdog"].category == "hermes"


def test_description_derived_from_purpose(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    by_slug = {s.target_slug: s for s in discover_learned_skills(root)}
    assert by_slug["sakthai-cron-watchdog"].description == "Heal the cron fleet automatically"


def test_frontmatter_description_and_version_preserved(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    by_slug = {s.target_slug: s for s in discover_learned_skills(root)}
    deploy = by_slug["sakthai-deploy-helper"]
    assert deploy.description == "Ship it safely"
    assert deploy.version == "2.1"
    assert "ci" in deploy.tags and "hermes" in deploy.tags


def test_sync_creates_valid_roundtrippable_skills(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "skills"
    outcome = sync_hermes_skills(root, dest)
    assert set(outcome.created) == {
        "sakthai-cron-watchdog",
        "sakthai-deploy-helper",
        "sakthai-special",
    }
    assert not outcome.updated and not outcome.unchanged
    # Every written skill parses cleanly and validates.
    skill = parse_skill(dest / "sakthai-deploy-helper" / "SKILL.md")
    assert skill.name == "sakthai-deploy-helper"
    assert validate_tree(dest) == []


def test_sync_is_idempotent(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "skills"
    sync_hermes_skills(root, dest)
    second = sync_hermes_skills(root, dest)
    assert second.created == [] and second.updated == []
    assert len(second.unchanged) == 3


def test_sync_updates_on_source_change(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "skills"
    sync_hermes_skills(root, dest)
    _write(root / "cron-watchdog" / "SKILL.md", "# Cron Watchdog\n\n## Purpose\n\nNew text now.\n")
    outcome = sync_hermes_skills(root, dest)
    assert outcome.updated == ["sakthai-cron-watchdog"]
    assert "New text now." in (dest / "sakthai-cron-watchdog" / "SKILL.md").read_text()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "skills"
    outcome = sync_hermes_skills(root, dest, dry_run=True)
    assert len(outcome.created) == 3
    assert not dest.exists()


def test_missing_root_yields_no_skills(tmp_path: Path) -> None:
    assert discover_learned_skills(tmp_path / "nope") == []


def test_malformed_yaml_frontmatter_is_recovered(tmp_path: Path) -> None:
    """An unquoted colon-space description (invalid YAML) must still parse, and the
    raw frontmatter fence must not leak into the body."""
    root = tmp_path / "hermes" / "skills"
    # description value contains ": " which yaml.safe_load rejects.
    _write(
        root / "broken-fm" / "SKILL.md",
        "---\nname: broken-fm\ndescription: Coverage: login and logout flows\n---\n\n# Broken\n\nBody.\n",
    )
    dest = tmp_path / "skills"
    sync_hermes_skills(root, dest)
    skill = parse_skill(dest / "sakthai-broken-fm" / "SKILL.md")
    assert skill.description == "Coverage: login and logout flows"
    assert "---" not in skill.body  # fence stripped, no leak
    assert validate_tree(dest) == []


def test_cli_sync_hermes_writes_skills(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "repo_skills"
    monkeypatch.setattr("sakthai.cli.skills.SKILLS_DIR", dest)
    result = CliRunner().invoke(main, ["skills", "sync-hermes", "--hermes-home", str(root)])
    assert result.exit_code == 0, result.output
    assert "synced 3 learned skill(s)" in result.output
    assert "+ sakthai-deploy-helper" in result.output
    assert (dest / "sakthai-deploy-helper" / "SKILL.md").is_file()


def test_cli_sync_hermes_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _hermes_root(tmp_path)
    dest = tmp_path / "repo_skills"
    monkeypatch.setattr("sakthai.cli.skills.SKILLS_DIR", dest)
    result = CliRunner().invoke(
        main, ["skills", "sync-hermes", "--hermes-home", str(root), "--dry-run"]
    )
    assert result.exit_code == 0, result.output
    assert "would sync 3" in result.output
    assert not dest.exists()


def test_cli_sync_hermes_missing_dir_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        main, ["skills", "sync-hermes", "--hermes-home", str(tmp_path / "absent")]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


# ---------------------------------------------------------------------------
# Unit tests for private text-parsing helpers
# ---------------------------------------------------------------------------


def test_first_sentence_truncates_at_max_desc() -> None:
    long_text = "A" * (_MAX_DESC + 10) + ". More text after."
    result = _first_sentence(long_text)
    assert len(result) <= _MAX_DESC
    assert result.endswith("…")


def test_first_sentence_no_truncation_for_short_text() -> None:
    result = _first_sentence("Short sentence.")
    assert result == "Short sentence"
    assert "…" not in result


def test_derive_title_extracts_h1() -> None:
    assert _derive_title("# My Skill Title\n\nBody text here.") == "My Skill Title"


def test_derive_title_returns_none_when_no_h1() -> None:
    assert _derive_title("## Only h2 heading\n\nBody.") is None
    assert _derive_title("No heading at all.") is None


def test_derive_description_fallback_stops_at_empty_line() -> None:
    # First non-heading paragraph ends at an empty line; only that paragraph is used.
    body = "## No Purpose\n\nFirst para text.\n\nSecond para ignored."
    result = _derive_description(body)
    assert result == "First para text"


def test_derive_description_fallback_stops_at_next_heading() -> None:
    body = "## No Purpose\n\nFirst para.\n## Next heading\nIgnored."
    result = _derive_description(body)
    assert result == "First para"


def test_derive_description_returns_none_for_headings_only() -> None:
    body = "# Title\n## Sub\n### Sub-sub"
    assert _derive_description(body) is None


def test_collect_paragraph_stops_at_empty_line_after_content() -> None:
    lines = ["First line.", "", "Second paragraph ignored."]
    result = _collect_paragraph(lines)
    assert result == "First line."


def test_collect_paragraph_stops_at_heading_after_content() -> None:
    lines = ["Content line.", "# Heading stops collection"]
    result = _collect_paragraph(lines)
    assert result == "Content line."


def test_collect_paragraph_skips_leading_heading_when_no_content() -> None:
    lines = ["# Heading with no prior content", "Actual content follows."]
    result = _collect_paragraph(lines)
    assert result == "Actual content follows."


# ---------------------------------------------------------------------------
# _category_for edge case: path not relative to skills_root
# ---------------------------------------------------------------------------


def test_category_for_returns_hermes_when_path_not_under_root(tmp_path: Path) -> None:
    skill_md = tmp_path / "some" / "other" / "SKILL.md"
    skill_md.parent.mkdir(parents=True, exist_ok=True)
    skill_md.touch()
    unrelated_root = tmp_path / "completely_different_root"
    unrelated_root.mkdir()
    # skill_md is not relative to unrelated_root → ValueError → returns "hermes"
    result = _category_for(skill_md, unrelated_root)
    assert result == "hermes"


# ---------------------------------------------------------------------------
# discover_learned_skills edge cases
# ---------------------------------------------------------------------------


def test_discover_skips_hidden_directories(tmp_path: Path) -> None:
    root = tmp_path / "hermes" / "skills"
    # A skill nested inside a hidden directory must be ignored.
    hidden = root / ".hidden-dir" / "my-skill"
    hidden.mkdir(parents=True)
    (hidden / "SKILL.md").write_text("# Hidden\n\nShould be skipped.\n", encoding="utf-8")
    skills = discover_learned_skills(root)
    assert all(".hidden" not in s.source_slug for s in skills)


def test_discover_deduplicates_same_target_slug(tmp_path: Path) -> None:
    root = tmp_path / "hermes" / "skills"
    # "foo" maps to "sakthai-foo"; "sakthai-foo" also maps to "sakthai-foo".
    # Only the first (alphabetically) should appear.
    for slug in ("foo", "sakthai-foo"):
        skill_dir = root / slug
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"# {slug}\n\nBody.\n", encoding="utf-8")
    skills = discover_learned_skills(root)
    target_slugs = [s.target_slug for s in skills]
    assert target_slugs.count("sakthai-foo") == 1
