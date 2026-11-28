"""Tests for Microsoft Entra ID JWT authentication in sak_mcp_gateway."""

from __future__ import annotations

import jwt
import pytest
from sak_mcp_gateway.auth import AuthenticationError, EntraJWTValidator
from sak_mcp_gateway.config import GatewayConfig


@pytest.fixture
def test_config() -> GatewayConfig:
    return GatewayConfig(
        entra_tenant_id="test-tenant-id",
        entra_audience="api://test-audience",
        entra_required_scope="Sak.Read",
        public_host="test.example.com",
        mock_auth=True,
    )


@pytest.fixture
def validator(test_config: GatewayConfig) -> EntraJWTValidator:
    return EntraJWTValidator(test_config)


def test_empty_token_raises_error(validator: EntraJWTValidator) -> None:
    with pytest.raises(AuthenticationError, match="token is missing"):
        validator.validate_token("")


def test_malformed_token_raises_error(validator: EntraJWTValidator) -> None:
    with pytest.raises(AuthenticationError, match="Malformed JWT"):
        validator.validate_token("not-a-real-jwt")


def test_valid_token_with_required_scope(validator: EntraJWTValidator) -> None:
    payload = {
        "aud": "api://test-audience",
        "iss": "https://login.microsoftonline.com/test-tenant-id/v2.0",
        "sub": "user-123",
        "scp": "Sak.Read User.Read",
    }
    token = jwt.encode(payload, "mock-test-secret-key-with-at-least-32-bytes!", algorithm="HS256")
    claims = validator.validate_token(token)
    assert claims["sub"] == "user-123"
    assert "Sak.Read" in claims["scp"]


def test_token_with_roles_claim(validator: EntraJWTValidator) -> None:
    payload = {
        "aud": "api://test-audience",
        "roles": ["Sak.Read"],
    }
    token = jwt.encode(payload, "mock-test-secret-key-with-at-least-32-bytes!", algorithm="HS256")
    claims = validator.validate_token(token)
    assert claims["roles"] == ["Sak.Read"]


def test_missing_required_scope_raises_error(validator: EntraJWTValidator) -> None:
    payload = {
        "aud": "api://test-audience",
        "scp": "User.Read Mail.Read",
    }
    token = jwt.encode(payload, "mock-test-secret-key-with-at-least-32-bytes!", algorithm="HS256")
    with pytest.raises(AuthenticationError, match="lacks required scope 'Sak.Read'"):
        validator.validate_token(token)
