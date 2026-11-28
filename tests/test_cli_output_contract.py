"""Tests for the sak.cli/v1 output contract, envelope schema, and system pilot commands."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from click.testing import CliRunner

import sakthai.cli.system as system_mod
from sakthai.cli import main
from sakthai.cli._output import (
    CLI_ENVELOPE_SCHEMA,
    CLI_SCHEMA_VERSION,
    EXIT_ERROR,
    EXIT_NOT_READY,
    EXIT_OK,
    OutputContext,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "cli-envelope.schema.json"


@pytest.fixture
def envelope_schema() -> dict[str, Any]:
    assert SCHEMA_PATH.is_file(), f"Schema file missing at {SCHEMA_PATH}"
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _fake_env(ready: bool = True) -> dict[str, Any]:
    return {
        "paths": {
            "sakthai_home": "/fake/home",
            "sakthai_home_exists": True,
            "memory_db": "/fake/memory.db",
            "memory_db_exists": True,
            "skills_dir": "/fake/skills",
            "skills_dir_exists": True,
        },
        "memory": {
            "db_exists": True,
            "db_writable": True,
            "fact_count": 10,
            "observation_count": 5,
            "error": None,
        },
        "env": {"ANTHROPIC_API_KEY": {"set": True, "required": True}},
        "auth": {
            "anthropic_source": "api_key",
            "anthropic_ok": True,
            "openai_ok": False,
            "gateway_ok": False,
            "huggingface_ok": False,
            "gemini_ok": True,
            "gemini_cli_oauth": False,
        },
        "skills": {"dir_exists": True, "skill_count": 4},
        "ready": ready,
    }


def test_schema_file_is_valid_json_schema(envelope_schema: dict[str, Any]) -> None:
    """Ensure schemas/cli-envelope.schema.json conforms to Draft 2020-12 metaschema."""
    assert envelope_schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert envelope_schema.get("title") == "Sak CLI Output Envelope Schema v1"


@pytest.mark.parametrize("command", ["doctor", "status", "tools"])
def test_pilot_commands_json_validate_against_schema(
    runner: CliRunner, command: str, envelope_schema: dict[str, Any]
) -> None:
    """Ensure doctor, status, and tools --json output strictly validates against cli-envelope.schema.json."""
    result = runner.invoke(main, [command, "--json"])
    assert result.exit_code == EXIT_OK, f"{command} failed: {result.output}"
    payload = json.loads(result.output)
    jsonschema.validate(instance=payload, schema=envelope_schema)
    assert payload["schema"] == CLI_SCHEMA_VERSION
    assert payload["$schema"] == CLI_ENVELOPE_SCHEMA
    assert payload["ok"] is True
    assert payload["error"] is None
    assert isinstance(payload["warnings"], list)


def test_doctor_json_unready_exit_code_and_schema(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, envelope_schema: dict[str, Any]
) -> None:
    """Verify doctor --json emits ok: false and exits with 3 (EXIT_NOT_READY) when unready."""
    monkeypatch.setattr(system_mod, "check_env", lambda: _fake_env(ready=False))
    result = runner.invoke(main, ["doctor", "--json"])
    assert result.exit_code == EXIT_NOT_READY
    payload = json.loads(result.output)
    jsonschema.validate(instance=payload, schema=envelope_schema)
    assert payload["ok"] is False
    assert payload["data"]["ready"] is False


def test_status_json_unready_exit_code_and_schema(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, envelope_schema: dict[str, Any]
) -> None:
    """Verify status --json emits ok: false and exits with 3 (EXIT_NOT_READY) when unready."""
    monkeypatch.setattr(system_mod, "check_env", lambda: _fake_env(ready=False))
    result = runner.invoke(main, ["status", "--json"])
    assert result.exit_code == EXIT_NOT_READY
    payload = json.loads(result.output)
    jsonschema.validate(instance=payload, schema=envelope_schema)
    assert payload["ok"] is False
    assert payload["data"]["ready"] is False


@pytest.mark.parametrize("command", ["doctor", "status", "tools"])
def test_legacy_json_backward_compatibility(runner: CliRunner, command: str) -> None:
    """Ensure --legacy-json emits bare payload without the envelope."""
    result = runner.invoke(main, [command, "--json", "--legacy-json"])
    assert result.exit_code == EXIT_OK
    payload = json.loads(result.output)
    assert "schema" not in payload
    assert "ok" not in payload


def test_sak_json_legacy_environment_variable(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure SAK_JSON_LEGACY=1 environment variable activates legacy mode."""
    monkeypatch.setenv("SAK_JSON_LEGACY", "1")
    result = runner.invoke(main, ["status", "--json"])
    assert result.exit_code == EXIT_OK
    payload = json.loads(result.output)
    assert "ready" in payload
    assert "schema" not in payload


