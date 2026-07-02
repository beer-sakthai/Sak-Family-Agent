"""Tests for sakthai.agent.providers detect_provider and build_client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from sakthai.agent.providers import AgentError, build_client, detect_provider

# -- detect_provider — client-based detection ------------------------------


def _client_with_module(module: str) -> object:
    class _Fake:
        pass

    _Fake.__module__ = module
    return _Fake()

@pytest.mark.parametrize(
    ("client", "model", "env", "creds", "expected"),
    [
        (None, "gateway/claude-3", {}, {}, "gateway"),
        (None, "gemini-1.5-pro", {}, {}, "google"),
        (_client_with_module("google.genai.client"), "m", {}, {}, "google"),
        (None, "local/my-model", {}, {}, "local"),
        (_client_with_module("openai._client"), "m", {}, {}, "openai"),
        (None, "gpt-4o", {}, {}, "openai"),
        (None, "ollama/llama3", {}, {}, "ollama"),
        (
            _client_with_module("anthropic._client"),
            "m",
            {},
            {},
            "anthropic",
        ),
        (None, "claude-3", {"GEMINI_API_KEY": "test"}, {}, "google"),
        (None, "claude-3", {}, {"openai": True}, "openai"),
        (None, "claude-3", {}, {"gateway": True}, "gateway"),
        (None, "claude-3", {}, {}, "anthropic"),  # Default fallback
    ],
)
def test_detect_provider_scenarios(client, model, env, creds, expected, monkeypatch):
    """Test provider detection logic across various signals."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with (
        patch(
            "sakthai.agent.providers.openai_credential_source",
            return_value="dummy" if creds.get("openai") else None,
        ),
        patch(
            "sakthai.agent.providers.gateway_credential_source",
            return_value="dummy" if creds.get("gateway") else None,
        ),
        patch(
            "sakthai.agent.providers.local_credential_source",
            return_value="dummy" if creds.get("local") else None,
        ),
        patch(
            "sakthai.agent.providers.anthropic_credential_source",
            return_value="dummy" if creds.get("anthropic") else None,
        ),
    ):
        assert detect_provider(client, model) == expected


def test_detect_provider_prefers_model_hint_over_client_and_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    with (
        patch("sakthai.agent.providers.openai_credential_source", return_value="dummy"),
        patch("sakthai.agent.providers.gateway_credential_source", return_value="dummy"),
    ):
        client = _client_with_module("anthropic._client")
        assert detect_provider(client, "gateway/claude-3") == "gateway"


def test_detect_gemini_via_client_module() -> None:
    client = _client_with_module("google.genai.client")
    assert detect_provider(client, "some-model") == "google"


def test_detect_openai_via_client_module() -> None:
    client = _client_with_module("openai._client")
    assert detect_provider(client, "some-model") == "openai"


def test_detect_anthropic_via_injected_client() -> None:
    client = _client_with_module("anthropic._client")
    assert detect_provider(client, "claude-3-5-sonnet-20241022") == "anthropic"


# -- detect_provider — model-name heuristics -------------------------------


@pytest.mark.parametrize("model", ["gemini-2.0-flash", "gemini-1.5-pro", "Gemini-Pro"])
def test_detect_gemini_model_name(model: str) -> None:
    assert detect_provider(None, model) == "google"


@pytest.mark.parametrize(
    "model",
    [
        "gpt-4o",
        "gpt-3.5-turbo",
        "qwen2.5-72b",
        "llama3.1",
        "deepseek-v2",
        "mistral-7b",
    ],
)
def test_detect_openai_model_keywords(model: str) -> None:
    assert detect_provider(None, model) == "openai"


@pytest.mark.parametrize("model", ["gateway/openai/gpt-4o", "gateway:claude", "Gateway-route"])
def test_detect_gateway_model_prefix(model: str) -> None:
    assert detect_provider(None, model) == "gateway"


# -- detect_provider — env-var fallbacks (no client, no model hint) --------


def test_detect_fallback_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with patch("sakthai.agent.providers.anthropic_credential_source", return_value="env"):
        assert detect_provider(None, "unknown-model") == "anthropic"


def test_detect_fallback_gemini_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "key123")
    with patch("sakthai.agent.providers.anthropic_credential_source", return_value=None):
        assert detect_provider(None, "unknown-model") == "google"


def test_detect_fallback_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey")
    with patch("sakthai.agent.providers.anthropic_credential_source", return_value=None):
        assert detect_provider(None, "unknown-model") == "google"


def test_detect_fallback_openai_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with (
        patch("sakthai.agent.providers.anthropic_credential_source", return_value=None),
        patch("sakthai.agent.providers.openai_credential_source", return_value="env"),
    ):
        assert detect_provider(None, "unknown-model") == "openai"


def test_detect_fallback_gateway_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with (
        patch("sakthai.agent.providers.anthropic_credential_source", return_value=None),
        patch("sakthai.agent.providers.openai_credential_source", return_value=None),
        patch("sakthai.agent.providers.gateway_credential_source", return_value="gateway_url"),
    ):
        assert detect_provider(None, "unknown-model") == "gateway"


def test_detect_fallback_default_is_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with (
        patch("sakthai.agent.providers.anthropic_credential_source", return_value=None),
        patch("sakthai.agent.providers.openai_credential_source", return_value=None),
        patch("sakthai.agent.providers.gateway_credential_source", return_value=None),
    ):
        assert detect_provider(None, "unknown-model") == "anthropic"


# -- build_client ----------------------------------------------------------


def test_build_client_returns_injected_client() -> None:
    sentinel = object()
    assert build_client("anthropic", sentinel) is sentinel


