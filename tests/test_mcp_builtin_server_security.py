"""Security properties of the MCP servers defined in code rather than config.

`mcp/servers.py` builds four servers from Python factories
(`BUILTIN_SERVER_FACTORIES`) and selects them per persona. They reach the model
and carry bearer tokens exactly as manifest servers do, but they were invisible
to every invariant in `test_persona_security_config.py` until that module's
`_mcp_servers()` grew to enumerate them — two parallel changes, each fine
alone, that between them left a whole class of server ungoverned.

That module now covers the host allowlist, HTTPS, npm pinning and literal
credentials for both sources. What it *cannot* check is the part that only
shows up when the environment is populated: a factory reads its credential
from `os.getenv` at construction, so with the env unset the headers are empty
and the credential assertions pass vacuously. These tests populate the
environment and check the properties that only exist then.
"""

from __future__ import annotations

import pytest

from sakthai.mcp.client import MCP_V2_AVAILABLE, is_mcp_v2_available
from sakthai.mcp.servers import (
    BUILTIN_SERVER_FACTORIES,
    STREAMABLE_HTTP,
    builtin_figma_server,
    builtin_google_dev_knowledge_server,
    builtin_huggingface_server,
)

#: (factory, env var it reads, header the credential lands in)
_CREDENTIALLED = [
    (builtin_figma_server, "FIGMA_ACCESS_TOKEN", "Authorization"),
    (builtin_huggingface_server, "HF_TOKEN", "Authorization"),
    (builtin_google_dev_knowledge_server, "GOOGLE_API_KEY", "x-goog-api-key"),
]


@pytest.fixture(autouse=True)
def _no_ambient_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """A real token in the developer's env would make these tests lie."""
    for var in (
        "FIGMA_ACCESS_TOKEN",
        "FIGMA_TOKEN",
        "HF_TOKEN",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)


# --- credentials come from the environment, never from the source -----------


@pytest.mark.parametrize(("factory", "env_var", "header"), _CREDENTIALLED)
def test_no_credential_without_an_env_var(factory, env_var: str, header: str) -> None:
    """With nothing in the environment there is no credential to leak."""
    assert factory().headers == {}


@pytest.mark.parametrize(("factory", "env_var", "header"), _CREDENTIALLED)
def test_the_credential_comes_from_the_environment(
    factory, env_var: str, header: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The token in the header is the one the env var holds, not a baked literal."""
    monkeypatch.setenv(env_var, "sentinel-token-value")
    headers = factory().headers
    assert any("sentinel-token-value" in v for v in headers.values()), headers
    assert header in headers


@pytest.mark.parametrize(("factory", "env_var", "header"), _CREDENTIALLED)
def test_no_factory_embeds_a_literal_secret(factory, env_var: str, header: str) -> None:
    """Guards the thing `_ENV_REFERENCE` guards for manifests.

    A manifest may only reference `${VAR}`; a factory's equivalent promise is
    that every header value is derived from the environment, so an empty
    environment yields no header at all.
    """
    import inspect

    source = inspect.getsource(factory)
    for marker in ("sk-", "ghp_", "hf_", "figd_", "Bearer ey"):
        assert marker not in source, f"{factory.__name__} looks like it embeds a secret"


def test_every_remote_builtin_uses_the_current_transport_name() -> None:
    """`"sse"` was deprecated in this package; the factories must not reintroduce it.

    They construct `MCPServerSpec` directly rather than going through
    `_parse_transport`, so nothing would warn if they used the old spelling.
    """
    for name, factory in BUILTIN_SERVER_FACTORIES.items():
        spec = factory()
        if spec.url:
            assert spec.transport == STREAMABLE_HTTP, f"{name} uses {spec.transport!r}"


def test_every_remote_builtin_is_https() -> None:
    for name, factory in BUILTIN_SERVER_FACTORIES.items():
        spec = factory()
        if spec.url:
            assert spec.url.startswith("https://"), f"{name}: {spec.url}"


# --- the SDK availability probe ---------------------------------------------


def test_the_probe_reports_the_module_level_flag() -> None:
    assert is_mcp_v2_available() is MCP_V2_AVAILABLE


@pytest.mark.parametrize("available", [True, False])
def test_both_probe_branches_behave(available: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin both outcomes rather than whichever the lockfile happens to give.

    `mcp` is importable here transitively, so the False branch is exercised by
    nobody and a packaging change elsewhere would flip it silently. Nothing in
    the package reads this flag today; these tests exist so that if something
    starts to, both paths are already covered.
    """
    import sakthai.mcp.client as client_mod

    monkeypatch.setattr(client_mod, "MCP_V2_AVAILABLE", available)
    assert client_mod.is_mcp_v2_available() is available
