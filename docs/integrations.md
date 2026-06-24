# Integrations

How to connect SakThai to other running agents and tool services. This is the
"connect to a live system" companion to [`plugins.md`](./plugins.md) (which covers
*how* the MCP/skill runtime works) — here we give concrete recipes.

All external MCP servers are configured in `~/.sakthai/mcp.json` using the standard
`mcpServers` shape (Claude-Desktop-compatible). During `sakthai run`, SakThai
connects to each, merges its tools into the registry namespaced as
`<server>__<tool>`, and fails soft if a server won't start. `--no-mcp` disables
all of them.

---

## SakKing (local, no cost)

[SakKing](https://github.com/) is a separate agent runtime installed at `~/.sakking`.
SakThai and SakKing interoperate over **local MCP stdio** — a subprocess JSON-RPC
channel, so there is **no network traffic and zero API/cloud cost** for the link
itself. (Reasoning still uses whichever LLM provider each agent is configured with;
pair this with a local Ollama model — see [`runtimes.md`](./runtimes.md) — for an
end-to-end no-cost setup.)

### SakKing → SakThai (already wired by SakKing)

SakKing registers SakThai's MCP server in its own `~/.sakking/config.yaml`, e.g.:

```yaml
mcp_servers:
  sakthai:
    command: /home/sakthai/sakthai-agent-v2/.venv/bin/sakthai
    args: [mcp]
    enabled: true
```

This lets SakKing read and write the shared `~/.sakthai/memory.db` through SakThai's
`learn` / `recall` / `search` / `forget` tools.

### SakThai → SakKing

Add SakKing to `~/.sakthai/mcp.json`. Its conversation/messaging tools then appear
in the SakThai agent loop namespaced `sakking__*`:

```json
{
  "mcpServers": {
    "sakking": { "command": "sakking", "args": ["mcp", "serve"] }
  }
}
```

If `sakking` is not on `PATH`, use the absolute path (e.g. `~/.local/bin/sakking`).
Verify discovery without spending anything:

```bash
sakthai run "list your tools" --dry-run     # preflight: prints tool_count, no API call
```

### Mirror SakKing-learned skills

SakKing accumulates *learned* (agent-created) skills over time. Import them into
this repo as first-class `sakthai-` skills:

```bash
sakthai skills sync-sakking            # import learned skills into skills/
sakthai skills sync-sakking --dry-run  # preview (idempotent: created / updated / unchanged)
sakthai skills sync-sakking --sakking-home /custom/.sakking/skills
```

The importer reads `$SAKKING_HOME/skills` (default `~/.sakking/skills`), skips
bundled and `sakking-*` internal skills, rewrites each with this repo's canonical
frontmatter (recording `metadata.sakthai.source: sakking:<slug>`), and prefixes the
name with `sakthai-`. See [`plugins.md`](./plugins.md#-syncing-skills-sakking-has-learned).

---

## Composio

[Composio](https://composio.dev) exposes managed tool integrations over MCP.
Canonicalize the server spec in `~/.sakthai/mcp.json` (rather than only in a host
agent's config) so every SakThai runtime sees the same tools:

```json
{
  "mcpServers": {
    "composio": {
      "command": "npx",
      "args": ["-y", "@composio/mcp@latest"],
      "env": { "COMPOSIO_API_KEY": "your-key-here" }
    }
  }
}
```

> Keep secrets in the `env` block of `~/.sakthai/mcp.json` (which is outside the
> repo), never committed. Prefer local/edge tools where possible to keep token
> spend down.

---

## Any other MCP server

The same recipe works for any stdio MCP server (GitHub, SQLite, filesystem, …):

```json
{
  "mcpServers": {
    "sqlite-explorer": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/path/to/some.db"]
    }
  }
}
```

Its tools arrive as `sqlite-explorer__<tool>`. See [`plugins.md`](./plugins.md) for
loading rules and namespacing details.
