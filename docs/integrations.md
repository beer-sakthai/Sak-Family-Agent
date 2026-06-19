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

## Hermes (local, no cost)

[Hermes](https://github.com/) is a separate agent runtime installed at `~/.hermes`.
SakThai and Hermes interoperate over **local MCP stdio** — a subprocess JSON-RPC
channel, so there is **no network traffic and zero API/cloud cost** for the link
itself. (Reasoning still uses whichever LLM provider each agent is configured with;
pair this with a local Ollama model — see [`runtimes.md`](./runtimes.md) — for an
end-to-end no-cost setup.)

### Hermes → SakThai (already wired by Hermes)

Hermes registers SakThai's MCP server in its own `~/.hermes/config.yaml`, e.g.:

```yaml
mcp_servers:
  sakthai:
    command: /home/sakthai/sakthai-agent-v2/.venv/bin/sakthai
    args: [mcp]
    enabled: true
```

This lets Hermes read and write the shared `~/.sakthai/memory.db` through SakThai's
`learn` / `recall` / `search` / `forget` tools.

### SakThai → Hermes

Add Hermes to `~/.sakthai/mcp.json`. Its conversation/messaging tools then appear
in the SakThai agent loop namespaced `hermes__*`:

```json
{
  "mcpServers": {
    "hermes": { "command": "hermes", "args": ["mcp", "serve"] }
  }
}
```

If `hermes` is not on `PATH`, use the absolute path (e.g. `~/.local/bin/hermes`).
Verify discovery without spending anything:

```bash
sakthai run "list your tools" --dry-run     # preflight: prints tool_count, no API call
```

### Mirror Hermes-learned skills

Hermes accumulates *learned* (agent-created) skills over time. Import them into
this repo as first-class `sakthai-` skills:

```bash
sakthai skills sync-hermes            # import learned skills into skills/
sakthai skills sync-hermes --dry-run  # preview (idempotent: created / updated / unchanged)
sakthai skills sync-hermes --hermes-home /custom/.hermes/skills
```

The importer reads `$HERMES_HOME/skills` (default `~/.hermes/skills`), skips
bundled and `hermes-*` internal skills, rewrites each with this repo's canonical
frontmatter (recording `metadata.sakthai.source: hermes:<slug>`), and prefixes the
name with `sakthai-`. See [`plugins.md`](./plugins.md#-syncing-skills-hermes-has-learned).

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
