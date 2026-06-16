"""A skeleton for deploying SakThai's memory agent to Google Cloud.

This is a **roadmap stub**, not a wired-up deployment. It lets the package
describe a cloud agent (project, location, model, Vertex toggle), report whether
the host is ready to deploy one, and render a deployment manifest — all without
importing Google ADK at module load. The heavy ``google-adk`` / Vertex
dependencies live behind the optional ``cloud`` extra and are imported lazily in
:func:`build_adk_agent`, so importing this module (and running CI) never
requires them.

The agent it would build wires SakThai's persistent memory (:mod:`sakthai.cloud.tools`)
into a Gemini model via ADK, mirroring the local agent loop's memory surface.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any

import yaml

from .. import __version__
from ..auth import load_gemini_cli_token
from ..config import (
    google_cloud_location,
    google_cloud_project,
    google_cloud_staging_bucket,
    use_vertexai,
)
from .tools import MEMORY_TOOL_FUNCTIONS

# Default Gemini model for the cloud agent. Overridable per spec.
DEFAULT_CLOUD_MODEL = "gemini-2.0-flash"

# The import path ADK is published under; used for a cheap "is it installed?"
# probe that never actually imports the package.
_ADK_MODULE = "google.adk"


class CloudRuntimeError(RuntimeError):
    """Raised when a cloud agent cannot be built or deployed."""


@dataclass(frozen=True)
class CloudAgentSpec:
    """A declarative description of the agent we would deploy.

    Resolved from the environment by :func:`resolve_cloud_spec`; carries no
    live clients, so it is cheap to build and safe to log.
    """

    project: str | None
    location: str
    model: str
    staging_bucket: str | None
    use_vertex: bool

    def display_name(self) -> str:
        """A stable, human-readable name for the deployed agent."""
        return "sakthai-memory-agent"


def adk_installed() -> bool:
    """True when the optional ``google-adk`` dependency is importable."""
    try:
        return importlib.util.find_spec(_ADK_MODULE) is not None
    except (ImportError, ValueError):
        return False


def resolve_cloud_spec(model: str = DEFAULT_CLOUD_MODEL) -> CloudAgentSpec:
    """Build a :class:`CloudAgentSpec` from config/environment values."""
    return CloudAgentSpec(
        project=google_cloud_project(),
        location=google_cloud_location(),
        model=model,
        staging_bucket=google_cloud_staging_bucket(),
        use_vertex=use_vertexai(),
    )


def cloud_status() -> dict[str, Any]:
    """Report cloud-deployment readiness without touching the network.

    Readiness means: the ADK extra is installed, a GCP project is configured,
    and a Google credential (Vertex via project, or a Gemini token/key) is
    resolvable. Each signal is reported separately so ``sakthai cloud status``
    can show exactly what is missing.
    """
    spec = resolve_cloud_spec()
    has_adk = adk_installed()
    has_project = spec.project is not None
    has_credential = spec.use_vertex or load_gemini_cli_token() is not None
    return {
        "adk_installed": has_adk,
        "project": spec.project,
        "location": spec.location,
        "model": spec.model,
        "use_vertex": spec.use_vertex,
        "staging_bucket": spec.staging_bucket,
        "credential": has_credential,
        "ready": has_adk and has_project and has_credential,
    }


def render_manifest(spec: CloudAgentSpec | None = None) -> str:
    """Render a deployment manifest (YAML) for the given or resolved spec.

    The manifest is intentionally tool-agnostic: it captures everything a
    future deploy step needs (project, region, model, entrypoint, extra) so the
    actual deployment can be wired up without re-deriving configuration.
    """
    spec = spec or resolve_cloud_spec()
    manifest: dict[str, Any] = {
        "name": spec.display_name(),
        "version": __version__,
        "runtime": "google-adk",
        "model": spec.model,
        "project": spec.project or "<set GOOGLE_CLOUD_PROJECT>",
        "location": spec.location,
        "use_vertex": spec.use_vertex,
        "staging_bucket": spec.staging_bucket or "<set GOOGLE_CLOUD_STAGING_BUCKET>",
        "entrypoint": "sakthai.cloud.runtime:build_adk_agent",
        "tools": [fn.__name__ for fn in MEMORY_TOOL_FUNCTIONS],
        "extras": ["cloud"],
    }
    return yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False)


def build_adk_agent(spec: CloudAgentSpec | None = None) -> Any:
    """Construct the ADK agent wiring SakThai memory into a Gemini model.

    Lazily imports ``google.adk``; raises :class:`CloudRuntimeError` with an
    install hint when the optional ``cloud`` extra is not present. Returns the
    constructed ADK ``Agent`` (typed ``Any`` to avoid a hard dependency on the
    ADK stubs in strict type-checking).
    """
    if not adk_installed():
        raise CloudRuntimeError(
            'Google ADK is not installed. Install the cloud extra:\n    pip install -e ".[cloud]"'
        )
    spec = spec or resolve_cloud_spec()
    try:
        from google.adk.agents import Agent  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised only with the extra
        raise CloudRuntimeError(f"Failed to import Google ADK: {exc}") from exc

    return Agent(
        name=spec.display_name(),
        model=spec.model,
        instruction=(
            "You are SakThai, a personal learning agent with persistent memory. "
            "Use the memory tools to recall what you know and to save new facts."
        ),
        tools=list(MEMORY_TOOL_FUNCTIONS),
    )


__all__ = [
    "DEFAULT_CLOUD_MODEL",
    "CloudAgentSpec",
    "CloudRuntimeError",
    "adk_installed",
    "build_adk_agent",
    "cloud_status",
    "render_manifest",
    "resolve_cloud_spec",
]
