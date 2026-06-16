"""Cloud runtime stubs — a skeleton for Google ADK / Vertex AI deployment.

This package is a **roadmap stub** (todo Phase 10.4). It can describe a cloud
agent, report deployment readiness, and render a manifest, all without the heavy
``google-adk`` dependency at import time — that lives behind the optional
``cloud`` extra and is imported lazily when a real agent is built.
"""

from __future__ import annotations

from .runtime import (
    DEFAULT_CLOUD_MODEL,
    CloudAgentSpec,
    CloudRuntimeError,
    adk_installed,
    build_adk_agent,
    cloud_status,
    render_manifest,
    resolve_cloud_spec,
)
from .tools import MEMORY_TOOL_FUNCTIONS

__all__ = [
    "DEFAULT_CLOUD_MODEL",
    "MEMORY_TOOL_FUNCTIONS",
    "CloudAgentSpec",
    "CloudRuntimeError",
    "adk_installed",
    "build_adk_agent",
    "cloud_status",
    "render_manifest",
    "resolve_cloud_spec",
]
