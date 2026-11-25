"""SakThai Runtime Gateway package.

Provides an OpenAI-compatible and REST API Gateway interface to House of Sak
agents, model tiers, and tools with DataLossGuardrail security.
"""

from __future__ import annotations

from .bench import GatewayTelemetryTracker, run_gateway_benchmark
from .config import GatewayConfig, resolve_gateway_config
from .memory import GatewayMemoryManager
from .router import GatewayRouter
from .server import RuntimeGatewayServer
from .voice import VOICE_PROFILES, GatewayVoiceHandler
from .webhooks import (
    WebhookPayload,
    dispatch_webhook_event,
    handle_auto_retrain,
    handle_bucket_job,
    handle_discussion_bot,
    handle_metadata_review,
    process_webhook_request,
    verify_webhook_secret,
)


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
    "VOICE_PROFILES",
    "GatewayConfig",
    "GatewayMemoryManager",
    "GatewayRouter",
    "GatewayTelemetryTracker",
    "GatewayVoiceHandler",
    "RuntimeGatewayServer",
    "WebhookPayload",
    "create_gateway_server",
    "dispatch_webhook_event",
    "handle_auto_retrain",
    "handle_bucket_job",
    "handle_discussion_bot",
    "handle_metadata_review",
    "process_webhook_request",
    "resolve_gateway_config",
    "run_gateway_benchmark",
    "verify_webhook_secret",
]