def test_build_client_anthropic_resolves_client() -> None:
    fake = MagicMock()
    with patch("sakthai.agent.providers.resolve_anthropic_client", return_value=fake):
        assert build_client("anthropic", None) is fake


def test_build_client_anthropic_auth_error_raises_agent_error() -> None:
    from sakthai.auth import AuthError

    with (
        patch(
            "sakthai.agent.providers.resolve_anthropic_client", side_effect=AuthError("no creds")
        ),
        pytest.raises(AgentError, match="no creds"),
    ):
        build_client("anthropic", None)


def test_build_client_openai_returns_httpx_client() -> None:
    with patch(
        "sakthai.auth.resolve_openai_credentials", return_value=("http://localhost:11434", "nokey")
    ):
        result = build_client("openai", None)
    assert isinstance(result, httpx.Client)


def test_build_client_openai_auth_error_raises_agent_error() -> None:
    from sakthai.auth import AuthError

    with (
        patch("sakthai.auth.resolve_openai_credentials", side_effect=AuthError("no openai creds")),
        pytest.raises(AgentError, match="no openai creds"),
    ):
        build_client("openai", None)


def test_build_client_gateway_returns_httpx_client() -> None:
    with patch(
        "sakthai.auth.resolve_gateway_credentials",
        return_value=("https://openrouter.ai/api/v1", "sk-test"),
    ):
        result = build_client("gateway", None)
    assert isinstance(result, httpx.Client)
    assert result.headers["Authorization"] == "Bearer sk-test"


def test_build_client_gateway_auth_error_raises_agent_error() -> None:
    from sakthai.auth import AuthError

    with (
        patch(
            "sakthai.auth.resolve_gateway_credentials",
            side_effect=AuthError("no gateway configured"),
        ),
        pytest.raises(AgentError, match="no gateway configured"),
    ):
        build_client("gateway", None)


def test_build_client_google_missing_key_raises_agent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # Ensure Gemini CLI OAuth token (if present on this machine) is not found.
    monkeypatch.setattr("sakthai.auth.load_gemini_cli_token", lambda: None)
    with pytest.raises(AgentError, match="Missing credentials for Google Gemini"):
        build_client("google", None)


def test_build_client_google_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_google_client = MagicMock()
    fake_genai = MagicMock()
    fake_genai.Client.return_value = fake_google_client
    # Patch the local import inside build_client
    with patch.dict(
        "sys.modules", {"google": MagicMock(genai=fake_genai), "google.genai": fake_genai}
    ):
        result = build_client("google", None)
    assert result is fake_google_client


def test_build_client_google_client_init_error_raises_agent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_genai = MagicMock()
    fake_genai.Client.side_effect = RuntimeError("bad api key")
    with (
        patch.dict(
            "sys.modules", {"google": MagicMock(genai=fake_genai), "google.genai": fake_genai}
        ),
        pytest.raises(AgentError, match="Failed to initialize Google Gemini client"),
    ):
        build_client("google", None)


# -- build_client — Gemini CLI OAuth / Vertex fallback ---------------------


def _gemini_oauth_modules(fake_genai: MagicMock) -> dict[str, MagicMock]:
    """sys.modules patch so the OAuth branch's `google.*` imports resolve."""
    return {
        "google": MagicMock(genai=fake_genai),
        "google.genai": fake_genai,
        "google.oauth2": MagicMock(),
        "google.oauth2.credentials": MagicMock(),
    }


def test_build_client_google_oauth_no_token_raises_agent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with (
        patch("sakthai.auth.load_gemini_cli_token", return_value=None),
        pytest.raises(AgentError, match="Missing credentials for Google Gemini"),
    ):
        build_client("google", None)


def test_build_client_google_oauth_uses_env_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-proj")
    fake_client = MagicMock()
    fake_genai = MagicMock()
    fake_genai.Client.return_value = fake_client
    with (
        patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token"),
        patch("subprocess.check_output") as check_output,
        patch.dict("sys.modules", _gemini_oauth_modules(fake_genai)),
    ):
        result = build_client("google", None)
    assert result is fake_client
    # With GOOGLE_CLOUD_PROJECT set, gcloud is never shelled out to.
    check_output.assert_not_called()
    _, kwargs = fake_genai.Client.call_args
    assert kwargs["vertexai"] is True
    assert kwargs["project"] == "my-proj"


def test_build_client_google_oauth_resolves_project_via_gcloud(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    fake_client = MagicMock()
    fake_genai = MagicMock()
    fake_genai.Client.return_value = fake_client
    with (
        patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token"),
        patch("subprocess.check_output", return_value="gcloud-proj\n") as check_output,
        patch.dict("sys.modules", _gemini_oauth_modules(fake_genai)),
    ):
        result = build_client("google", None)
    assert result is fake_client
    check_output.assert_called_once()
    _, kwargs = fake_genai.Client.call_args
    assert kwargs["project"] == "gcloud-proj"


def test_build_client_google_oauth_no_project_raises_agent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    fake_genai = MagicMock()
    with (
        patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token"),
        patch("subprocess.check_output", side_effect=FileNotFoundError("gcloud")),
        patch.dict("sys.modules", _gemini_oauth_modules(fake_genai)),
        pytest.raises(AgentError, match="Missing GCP Project ID"),
    ):
        build_client("google", None)


def test_build_client_google_oauth_client_init_error_raises_agent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-proj")
    fake_genai = MagicMock()
    fake_genai.Client.side_effect = RuntimeError("vertex down")
    with (
        patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token"),
        patch.dict("sys.modules", _gemini_oauth_modules(fake_genai)),
        pytest.raises(AgentError, match="Failed to initialize Google Gemini client with OAuth"),
    ):
        build_client("google", None)
