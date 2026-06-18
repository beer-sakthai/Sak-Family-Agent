"""Tests for importing Hermes-learned skills into the repo skills/ tree."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.hermes_skills import (
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
