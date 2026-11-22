"""Comprehensive unit tests for LaunchDarkly AgentControl writing assistant."""

from __future__ import annotations

import json
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

# Stand-in modules for Python 3.11 environment where launchdarkly-ai-server (requires >= 3.12) is omitted
if "launchdarkly_ai_server" not in sys.modules:
    try:
        import launchdarkly_ai_server  # noqa: F401
    except ImportError:
        fake_ai = types.ModuleType("launchdarkly_ai_server")
        fake_ai.init_client = AsyncMock()
        fake_ai.inspect_config = AsyncMock()
        fake_ai.get_registered_handlers = MagicMock(
            return_value=[("Anthropic", "messages"), ("Anthropic", "agent")]
        )
        fake_ai.create_handler = MagicMock(
            side_effect=lambda key, fn, stream_fn=None: MagicMock(
                provides_for=key, _fn=fn, _stream_fn=stream_fn
            )
        )
        fake_ai.config = MagicMock()
        fake_ai.invoke = AsyncMock()
        sys.modules["launchdarkly_ai_server"] = fake_ai

if "launchdarkly_ai_claude_messages" not in sys.modules:
    try:
        import launchdarkly_ai_claude_messages  # noqa: F401
    except ImportError:
        fake_claude = types.ModuleType("launchdarkly_ai_claude_messages")
        dummy_h = MagicMock(
            provides_for=("Anthropic", "messages"),
            _fn=MagicMock(),
            _stream_fn=MagicMock(),
        )
        fake_claude.create_claude_messages_handler = MagicMock(return_value=dummy_h)
        sys.modules["launchdarkly_ai_claude_messages"] = fake_claude

import pytest
from click.testing import CliRunner

from sakthai.agent.writing_assistant import (
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_WRITING_CONFIG_KEY,
    DEFAULT_WRITING_INSTRUCTIONS,
    WritingAssistantConfig,
    WritingAssistantResult,
    _build_fallback_response,
    _extract_summary_from_rewrite,
    _extract_text_content,
    _get_registered_handlers,
    generate_writing,
    generate_writing_with_agentcontrol,
    get_writing_assistant_config,
    init_writing_assistant_client,
    inspect_writing_config,
)
from sakthai.cli import main


def test_writing_assistant_config_defaults() -> None:
    cfg = WritingAssistantConfig()
    assert cfg.sdk_key is None
    assert cfg.ai_config_key == DEFAULT_WRITING_CONFIG_KEY
    assert cfg.project_key == "default"
    assert cfg.environment_key == "production"
    assert cfg.service_name == "sakthai-writing-assistant"
    assert cfg.environment == "production"
    assert cfg.timeout_seconds == 10.0


def test_get_writing_assistant_config_custom_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LD_SDK_KEY", "sdk-test-custom-12345")
    monkeypatch.setenv("LAUNCHDARKLY_AI_CONFIG_KEY", "custom-config")
    monkeypatch.setenv("LAUNCHDARKLY_PROJECT_KEY", "proj-alpha")
    monkeypatch.setenv("LAUNCHDARKLY_ENVIRONMENT_KEY", "staging")
    monkeypatch.setenv("LD_SERVICE_NAME", "custom-service")
    monkeypatch.setenv("LD_ENVIRONMENT", "staging")

    cfg = get_writing_assistant_config()
    assert cfg.sdk_key == "sdk-test-custom-12345"
    assert cfg.ai_config_key == "custom-config"
    assert cfg.project_key == "proj-alpha"
    assert cfg.environment_key == "staging"
    assert cfg.service_name == "custom-service"
    assert cfg.environment == "staging"


@pytest.mark.asyncio
async def test_init_writing_assistant_client_no_sdk_key() -> None:
    cfg = WritingAssistantConfig(sdk_key=None)
    client = await init_writing_assistant_client(cfg)
    assert client is None


@pytest.mark.asyncio
async def test_init_writing_assistant_client_with_key() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch("launchdarkly_ai_server.init_client", new_callable=AsyncMock) as mock_init:
        mock_client = MagicMock()
        mock_init.return_value = mock_client
        res = await init_writing_assistant_client(cfg)
        assert res == mock_client
        mock_init.assert_awaited_once_with(
            {
                "sdkKey": "sdk-mock-key",
                "serviceName": cfg.service_name,
                "environment": cfg.environment,
            }
        )


@pytest.mark.asyncio
async def test_init_writing_assistant_client_error() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch("launchdarkly_ai_server.init_client", new_callable=AsyncMock) as mock_init:
        mock_init.side_effect = RuntimeError("Connection timeout")
        res = await init_writing_assistant_client(cfg)
        assert res is None


