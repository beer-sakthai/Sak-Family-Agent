# Connecting Plugins & Skills

House of Sak features an extensible tool and skill runtime that lets you connect external Model Context Protocol (MCP) servers and inject custom domain skills dynamically.

---

## 🧩 Model Context Protocol (MCP) Servers

SakThai can automatically spawn, connect to, and route tool calls through external MCP servers communicating over standard input/output (stdio) or remote HTTP/SSE. For concrete recipes (SakKing, Composio, GitHub, SQLite, …) see [integrations.md](./integrations.md).

### Configuration (`mcp.json`)

To register external MCP servers, configure `~/.sakthai/mcp.json` (or persona configs under `personas/<name>/config/mcp.json`). It supports the standard `mcpServers` format:

```json
{
  "mcpServers": {
    "sqlite-explorer": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/path/to/some.db"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here"
      }
    },
    "remote-service": {
      "url": "http://127.0.0.1:8000/sse",
      "transport": "sse"
    }
  }
}
```

### Loading Rules & Namespacing

1. **Auto-Discovery**: During `sakthai run` or `sakthai chat`, the registry reads `~/.sakthai/mcp.json` and connects to all active servers.
2. **Namespacing**: To avoid tool name collisions, tools imported from an MCP server named `<server>` are exposed with the prefix `<server>__`.
   * For example, the `query` tool in `sqlite-explorer` becomes `sqlite-explorer__query`.
3. **Graceful Failures**: If an MCP server fails to start, its errors are logged, and the agent loop continues with remaining tools.
4. **Disabling MCP**: Pass `--no-mcp` to `sakthai run` to run the loop with only built-in tools.

---

## 📜 Custom Skills

A *skill* in House of Sak is a directory containing a `SKILL.md` file that defines system prompt instructions, domain workflows, and procedural guidance.

### Skill Locations & Overlays

SakThai scans the following directories for skills:
1. `personas/<persona>/skills/` — Persona-specific skill overlays (SakThai 170, SakSee 106, SakKing 59, SakJules 56, SakSit 45, SakTan 26).
2. `personas/shared/skills/` — Universal shared skills available to all six personas (19 skills).
3. `~/.sakthai/<persona>/extensions/` — Persona-scoped installed git extensions.
4. `~/.sakthai/extensions/` — Shared installed third-party git extensions and plugins.
5. `~/.gemini/extensions/` — Gemini CLI extensions (when present).

> *Note: There is no root-level `skills/` directory.*

### Structure of a Skill

Each skill directory contains a `SKILL.md` file beginning with standardized YAML frontmatter:

```markdown
---
name: SakKing-coding-python-expert
description: Instructs the agent to prefer idiomatic, typed Python 3.11+.
category: coding
keywords: [python, type-hints, pep8, clean-code]
---

# Python Expert Skill

When writing Python code:
- Always use strict type hints.
- Favor list comprehensions over loops when readable.
- Adhere strictly to PEP 8 standards and Ruff conventions.
```

### Validation & Injection

* **List available skills**: Run `sakthai skills list`.
* **Validate skill metadata**: Run `sakthai skills validate` to check frontmatter schema compliance across all 481 skills.
* **Inject into a run**: Pass `--with-skills <skill-name>` to `sakthai run`:
  ```bash
  sakthai run "refactor this module" --with-skills SakKing-coding-python-expert
  ```

---

## 🔁 Syncing Skills SakKing Has Learned

SakKing accumulates *learned* (agent-created) skills over time at `~/.sakking/skills`. To pull the skills SakKing has **learned** into this repo as first-class `SakKing-` skills:

```bash
sakthai skills sync-sakking            # import learned skills into personas/sakking/skills/
sakthai skills sync-sakking --dry-run  # preview what would change
sakthai skills sync-sakking --sakking-home /custom/.sakking/skills
```

The importer reads `$SAKKING_HOME/skills` (default `~/.sakking/skills`), skips bundled and internal skills, rewrites each with canonical YAML frontmatter (recording `metadata.sakthai.source: sakking:<slug>`), and prefixes the name with `SakKing-`. The sync is **idempotent**: re-running rewrites only skills whose rendered content changed.

---

## 📦 Extensions (Git Bundles with Skills & MCP Servers)

SakThai enables cloning, managing, and evaluating third-party git extensions that provide bundled skills and Model Context Protocol (MCP) servers.

### Scoping: Shared vs. Persona-Scoped

Extensions can be installed globally or scoped to a specific persona:
* **Shared extensions**: Installed in `~/.sakthai/extensions/` (recorded in `~/.sakthai/extensions.json`). Available fleet-wide.
* **Persona-scoped extensions**: Installed in `~/.sakthai/<persona>/extensions/` (recorded in `~/.sakthai/<persona>/extensions.json`). Scoped strictly to that agent.

### Extension Manifest (`gemini-extension.json`)

Extensions may define MCP servers using `gemini-extension.json` at the root of the cloned repository:

```json
{
  "name": "example-extension",
  "version": "1.0.0",
  "description": "Example extension providing skills and MCP tools",
  "mcpServers": {
    "example-server": {
      "command": "uvx",
      "args": ["example-mcp-server"],
      "env": {
        "DEBUG": "0"
      }
    }
  }
}
```

### Extension Management CLI (`sakthai extensions`)

```bash
# List installed extensions
sakthai extensions list
sakthai extensions list --persona saksee
sakthai extensions list --all-personas --json

# Install an extension
sakthai extensions install https://github.com/foo/bar
sakthai extensions install https://github.com/foo/bar --persona sakjules

# Inspect extension details
sakthai extensions info bar [--persona sakjules] [--json]

# Validate extension containment, manifest schema, and skills
sakthai extensions validate [name] [--persona sakjules] [--json]

# Update extensions via git pull
sakthai extensions update [name] [--persona sakjules] [--all]

# Remove an extension
sakthai extensions remove bar [--persona sakjules]
```

### Extension Health Evaluation (`sakthai eval extensions`)

The fleet includes an 8-factor automated rubric (`EXTENSIONS_RUBRIC_CRITERIA`):
1. **`registry_valid`**: Extension registry is valid, non-corrupt JSON.
2. **`paths_contained`**: All extensions reside within authorized directories (zero path escape).
3. **`names_valid`**: Extension names conform to regex convention (`^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$`).
4. **`manifests_valid`**: `gemini-extension.json` passes schema and command checks.
5. **`skills_valid`**: All bundled `SKILL.md` files comply with YAML frontmatter rules.
6. **`isolation_safe`**: MCP server commands contain no dangerous shell injection patterns.
7. **`discovery_health`**: Discovery routines handle missing or corrupt files safely without crashing.
8. **`persona_scoping_ready`**: Extension infrastructure supports per-persona scoping across the fleet.

```bash
# Audit extension health across all personas
sakthai eval extensions

# Detailed rubric check for a single persona
sakthai eval extensions --persona sakjules --detailed

# Multi-trial consistency benchmark
sakthai eval extensions --times 10 --json
```
