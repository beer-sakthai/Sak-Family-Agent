"""Tests for Production Pro-Tips (Safety Interception, Progressive Disclosure, Model Presets, Isolated Runner)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from sakthai.agent.guardrails import GuardrailAction
from sakthai.agent.guardrails_hardened import (
    check_data_loss_guardrail,
    create_pre_execution_guardrail_hardened,
)
from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.agent_platform.agent_engine import (
    ModelPreset,
    ModelTier,
    UnifiedAgentConfig,
    resolve_model_preset,
)
from sakthai.agent_platform.dep_manager import (
    wrap_with_isolated_runner,
)
from sakthai.agent_platform.safety import DataLossGuardrail
from sakthai.cli.platform import platform_cmd
from sakthai.memory.store import MemoryStore
from sakthai.skills import SkillInfo, render_skills_progressive_summary


class TestProTip1SafetyInterception:
    """Pro-Tip 1: Safety Interception using DataLossGuardrail in guardrails."""

    def test_safe_command_allowed(self) -> None:
        result = check_data_loss_guardrail("echo hello world")
        assert result.action == GuardrailAction.ALLOW

    def test_destructive_shell_command_denied_without_token(self) -> None:
        result = check_data_loss_guardrail("rm -rf /tmp/data")
        assert result.action == GuardrailAction.DENY
        assert "Data loss guardrail violation" in (result.reason or "")
        assert "Provide approval token" in (result.reason or "")

    def test_destructive_shell_command_allowed_with_token(self) -> None:
        cmd = "rm -rf /tmp/data"
        token = DataLossGuardrail().generate_approval_token(cmd)
        result = check_data_loss_guardrail(cmd, approval_token=token)
        assert result.action == GuardrailAction.ALLOW

    def test_destructive_shell_command_denied_with_invalid_token(self) -> None:
        cmd = "rm -rf /tmp/data"
        result = check_data_loss_guardrail(cmd, approval_token="APPROVE_invalid")
        assert result.action == GuardrailAction.DENY

    def test_destructive_cloud_commands_denied(self) -> None:
        for cmd in [
            "gsutil rm -r gs://my-bucket/data",
            "bq rm -f dataset.table",
            "git reset --hard HEAD~1",
            "git clean -fd",
            "terraform destroy",
            "kubectl delete namespace prod",
        ]:
            res = check_data_loss_guardrail(cmd)
            assert res.action == GuardrailAction.DENY, f"Expected {cmd} to be blocked"

    def test_destructive_sql_denied(self) -> None:
        res = check_data_loss_guardrail("DROP TABLE customer_records;")
        assert res.action == GuardrailAction.DENY
        assert "Data loss guardrail violation" in (res.reason or "")

    def test_safe_sql_allowed(self) -> None:
        res = check_data_loss_guardrail("SELECT * FROM users WHERE active = 1;")
        assert res.action == GuardrailAction.ALLOW

    def test_hardened_pre_check_denies_destructive_run_command(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
        from sakthai.agent import security_hardening as sh

        sh._env_pinner = sh.EnvironmentVariablePinning()
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")
        res = guardrail(cmd_tool, {"command": "terraform destroy"}, store)
        assert res.action == GuardrailAction.DENY
        assert "Data loss guardrail violation" in (res.reason or "")

    def test_hardened_pre_check_allows_destructive_run_command_with_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
        from sakthai.agent import security_hardening as sh

        sh._env_pinner = sh.EnvironmentVariablePinning()
        guardrail = create_pre_execution_guardrail_hardened()
        store = MemoryStore(":memory:")
        cmd = "git reset --hard HEAD"
        token = DataLossGuardrail().generate_approval_token(cmd)
        cmd_tool = next(t for t in BUILTIN_TOOLS if t.name == "run_command")
        # Bypasses data loss check; reaches DEFAULT_POLICY check
        res = guardrail(cmd_tool, {"command": cmd, "approval_token": token}, store)
        # Note: DEFAULT_POLICY allows git reset (not rm -rf /), so action is ALLOW
        assert res.action == GuardrailAction.ALLOW


class TestProTip2ProgressiveDisclosureSkills:
    """Pro-Tip 2: Progressive disclosure for skills catalog rendering."""

    def test_render_empty_skills_returns_empty_string(self) -> None:
        result = render_skills_progressive_summary(names=["non_existent_skill_xyz"])
        assert result == ""

    def test_render_summary_with_mocked_skills(self) -> None:
        skills = [
            SkillInfo(
                name="Sak-code-review",
                path=Path("/skills/code-review/SKILL.md"),
                category="quality",
                description="Performs automated PR code review.",
            ),
            SkillInfo(
                name="Sak-cloud-deploy",
                path=Path("/skills/cloud-deploy/SKILL.md"),
                category="devops",
                description="Deploy to Cloud Run | with pipes and\nnewlines.",
            ),
        ]
        with patch("sakthai.skills.collect_skills", return_value=skills):
            output = render_skills_progressive_summary()
            assert "## Available Skills (Progressive Disclosure)" in output
            assert "| `Sak-code-review` | quality |" in output
            assert "| `Sak-cloud-deploy` | devops |" in output
            assert "\\| with pipes and newlines." in output

    def test_render_summary_filter_names(self) -> None:
        skills = [
            SkillInfo(
                name="Sak-skill-1",
                path=Path("/skills/1/SKILL.md"),
                category="cat1",
                description="Desc 1",
            ),
            SkillInfo(
                name="Sak-skill-2",
                path=Path("/skills/2/SKILL.md"),
                category="cat2",
                description="Desc 2",
            ),
        ]
        with patch("sakthai.skills.collect_skills", return_value=skills):
            output = render_skills_progressive_summary(names=["Sak-skill-1"], persona="sakthai")
            assert "Sak-skill-1" in output
            assert "Sak-skill-2" not in output


class TestProTip3ModelSelectionPresets:
    """Pro-Tip 3: Model selection presets (fast, reasoning, local, lead)."""

    def test_resolve_all_tiers_by_enum(self) -> None:
        for tier in ModelTier:
            preset = resolve_model_preset(tier)
            assert isinstance(preset, ModelPreset)
            assert preset.tier == tier
            assert preset.model_name
            assert 0.0 <= preset.temperature <= 1.0

    def test_resolve_all_tiers_by_string_case_insensitive(self) -> None:
        fast_preset = resolve_model_preset("FAST")
        assert fast_preset.tier == ModelTier.FAST
        assert fast_preset.model_name == "gemini-2.5-flash"

        reasoning_preset = resolve_model_preset("  Reasoning ")
        assert reasoning_preset.tier == ModelTier.REASONING
        assert reasoning_preset.model_name == "gemini-3.7-flash"

        local_preset = resolve_model_preset("local")
        assert local_preset.tier == ModelTier.LOCAL
        assert local_preset.provider == "local"

        lead_preset = resolve_model_preset("lead")
        assert lead_preset.tier == ModelTier.LEAD

    def test_resolve_invalid_tier_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown model tier"):
            resolve_model_preset("quantum_ai_9000")

        from enum import StrEnum

        class FakeTier(StrEnum):
            UNKNOWN = "unknown"

        with pytest.raises(ValueError, match="Unknown model tier"):
            resolve_model_preset(FakeTier.UNKNOWN)  # type: ignore[arg-type]

    def test_unified_agent_config_initializes_with_tier(self) -> None:
        cfg = UnifiedAgentConfig(name="test-agent", tier=ModelTier.REASONING)
        assert cfg.model == "gemini-3.7-flash"

        cfg_str = UnifiedAgentConfig(name="test-agent", tier="fast")
        assert cfg_str.model == "gemini-2.5-flash"


class TestProTip4EnvironmentIntrospection:
    """Pro-Tip 4: Environment introspection and wrap_with_isolated_runner."""

    def test_empty_command_returns_empty(self) -> None:
        assert wrap_with_isolated_runner("") == ""
        assert wrap_with_isolated_runner("   ") == ""

    def test_already_wrapped_commands_unchanged(self) -> None:
        for cmd in [
            "uv run pytest tests/",
            "poetry run python main.py",
            "pipenv run python script.py",
            "conda run python -c 'print()'",
            ".venv/bin/python main.py",
        ]:
            assert wrap_with_isolated_runner(cmd) == cmd

    def test_uv_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("", encoding="utf-8")
        assert wrap_with_isolated_runner("pytest tests/", tmp_path) == "uv run pytest tests/"
        assert wrap_with_isolated_runner("python script.py", tmp_path) == "uv run python script.py"
        assert wrap_with_isolated_runner("script.py", tmp_path) == "uv run python script.py"

    def test_poetry_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname='test'\n", encoding="utf-8")
        assert wrap_with_isolated_runner("pytest tests/", tmp_path) == "poetry run pytest tests/"

    def test_pipenv_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "Pipfile").write_text("[packages]\n", encoding="utf-8")
        assert (
            wrap_with_isolated_runner("python script.py", tmp_path) == "pipenv run python script.py"
        )

    def test_conda_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "environment.yml").write_text("name: base\n", encoding="utf-8")
        assert wrap_with_isolated_runner("pytest tests/", tmp_path) == "conda run pytest tests/"

    def test_venv_fallback_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        assert wrap_with_isolated_runner("pytest tests/", tmp_path) == ".venv/bin/pytest tests/"
        assert wrap_with_isolated_runner("python main.py", tmp_path) == ".venv/bin/python main.py"
        assert wrap_with_isolated_runner("main.py", tmp_path) == ".venv/bin/python main.py"

    def test_non_python_command_not_wrapped_unless_forced(self, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("", encoding="utf-8")
        assert wrap_with_isolated_runner("git status", tmp_path) == "git status"
        assert wrap_with_isolated_runner("git status", tmp_path, force=True) == "uv run git status"


class TestPlatformCLIPorTips:
    """CLI integration tests for wrap-cmd and antigravity --tier."""

    def test_wrap_cmd_cli(self, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("", encoding="utf-8")
        runner = CliRunner()
        res = runner.invoke(platform_cmd, ["wrap-cmd", "--path", str(tmp_path), "pytest tests/"])
        assert res.exit_code == 0
        assert "uv run pytest tests/" in res.output

    def test_antigravity_cli_with_tier(self) -> None:
        runner = CliRunner()
        mock_runner = AsyncMock()

        async def _mock_tokens(prompt: str):
            yield "Hello from tier"

        mock_runner.stream_chat = _mock_tokens

        with (
            patch("sakthai.cli.platform.AntigravityAgentRunner", return_value=mock_runner),
            patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"}),
        ):
            res = runner.invoke(
                platform_cmd, ["antigravity", "--tier", "reasoning", "Plan a refactor"]
            )
            assert res.exit_code == 0
            assert "gemini-3.7-flash" in res.output
            assert "Hello from tier" in res.output
