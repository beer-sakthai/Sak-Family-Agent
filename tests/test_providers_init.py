"""Tests for sakthai.agent.providers.__init__ (provider detection/client build)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.providers import (
    _build_anthropic_client,
    _build_google_client,
    _build_local_client,
    _build_ollama_client,
    _build_openai_compat_client,
    detect_provider,
)
from sakthai.agent.providers.base import AgentError
from sakthai.auth import AuthError


@pytest.mark.parametrize(
    ("client", "model", "env", "creds", "expected"),
    [
        (None, "gateway-claude-3", {}, {}, "gateway"),
        (None, "gemini-1.5-pro", {}, {}, "google"),
        (MagicMock(__class__=MagicMock(__module__="google.genai.client")), "m", {}, {}, "google"), (None, "local/my-model", {}, {}, "local"),
        (MagicMock(__class__=MagicMock(__module__="openai.lib.client")), "m", {}, {}, "openai"),
        (None, "gpt-4o", {}, {}, "openai"), (None, "ollama/llama3", {}, {}, "ollama"),
        (MagicMock(__class__=MagicMock(__module__="anthropic.lib.client")), "m", {}, {}, "anthropic"),
        (None, "claude-3", {"GEMINI_API_KEY": "test"}, {}, "google"),
        (None, "claude-3", {}, {"openai": True}, "openai"),
        (None, "claude-3", {}, {"gateway": True}, "gateway"),
        (None, "claude-3", {}, {}, "anthropic"),
    ],
)
def test_detect_provider(client, model, env, creds, expected, monkeypatch):
    """Test provider detection logic across various signals."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with patch(
        "sakthai.agent.providers.openai_credential_source",
        return_value="dummy" if creds.get("openai") else None,
    ), patch(
        "sakthai.agent.providers.gateway_credential_source",
        return_value="dummy" if creds.get("gateway") else None,
    ), patch(
        "sakthai.agent.providers.local_credential_source",
        return_value="dummy" if creds.get("local") else None,
    ):
        assert detect_provider(client, model) == expected


@patch("sakthai.agent.providers.resolve_anthropic_client")
def test_build_anthropic_client_success(mock_resolve):
    """Test _build_anthropic_client returns the resolved client."""
    mock_client = MagicMock()
    mock_resolve.return_value = mock_client
    client = _build_anthropic_client()
    assert client is mock_client
    mock_resolve.assert_called_once()


@patch("sakthai.agent.providers.resolve_anthropic_client", side_effect=AuthError("test err"))
def test_build_anthropic_client_auth_error(mock_resolve):
    """Test _build_anthropic_client raises AgentError on AuthError."""
    with pytest.raises(AgentError, match="test err"):
        _build_anthropic_client()


@patch("sakthai.agent.providers.resolve_openai_credentials")
def test_build_openai_compat_client_openai(mock_resolve):
    """Test _build_openai_compat_client for the 'openai' provider."""
    mock_resolve.return_value = ("https://api.openai.com/v1", "sk-key")
    client = _build_openai_compat_client("openai")
    assert client.base_url == "https://api.openai.com/v1"
    assert client.headers["Authorization"] == "Bearer sk-key"


@patch("sakthai.agent.providers.resolve_gateway_credentials")
def test_build_openai_compat_client_gateway(mock_resolve):
    """Test _build_openai_compat_client for the 'gateway' provider."""
    mock_resolve.return_value = ("https://my-gateway/v1", "gw-key")
    client = _build_openai_compat_client("gateway")
    assert client.base_url == "https://my-gateway/v1"
    assert client.headers["Authorization"] == "Bearer gw-key"


@patch("sakthai.agent.providers.resolve_openai_credentials", side_effect=AuthError("test err"))
def test_build_openai_compat_client_auth_error(mock_resolve):
    """Test _build_openai_compat_client raises AgentError on AuthError."""
    with pytest.raises(AgentError, match="test err"):
        _build_openai_compat_client("openai")


