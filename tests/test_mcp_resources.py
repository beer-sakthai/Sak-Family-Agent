"""The resource registry and the MCP Apps (`ui://`) view.

`resources/list` and `resources/read` were a pair of hardcoded branches in
`mcp/server.py` serving one URI compared with `==`. `mcp/resources.py` makes
them a registry, the same seam `BUILTIN_TOOLS` gives tools.

The MCP Apps extension (`io.modelcontextprotocol/ui`, SEP-1865) is **Draft**,
so the view, the `_meta.ui` link on `recall` and the `capabilities.extensions`
declaration are all behind `SAKTHAI_EXPERIMENTAL`. These tests pin that the
three move together: a host must never be told about a view we would then
refuse to read.
"""

from __future__ import annotations

import json

import pytest

from sakthai.mcp.resources import (
    APP_MIME_TYPE,
    BUILTIN_RESOURCES,
    MEMORY_BROWSER_URI,
    TOOL_VIEWS,
    UI_EXTENSION,
    available,
    by_uri,
    tool_view_meta,
)
from sakthai.mcp.server import handle_request
from sakthai.memory.store import MemoryStore


@pytest.fixture
def experimental(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_EXPERIMENTAL", "1")


@pytest.fixture(autouse=True)
def _default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Draft extensions are off unless a test opts in."""
    monkeypatch.delenv("SAKTHAI_EXPERIMENTAL", raising=False)


# --- registry invariants -----------------------------------------------------


def test_resource_uris_are_unique() -> None:
    uris = [r.uri for r in BUILTIN_RESOURCES]
    assert len(set(uris)) == len(uris)


def test_the_app_view_uses_the_ui_scheme() -> None:
    """`ui://` is what tells a host this is an MCP Apps resource."""
    assert MEMORY_BROWSER_URI.startswith("ui://")


def test_the_app_view_declares_the_exact_mime_type() -> None:
    """The `profile` parameter is what distinguishes it from ordinary HTML.

    A host matching on the full string will not recognise bare `text/html`.
    """
    assert APP_MIME_TYPE == "text/html;profile=mcp-app"
    view = next(r for r in BUILTIN_RESOURCES if r.uri == MEMORY_BROWSER_URI)
    assert view.mime_type == APP_MIME_TYPE


def test_the_app_view_is_marked_experimental() -> None:
    view = next(r for r in BUILTIN_RESOURCES if r.uri == MEMORY_BROWSER_URI)
    assert view.experimental is True


def test_the_memory_status_resource_is_not_experimental() -> None:
    """It predates this work and must keep being served unconditionally."""
    status = next(r for r in BUILTIN_RESOURCES if r.uri == "sakthai://memory/status")
    assert status.experimental is False


# --- the experimental gate ---------------------------------------------------


def test_the_view_is_hidden_by_default() -> None:
    assert MEMORY_BROWSER_URI not in {r.uri for r in available()}


def test_the_view_appears_when_enabled(experimental: None) -> None:
    assert MEMORY_BROWSER_URI in {r.uri for r in available()}


def test_a_gated_resource_is_not_readable_by_uri() -> None:
    """Listing and reading must agree.

    A host that cached a listing from an enabled run must not still be able to
    fetch what we have since stopped offering.
    """
    assert by_uri(MEMORY_BROWSER_URI) is None


def test_a_gated_resource_is_readable_when_enabled(experimental: None) -> None:
    assert by_uri(MEMORY_BROWSER_URI) is not None


def test_by_uri_rejects_non_strings() -> None:
    assert by_uri(None) is None
    assert by_uri(42) is None


def test_by_uri_rejects_unknown_uris() -> None:
    assert by_uri("sakthai://nope") is None


# --- the tool link -----------------------------------------------------------


def test_recall_carries_the_view(experimental: None) -> None:
    assert tool_view_meta("recall") == {"ui": {"resourceUri": MEMORY_BROWSER_URI}}


def test_the_link_uses_the_nested_spelling(experimental: None) -> None:
    """The flat `_meta["ui/resourceUri"]` is deprecated and goes before GA."""
    meta = tool_view_meta("recall")
    assert "ui" in meta
    assert "ui/resourceUri" not in meta


def test_the_link_is_absent_by_default() -> None:
    assert tool_view_meta("recall") == {}


def test_a_tool_without_a_view_gets_no_meta(experimental: None) -> None:
    assert tool_view_meta("search") == {}


def test_every_tool_view_points_at_a_real_resource() -> None:
    uris = {r.uri for r in BUILTIN_RESOURCES}
    for tool_name, uri in TOOL_VIEWS.items():
        assert uri in uris, f"{tool_name} points at missing resource {uri}"


def test_every_tool_view_names_a_real_tool() -> None:
    from sakthai.agent.tools import BUILTIN_TOOLS

    names = {t.name for t in BUILTIN_TOOLS}
    for tool_name in TOOL_VIEWS:
        assert tool_name in names


# --- over the protocol -------------------------------------------------------


def test_resources_list_hides_the_view_by_default(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "resources/list"}, store)
    uris = {r["uri"] for r in resp["result"]["resources"]}
    assert "sakthai://memory/status" in uris
    assert MEMORY_BROWSER_URI not in uris


def test_resources_list_offers_the_view_when_enabled(
    store: MemoryStore, experimental: None
) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "resources/list"}, store)
    uris = {r["uri"] for r in resp["result"]["resources"]}
    assert MEMORY_BROWSER_URI in uris


def test_reading_the_view_returns_a_self_contained_document(
    store: MemoryStore, experimental: None
) -> None:
    """With `ui.csp` omitted the host blocks every external fetch.

    So the document must carry its own styles and script or it renders blank.
    """
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": MEMORY_BROWSER_URI},
        },
        store,
    )
    content = resp["result"]["contents"][0]
    assert content["mimeType"] == APP_MIME_TYPE
    html = content["text"]
    assert html.startswith("<!doctype html>")
    assert "<style>" in html and "<script>" in html
    for external in ('src="http', 'href="http', "cdn.", "fetch("):
        assert external not in html, f"view reaches outside the sandbox: {external}"


def test_the_view_speaks_the_apps_lifecycle(store: MemoryStore, experimental: None) -> None:
    """SEP-1865: request `ui/initialize`, then notify `ui/notifications/initialized`."""
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": MEMORY_BROWSER_URI},
        },
        store,
    )
    html = resp["result"]["contents"][0]["text"]
    assert "ui/initialize" in html
    assert "ui/notifications/initialized" in html
    assert "ui/notifications/tool-result" in html


def test_reading_the_gated_view_is_resource_not_found(store: MemoryStore) -> None:
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": MEMORY_BROWSER_URI},
        },
        store,
    )
    assert resp["error"]["code"] == -32002


def test_memory_status_still_reads_as_json(store: MemoryStore) -> None:
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "sakthai://memory/status"},
        },
        store,
    )
    content = resp["result"]["contents"][0]
    assert content["mimeType"] == "application/json"
    assert "fact_count" in json.loads(content["text"])


# --- capabilities ------------------------------------------------------------


def test_capabilities_omit_the_extension_by_default(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, store)
    assert "extensions" not in resp["result"]["capabilities"]


def test_capabilities_declare_the_extension_when_enabled(
    store: MemoryStore, experimental: None
) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, store)
    assert resp["result"]["capabilities"]["extensions"] == {UI_EXTENSION: {}}


def test_the_extension_id_is_the_spec_s_own() -> None:
    """Prefixes whose second label is `modelcontextprotocol` are reserved."""
    assert UI_EXTENSION == "io.modelcontextprotocol/ui"


def test_tools_list_carries_the_link_when_enabled(store: MemoryStore, experimental: None) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, store)
    recall = next(t for t in resp["result"]["tools"] if t["name"] == "recall")
    assert recall["_meta"]["ui"]["resourceUri"] == MEMORY_BROWSER_URI


def test_tools_list_omits_meta_by_default(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, store)
    for tool in resp["result"]["tools"]:
        assert "_meta" not in tool
