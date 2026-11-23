"""`sakthai mcp registry` and the doctor supply-chain report.

Hermetic: `sync` is patched out, and every other command reads a cache this
test wrote. Nothing reaches the registry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.mcp.registry import OFFICIAL_META_KEY, parse_entry, write_cache


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _row(name: str, status: str = "active", version: str = "1.0.0") -> Any:
    return parse_entry(
        {
            "server": {"name": name, "description": f"{name} does things", "version": version},
            "_meta": {OFFICIAL_META_KEY: {"status": status, "isLatest": True}},
        }
    )


@pytest.fixture
def cache(sakthai_home: Path) -> Path:
    """A populated registry cache at the path the CLI reads."""
    path = sakthai_home / "registry" / "servers.jsonl"
    write_cache(
        [
            _row("io.github.acme/playwright"),
            _row("io.github.acme/filesystem"),
            _row("io.github.evil/backdoor", status="deleted"),
        ],
        path,
    )
    return path


# --- search ------------------------------------------------------------------


def test_search_lists_matches(runner: CliRunner, cache: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", "playwright"])
    assert result.exit_code == 0, result.output
    assert "io.github.acme/playwright" in result.output


def test_search_hides_withdrawn_servers(runner: CliRunner, cache: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", ""])
    assert result.exit_code == 0
    assert "backdoor" not in result.output


def test_search_can_show_withdrawn_servers(runner: CliRunner, cache: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", "", "--all"])
    assert result.exit_code == 0
    assert "backdoor" in result.output
    assert "deleted" in result.output


def test_search_json_output(runner: CliRunner, cache: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", "acme", "--json"])
    assert result.exit_code == 0
    rows = json.loads(result.output)
    assert {r["name"] for r in rows} == {
        "io.github.acme/playwright",
        "io.github.acme/filesystem",
    }


def test_search_reports_no_match(runner: CliRunner, cache: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", "nothing-like-this"])
    assert result.exit_code == 0
    assert "No match" in result.output


def test_search_without_a_cache_explains_itself(runner: CliRunner, sakthai_home: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "search", "x"])
    assert result.exit_code != 0
    assert "registry sync" in result.output


# --- check -------------------------------------------------------------------


def test_check_passes_when_nothing_is_withdrawn(
    runner: CliRunner, cache: Path, sakthai_home: Path
) -> None:
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"playwright": {"command": "npx"}}}), encoding="utf-8"
    )
    result = runner.invoke(main, ["mcp", "registry", "check"])
    assert result.exit_code == 0, result.output
    assert "active upstream" in result.output


def test_check_fails_when_a_configured_server_is_withdrawn(
    runner: CliRunner, cache: Path, sakthai_home: Path
) -> None:
    """Non-zero so it can gate a deploy.

    The local name `backdoor` is matched against `io.github.evil/backdoor` by
    its tail, because names in mcp.json are whatever the operator wrote.
    """
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"backdoor": {"command": "npx"}}}), encoding="utf-8"
    )
    result = runner.invoke(main, ["mcp", "registry", "check"])
    assert result.exit_code == 1
    assert "withdrawn upstream" in result.output
    assert "deleted" in result.output


def test_check_json_output(runner: CliRunner, cache: Path, sakthai_home: Path) -> None:
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"backdoor": {"command": "npx"}}}), encoding="utf-8"
    )
    result = runner.invoke(main, ["mcp", "registry", "check", "--json"])
    assert result.exit_code == 1
    rows = json.loads(result.output)
    assert rows[0]["configured_as"] == "backdoor"
    assert rows[0]["status"] == "deleted"


def test_check_without_a_cache_explains_itself(runner: CliRunner, sakthai_home: Path) -> None:
    result = runner.invoke(main, ["mcp", "registry", "check"])
    assert result.exit_code != 0
    assert "registry sync" in result.output


# --- sync --------------------------------------------------------------------


def test_sync_reports_what_it_cached(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    import sakthai.mcp.registry as registry_mod

    monkeypatch.setattr(registry_mod, "sync", lambda **kw: 7)
    result = runner.invoke(main, ["mcp", "registry", "sync"])
    assert result.exit_code == 0, result.output
    assert "Cached 7 server(s)" in result.output


def test_sync_surfaces_a_registry_failure(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    import sakthai.mcp.registry as registry_mod

    def boom(**_kw: Any) -> int:
        raise registry_mod.RegistryError("host unreachable")

    monkeypatch.setattr(registry_mod, "sync", boom)
    result = runner.invoke(main, ["mcp", "registry", "sync"])
    assert result.exit_code != 0
    assert "host unreachable" in result.output


def test_sync_honours_a_custom_registry_url(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    """Pointing at a private subregistry is the curation story."""
    monkeypatch.setenv("SAKTHAI_MCP_REGISTRY_URL", "https://registry.internal")
    import sakthai.mcp.registry as registry_mod

    monkeypatch.setattr(registry_mod, "sync", lambda **kw: 0)
    result = runner.invoke(main, ["mcp", "registry", "sync"])
    assert "https://registry.internal" in result.output


# --- doctor ------------------------------------------------------------------


def test_doctor_reports_a_withdrawn_server(
    runner: CliRunner, cache: Path, sakthai_home: Path
) -> None:
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"backdoor": {"command": "npx"}}}), encoding="utf-8"
    )
    result = runner.invoke(main, ["doctor"])
    assert "MCP supply chain" in result.output
    assert "deleted upstream" in result.output


def test_doctor_is_quiet_without_a_registry_cache(runner: CliRunner, sakthai_home: Path) -> None:
    """Syncing is an explicit choice; nagging about an unused feature is noise."""
    result = runner.invoke(main, ["doctor"])
    assert "MCP supply chain" not in result.output
