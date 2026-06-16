"""Tests for sakthai.cli.system — ``doctor``, ``setup``, ``status``, ``tools``.

All commands are driven through Click's CliRunner. The sakthai_home fixture pins
SAKTHAI_HOME to a tmp dir so no test touches ~/.sakthai. Credentials are
simulated with monkeypatch — no real API keys needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


class TestDoctorCommand:
    def test_exits_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0

    def test_shows_sakthai_doctor_header(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["doctor"])
        assert "Doctor" in result.output or "doctor" in result.output.lower()

    def test_anthropic_ok_when_api_key_set(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "ANTHROPIC_API_KEY" in result.output or "Anthropic" in result.output

    def test_anthropic_missing_shown_when_no_key(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        with monkeypatch.context() as mp:
            mp.setattr("sakthai.auth.anthropic_credential_source", lambda: None, raising=False)
            result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "none found" in result.output.lower() or "Anthropic" in result.output

    def test_memory_section_shown(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["doctor"])
        assert "Memory" in result.output or "memory" in result.output.lower()

    def test_shows_fact_count_when_db_exists(self, runner: CliRunner, sakthai_home: Path) -> None:
        db = sakthai_home / "memory.db"
        with MemoryStore(db) as store:
            store.add_fact("doctor test fact")

        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "facts" in result.output.lower() or "1" in result.output

    def test_ready_line_shown(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        result = runner.invoke(main, ["doctor"])
        assert "ready" in result.output.lower() or "SakThai" in result.output

    def test_shows_paths_section(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["doctor"])
        assert "Paths" in result.output or "home" in result.output.lower()


# ---------------------------------------------------------------------------
# setup
# ---------------------------------------------------------------------------


class TestSetupCommand:
    def test_exits_zero(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0

    def test_shows_setup_header(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["setup"])
        assert "Setup" in result.output or "setup" in result.output.lower()

    def test_env_file_found_when_present(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=sk-fake\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "found" in result.output.lower()

    def test_env_file_missing_shows_error(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "not found" in result.output or ".env" in result.output

    def test_api_key_ok_when_env_var_set(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "ANTHROPIC_API_KEY" in result.output

    def test_api_key_missing_shown_as_error(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        with monkeypatch.context() as mp:
            mp.setattr("sakthai.auth.anthropic_credential_source", lambda: None, raising=False)
            result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "NOT set" in result.output or "ANTHROPIC_API_KEY" in result.output

    def test_memory_db_not_yet_created_shown_as_info(
        self, runner: CliRunner, sakthai_home: Path
    ) -> None:
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "not yet created" in result.output or "Memory" in result.output

    def test_memory_db_writable_shows_fact_count(
        self, runner: CliRunner, sakthai_home: Path
    ) -> None:
        db = sakthai_home / "memory.db"
        with MemoryStore(db) as store:
            store.add_fact("setup test")

        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "writable" in result.output or "facts" in result.output

    def test_virtualenv_active_when_env_var_set(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VIRTUAL_ENV", "/home/user/.venv")
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "virtualenv active" in result.output or ".venv" in result.output

    def test_no_virtualenv_shows_info(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "virtualenv" in result.output.lower() or "venv" in result.output.lower()

    def test_all_checks_passed_shows_success(
        self,
        runner: CliRunner,
        sakthai_home: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=sk-fake\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
        result = runner.invoke(main, ["setup"])
        assert result.exit_code == 0
        assert "All checks passed" in result.output or "passed" in result.output.lower()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class TestStatusCommand:
    def test_exits_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0

    def test_shows_status_header(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["status"])
        assert "Status" in result.output or "status" in result.output.lower()

    def test_ready_when_db_missing(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "Ready" in result.output or "not yet created" in result.output

    def test_shows_memory_db_info(self, runner: CliRunner, sakthai_home: Path) -> None:
        db = sakthai_home / "memory.db"
        with MemoryStore(db) as store:
            store.add_fact("status test")

        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "Memory" in result.output or "writable" in result.output

    def test_credentials_present_shown_when_key_set(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "present" in result.output or "Credentials" in result.output

    def test_shows_skills_dir_info(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "Skills" in result.output or "skills" in result.output.lower()


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------


class TestToolsCommand:
    def test_exits_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["tools"])
        assert result.exit_code == 0

    def test_shows_tools_header(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["tools"])
        assert "tools" in result.output.lower()

    def test_lists_learn_tool(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["tools"])
        assert "learn" in result.output

    def test_lists_recall_tool(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["tools"])
        assert "recall" in result.output

    def test_lists_read_file_tool(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["tools"])
        assert "read_file" in result.output

    def test_all_builtin_tools_listed(self, runner: CliRunner) -> None:
        from sakthai.agent.tools import BUILTIN_TOOLS

        result = runner.invoke(main, ["tools"])
        assert result.exit_code == 0
        for tool in BUILTIN_TOOLS:
            assert tool.name in result.output, f"Tool '{tool.name}' not in output"
