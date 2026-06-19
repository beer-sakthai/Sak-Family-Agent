"""Integration tests for the sakthai doctor command.

These tests exercise the full doctor command logic including environment
detection, filesystem checks, and memory database integration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.memory.store import MemoryStore


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a fully isolated SakThai environment."""
    home = tmp_path / "sakthai_home"
    home.mkdir()

    # Isolate SAKTHAI_HOME
    monkeypatch.setenv("SAKTHAI_HOME", str(home))

    # Isolate skills directory (config.py uses REPO_ROOT / "skills" by default,
    # but we want to test how doctor reports it).
    # Actually SKILLS_DIR in config.py is relative to REPO_ROOT.
    # To properly test doctor's reporting of the skills dir, we might need to
    # monkeypatch the SKILLS_DIR in sakthai.config if we want to change it.

    return home


def test_doctor_happy_path(
    runner: CliRunner, isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test doctor output when everything is correctly set up."""
    # 1. Setup credentials
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")

    # 2. Setup memory DB with data
    db_path = isolated_env / "memory.db"
    with MemoryStore(db_path) as store:
        store.add_fact("test fact 1", tags=["tag1"])
        store.add_observation("test observation 1")

    # 3. Setup skills dir
    # Since SKILLS_DIR is fixed at REPO_ROOT / "skills", we'll just check if it's reported correctly.
    # In a real environment, we might not want to mess with REPO_ROOT.
    # However, doctor uses check_env which uses config.SKILLS_DIR.

    result = runner.invoke(main, ["doctor"])

    assert result.exit_code == 0
    assert "SakThai Doctor" in result.output

    # Paths section
    assert f"sakthai home : {isolated_env}" in result.output
    assert "memory db    :" in result.output

    # Memory section
    assert "exists  : True" in result.output
    assert "writable: True" in result.output
    assert "facts: 1" in result.output
    assert "observations: 1" in result.output

    # Credentials section
    assert "Anthropic    : ANTHROPIC_API_KEY env var" in result.output

    # Ready status
    assert "SakThai is ready." in result.output


def test_doctor_missing_credentials(
    runner: CliRunner, isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test doctor output when credentials are missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    # Ensure no other sources are found
    monkeypatch.setattr("sakthai.auth.anthropic_credential_source", lambda: None)

    result = runner.invoke(main, ["doctor"])

    assert result.exit_code == 0
    assert "Anthropic    : none found" in result.output
    assert "set ANTHROPIC_API_KEY" in result.output


def test_doctor_corrupt_db(
    runner: CliRunner, isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test doctor output when the memory database is corrupt."""
    db_path = isolated_env / "memory.db"
    db_path.write_text("not a database", encoding="utf-8")

    result = runner.invoke(main, ["doctor"])

    assert result.exit_code == 0
    assert "error:" in result.output
    # Depending on sqlite3 version, the error message might vary, but "database" is likely.
    assert "database" in result.output.lower()
    assert "SakThai is ready." not in result.output


def test_doctor_non_writable_db(
    runner: CliRunner, isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test doctor output when the database is not writable."""
    db_path = isolated_env / "memory.db"
    with MemoryStore(db_path) as store:
        store.add_fact("test")

    # Make it read-only
    os.chmod(db_path, 0o444)

    try:
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "writable: False" in result.output
        assert "Core components missing" in result.output
    finally:
        # Restore permissions so cleanup works
        os.chmod(db_path, 0o644)