@patch("sakthai.agent.providers.resolve_ollama_credentials")
def test_build_ollama_client(mock_resolve):
    """Test _build_ollama_client for the 'ollama' provider."""
    mock_resolve.return_value = ("http://localhost:11434/v1", "nokey")
    client = _build_ollama_client()
    assert client.base_url == "http://localhost:11434/v1"


@patch("sakthai.agent.providers.resolve_ollama_credentials", side_effect=AuthError("test err"))
def test_build_ollama_client_auth_error(mock_resolve):
    """Test _build_ollama_client raises AgentError on AuthError."""
    with pytest.raises(AgentError, match="test err"):
        _build_ollama_client()


@patch("sakthai.agent.providers.resolve_local_credentials")
def test_build_local_client(mock_resolve):
    """Test _build_local_client for the 'local' provider."""
    mock_resolve.return_value = ("http://127.0.0.1:8000/v1", "local-key")
    client = _build_local_client()
    assert client.base_url == "http://127.0.0.1:8000/v1"


@patch("sakthai.agent.providers.resolve_local_credentials", side_effect=AuthError("test err"))
def test_build_local_client_auth_error(mock_resolve):
    """Test _build_local_client raises AgentError on AuthError."""
    with pytest.raises(AgentError, match="test err"):
        _build_local_client()


@patch("google.genai.Client")
def test_build_google_client_api_key(mock_genai_client, monkeypatch):
    """Test _build_google_client with an API key."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_instance = MagicMock()
    mock_genai_client.return_value = mock_instance

    client = _build_google_client()

    assert client is mock_instance
    mock_genai_client.assert_called_once_with(api_key="test-key")


@patch("google.genai.Client", side_effect=Exception("bad key"))
def test_build_google_client_api_key_fails(mock_genai_client, monkeypatch):
    """Test _build_google_client raises AgentError on bad API key."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    with pytest.raises(AgentError, match="Failed to initialize Google Gemini client: bad key"):
        _build_google_client()


@patch("google.genai.Client")
@patch("google.oauth2.credentials.Credentials")
@patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token")
@patch("subprocess.check_output", return_value="gcp-project-id\n")
def test_build_google_client_oauth(
    mock_check_output, mock_load_token, mock_creds, mock_genai_client, monkeypatch
):
    """Test _build_google_client with Gemini CLI OAuth credentials."""
    mock_creds_instance = MagicMock()
    mock_creds.return_value = mock_creds_instance
    mock_client_instance = MagicMock()
    mock_genai_client.return_value = mock_client_instance

    client = _build_google_client()

    assert client is mock_client_instance
    mock_load_token.assert_called_once()
    mock_check_output.assert_called_once_with(
        ["gcloud", "config", "get-value", "project"],
        stderr=subprocess.DEVNULL,
        text=True,
    )
    mock_creds.assert_called_once_with(token="oauth-token")
    mock_genai_client.assert_called_once_with(
        vertexai=True,
        project="gcp-project-id",
        location="us-central1",
        credentials=mock_creds_instance,
    )


@patch("sakthai.auth.load_gemini_cli_token", return_value=None)
def test_build_google_client_no_creds(mock_load_token):
    """Test _build_google_client raises AgentError when no credentials are found."""
    with pytest.raises(AgentError, match="Missing credentials for Google Gemini"):
        _build_google_client()


@patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token")
@patch("subprocess.check_output", side_effect=Exception("gcloud not found"))
def test_build_google_client_no_project(mock_check_output, mock_load_token, monkeypatch):
    """Test _build_google_client raises AgentError when no GCP project is found."""
    with pytest.raises(AgentError, match="Missing GCP Project ID"):
        _build_google_client()


@patch("google.genai.Client", side_effect=Exception("oauth failed"))
@patch("google.oauth2.credentials.Credentials")
@patch("sakthai.auth.load_gemini_cli_token", return_value="oauth-token")
def test_build_google_client_oauth_fails(mock_load_token, mock_creds, mock_genai_client, monkeypatch):
    """Test _build_google_client raises AgentError on OAuth client init failure."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "gcp-project-id")
    with pytest.raises(AgentError, match="Failed to initialize Google Gemini client with OAuth"):
        _build_google_client()