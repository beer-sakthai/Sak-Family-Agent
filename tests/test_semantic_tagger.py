"""Unit tests for semantic version tagger helper."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.semantic_tagger import (
    calculate_next_tag,
    determine_bump_type,
    format_semver,
    get_commits_since_tag,
    get_latest_tag,
    main,
    parse_semver,
    write_github_output,
)


def test_parse_semver() -> None:
    assert parse_semver("v1.2.3") == (1, 2, 3)
    assert parse_semver("2.4.15") == (2, 4, 15)
    with pytest.raises(ValueError, match="Invalid semver tag"):
        parse_semver("invalid-tag")


def test_format_semver() -> None:
    assert format_semver(1, 2, 3) == "v1.2.3"
    assert format_semver(2, 0, 0, prefix="") == "2.0.0"


def test_determine_bump_type() -> None:
    assert determine_bump_type([]) == "none"

    # Breaking changes
    assert determine_bump_type(["feat!: breaking api change"]) == "major"
    assert determine_bump_type(["fix: small fix\n\nBREAKING CHANGE: broken"]) == "major"
    assert determine_bump_type(["refactor(core)!: redesign architecture"]) == "major"

    # Minor features
    assert determine_bump_type(["feat: add new tool"]) == "minor"
    assert determine_bump_type(["feat(mcp): add transport"]) == "minor"

    # Patch fixes
    assert determine_bump_type(["fix: resolve crash"]) == "patch"
    assert determine_bump_type(["chore: update deps", "docs: update readme"]) == "patch"


def test_calculate_next_tag() -> None:
    assert calculate_next_tag(None, "minor", fallback="v2.0.0") == "v2.0.0"
    assert calculate_next_tag("v2.0.0", "patch") == "v2.0.1"
    assert calculate_next_tag("v2.0.1", "minor") == "v2.1.0"
    assert calculate_next_tag("v2.1.0", "major") == "v3.0.0"
    assert calculate_next_tag("2.0.0", "patch") == "2.0.1"
    assert calculate_next_tag("v2.0.0", "none") == "v2.0.0"


def test_write_github_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    write_github_output({"key1": "val1", "key2": "val2"})
    assert output_file.read_text(encoding="utf-8") == "key1=val1\nkey2=val2\n"


def test_git_tag_and_commit_helpers(tmp_path: Path) -> None:
    # Initialize a temporary git repository
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )

    # Empty repo checks
    assert get_latest_tag(tmp_path) is None
    assert get_commits_since_tag(None, tmp_path) == []

    # Commit 1
    dummy_file = tmp_path / "test.txt"
    dummy_file.write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=tmp_path, check=True)

    # Tag commit 1 as v1.0.0
    subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, check=True)
    assert get_latest_tag(tmp_path) == "v1.0.0"

    # Commit 2
    dummy_file.write_text("world", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "feat: new feature"], cwd=tmp_path, check=True)

    commits = get_commits_since_tag("v1.0.0", tmp_path)
    assert len(commits) == 1
    assert "feat: new feature" in commits[0]


def test_main_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output_file = tmp_path / "gh_out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    ret = main(["--dry-run", "--fallback", "v2.5.0"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Bump Type:" in captured.out
