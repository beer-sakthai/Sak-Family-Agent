"""Configuration settings for the SakThai Runtime Gateway."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GatewayConfig:
    """Runtime Gateway operational settings."""

    host: str = "127.0.0.1"
    port: int = 8080
    bearer_token: str | None = None
    cors_origin: str | None = None
    request_timeout: float = 60.0
    rate_limit_per_minute: int = 120
    default_persona: str = "sakthai"
    workspace_dir: Path | None = None


def resolve_gateway_config(
    host: str | None = None,
    port: int | None = None,
    bearer_token: str | None = None,
    cors_origin: str | None = None,
    request_timeout: float | None = None,
    rate_limit_per_minute: int | None = None,
    default_persona: str | None = None,
    workspace_dir: Path | None = None,
) -> GatewayConfig:
    """Resolve GatewayConfig from explicit arguments falling back to environment variables.

    Environment variables:
        SAKTHAI_GATEWAY_HOST: Host address to bind (default: 127.0.0.1).
        SAKTHAI_GATEWAY_PORT: Port number to bind (default: 8080).
        SAKTHAI_GATEWAY_BEARER_TOKEN or SAKTHAI_GATEWAY_TOKEN: Optional API key.
        SAKTHAI_GATEWAY_CORS_ORIGIN: Allowed CORS origin.
        SAKTHAI_GATEWAY_TIMEOUT: Request timeout in seconds.
        SAKTHAI_GATEWAY_DEFAULT_PERSONA: Default persona name.
    """
    resolved_host = host or os.environ.get("SAKTHAI_GATEWAY_HOST") or "127.0.0.1"

    port_env = os.environ.get("SAKTHAI_GATEWAY_PORT")
    resolved_port = port if port is not None else (int(port_env) if port_env else 8080)

    resolved_token = (
        bearer_token
        or os.environ.get("SAKTHAI_GATEWAY_BEARER_TOKEN")
        or os.environ.get("SAKTHAI_GATEWAY_TOKEN")
    )
    if not resolved_token:
        try:
            from ..memory.store import MemoryStore

            with MemoryStore() as store:
                fact = store.get_fact_by_key(kind="web_auth", key="bearer_token")
                if fact:
                    resolved_token = fact.value
        except Exception:
            resolved_token = None

    resolved_cors = cors_origin or os.environ.get("SAKTHAI_GATEWAY_CORS_ORIGIN")

    timeout_env = os.environ.get("SAKTHAI_GATEWAY_TIMEOUT")
    resolved_timeout = (
        request_timeout
        if request_timeout is not None
        else (float(timeout_env) if timeout_env else 60.0)
    )

    resolved_default_persona = (
        default_persona or os.environ.get("SAKTHAI_GATEWAY_DEFAULT_PERSONA") or "sakthai"
    )

    return GatewayConfig(
        host=resolved_host,
        port=resolved_port,
        bearer_token=resolved_token,
        cors_origin=resolved_cors,
        request_timeout=resolved_timeout,
        rate_limit_per_minute=rate_limit_per_minute if rate_limit_per_minute is not None else 120,
        default_persona=resolved_default_persona,
        workspace_dir=workspace_dir,
    )