@pytest.mark.asyncio
async def test_inspect_writing_config_success() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    expected_variation = {
        "enabled": True,
        "config": {
            "provider": {"name": "Anthropic"},
            "instructions": "Custom prompt",
            "model": {"name": "claude-sonnet-4-6"},
        },
        "meta": {"mode": "agent"},
    }
    with (
        patch(
            "sakthai.agent.writing_assistant.init_writing_assistant_client", new_callable=AsyncMock
        ),
        patch("launchdarkly_ai_server.inspect_config", new_callable=AsyncMock) as mock_inspect,
    ):
        mock_inspect.return_value = expected_variation
        res = await inspect_writing_config(user_id="user-1", persona="sakjules", config=cfg)
        assert res == expected_variation


@pytest.mark.asyncio
async def test_inspect_writing_config_fallback() -> None:
    cfg = WritingAssistantConfig(sdk_key=None)
    res = await inspect_writing_config(user_id="user-1", persona="sakthai", config=cfg)
    assert res["enabled"] is True
    assert res["config"]["provider"]["name"] == "Anthropic"
    assert res["config"]["model"]["name"] == DEFAULT_FALLBACK_MODEL
    assert res["config"]["instructions"] == DEFAULT_WRITING_INSTRUCTIONS


def test_extract_text_content() -> None:
    assert _extract_text_content(None) == ""
    assert _extract_text_content("hello string") == "hello string"
    assert _extract_text_content({"text": "dict text"}) == "dict text"
    assert _extract_text_content({"output": "output text"}) == "output text"
    assert _extract_text_content({"content": "nested content"}) == "nested content"

    # Mock object with content attribute
    mock_obj = MagicMock()
    mock_obj.content = "content attribute"
    assert _extract_text_content(mock_obj) == "content attribute"

    # List of parts
    part1 = MagicMock()
    part1.text = "Hello "
    part2 = {"text": "World"}
    part3 = "!"
    mock_obj.content = [part1, part2, part3]
    assert _extract_text_content(mock_obj) == "Hello World!"


def test_extract_summary_from_rewrite() -> None:
    sample_rewrite = (
        "### Summary of changes: Fixed grammatical tense and clarified mission.\n\n"
        "### Improved Version:\nWe build high-performance agentic systems."
    )
    summary, text = _extract_summary_from_rewrite(sample_rewrite)
    assert summary == "Fixed grammatical tense and clarified mission."
    assert text == sample_rewrite

    no_summary = "Just plain text without change log"
    summary, text = _extract_summary_from_rewrite(no_summary)
    assert summary is None
    assert text == no_summary


def test_build_fallback_response_rewrite() -> None:
    res = _build_fallback_response("rewrite: this are bad words", persona="sakking")
    assert res.provider == "fallback"
    assert res.source == "house-of-sak-fallback"
    assert "Summary of Changes" in res.content
    assert "This are bad words." in res.content
    assert res.summary is not None


def test_build_fallback_response_summarize() -> None:
    res = _build_fallback_response(
        "summarize: Market expansion plan in APAC region", persona="saksee"
    )
    assert res.provider == "fallback"
    assert "Executive Summary" in res.content
    assert res.summary == "Executive bullet summary generated."


def test_build_fallback_response_draft() -> None:
    res = _build_fallback_response("Welcome letter for new team members", persona="saksit")
    assert res.provider == "fallback"
    assert "Welcome Letter For New Team Members" in res.content
    assert "saksit" in res.content
    assert res.summary is None


def test_get_registered_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    handlers = _get_registered_handlers()
    # At least 1 provider handler is loaded in this environment
    assert len(handlers) >= 1

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-mock-key")
    handlers_with_openai = _get_registered_handlers()
    assert len(handlers_with_openai) >= len(handlers)


