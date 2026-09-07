from unittest.mock import MagicMock, patch

import httpx
import pytest

from teams_copilot_mcp.graph_client import GraphAuthError, GraphClient


def _valid_credentials(monkeypatch):
    monkeypatch.setenv("MSGRAPH_TENANT_ID", "tenant-123")
    monkeypatch.setenv("MSGRAPH_CLIENT_ID", "client-123")
    monkeypatch.setenv("MSGRAPH_CLIENT_SECRET", "secret-123")


def test_request_raises_when_all_credentials_missing(monkeypatch):
    monkeypatch.delenv("MSGRAPH_TENANT_ID", raising=False)
    monkeypatch.delenv("MSGRAPH_CLIENT_ID", raising=False)
    monkeypatch.delenv("MSGRAPH_CLIENT_SECRET", raising=False)
    client = GraphClient()

    with pytest.raises(GraphAuthError) as exc_info:
        client.request("GET", "/me")

    message = str(exc_info.value)
    assert "MSGRAPH_TENANT_ID" in message
    assert "MSGRAPH_CLIENT_ID" in message
    assert "MSGRAPH_CLIENT_SECRET" in message


def test_request_names_only_the_missing_vars(monkeypatch):
    monkeypatch.setenv("MSGRAPH_TENANT_ID", "tenant-123")
    monkeypatch.delenv("MSGRAPH_CLIENT_ID", raising=False)
    monkeypatch.delenv("MSGRAPH_CLIENT_SECRET", raising=False)
    client = GraphClient()

    with pytest.raises(GraphAuthError) as exc_info:
        client.request("GET", "/me")

    message = str(exc_info.value)
    assert "MSGRAPH_TENANT_ID" not in message
    assert "MSGRAPH_CLIENT_ID" in message
    assert "MSGRAPH_CLIENT_SECRET" in message


def test_request_sends_bearer_token_from_acquired_access_token(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_response = httpx.Response(
        200, json={"value": "ok"}, request=httpx.Request("GET", "https://x")
    )
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "the-real-token",
        "expires_in": 3600,
    }

    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response) as mock_request,
    ):
        result = client.request("GET", "/me")

    sent_headers = mock_request.call_args.kwargs["headers"]
    assert sent_headers["Authorization"] == "Bearer the-real-token"


def test_token_is_cached_across_requests(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_response = httpx.Response(200, json={}, request=httpx.Request("GET", "https://x"))
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "cached-token",
        "expires_in": 3600,
    }

    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response),
    ):
        client.request("GET", "/me")
        client.request("GET", "/me")

    assert fake_app.acquire_token_for_client.call_count == 1


def test_raises_graph_auth_error_when_token_acquisition_fails(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "error": "invalid_client",
        "error_description": "bad secret",
    }

    with patch(
        "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
        return_value=fake_app,
    ):
        with pytest.raises(GraphAuthError) as exc_info:
            client.request("GET", "/me")

    message = str(exc_info.value)
    assert "invalid_client" in message
    assert "bad secret" in message


def test_204_response_returns_empty_dict(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_response = httpx.Response(204, request=httpx.Request("DELETE", "https://x"))
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "t",
        "expires_in": 3600,
    }

    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response),
    ):
        result = client.request("DELETE", "/me/something")

    assert result == {}


def test_non_2xx_response_raises(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_request = httpx.Request("GET", "https://graph.microsoft.com/v1.0/me")
    fake_response = httpx.Response(403, json={"error": "Forbidden"}, request=fake_request)
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "t",
        "expires_in": 3600,
    }

    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response),
    ):
        with pytest.raises(httpx.HTTPStatusError):
            client.request("GET", "/me")


def test_request_allows_valid_graph_absolute_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    fake_response = httpx.Response(
        200, json={"value": "ok"}, request=httpx.Request("GET", "https://x")
    )
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "token",
        "expires_in": 3600,
    }

    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response) as mock_request,
    ):
        client.request("GET", "https://graph.microsoft.com/v1.0/me")

    assert mock_request.call_args.args[1] == "https://graph.microsoft.com/v1.0/me"


def test_request_blocks_external_absolute_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Absolute URLs must target graph.microsoft.com"):
        client.request("GET", "https://attacker.com/leak")


def test_request_blocks_insecure_graph_absolute_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Only HTTPS is supported"):
        client.request("GET", "http://graph.microsoft.com/v1.0/me")


def test_request_blocks_protocol_relative_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="protocol-relative paths are blocked"):
        client.request("GET", "//attacker.com/leak")


def test_request_blocks_obfuscated_backslash_absolute_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Backslashes are not allowed"):
        client.request("GET", "https:\\\\graph.microsoft.com\\leak")


def test_request_blocks_path_traversal_relative_url(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "../beta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "/../beta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "me/../users")


def test_request_blocks_path_traversal_backslash(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "..\\beta\\me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "me\\..\\users")


def test_request_blocks_path_traversal_url_encoded(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%2e%2e/beta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%2e%2e%2fbeta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "me%2f%2e%2e%2fusers")


def test_request_blocks_double_and_multi_encoded_path_traversal(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    # Double encoded ".." -> %252e%252e
    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%252e%252e/beta/me")

    # Double encoded ".." and "/" together
    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%252e%252e%252fbeta/me")

    # Triple encoded ".." -> %25252e%25252e
    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%25252e%25252e/beta/me")

    # Double encoded "/" -> %252f
    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "me%252f%252e%252e%252fusers")


def test_request_blocks_custom_schemes_absolute_urls(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Only HTTPS is supported"):
        client.request("GET", "ftp://attacker.com/leak")

    with pytest.raises(ValueError, match="Only HTTPS is supported"):
        client.request("GET", "ws://attacker.com/leak")

    with pytest.raises(ValueError, match="Only HTTPS is supported"):
        client.request("GET", "gopher://attacker.com/leak")


def test_request_blocks_path_traversal_double_url_encoded(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%252e%252e/beta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "%252e%252e%252fbeta/me")

    with pytest.raises(ValueError, match="Path traversal sequences are not allowed"):
        client.request("GET", "me%252f%252e%252e%252fusers")
