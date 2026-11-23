"""The resources the inbound MCP server serves, as a registry.

``resources/list`` and ``resources/read`` were a pair of hardcoded branches in
``mcp/server.py`` serving exactly one URI, compared with ``==``. This is the
same seam ``BUILTIN_TOOLS`` gives tools: add a :class:`Resource` here and both
methods pick it up, which is what makes an MCP App view possible without
touching the request handler.

**MCP Apps.** The ``ui://`` entry implements the MCP Apps extension
(``io.modelcontextprotocol/ui``, SEP-1865): a tool carries
``_meta.ui.resourceUri`` pointing at an HTML resource, and a host that supports
the extension renders that resource in a sandboxed iframe and pushes the tool's
result into it. The extension is **Draft**, so everything about it is gated
behind ``SAKTHAI_EXPERIMENTAL`` — see :func:`available`.

**What this does not do.** It serves the view; it does not host one. The
extension requires the iframe document be served by a server the *host*
controls, and makes the host responsible for the sandbox attributes, the CSP
and the ``ui/*`` postMessage methods. SakThai is a server, so the host side is
out of scope and recorded as such in ``docs/mcp-support-matrix.md``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .. import config
from ..memory.store import MemoryStore

#: MIME type for an MCP Apps view, verbatim from SEP-1865. The ``profile``
#: parameter is what distinguishes it from ordinary HTML, so it must be sent
#: exactly: a host matching on the full string will not recognise ``text/html``.
APP_MIME_TYPE = "text/html;profile=mcp-app"

#: The extension identifier, as negotiated in ``capabilities.extensions``.
UI_EXTENSION = "io.modelcontextprotocol/ui"


@dataclass(frozen=True)
class Resource:
    """One resource, with the reader that produces its body on demand."""

    uri: str
    name: str
    description: str
    mime_type: str
    #: Called with the store when the resource is read. Takes the store even
    #: when it does not need it, so the registry stays uniform.
    reader: Callable[[MemoryStore], str]
    #: True for a resource whose specification is still Draft upstream. Hidden
    #: unless ``SAKTHAI_EXPERIMENTAL`` is set.
    experimental: bool = False

    def descriptor(self) -> dict[str, Any]:
        """The ``resources/list`` entry for this resource."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


def _memory_status(store: MemoryStore) -> str:
    return json.dumps(
        {"fact_count": store.stats()["facts"]["total"], "health": store.healthcheck()}
    )


# The view is a single self-contained document on purpose. With ``ui.csp``
# omitted, the MCP Apps spec has the host apply
# ``default-src 'none'; script-src 'self' 'unsafe-inline'; … connect-src 'none'``
# — so no CDN, no external stylesheet, no fetch. Everything the view needs is
# inline or it does not work.
_MEMORY_BROWSER_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SakThai Memory</title>
<style>
  :root {
    color-scheme: light dark;
    --fg: #16181d; --fg-dim: #5c6370; --bg: #ffffff;
    --line: #e3e6ea; --accent: #3b6ea5;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --fg: #e6e8eb; --fg-dim: #9aa3ad; --bg: #16181d;
      --line: #2b2f36; --accent: #8ab4f8;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 16px; background: var(--bg); color: var(--fg);
    font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
  }
  h1 { font-size: 15px; margin: 0 0 12px; font-weight: 600; }
  #count { color: var(--fg-dim); font-weight: 400; }
  #filter {
    width: 100%; padding: 7px 10px; margin-bottom: 12px; color: var(--fg);
    background: transparent; border: 1px solid var(--line); border-radius: 6px;
    font: inherit;
  }
  #filter:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
  ul { list-style: none; margin: 0; padding: 0; }
  li { padding: 8px 0; border-top: 1px solid var(--line); }
  .k { color: var(--accent); font-weight: 600; }
  .v { white-space: pre-wrap; overflow-wrap: anywhere; }
  .meta { color: var(--fg-dim); font-size: 12px; margin-top: 2px; }
  #empty { color: var(--fg-dim); padding: 24px 0; text-align: center; }
