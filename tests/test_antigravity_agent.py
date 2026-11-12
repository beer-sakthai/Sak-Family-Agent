"""Unit tests for the Google Antigravity Agent integration and runner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sakthai.agent_platform.antigravity_agent import (
    AI_STUDIO_KEY_URL,
    AntigravityAgentRunner,
    AntigravityRunnerConfig,
)
from sakthai.cli import main


def test_runner_config_hosted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-env-key")
    runner = AntigravityAgentRunner(
        AntigravityRunnerConfig(backend="hosted", model="gemini-2.5-flash")
    )
    sdk_cfg = runner.build_sdk_config()
    assert sdk_cfg.model == "gemini-2.5-flash"
    assert getattr(sdk_cfg, "api_key", None) == "test-env-key"


def test_runner_config_openai() -> None:
    runner = AntigravityAgentRunner(
        AntigravityRunnerConfig(
            backend="openai",
            model="gemma-2b",
            base_url="http://localhost:11434/v1",
        )
    )
    sdk_cfg = runner.build_sdk_config()
    assert getattr(sdk_cfg, "base_url", None) == "http://localhost:11434/v1"


def test_runner_config_litert(tmp_path: Path) -> None:
    model_file = tmp_path / "model.bin"
    model_file.write_text("weights")
    runner = AntigravityAgentRunner(
        AntigravityRunnerConfig(
            backend="litert",
            model_path=str(model_file),
        )
    )
    sdk_cfg = runner.build_sdk_config()
    assert getattr(sdk_cfg, "model_path", None) == str(model_file)


def test_runner_config_litert_missing_path() -> None:
    runner = AntigravityAgentRunner(AntigravityRunnerConfig(backend="litert"))
    with pytest.raises(ValueError, match="requires 'model_path'"):
        runner.build_sdk_config()


def test_runner_config_unknown_backend() -> None:
    runner = AntigravityAgentRunner(AntigravityRunnerConfig(backend="invalid_backend"))
    with pytest.raises(ValueError, match="Unknown backend"):
        runner.build_sdk_config()


def test_runner_safe_tools(tmp_path: Path) -> None:
    runner = AntigravityAgentRunner(AntigravityRunnerConfig(workspace_dir=tmp_path))
    safe_run, safe_read, inspect_ws = runner.create_safe_tools()

    # 1. safe_run_command
    safe_res = safe_run("echo safe")
    assert "Command permitted" in safe_res

    blocked_res = safe_run("rm -rf /vital_data")
    assert "BLOCKED by DataLossGuardrail" in blocked_res
    assert "APPROVE_" in blocked_res

    # 2. safe_read_file
    sample_file = tmp_path / "hello.txt"
    sample_file.write_text("SakThai Antigravity", encoding="utf-8")
    read_res = safe_read("hello.txt")
    assert "SakThai Antigravity" in read_res

    # Non-existent
    assert "File not found" in safe_read("missing.txt")

    # Outside workspace
    outside_res = safe_read("../../etc/passwd")
    assert "Access Denied" in outside_res

    # Directory instead of file
    sub_dir = tmp_path / "sub_folder"
    sub_dir.mkdir()
    assert "not a regular file" in safe_read("sub_folder")

    # Read error
    with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
        assert "Error reading file" in safe_read("hello.txt")

    # Authorized safe_run
    cmd = "rm -rf /test_data"
    token = runner.guardrail.generate_approval_token(cmd)
    auth_res = safe_run(cmd, approval_token=token)
    assert "Command permitted" in auth_res

    # 3. inspect_workspace
    ws_res = inspect_ws()
    assert tmp_path.name in ws_res


@pytest.mark.asyncio
async def test_stream_chat_mocked() -> None:
    runner = AntigravityAgentRunner(AntigravityRunnerConfig(backend="hosted", api_key="dummy-key"))

    class MockAsyncResponse:
        def __init__(self, tokens: list[str]) -> None:
            self._tokens = list(tokens)

        def __aiter__(self) -> MockAsyncResponse:
            return self

        async def __anext__(self) -> str:
            if not self._tokens:
                raise StopAsyncIteration
            return self._tokens.pop(0)

    class MockAgentContext:
        async def __aenter__(self) -> MockAgentContext:
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def chat(self, prompt: str) -> MockAsyncResponse:
            return MockAsyncResponse(["Hello ", "from ", "Antigravity!"])

    with patch("sakthai.agent_platform.antigravity_agent.Agent", return_value=MockAgentContext()):
        tokens = [token async for token in runner.stream_chat("Test prompt")]
        assert "".join(tokens) == "Hello from Antigravity!"


def test_platform_antigravity_cli_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    cli_runner = CliRunner()
    result = cli_runner.invoke(main, ["platform", "antigravity", "Hello"])
    assert result.exit_code != 0
    assert "Authentication Required" in result.output
    assert AI_STUDIO_KEY_URL in result.output


def test_platform_antigravity_cli_mocked() -> None:
    cli_runner = CliRunner()

    async def mock_stream(prompt: str):
        for token in ["Mocked ", "Token ", "Stream"]:
            yield token

    with patch.object(AntigravityAgentRunner, "stream_chat", side_effect=mock_stream):
        result = cli_runner.invoke(
            main,
            ["platform", "antigravity", "--api-key", "dummy", "Hello test"],
        )
        assert result.exit_code == 0
        assert "Mocked Token Stream" in result.output


def test_platform_antigravity_cli_execution_error() -> None:
    cli_runner = CliRunner()
    with patch.object(
        AntigravityAgentRunner,
        "stream_chat",
        side_effect=RuntimeError("Connection refused"),
    ):
        result = cli_runner.invoke(
            main,
            ["platform", "antigravity", "--api-key", "dummy", "Hello fail"],
        )
        assert result.exit_code != 0
        assert "Execution failed" in result.output
