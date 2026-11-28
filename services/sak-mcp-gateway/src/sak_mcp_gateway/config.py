"""Configuration settings for Sak MCP Gateway."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayConfig:
    """Gateway runtime configuration."""

    entra_tenant_id: str
    entra_audience: str
    entra_required_scope: str
    public_host: str
    port: int = 8000
    host: str = "127.0.0.1"
    work_iq_endpoint: str = "https://api.workiq.microsoft.com/mcp"
    mock_auth: bool = False

    @classmethod
    def from_env(cls) -> GatewayConfig:
        return cls(
            entra_tenant_id=os.environ.get("ENTRA_TENANT_ID", "common"),
            entra_audience=os.environ.get("ENTRA_AUDIENCE", "api://YOUR_DOMAIN.example"),
            entra_required_scope=os.environ.get("ENTRA_REQUIRED_SCOPE", "Sak.Read"),
            public_host=os.environ.get("SAK_MCP_PUBLIC_HOST", "YOUR_DOMAIN.example"),
            port=int(os.environ.get("PORT", "8000")),
            host=os.environ.get("HOST", "127.0.0.1"),
            work_iq_endpoint=os.environ.get(
                "WORK_IQ_ENDPOINT", "https://api.workiq.microsoft.com/mcp"
            ),
            mock_auth=os.environ.get("MOCK_AUTH", "false").lower() in ("true", "1", "yes"),
        )