def test_claude_handlers_creatable() -> None:
    import launchdarkly_ai_server as ai
    from launchdarkly_ai_claude_messages import create_claude_messages_handler

    h_msg = create_claude_messages_handler()
    assert h_msg.provides_for == ("Anthropic", "messages")

    h_agent = ai.create_handler(
        ("Anthropic", "agent"),
        h_msg._fn,
        stream_fn=h_msg._stream_fn,
    )
    assert h_agent.provides_for == ("Anthropic", "agent")


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_forced_fallback() -> None:
    res = await generate_writing_with_agentcontrol(
        "draft an announcement",
        force_fallback=True,
    )
    assert res.source == "house-of-sak-fallback"
    assert res.provider == "fallback"
    assert res.error == "LaunchDarkly SDK key not set or fallback forced"


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_disabled_config() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch(
        "sakthai.agent.writing_assistant.inspect_writing_config", new_callable=AsyncMock
    ) as mock_inspect:
        mock_inspect.return_value = {
            "enabled": False,
            "config": {"instructions": "Prompt", "model": {"name": "claude-sonnet-4-6"}},
        }
        res = await generate_writing_with_agentcontrol(
            "Draft notes",
            config=cfg,
        )
        assert res.source == "house-of-sak-fallback"
        assert res.error == f"Config {cfg.ai_config_key} disabled"


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_invoke_success() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    mock_resp = MagicMock()
    mock_resp.response = "Here is the completed draft."
    mock_resp.usage = {"input_tokens": 10, "output_tokens": 20}

    mock_conf_instance = MagicMock()
    mock_conf_instance.invoke = AsyncMock(return_value=mock_resp)

    with (
        patch(
            "sakthai.agent.writing_assistant.inspect_writing_config", new_callable=AsyncMock
        ) as mock_inspect,
        patch("launchdarkly_ai_server.config", return_value=mock_conf_instance),
    ):
        mock_inspect.return_value = {
            "enabled": True,
            "config": {
                "provider": {"name": "Anthropic"},
                "model": {"name": "claude-sonnet-4-6"},
                "instructions": "Instructions",
            },
            "meta": {"mode": "agent"},
        }
        res = await generate_writing_with_agentcontrol(
            "Write about telemetry",
            config=cfg,
        )
        assert isinstance(res, WritingAssistantResult)
        assert res.source == "launchdarkly-agentcontrol"
        assert res.provider == "Anthropic"
        assert res.model == "claude-sonnet-4-6"
        assert res.content == "Here is the completed draft."
        assert res.usage == {"input_tokens": 10, "output_tokens": 20}


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_invoke_failure_fallback() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    mock_conf_instance = MagicMock()
    mock_conf_instance.invoke = AsyncMock(side_effect=RuntimeError("Provider API timeout"))

    with (
        patch(
            "sakthai.agent.writing_assistant.inspect_writing_config", new_callable=AsyncMock
        ) as mock_inspect,
        patch("launchdarkly_ai_server.config", return_value=mock_conf_instance),
    ):
        mock_inspect.return_value = {
            "enabled": True,
            "config": {
                "provider": {"name": "Anthropic"},
                "model": {"name": "claude-sonnet-4-6"},
                "instructions": "Instructions",
            },
            "meta": {"mode": "agent"},
        }
        res = await generate_writing_with_agentcontrol(
            "rewrite: test words",
            config=cfg,
        )
        assert res.source == "house-of-sak-fallback"
        assert res.error == "RuntimeError: Provider API timeout"


def test_generate_writing_sync_interface() -> None:
    res = generate_writing("rewrite: sync test prompt", force_fallback=True)
    assert res.source == "house-of-sak-fallback"
    assert "Summary of Changes" in res.content


def test_cli_write_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "--help"])
    assert result.exit_code == 0
    assert "LaunchDarkly AgentControl" in result.output
    assert "--persona" in result.output
    assert "--inspect" in result.output
    assert "--fallback" in result.output
    assert "--raw" in result.output
    assert "--json" in result.output


def test_cli_write_inspect() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "--inspect"])
    assert result.exit_code == 0
    assert "gensandees-writing-assistant" in result.output
    assert "System Instructions" in result.output


def test_cli_write_inspect_json() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "--inspect", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "enabled" in data
    assert "config" in data


def test_cli_write_fallback_raw() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["write", "draft an email", "--fallback", "--raw", "--persona", "sakjules"]
    )
    assert result.exit_code == 0
    assert "Draft An Email" in result.output
    assert "sakjules" in result.output


def test_cli_write_fallback_json() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "summarize: Q3 results", "--fallback", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["source"] == "house-of-sak-fallback"
    assert data["provider"] == "fallback"
    assert "Executive Summary" in data["content"]


def test_cli_write_empty_prompt() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", ""])
    assert result.exit_code == 1
    assert "Error: prompt cannot be empty." in result.output


def test_cli_write_rich_output_with_summary() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "rewrite: Fix grammar errors", "--fallback"])
    assert result.exit_code == 0
    assert "Summary of Changes" in result.output
    assert "Writing Assistant" in result.output


def test_cli_write_rich_output_without_summary() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "Draft an announcement", "--fallback"])
    assert result.exit_code == 0
    assert "Writing Assistant" in result.output


def test_cli_write_inspect_raw() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "--inspect", "--raw"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "enabled" in data


def test_cli_write_stdin_input() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["write", "--fallback", "--raw"], input="Piped text here")
    assert result.exit_code == 0
    assert "Piped text here" in result.output