def test_tools_quiet_mode_outputs_bare_names(runner: CliRunner) -> None:
    """tools -q should output one tool name per line."""
    result = runner.invoke(main, ["tools", "-q"])
    assert result.exit_code == EXIT_OK
    names = [line.strip() for line in result.output.splitlines() if line.strip()]
    assert len(names) > 0
    assert "learn" in names or "recall" in names or "huggingface_inference" in names


def test_quiet_json_outputs_compact_one_line(runner: CliRunner) -> None:
    """Combining -q and --json produces minified one-line JSON without multi-line indentation."""
    result = runner.invoke(main, ["tools", "-q", "--json"])
    assert result.exit_code == EXIT_OK
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert len(lines) == 1, "Compact JSON should be emitted on a single line"
    payload = json.loads(lines[0])
    assert payload["ok"] is True


def test_output_context_color_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify precedence: --no-color > NO_COLOR > FORCE_COLOR > isatty."""
    # 1. explicit --no-color flag
    out1 = OutputContext(no_color=True)
    assert out1.no_color is True

    # 2. NO_COLOR env var
    monkeypatch.setenv("NO_COLOR", "1")
    out2 = OutputContext(no_color=False)
    assert out2.no_color is True
    monkeypatch.delenv("NO_COLOR")

    # 3. FORCE_COLOR env var overrides non-tty
    fake_stream = io.StringIO()
    monkeypatch.setenv("FORCE_COLOR", "1")
    out3 = OutputContext(stdout=fake_stream, no_color=False)
    assert out3.no_color is False

    # 4. non-tty default without FORCE_COLOR
    monkeypatch.delenv("FORCE_COLOR")
    out4 = OutputContext(stdout=fake_stream, no_color=False)
    assert out4.no_color is True


def test_output_context_error_envelope_and_stream_hygiene(
    envelope_schema: dict[str, Any],
) -> None:
    """Verify out.error in JSON mode sends envelope to stdout and leaves stderr clean."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    out = OutputContext(json_output=True, stdout=stdout_buf, stderr=stderr_buf)

    with pytest.raises(SystemExit) as exc_info:
        out.error(
            "Database connection failed",
            code="DB_ERROR",
            details={"path": "/tmp/db.sqlite"},
            exit_code=EXIT_ERROR,
        )

    assert exc_info.value.code == EXIT_ERROR
    # stderr must remain silent
    assert stderr_buf.getvalue() == ""

    # stdout must contain valid schema-compliant error envelope
    stdout_str = stdout_buf.getvalue().strip()
    payload = json.loads(stdout_str)
    jsonschema.validate(instance=payload, schema=envelope_schema)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "DB_ERROR"
    assert payload["error"]["message"] == "Database connection failed"
    assert payload["error"]["details"]["path"] == "/tmp/db.sqlite"


def test_rainbow_flourishes_in_tty(runner: CliRunner) -> None:
    """Verify doctor and status render signature rainbow banners in TTY mode."""
    res_doc = runner.invoke(main, ["doctor"])
    assert res_doc.exit_code == EXIT_OK
    assert "Doctor" in res_doc.output

    res_stat = runner.invoke(main, ["status"])
    assert res_stat.exit_code == EXIT_OK
    assert "Status" in res_stat.output
