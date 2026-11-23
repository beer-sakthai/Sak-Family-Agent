"""Tool-list pagination and server-capability handling in the outbound client.

Two silent data losses, both in `start()`:

* `tools/list` was called once with no cursor and the reply's `nextCursor`
  ignored, so only the **first page** of a paginating server's tools was ever
  visible. Silent, because a short list looks exactly like a complete one.
* The `initialize` reply's `capabilities` object was discarded — `start()`
  checked for `"error"` and looked no further — so a server advertising no
  tools was asked for `tools/list` anyway, and the resulting error was logged
  by the manager as a failed server.
"""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.mcp.client import (
    MCPClientError,
    RemoteMCPClient,
    StdioMCPClient,
    _paginate_tools,
    _read_handshake,
    supports_tools,
)
from sakthai.mcp.protocol import LATEST_PROTOCOL_VERSION


def _pager(pages: list[dict[str, Any]]):
    """A fake `_request` serving `pages` in order, recording the cursors seen."""
    seen: list[Any] = []

    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        assert method == "tools/list"
        seen.append((params or {}).get("cursor"))
        return {"result": pages[len(seen) - 1]}

    request.seen = seen  # type: ignore[attr-defined]
    return request


# --- _paginate_tools ---------------------------------------------------------


def test_single_page_is_returned_whole() -> None:
    request = _pager([{"tools": [{"name": "a"}, {"name": "b"}]}])
    assert [t["name"] for t in _paginate_tools(request, "srv")] == ["a", "b"]


def test_all_pages_are_followed() -> None:
    """The regression: page two onward was never fetched."""
    request = _pager(
        [
            {"tools": [{"name": "a"}], "nextCursor": "c1"},
            {"tools": [{"name": "b"}], "nextCursor": "c2"},
            {"tools": [{"name": "c"}]},
        ]
    )
    assert [t["name"] for t in _paginate_tools(request, "srv")] == ["a", "b", "c"]
    assert request.seen == [None, "c1", "c2"]  # type: ignore[attr-defined]


def test_start_cursor_is_honoured() -> None:
    request = _pager([{"tools": [{"name": "b"}]}])
    assert [t["name"] for t in _paginate_tools(request, "srv", "c1")] == ["b"]
    assert request.seen == ["c1"]  # type: ignore[attr-defined]


def test_an_empty_cursor_ends_pagination() -> None:
    request = _pager([{"tools": [{"name": "a"}], "nextCursor": ""}])
    assert len(_paginate_tools(request, "srv")) == 1


def test_a_non_string_cursor_ends_pagination() -> None:
    request = _pager([{"tools": [{"name": "a"}], "nextCursor": 7}])
    assert len(_paginate_tools(request, "srv")) == 1


def test_a_repeated_cursor_does_not_spin() -> None:
    """A server echoing its own cursor back would otherwise loop forever."""
    calls = {"n": 0}

    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        calls["n"] += 1
        return {"result": {"tools": [{"name": f"t{calls['n']}"}], "nextCursor": "same"}}

    tools = _paginate_tools(request, "srv")
    assert calls["n"] == 2  # first page, then the repeat is detected
    assert len(tools) == 2


def test_runaway_pagination_is_bounded() -> None:
    """A server with an endless supply of fresh cursors is truncated, not hung."""
    calls = {"n": 0}

    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        calls["n"] += 1
        return {"result": {"tools": [{"name": f"t{calls['n']}"}], "nextCursor": f"c{calls['n']}"}}

    tools = _paginate_tools(request, "srv")
    assert calls["n"] == 50
    assert len(tools) == 50


def test_an_error_mid_pagination_raises() -> None:
    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if (params or {}).get("cursor"):
            return {"error": {"message": "nope"}}
        return {"result": {"tools": [{"name": "a"}], "nextCursor": "c1"}}

    with pytest.raises(MCPClientError, match="tools/list failed"):
        _paginate_tools(request, "srv")


def test_malformed_page_stops_cleanly() -> None:
    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"result": "not a dict"}

    assert _paginate_tools(request, "srv") == []


def test_non_dict_entries_are_skipped() -> None:
    request = _pager([{"tools": [{"name": "a"}, "junk", None, 7]}])
    assert [t["name"] for t in _paginate_tools(request, "srv")] == ["a"]


# --- _read_handshake ---------------------------------------------------------


def test_handshake_records_version_and_capabilities() -> None:
    version, caps = _read_handshake(
        {"result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}}}, "srv"
    )
    assert version == "2025-06-18"
    assert caps == {"tools": {}}


def test_handshake_defaults_when_the_reply_is_bare() -> None:
    version, caps = _read_handshake({"result": {}}, "srv")
    assert version == LATEST_PROTOCOL_VERSION
    assert caps == {}


def test_handshake_tolerates_a_malformed_result() -> None:
    version, caps = _read_handshake({"result": "nope"}, "srv")
    assert version == LATEST_PROTOCOL_VERSION
    assert caps == {}


def test_handshake_warns_but_accepts_an_unknown_version(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The manager fails soft per server; one odd server should not be silent."""
    with caplog.at_level("WARNING"):
        version, _ = _read_handshake({"result": {"protocolVersion": "2026-07-28"}}, "srv")
    assert version == "2026-07-28"
    assert "does not implement" in caplog.text


def test_handshake_ignores_non_dict_capabilities() -> None:
    _, caps = _read_handshake({"result": {"capabilities": ["tools"]}}, "srv")
    assert caps == {}


# --- supports_tools ----------------------------------------------------------


def test_empty_capabilities_is_treated_as_supporting_tools() -> None:
    """Servers in the wild are inconsistent about declaring it."""
    assert supports_tools({})


def test_a_declared_tools_capability_supports_tools() -> None:
    assert supports_tools({"tools": {"listChanged": False}})


def test_an_explicit_capabilities_object_without_tools_does_not() -> None:
    assert not supports_tools({"resources": {}, "prompts": {}})


# --- the clients -------------------------------------------------------------


def test_stdio_client_skips_tools_list_without_the_capability() -> None:
    client = StdioMCPClient("dummy", name="test")
    client._server_capabilities = {"resources": {}}
    calls: list[str] = []

    def request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        calls.append(method)
        return {"result": {"tools": []}}

    client._request = request  # type: ignore[method-assign]
    assert client._fetch_tools_if_supported() == []
    assert calls == []


def test_stdio_client_paginates_when_the_capability_is_present() -> None:
    client = StdioMCPClient("dummy", name="test")
    client._server_capabilities = {"tools": {}}
    client._request = _pager(  # type: ignore[method-assign]
        [
            {"tools": [{"name": "a"}], "nextCursor": "c1"},
            {"tools": [{"name": "b"}]},
        ]
    )
    assert [t["name"] for t in client._fetch_tools_if_supported()] == ["a", "b"]


def test_remote_client_list_tools_follows_pagination() -> None:
    client = RemoteMCPClient("https://example.com/mcp", name="test")
    client._request = _pager(  # type: ignore[method-assign]
        [
            {"tools": [{"name": "a"}], "nextCursor": "c1"},
            {"tools": [{"name": "b"}]},
        ]
    )
    assert [t["name"] for t in client.list_tools()] == ["a", "b"]


def test_remote_client_still_rejects_a_malformed_first_page() -> None:
    """The existing strict check on page one is kept."""
    client = RemoteMCPClient("https://example.com/mcp", name="test")
    client._request = lambda m, p=None: {"result": {}}  # type: ignore[method-assign]
    with pytest.raises(MCPClientError, match="malformed"):
        client.list_tools()