@pytest.mark.asyncio
async def test_generate_writing_in_running_async_loop() -> None:
    res = generate_writing("rewrite: async loop prompt", force_fallback=True)
    assert res.source == "house-of-sak-fallback"
    assert "Summary of Changes" in res.content


def test_ensure_env_loaded_exception() -> None:
    from sakthai.agent.writing_assistant import _ensure_env_loaded

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.read_text", side_effect=OSError("Read error")),
    ):
        _ensure_env_loaded()


@pytest.mark.asyncio
async def test_inspect_writing_config_exception() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with (
        patch(
            "sakthai.agent.writing_assistant.init_writing_assistant_client", new_callable=AsyncMock
        ),
        patch("launchdarkly_ai_server.inspect_config", side_effect=RuntimeError("LD error")),
    ):
        res = await inspect_writing_config(config=cfg)
        assert res["enabled"] is True
        assert res["meta"]["variationKey"] == "fallback"


def test_extract_text_content_deep() -> None:
    # Nested content dict
    nested = {"content": {"text": "inner text"}}
    assert _extract_text_content(nested) == "inner text"

    # Part without text
    mock_obj = MagicMock()
    mock_obj.content = [{"unknown": 123}]
    assert _extract_text_content(mock_obj) == ""


def test_build_fallback_response_edge_cases() -> None:
    # Empty cleaned text
    res1 = _build_fallback_response("rewrite:")
    assert res1.provider == "fallback"

    # Already punctuated
    res2 = _build_fallback_response("rewrite: already punctuated.")
    assert "Already punctuated." in res2.content


def test_get_registered_handlers_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.agent.writing_assistant import _get_registered_handlers

    with patch(
        "launchdarkly_ai_claude_messages.create_claude_messages_handler",
        side_effect=RuntimeError("Handler error"),
    ):
        handlers = _get_registered_handlers()
        assert isinstance(handlers, list)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    handlers2 = _get_registered_handlers()
    assert isinstance(handlers2, list)


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_no_handlers() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with (
        patch(
            "sakthai.agent.writing_assistant.inspect_writing_config", new_callable=AsyncMock
        ) as mock_insp,
        patch("sakthai.agent.writing_assistant._get_registered_handlers", return_value=[]),
    ):
        mock_insp.return_value = {
            "enabled": True,
            "config": {
                "provider": {"name": "Anthropic"},
                "model": {"name": "claude-sonnet-4-6"},
                "instructions": "Instructions",
            },
            "meta": {"mode": "agent"},
        }
        res = await generate_writing_with_agentcontrol("Test prompt", config=cfg)
        assert res.source == "house-of-sak-fallback"
        assert "RuntimeError: No compatible LaunchDarkly AI handlers installed" in (res.error or "")


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_usage_object() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")

    class FakeUsage:
        def __init__(self) -> None:
            self.input_tokens = 5
            self.output_tokens = 15

    mock_resp = MagicMock()
    mock_resp.response = "Sample output."
    mock_resp.usage = FakeUsage()

    mock_conf = MagicMock()
    mock_conf.invoke = AsyncMock(return_value=mock_resp)

    with (
        patch(
            "sakthai.agent.writing_assistant.inspect_writing_config", new_callable=AsyncMock
        ) as mock_insp,
        patch("launchdarkly_ai_server.config", return_value=mock_conf),
    ):
        mock_insp.return_value = {
            "enabled": True,
            "config": {
                "provider": {"name": "Anthropic"},
                "model": {"name": "claude-sonnet-4-6"},
                "instructions": "Instructions",
            },
            "meta": {"mode": "agent"},
        }
        res = await generate_writing_with_agentcontrol("Test prompt", config=cfg)
        assert res.source == "launchdarkly-agentcontrol"
        assert res.usage.get("input_tokens") == 5


@pytest.mark.asyncio
async def test_generate_writing_with_agentcontrol_missing_module() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch.dict(sys.modules, {"launchdarkly_ai_server": None}):
        res = await generate_writing_with_agentcontrol("Test prompt", config=cfg)
        assert res.source == "house-of-sak-fallback"
        assert "ModuleNotFoundError" in (res.error or "")


@pytest.mark.asyncio
async def test_init_writing_assistant_client_missing_module() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch.dict(sys.modules, {"launchdarkly_ai_server": None}):
        client = await init_writing_assistant_client(cfg)
        assert client is None


@pytest.mark.asyncio
async def test_inspect_writing_config_missing_module() -> None:
    cfg = WritingAssistantConfig(sdk_key="sdk-mock-key")
    with patch.dict(sys.modules, {"launchdarkly_ai_server": None}):
        data = await inspect_writing_config(config=cfg)
        assert data["enabled"] is True
        assert data["meta"]["variationKey"] == "fallback"
