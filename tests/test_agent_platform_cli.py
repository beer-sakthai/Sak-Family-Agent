"""Unit tests for the platform CLI command group."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from sakthai.cli import main


def test_platform_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["platform", "--help"])
    assert result.exit_code == 0
    assert "Unified AI agent platform" in result.output


def test_platform_detect_deps(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["platform", "detect-deps", "-p", str(tmp_path)])
    assert result.exit_code == 0
    assert "Manager:       uv" in result.output
    assert "uv sync" in result.output

    # JSON output
    res_json = runner.invoke(main, ["platform", "detect-deps", "-p", str(tmp_path), "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["manager"] == "uv"
    assert "uv add" in data["install_cmd"]


def test_platform_check_safety_safe() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["platform", "check-safety", "echo hello"])
    assert result.exit_code == 0
    assert "Command verified safe" in result.output


def test_platform_check_safety_blocked_and_authorized() -> None:
    runner = CliRunner()
    cmd = "rm -rf /important_dir"
    result = runner.invoke(main, ["platform", "check-safety", cmd])
    assert result.exit_code == 0
    assert "BLOCKED: Potential accidental data loss detected!" in result.output
    assert "Required Token: APPROVE_" in result.output

    # Extract token
    for line in result.output.splitlines():
        if "Required Token:" in line:
            token = line.split(":", 1)[1].strip()
            break
    else:
        raise AssertionError("Token not found in output")

    # Authorize with token
    auth_result = runner.invoke(main, ["platform", "check-safety", cmd, "-t", token])
    assert auth_result.exit_code == 0
    assert "Destructive operation authorized" in auth_result.output

    # Test JSON output
    json_result = runner.invoke(main, ["platform", "check-safety", cmd, "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert data["is_destructive"] is True
    assert data["blocked"] is True


def test_platform_skills_discovery(tmp_path: Path) -> None:
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-cool-skill\ndescription: A test skill\n---\nBody",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["platform", "skills", "-p", str(tmp_path)])
    assert result.exit_code == 0
    assert "my_skill" in result.output

    json_result = runner.invoke(main, ["platform", "skills", "-p", str(tmp_path), "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert len(data) == 1
    assert data[0]["name"] == "my_skill"


def test_platform_skills_empty(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["platform", "skills", "-p", str(tmp_path)])
    assert result.exit_code == 0
    assert "No SKILL.md files found" in result.output


def test_platform_export_harness(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "platform",
            "export-harness",
            "-n",
            "Auditor",
            "-t",
            "Perform security checks",
            "-m",
            "github_mcp",
            "-m",
            "slack_mcp",
        ],
    )
    assert result.exit_code == 0
    assert "version: 1" in result.output
    assert "github_mcp" in result.output

    # File output
    out_file = tmp_path / "agent.yaml"
    res_file = runner.invoke(
        main,
        [
            "platform",
            "export-harness",
            "-n",
            "Auditor",
            "-t",
            "Perform security checks",
            "-o",
            str(out_file),
        ],
    )
    assert res_file.exit_code == 0
    assert out_file.exists()
    assert "Harness agent spec written" in res_file.output