</style>
</head>
<body>
<h1>Memory <span id="count"></span></h1>
<input id="filter" type="search" placeholder="Filter…" autocomplete="off">
<ul id="rows"></ul>
<div id="empty">Waiting for the tool result…</div>
<script>
(function () {
  "use strict";
  var rowsEl = document.getElementById("rows");
  var emptyEl = document.getElementById("empty");
  var countEl = document.getElementById("count");
  var filterEl = document.getElementById("filter");
  var items = [];
  var nextId = 1;
  var pending = {};

  function rpc(method, params) {
    var id = nextId++;
    window.parent.postMessage(
      { jsonrpc: "2.0", id: id, method: method, params: params || {} }, "*");
    return id;
  }
  function notify(method, params) {
    window.parent.postMessage(
      { jsonrpc: "2.0", method: method, params: params || {} }, "*");
  }

  // The tool returns text, so the view parses the lines it recognises rather
  // than receiving structured rows. Anything unparseable is shown verbatim,
  // which is the useful failure mode: never hide what the tool actually said.
  function parse(text) {
    var out = [];
    text.split(/\\r?\\n/).forEach(function (line) {
      var trimmed = line.trim();
      if (!trimmed) return;
      var m = /^[-*\\u2022]?\\s*(?:\\[(\\d+)\\]\\s*)?([\\w.:-]+)\\s*=\\s*(.+)$/.exec(trimmed);
      if (m) out.push({ id: m[1] || "", key: m[2], value: m[3] });
      else out.push({ id: "", key: "", value: trimmed });
    });
    return out;
  }

  function render() {
    var needle = filterEl.value.toLowerCase();
    var shown = items.filter(function (it) {
      return !needle ||
        (it.key + " " + it.value).toLowerCase().indexOf(needle) !== -1;
    });
    rowsEl.textContent = "";
    shown.forEach(function (it) {
      var li = document.createElement("li");
      if (it.key) {
        var k = document.createElement("span");
        k.className = "k";
        k.textContent = it.key + " ";
        li.appendChild(k);
      }
      var v = document.createElement("span");
      v.className = "v";
      v.textContent = it.value;
      li.appendChild(v);
      if (it.id) {
        var meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = "id " + it.id;
        li.appendChild(meta);
      }
      rowsEl.appendChild(li);
    });
    countEl.textContent = items.length
      ? "(" + shown.length + (shown.length === items.length ? "" : " of " + items.length) + ")"
      : "";
    emptyEl.style.display = shown.length ? "none" : "block";
    if (items.length && !shown.length) emptyEl.textContent = "Nothing matches that filter.";
  }

  function onResult(result) {
    var text = (result && result.content || [])
      .filter(function (b) { return b && b.type === "text"; })
      .map(function (b) { return b.text || ""; })
      .join("\\n");
    items = parse(text);
    if (!items.length) emptyEl.textContent = "No memory to show.";
    render();
  }

  filterEl.addEventListener("input", render);

  window.addEventListener("message", function (event) {
    var msg = event.data;
    if (!msg || msg.jsonrpc !== "2.0") return;
    if (msg.method === "ui/notifications/tool-result") {
      onResult(msg.params && msg.params.result);
    } else if (msg.id && pending[msg.id]) {
      delete pending[msg.id];
    }
  });

  // Lifecycle per SEP-1865: request ui/initialize, then notify initialized.
  // The host must send nothing before that notification.
  pending[rpc("ui/initialize", {
    appCapabilities: {},
    appInfo: { name: "SakThai Memory", version: "1.0.0" }
  })] = true;
  notify("ui/notifications/initialized", {});
})();
</script>
</body>
</html>
"""


def _memory_browser(_store: MemoryStore) -> str:
    return _MEMORY_BROWSER_HTML


#: The URI of the memory-browser view. ``ui://`` is what tells a host this is an
#: MCP Apps resource rather than ordinary content; the path after it is ours.
MEMORY_BROWSER_URI = "ui://sakthai/memory-browser.html"

BUILTIN_RESOURCES: tuple[Resource, ...] = (
    Resource(
        uri="sakthai://memory/status",
        name="Memory Store Status",
        description="Summary of active items and tags in SakThai memory",
        mime_type="application/json",
        reader=_memory_status,
    ),
    Resource(
        uri=MEMORY_BROWSER_URI,
        name="Memory Browser",
        description="An interactive view of the facts and observations a recall returned",
        mime_type=APP_MIME_TYPE,
        reader=_memory_browser,
        experimental=True,
    ),
)


#: Which tool each MCP App view belongs to, by tool name.
#:
#: The mapping lives here rather than as a field on ``Tool`` deliberately.
#: ``agent/tools.py`` is shared by the agent loop and this server, and
#: ``_meta.ui`` means nothing in the loop — putting it on the tool would push
#: MCP-App knowledge down a layer that does not have it, and would make
#: ``agent`` import from ``mcp``, inverting the dependency.
#:
#: ``recall`` carries the memory browser because its output is exactly what the
#: view exists to make browsable. ``visibility`` is left at its default of
#: ``["model", "app"]``: the model must keep being able to call ``recall`` on a
#: host with no UI at all.
TOOL_VIEWS: dict[str, str] = {"recall": MEMORY_BROWSER_URI}


def tool_view_meta(tool_name: str) -> dict[str, Any]:
    """The ``_meta`` fragment linking ``tool_name`` to its view, if it has one.

    Empty unless ``SAKTHAI_EXPERIMENTAL`` is set, which keeps ``tools/list``
    honest against ``resources/list``: the view is hidden by the same gate, so
    advertising the link would name a resource we would then refuse to read.

    Emits the nested ``_meta.ui.resourceUri`` spelling. The flat
    ``_meta["ui/resourceUri"]`` form is deprecated upstream and stated to be
    removed before the extension reaches GA — see ``mcp/lifecycle.py``.
    """
    uri = TOOL_VIEWS.get(tool_name)
    if uri is None or not config.sakthai_experimental():
        return {}
    return {"ui": {"resourceUri": uri}}


def available(resources: tuple[Resource, ...] = BUILTIN_RESOURCES) -> tuple[Resource, ...]:
    """The resources currently offered, after the experimental gate."""
    if config.sakthai_experimental():
        return resources
    return tuple(r for r in resources if not r.experimental)


def by_uri(uri: object, resources: tuple[Resource, ...] = BUILTIN_RESOURCES) -> Resource | None:
    """The offered resource with this URI, or None.

    Resolves against :func:`available`, so an experimental resource is not
    readable by URI while the gate is closed — listing and reading must agree,
    or a host that cached a listing could still fetch what we stopped offering.
    """
    if not isinstance(uri, str):
        return None
    return next((r for r in available(resources) if r.uri == uri), None)
