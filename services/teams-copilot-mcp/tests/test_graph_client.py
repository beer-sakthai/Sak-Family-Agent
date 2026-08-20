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
    ), pytest.raises(GraphAuthError) as exc_info:
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


def test_request_blocks_userinfo_in_absolute_urls(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Userinfo \\(username/password\\) is not allowed"):
        client.request("GET", "https://user:pass@graph.microsoft.com/v1.0/me")


def test_request_redacts_client_secret_and_token_from_exceptions(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    # Mock _get_token to raise a ValueError containing the secret and token
    client._token = "cached-token"
    with patch.object(client, "_get_token", side_effect=ValueError("Failed with secret-123 and cached-token")):
        with pytest.raises(ValueError) as exc_info:
            client.request("GET", "/me")

    # The exception string must NOT contain 'secret-123' or 'cached-token', but MUST contain '[REDACTED]'
    err_msg = str(exc_info.value)
    assert "secret-123" not in err_msg
    assert "cached-token" not in err_msg
    assert "[REDACTED]" in err_msg


def test_request_validates_http_methods(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    # Invalid non-string HTTP method
    with pytest.raises(ValueError, match="HTTP method must be a string"):
        client.request(123, "/me")  # type: ignore

    # Unsupported HTTP method
    with pytest.raises(ValueError, match="Unsupported or invalid HTTP method: INVALID"):
        client.request("INVALID", "/me")

    # Case-sensitive check: lowercase methods are invalid
    with pytest.raises(ValueError, match="Unsupported or invalid HTTP method: get"):
        client.request("get", "/me")

    # Supported valid HTTP methods should not raise a ValueError about the method
    fake_response = httpx.Response(
        200, json={"value": "ok"}, request=httpx.Request("GET", "https://x")
    )
    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "access_token": "token",
        "expires_in": 3600,
    }

    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
        with (
            patch(
                "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
                return_value=fake_app,
            ),
            patch.object(httpx.Client, "request", return_value=fake_response),
        ):
            client.request(method, "/me")


def test_request_blocks_non_string_paths(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Path must be a string"):
        client.request("GET", 123)  # type: ignore


def test_request_blocks_control_characters_in_paths(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        path = f"/me{bad_char}/messages"
        with pytest.raises(ValueError, match="Control characters are not allowed in paths"):
            client.request("GET", path)


def test_request_validates_query_params_type(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Query parameters must be a dictionary"):
        client.request("GET", "/me", params="not-a-dict")  # type: ignore


def test_request_validates_query_params_keys_type(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    with pytest.raises(ValueError, match="Query parameter keys must be strings"):
        client.request("GET", "/me", params={123: "value"})  # type: ignore


def test_request_blocks_control_characters_in_query_param_keys(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {f"key{bad_char}": "value"}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter keys"):
            client.request("GET", "/me", params=params)


def test_request_blocks_control_characters_in_query_param_values(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {"key": f"value{bad_char}"}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter values"):
            client.request("GET", "/me", params=params)


def test_request_blocks_control_characters_in_query_param_list_values(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {"key": ["good", f"bad{bad_char}"]}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter values"):
            client.request("GET", "/me", params=params)


def test_request_allows_valid_query_params(monkeypatch):
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

    params = {"$top": 10, "$orderby": "start/dateTime", "filter": ["name eq 'test'", "active"]}
    with (
        patch(
            "teams_copilot_mcp.graph_client.msal.ConfidentialClientApplication",
            return_value=fake_app,
        ),
        patch.object(httpx.Client, "request", return_value=fake_response) as mock_request,
    ):
        result = client.request("GET", "/me", params=params)

    assert result == {"value": "ok"}
    mock_request.assert_called_once()


def test_request_blocks_control_characters_in_query_param_dict_keys(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {"key": {f"inner{bad_char}": "value"}}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter keys"):
            client.request("GET", "/me", params=params)


def test_request_blocks_control_characters_in_query_param_dict_values(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {"key": {"inner": f"value{bad_char}"}}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter values"):
            client.request("GET", "/me", params=params)


def test_request_blocks_control_characters_in_query_param_nested_dict_and_sets(monkeypatch):
    _valid_credentials(monkeypatch)
    client = GraphClient()

    # Nested set containing a control character in its element
    for bad_char in ["\n", "\r", "\t", "\x00", "\x1f", "\x7f"]:
        params = {"key": {f"good", f"bad{bad_char}"}}
        with pytest.raises(ValueError, match="Control characters are not allowed in query parameter values"):
            client.request("GET", "/me", params=params)


def test_request_redacts_other_ms_graph_secrets_from_exceptions(monkeypatch):
    _valid_credentials(monkeypatch)
    # Inject extra secret env vars
    monkeypatch.setenv("MS_GRAPH_CLIENT_SECRET", "super-secret-1")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "refresh-secret-2")

    client = GraphClient()
    client._token = "cached-token"

    # Mock _get_token to raise a ValueError containing our extra environment secrets
    with patch.object(
        client,
        "_get_token",
        side_effect=ValueError("Failed with super-secret-1 and refresh-secret-2 and secret-123"),
    ):
        with pytest.raises(ValueError) as exc_info:
            client.request("GET", "/me")

    err_msg = str(exc_info.value)
    assert "super-secret-1" not in err_msg
    assert "refresh-secret-2" not in err_msg
    assert "secret-123" not in err_msg
    assert "[REDACTED]" in err_msg
