"""App-only Microsoft Graph client (client-credentials flow).

Reuses the MSGRAPH_TENANT_ID / MSGRAPH_CLIENT_ID / MSGRAPH_CLIENT_SECRET env
var convention already established by the `hermes teams-pipeline` skill, so
the same Azure AD app registration can back both.
"""

from __future__ import annotations

import os
import time
from typing import Any
import urllib.parse

import httpx
import msal

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


class GraphAuthError(RuntimeError):
    pass


class GraphClient:
    def __init__(self) -> None:
        self._tenant_id = os.environ.get("MSGRAPH_TENANT_ID")
        self._client_id = os.environ.get("MSGRAPH_CLIENT_ID")
        self._client_secret = os.environ.get("MSGRAPH_CLIENT_SECRET")
        self._app: msal.ConfidentialClientApplication | None = None
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = httpx.Client(base_url=GRAPH_BASE, timeout=30.0)

    def _require_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("MSGRAPH_TENANT_ID", self._tenant_id),
                ("MSGRAPH_CLIENT_ID", self._client_id),
                ("MSGRAPH_CLIENT_SECRET", self._client_secret),
            )
            if not value
        ]
        if missing:
            raise GraphAuthError(
                "Missing required env var(s): "
                + ", ".join(missing)
                + ". See services/teams-copilot-mcp/README.md."
            )

    def _get_app(self) -> msal.ConfidentialClientApplication:
        if self._app is None:
            self._require_config()
            self._app = msal.ConfidentialClientApplication(
                client_id=self._client_id,
                client_credential=self._client_secret,
                authority=f"https://login.microsoftonline.com/{self._tenant_id}",
            )
        return self._app

    def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token

        app = self._get_app()
        result = app.acquire_token_for_client(scopes=GRAPH_SCOPE)
        if "access_token" not in result:
            raise GraphAuthError(
                f"Token acquisition failed: {result.get('error')} — "
                f"{result.get('error_description')}"
            )

        self._token = result["access_token"]
        # Refresh a minute early to avoid edge-of-expiry failures mid-call.
        self._token_expires_at = time.monotonic() + int(result.get("expires_in", 3600)) - 60
        return self._token

    def _redact(self, text: str) -> str:
        """Redact sensitive credentials (client secret, access token) from any string."""
        if not isinstance(text, str):
            return text
        if self._client_secret and self._client_secret in text:
            text = text.replace(self._client_secret, "[REDACTED]")
        if self._token and self._token in text:
            text = text.replace(self._token, "[REDACTED]")
        # Defense-in-depth: also redact other Microsoft Graph secrets from the env
        for env_var in ("MS_GRAPH_REFRESH_TOKEN", "MS_GRAPH_CLIENT_SECRET"):
            val = os.environ.get(env_var)
            if val and val in text:
                text = text.replace(val, "[REDACTED]")
        return text

    def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        """Call an arbitrary Graph endpoint.

        `path` is relative to the v1.0 base (e.g. "/me/joinedTeams") unless
        it's already a full URL (Graph pagination @odata.nextLink values are
        full URLs — pass those straight through).
        """
        # HTTP Method Validation:
        if not isinstance(method, str):
            raise ValueError("HTTP method must be a string")
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
            raise ValueError(f"Unsupported or invalid HTTP method: {method}")

        # Path Validation:
        if not isinstance(path, str):
            raise ValueError("Path must be a string")
        if any(ord(c) < 32 or ord(c) == 127 for c in path):
            raise ValueError("Control characters are not allowed in paths")

        # Query Parameters Validation:
        if params is not None:
            if not isinstance(params, dict):
                raise ValueError("Query parameters must be a dictionary")
            for k, v in params.items():
                if not isinstance(k, str):
                    raise ValueError("Query parameter keys must be strings")
                if any(ord(c) < 32 or ord(c) == 127 for c in k):
                    raise ValueError("Control characters are not allowed in query parameter keys")

                def _check_val(val: Any) -> None:
                    if isinstance(val, str):
                        if any(ord(c) < 32 or ord(c) == 127 for c in val):
                            raise ValueError("Control characters are not allowed in query parameter values")
                    elif isinstance(val, (list, tuple, set)):
                        for item in val:
                            _check_val(item)
                    elif isinstance(val, dict):
                        for r_k, r_v in val.items():
                            if isinstance(r_k, str):
                                if any(ord(c) < 32 or ord(c) == 127 for c in r_k):
                                    raise ValueError("Control characters are not allowed in query parameter keys")
                            _check_val(r_v)

                _check_val(v)

        try:
            # SSRF and Token Exfiltration protection:
            # Prevent protocol-relative URLs (e.g., //attacker.com)
            if path.startswith(("/", "\\")):
                if path.startswith(("//", "\\\\", "/\\", "\\/")):
                    raise ValueError("Invalid path format: protocol-relative paths are blocked")

            # If it has a scheme or a network location, treat as absolute/protocol-relative,
            # and strictly validate that it is HTTPS and targets graph.microsoft.com
            parsed = urllib.parse.urlparse(path)
            if parsed.scheme or parsed.netloc:
                if "\\" in path:
                    raise ValueError("Backslashes are not allowed in absolute URLs")
                scheme = parsed.scheme.lower()
                if scheme != "https":
                    raise ValueError("Only HTTPS is supported for absolute URLs")
                if parsed.username or parsed.password:
                    raise ValueError("Userinfo (username/password) is not allowed in absolute URLs")
                host = parsed.hostname
                if not host or host.casefold() != "graph.microsoft.com":
                    raise ValueError("Absolute URLs must target graph.microsoft.com")

            # Path traversal protection:
            # Validate that no relative path traversal segments ("..") are present in either raw or recursively URL-decoded path components up to 5 levels deep.
            parsed_url = urllib.parse.urlsplit(path)
            path_variants = [parsed_url.path]
            current = parsed_url.path
            for _ in range(5):
                unquoted = urllib.parse.unquote(current)
                if unquoted == current:
                    break
                path_variants.append(unquoted)
                current = unquoted

            for path_val in path_variants:
                # Normalize backslashes to slashes to handle Windows-style path delimiters
                normalized = path_val.replace("\\", "/")
                if ".." in normalized.split("/"):
                    raise ValueError("Path traversal sequences are not allowed")

            token = self._get_token()
            headers = {"Authorization": f"Bearer {token}"}
            url = path if path.startswith("http") else path

            response = self._http.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
            )
            if response.status_code == 204:
                return {}
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()
        except Exception as exc:
            # Redact client secret and active bearer token from any exception strings
            exc.args = (self._redact(str(exc)),)
            raise


_client: GraphClient | None = None


def get_client() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
