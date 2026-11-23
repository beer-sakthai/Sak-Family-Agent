"""Security invariants for every persona's ``config/`` directory.

``sakthai run --persona X`` launches the stdio MCP servers listed in
``personas/X/config/mcp.json``, and ``config.yaml`` is the runtime
config each persona is deployed with. Both are edited by hand and by the
agent runtime itself, so nothing but a test keeps them safe:

* every ``npx`` server is pinned to an exact version. ``npx -y pkg@latest``
  installs and runs whatever was published last, on every launch, with no
  review; one compromised release would run on every persona at once.
* no dangerous-command category is pre-approved in ``command_allowlist``.
  An entry there skips the approval prompt for that category for good.
* every persona has a ``security`` block that fails closed, and approvals
  stay manual (cron jobs denied).
* remote MCP headers never carry a literal credential, only a ``${VAR}``
  reference or an empty value filled in at deploy time.
* every remote MCP server points at HTTPS and at a host on
  :data:`_ALLOWED_MCP_HOSTS`. A ``url`` was previously unconstrained, so any
  reachable endpoint passed — including a plaintext ``http://`` one, and
  including a host no reviewer had ever seen. A remote MCP server is handed a
  bearer token and its tool descriptions are fed to the model, so the host it
  resolves to is a trust decision and belongs in review, not in a diff nobody
  gates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
import yaml

from sakthai.config import PERSONA_NAMES

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"

# An npm package spec carrying an exact semver: ``pkg@1.2.3`` or
# ``@scope/pkg@1.2.3``. Ranges, dist-tags (``latest``) and bare names fail.
_PINNED_NPM_SPEC = re.compile(r"^(@[a-z0-9][\w.-]*/)?[a-z0-9][\w.-]*@\d+\.\d+\.\d+$")
_ENV_REFERENCE = re.compile(r"^(\w+ )?\$\{[A-Z][A-Z0-9_]*\}$")

#: Hosts the family's remote MCP servers may point at. Exact hostnames, no
#: wildcards: a wildcard would let a subdomain takeover through the gate, which
#: is the main thing this list exists to stop. Adding a host here is the review
#: step — do it in the same change that adds the server, and say why.
_ALLOWED_MCP_HOSTS = frozenset(
    {
        "agent.api.stepsecurity.io",  # StepSecurity supply-chain agent
        "microsoft365.mcp.claude.com",  # Microsoft 365 connector (read-only tool set)
        "learn.microsoft.com",  # Microsoft Learn docs, unauthenticated
        "gemini-api-docs-mcp.dev",  # Gemini API docs, unauthenticated
    }
)


def _load_yaml(persona: str) -> dict[str, Any]:
    path = PERSONAS_DIR / persona / "config" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} is not a mapping"
    return data


def _mcp_servers(persona: str) -> list[tuple[str, dict[str, Any]]]:
    """Every MCP server a persona declares, from both config files."""
    config_dir = PERSONAS_DIR / persona / "config"
    manifest = json.loads((config_dir / "mcp.json").read_text(encoding="utf-8"))
    servers = [(f"mcp.json:{name}", spec) for name, spec in manifest["mcpServers"].items()]
    yaml_servers = _load_yaml(persona).get("mcp_servers") or {}
    servers += [(f"config.yaml:{name}", spec) for name, spec in yaml_servers.items()]
    return servers


def _npx_package(args: list[str]) -> str:
    """The package ``npx`` would install: its first non-flag argument."""
    return next(arg for arg in args if not arg.startswith("-"))


@pytest.mark.parametrize("spec", ["pkg@1.2.3", "@scope/pkg@0.0.83", "chrome-devtools-mcp@1.10.1"])
def test_pinned_spec_pattern_accepts_exact_versions(spec: str) -> None:
    assert _PINNED_NPM_SPEC.match(spec)


@pytest.mark.parametrize(
    "spec", ["pkg", "@scope/pkg", "pkg@latest", "@scope/pkg@latest", "pkg@^1.2.3", "pkg@1.2"]
)
def test_pinned_spec_pattern_rejects_floating_versions(spec: str) -> None:
    assert not _PINNED_NPM_SPEC.match(spec)


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_npx_mcp_servers_are_version_pinned(persona: str) -> None:
    for name, spec in _mcp_servers(persona):
        if Path(str(spec.get("command", ""))).name not in {"npx", "npx.cmd"}:
            continue
        package = _npx_package([str(a) for a in spec.get("args", [])])
        assert _PINNED_NPM_SPEC.match(package), (
            f"personas/{persona} {name}: npx runs {package!r}; pin an exact version "
            "(pkg@X.Y.Z) so a new npm release cannot run unreviewed"
        )


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_no_dangerous_command_is_pre_approved(persona: str) -> None:
    config = _load_yaml(persona)
    assert "command_allowlist" in config, (
        f"personas/{persona}/config/config.yaml sets no command_allowlist"
    )
    allowlist = config["command_allowlist"]
    assert allowlist == [], (
        f"personas/{persona}/config/config.yaml pre-approves {allowlist}; each entry "
        "skips the approval prompt for that command category permanently"
    )


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_security_block_fails_closed(persona: str) -> None:
    config = _load_yaml(persona)
    for block in ("security", "approvals"):
        assert block in config, f"personas/{persona}/config/config.yaml has no {block} block"
    security = config["security"]
    assert security["tirith_enabled"] is True
    assert security["tirith_fail_open"] is False
    assert security["allow_lazy_installs"] is False
    assert security["redact_secrets"] is True
    assert security["allow_private_urls"] is False
    assert config["approvals"]["mode"] == "manual"
    assert config["approvals"]["cron_mode"] == "deny"


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_remote_mcp_servers_use_https(persona: str) -> None:
    for name, spec in _mcp_servers(persona):
        url = str(spec.get("url") or "")
        if not url:
            continue
        assert url.startswith("https://"), (
            f"personas/{persona} {name}: url {url!r} is not HTTPS. The request "
            "carries a bearer token, so plaintext would expose it on the wire"
        )


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_remote_mcp_servers_point_at_reviewed_hosts(persona: str) -> None:
    for name, spec in _mcp_servers(persona):
        url = str(spec.get("url") or "")
        if not url:
            continue
        host = (urlparse(url).hostname or "").lower()
        assert host in _ALLOWED_MCP_HOSTS, (
            f"personas/{persona} {name}: url points at {host!r}, which is not in "
            "_ALLOWED_MCP_HOSTS. A remote MCP server receives a bearer token and "
            "its tool descriptions reach the model — add the host to that list in "
            "this change, with a comment saying what it is"
        )


@pytest.mark.parametrize("persona", PERSONA_NAMES)
def test_mcp_headers_hold_no_literal_credentials(persona: str) -> None:
    for name, spec in _mcp_servers(persona):
        for header, value in (spec.get("headers") or {}).items():
            if header.lower() in {"accept", "content-type"}:
                continue
            assert value == "" or _ENV_REFERENCE.match(str(value)), (
                f"personas/{persona} {name}: header {header!r} holds a literal value; "
                "reference an environment variable (${VAR}) instead"
            )
