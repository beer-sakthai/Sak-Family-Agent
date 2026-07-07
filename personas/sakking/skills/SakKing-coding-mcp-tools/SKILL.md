---
name: SakKing-coding-mcp-tools
category: coding
description: Add and wire tools in sakthai-agent-v2 — one definition surfaced through both the agent loop and the MCP stdio server, plus outbound MCP server discovery. Use when adding a built-in tool, editing the registry, or integrating an external MCP server.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - mcp
      - tools
      - registry
      - json-rpc
    related_skills:
      - sakthai-coding-llm-prompting
      - sakthai-coding-type-safety
      - sakthai-coding-testing
---

# sakthai-coding-mcp-tools

In `sakthai-agent-v2` a tool is defined **once** and appears on **two surfaces**:
the in-process agent loop and the MCP stdio server. The seam is
`agent/tools.py` (definitions) + `agent/registry.py` (lookup). v2 is also an MCP
*client*: `sakthai run` can discover tools from external servers and merge them
into the same registry for that run.

## When to use this skill

- Adding a new built-in tool the agent (and MCP clients) can call
- Editing `BUILTIN_TOOLS` or `ToolRegistry`
- Understanding why a tool shows up in both `sakthai run` and `sakthai mcp`
- Wiring an external MCP server into a run, or debugging a name clash
- Writing the inbound JSON-RPC server or testing its protocol

## One tool, one place

A `Tool` (frozen dataclass) pairs a model-facing JSON schema with a Python
handler `(args, store) -> str`. Add it to `BUILTIN_TOOLS` and it's live on both
surfaces — never define a tool twice.

```python
def _my_tool(args: dict[str, Any], store: MemoryStore) -> str:
    return str(store.do_something(args["value"]))

Tool(
    name="my_tool",
    description="What it does and WHEN the model should reach for it.",
    input_schema={
        "type": "object",
        "properties": {"value": {"type": "string", "description": "..."}},
        "required": ["value"],
    },
    handler=_my_tool,
)
```

Conventions to match the existing tools:

- **Description sells the *when*, not just the *what*** — the model picks tools
  off these strings (see `learn`/`recall`).
- **Handler returns a `str`.** Serialize structured results yourself (the codebase
  uses `json.dumps`); the loop and MCP both expect text content back.
- **Touch SQLite only via the `store` arg** — the handler receives a
  `MemoryStore`; don't open the DB directly.
- **Cap output.** Follow `MAX_FILE_READ_CHARS` / `MAX_CMD_OUTPUT_CHARS` patterns
  so a tool can't flood the context window.
- **Respect the sandbox.** `read_file` is restricted to cwd + `~/.sakthai` +
  `SAKTHAI_READ_ALLOW`; `run_command` is opt-in via `SAKTHAI_SHELL_ALLOW`. Don't
  widen these.

## The registry

`ToolRegistry` keys tools by name for both the loop and the server.
`builtin_registry()` wraps `BUILTIN_TOOLS`; `with_tools(extra)` returns a new
registry with extras merged. **On a name clash the later tool wins**, so a
plugin/MCP tool can deliberately shadow a built-in. It's immutable-style — build
a new registry rather than mutating one.

## Inbound: the MCP server is a pure function

`mcp/server.py`'s `handle_request(request, ...)` is a **pure function** mapping a
JSON-RPC 2.0 dict to a response dict. It implements `initialize`, `tools/list`,
`tools/call`, `ping`, and ignores `notifications/*`. Because it's pure, test the
protocol with plain dicts — no subprocess:

```python
resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
assert "tools" in resp["result"]
```

Tool errors are returned as content with `isError: true` (not raised), matching
how the loop surfaces tool failures back to the model.

## Outbound: merging external MCP servers

`sakthai run` can pull tools *in* from other servers:

- `mcp/servers.py` — discovers specs from `~/.sakthai/mcp.json` (primary) and each
  installed extension. **On a name clash `mcp.json` wins over an extension.**
- `mcp/client.py` — `StdioMCPClient` speaks JSON-RPC to one subprocess and
  `as_tools(prefix=...)` wraps each remote tool as a local `Tool`.
- `mcp/manager.py` — `connect_servers()` is a context manager: starts each server
  **failing soft** (a server that won't start is logged and skipped), yields the
  merged tools **namespaced `<server>__<tool>`** so they can't clash with
  built-ins, and tears them all down.

```python
with connect_servers() as mcp_tools:
    registry = builtin_registry().with_tools(mcp_tools)
```

## Common pitfalls

1. **Don't define a tool in two places.** One `Tool` in `BUILTIN_TOOLS` covers
   both surfaces.
2. **Don't raise out of a handler for expected failures.** Return an error string
   / structured error; the loop and server convert exceptions to `isError`
   results, but explicit messages read better to the model.
3. **Don't open SQLite in a handler** — use the injected `store` (keeps tests
   hermetic and the seam intact).
4. **Don't drop the `<server>__` namespace** when adding outbound tools — it's
   what prevents external tools from silently shadowing built-ins.
5. **Don't make `handle_request` impure** — its purity is what makes the protocol
   unit-testable. Keep I/O in `serve()`.
