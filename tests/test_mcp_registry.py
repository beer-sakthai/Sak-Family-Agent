"""The MCP registry client and the supply-chain check it enables.

Hermetic: every test injects a `Fetcher`, so nothing here reaches the network.
That is also the production posture — syncing is an explicit command, never
something an agent run does on its own.

The point of the module is the status field. An exact `npx` version pin, which
`tests/test_persona_security_config.py` enforces, stops an unreviewed *new*
release from running. It says nothing about the release you already pinned
being withdrawn upstream for malware, which is what `deleted` records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sakthai.mcp.registry import (
    API_VERSION,
    OFFICIAL_META_KEY,
    RegistryError,
    RegistryServer,
    check_configured_servers,
    iter_servers,
    parse_entry,
    read_cache,
    search,
    sync,
    write_cache,
)


def _entry(name: str, status: str = "active", **server: Any) -> dict[str, Any]:
    """A listing entry in the registry's own shape.

    Note `_meta` is a *sibling* of `server`, not inside it — getting that wrong
    silently loses every status, which is the whole point of the module.
    """
    return {
        "server": {"name": name, "description": f"{name} description", **server},
        "_meta": {
            OFFICIAL_META_KEY: {"status": status, "publishedAt": "2026-01-01", "isLatest": True}
        },
    }


def _pages(*pages: dict[str, Any]):
    """A Fetcher serving `pages` in order, recording the params it was given."""
    calls: list[dict[str, Any]] = []

    def fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
        calls.append({"url": url, **params})
        return pages[len(calls) - 1]

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


# --- parse_entry -------------------------------------------------------------


def test_parse_reads_the_nested_shape() -> None:
    server = parse_entry(_entry("io.github.acme/thing", version="1.2.3"))
    assert server is not None
    assert server.name == "io.github.acme/thing"
    assert server.version == "1.2.3"
    assert server.status == "active"
    assert server.is_latest is True


def test_parse_reads_the_status() -> None:
    assert parse_entry(_entry("a/b", status="deleted")).status == "deleted"


def test_parse_defaults_status_to_active_without_meta() -> None:
    """A subregistry need not add the official meta block."""
    server = parse_entry({"server": {"name": "a/b"}})
    assert server is not None
    assert server.status == "active"


def test_parse_reads_packages_and_remotes() -> None:
    server = parse_entry(
        _entry(
            "a/b",
            packages=[{"registryType": "npm", "identifier": "x"}, "junk"],
            remotes=[{"type": "streamable-http", "url": "https://x/mcp"}],
        )
    )
    assert server is not None
    assert len(server.packages) == 1  # the junk entry is dropped
    assert server.remotes[0]["type"] == "streamable-http"


def test_parse_reads_the_repository_url() -> None:
    server = parse_entry(_entry("a/b", repository={"url": "https://github.com/a/b"}))
    assert server is not None
    assert server.repository_url == "https://github.com/a/b"


@pytest.mark.parametrize(
    "bad",
    [None, "string", 42, {}, {"server": "not a dict"}, {"server": {}}, {"server": {"name": ""}}],
)
def test_parse_rejects_unusable_entries(bad: Any) -> None:
    """The name is the key everything joins on; without it the row is useless."""
    assert parse_entry(bad) is None


def test_is_problem_covers_deprecated_and_deleted() -> None:
    assert parse_entry(_entry("a/b", status="deprecated")).is_problem
    assert parse_entry(_entry("a/b", status="deleted")).is_problem
    assert not parse_entry(_entry("a/b", status="active")).is_problem


# --- iter_servers ------------------------------------------------------------


def test_single_page_is_returned() -> None:
    fetch = _pages({"servers": [_entry("a/b"), _entry("c/d")], "metadata": {"count": 2}})
    assert [s.name for s in iter_servers(fetcher=fetch)] == ["a/b", "c/d"]


def test_cursors_are_followed() -> None:
    fetch = _pages(
        {"servers": [_entry("a/b")], "metadata": {"nextCursor": "c1"}},
        {"servers": [_entry("c/d")], "metadata": {"nextCursor": "c2"}},
        {"servers": [_entry("e/f")], "metadata": {}},
    )
    assert [s.name for s in iter_servers(fetcher=fetch)] == ["a/b", "c/d", "e/f"]
    assert [c.get("cursor") for c in fetch.calls] == [None, "c1", "c2"]  # type: ignore[attr-defined]


def test_updated_since_is_sent_on_every_page() -> None:
    """Dropping it mid-walk would silently widen the window."""
    fetch = _pages(
        {"servers": [_entry("a/b")], "metadata": {"nextCursor": "c1"}},
        {"servers": [_entry("c/d")], "metadata": {}},
    )
    list(iter_servers(fetcher=fetch, updated_since="2026-01-01T00:00:00Z"))
    assert all(c["updated_since"] == "2026-01-01T00:00:00Z" for c in fetch.calls)  # type: ignore[attr-defined]


def test_the_url_targets_the_versioned_path() -> None:
    fetch = _pages({"servers": [], "metadata": {}})
    list(iter_servers(base_url="https://reg.example/", fetcher=fetch))
    assert fetch.calls[0]["url"] == f"https://reg.example/{API_VERSION}/servers"  # type: ignore[attr-defined]


def test_a_repeated_cursor_does_not_spin() -> None:
    calls = {"n": 0}

    def fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
        calls["n"] += 1
        return {"servers": [_entry(f"a/{calls['n']}")], "metadata": {"nextCursor": "same"}}

    assert len(list(iter_servers(fetcher=fetch))) == 2


def test_a_malformed_page_does_not_crash_the_walk() -> None:
    fetch = _pages({"servers": "not a list", "metadata": {}})
    assert list(iter_servers(fetcher=fetch)) == []


def test_fetch_failures_surface_as_registry_error() -> None:
    def fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
        raise RegistryError("boom")

    with pytest.raises(RegistryError):
        list(iter_servers(fetcher=fetch))


# --- the cache ---------------------------------------------------------------


def test_cache_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "servers.jsonl"
    servers = [parse_entry(_entry("a/b", status="deleted")), parse_entry(_entry("c/d"))]
    assert write_cache(servers, path) == 2
    back = read_cache(path)
    assert [s.name for s in back] == ["a/b", "c/d"]
    assert back[0].status == "deleted"


def test_cache_is_written_atomically(tmp_path: Path) -> None:
    """A failed sync must not leave a half-written file behind."""
    path = tmp_path / "servers.jsonl"
    write_cache([parse_entry(_entry("a/b"))], path)
    assert not list(tmp_path.glob("*.tmp"))


def test_cache_write_replaces_rather_than_appends(tmp_path: Path) -> None:
    """A full sync is the only way to learn an entry disappeared."""
    path = tmp_path / "servers.jsonl"
    write_cache([parse_entry(_entry("a/b")), parse_entry(_entry("c/d"))], path)
    write_cache([parse_entry(_entry("a/b"))], path)
    assert [s.name for s in read_cache(path)] == ["a/b"]


def test_missing_cache_reads_as_empty(tmp_path: Path) -> None:
    assert read_cache(tmp_path / "nope.jsonl") == []


def test_a_malformed_line_is_skipped(tmp_path: Path) -> None:
    """One bad row must not make the whole cache unreadable."""
    path = tmp_path / "servers.jsonl"
    path.write_text(
        json.dumps({"name": "a/b"}) + "\nnot json\n\n" + json.dumps({"name": "c/d"}) + "\n",
        encoding="utf-8",
    )
    assert [s.name for s in read_cache(path)] == ["a/b", "c/d"]


def test_sync_writes_what_it_fetched(tmp_path: Path) -> None:
    path = tmp_path / "servers.jsonl"
    fetch = _pages({"servers": [_entry("a/b"), _entry("c/d")], "metadata": {}})
    assert sync(path=path, fetcher=fetch) == 2
    assert len(read_cache(path)) == 2


# --- search ------------------------------------------------------------------


def _rows() -> list[RegistryServer]:
    return [
        parse_entry(_entry("io.github.acme/playwright")),
        parse_entry(_entry("io.github.acme/filesystem")),
        parse_entry(_entry("io.github.evil/backdoor", status="deleted")),
        parse_entry(_entry("io.github.old/retired", status="deprecated")),
    ]


def test_search_matches_the_name() -> None:
    assert [s.name for s in search("playwright", servers=_rows())] == ["io.github.acme/playwright"]


def test_search_matches_the_description() -> None:
    assert len(search("filesystem description", servers=_rows())) == 1


def test_search_is_case_insensitive() -> None:
    assert len(search("PLAYWRIGHT", servers=_rows())) == 1


def test_search_hides_withdrawn_servers() -> None:
    """Offering a withdrawn server as an install candidate is the opposite of
    what this module exists for."""
    names = {s.name for s in search("", servers=_rows())}
    assert "io.github.evil/backdoor" not in names
    assert "io.github.old/retired" not in names
    assert len(names) == 2


def test_search_can_include_withdrawn_servers() -> None:
    assert len(search("", servers=_rows(), include_problems=True)) == 4


def test_search_honours_the_limit() -> None:
    assert len(search("", servers=_rows(), limit=1)) == 1


def test_an_empty_query_lists_everything_active() -> None:
    assert len(search("", servers=_rows())) == 2


# --- the supply-chain check --------------------------------------------------


def test_a_withdrawn_server_is_reported_by_exact_name() -> None:
    found = check_configured_servers(["io.github.evil/backdoor"], servers=_rows())
    assert [(n, e.status) for n, e in found] == [("io.github.evil/backdoor", "deleted")]


def test_a_withdrawn_server_is_matched_by_its_tail() -> None:
    """Local names are whatever the operator wrote in mcp.json.

    They need not match the registry's namespaced `io.github.owner/repo` form,
    so a bare `backdoor` must still be caught.
    """
    found = check_configured_servers(["backdoor"], servers=_rows())
    assert len(found) == 1
    assert found[0][1].name == "io.github.evil/backdoor"


def test_tail_matching_is_case_insensitive() -> None:
    assert len(check_configured_servers(["BackDoor"], servers=_rows())) == 1


def test_active_servers_are_not_reported() -> None:
    assert check_configured_servers(["playwright", "filesystem"], servers=_rows()) == []


def test_a_deprecated_server_is_reported_too() -> None:
    found = check_configured_servers(["retired"], servers=_rows())
    assert found and found[0][1].status == "deprecated"


def test_unknown_servers_are_silent() -> None:
    """Most configured servers are not in the registry at all."""
    assert check_configured_servers(["something-local"], servers=_rows()) == []


def test_an_empty_cache_reports_nothing() -> None:
    assert check_configured_servers(["anything"], servers=[]) == []


class _FakeResponse:
    def __init__(self, body: Any, error: Exception | None = None) -> None:
        self._body = body
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error

    def json(self) -> Any:
        return self._body


def _patch_httpx_get(
    monkeypatch: pytest.MonkeyPatch, response: _FakeResponse
) -> list[dict[str, Any]]:
    import httpx

    calls: list[dict[str, Any]] = []

    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr(httpx, "get", fake_get)
    return calls


def test_httpx_fetcher_returns_the_decoded_object(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.mcp.registry import _httpx_fetcher

    calls = _patch_httpx_get(monkeypatch, _FakeResponse({"servers": []}))
    assert _httpx_fetcher(5.0)("https://r.example/v0/servers", {"limit": 1}) == {"servers": []}
    assert calls[0]["params"] == {"limit": 1}
    assert calls[0]["timeout"] == 5.0
    assert calls[0]["follow_redirects"] is True


def test_httpx_fetcher_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.mcp.registry import _httpx_fetcher

    _patch_httpx_get(monkeypatch, _FakeResponse({}, error=RuntimeError("503")))
    with pytest.raises(RegistryError, match="failed: 503"):
        _httpx_fetcher(1.0)("https://r.example", {})


def test_httpx_fetcher_rejects_a_non_object_body(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.mcp.registry import _httpx_fetcher

    _patch_httpx_get(monkeypatch, _FakeResponse(["not", "an", "object"]))
    with pytest.raises(RegistryError, match="non-object body"):
        _httpx_fetcher(1.0)("https://r.example", {})
