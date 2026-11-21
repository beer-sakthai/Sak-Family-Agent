"""SakThai Runtime Gateway package.

Provides an OpenAI-compatible and REST API Gateway interface to House of Sak
agents, model tiers, and tools with DataLossGuardrail security.
"""

from __future__ import annotations

from .config import GatewayConfig, resolve_gateway_config
from .router import GatewayRouter
from .server import RuntimeGatewayServer


def create_gateway_server(
    host: str | None = None,
    port: int | None = None,
    bearer_token: str | None = None,
    cors_origin: str | None = None,
    default_persona: str | None = None,
) -> RuntimeGatewayServer:
    """Convenience factory to construct and return a RuntimeGatewayServer."""
    cfg = resolve_gateway_config(
        host=host,
        port=port,
        bearer_token=bearer_token,
        cors_origin=cors_origin,
        default_persona=default_persona,
    )
    router = GatewayRouter(config=cfg)
    return RuntimeGatewayServer(config=cfg, router=router)


__all__ = [
    "GatewayConfig",
    "GatewayRouter",
    "RuntimeGatewayServer",
    "create_gateway_server",
    "resolve_gateway_config",
]
