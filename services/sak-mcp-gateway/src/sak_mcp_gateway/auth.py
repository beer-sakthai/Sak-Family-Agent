"""Microsoft Entra ID (Azure AD) JWT token authentication and scope verification."""

from __future__ import annotations

import jwt
from jwt import PyJWKClient

from sak_mcp_gateway.config import GatewayConfig


class AuthenticationError(Exception):
    """Raised when JWT verification fails."""


class EntraJWTValidator:
    """Validates Entra ID OAuth 2.0 access tokens."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._jwks_url = (
            f"https://login.microsoftonline.com/{config.entra_tenant_id}/discovery/v2.0/keys"
        )
        self._jwks_client: PyJWKClient | None = None

    @property
    def jwks_client(self) -> PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self._jwks_url)
        return self._jwks_client

    def validate_token(self, token: str) -> dict:
        """Validate bearer token and verify required delegated scopes."""
        if not token:
            raise AuthenticationError("Authorization token is missing")

        if self.config.mock_auth:
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
            except Exception as err:
                raise AuthenticationError(f"Malformed JWT token: {err}") from err
            self._verify_scopes(claims)
            return claims

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.config.entra_audience,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                },
            )
        except jwt.PyJWTError as err:
            raise AuthenticationError(f"Invalid JWT: {err}") from err

        self._verify_scopes(claims)
        return claims

    def _verify_scopes(self, claims: dict) -> None:
        required_scope = self.config.entra_required_scope
        if not required_scope:
            return

        # Scopes can appear as space-delimited string in 'scp' or list in 'roles'
        raw_scp = claims.get("scp", "")
        scopes = set(raw_scp.split()) if isinstance(raw_scp, str) else set()
        roles = set(claims.get("roles", []))

        all_permissions = scopes | roles
        if required_scope not in all_permissions:
            raise AuthenticationError(
                f"Token lacks required scope '{required_scope}'. Present permissions: {sorted(all_permissions)}"
            )
