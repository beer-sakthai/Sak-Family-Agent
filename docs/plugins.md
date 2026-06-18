# Connecting Plugins & Skills

SakThai v2 features a pluggable tool and skill runtime that lets you hook up external Model Context Protocol (MCP) servers and inject custom instructions dynamically.

---

## 🧩 Model Context Protocol (MCP) Servers

SakThai can automatically spawn, connect to, and route tool calls through external MCP servers communicating over standard input/output (stdio).

### Configuration (`mcp.json`)

To register one or more external MCP servers, create or edit the file `~/.sakthai/mcp.json`. It follows the standard `mcpServers` JSON format used by Claude Desktop:

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
    }
  }
}
```

### Loading Rules & Namespacing

1. **Auto-Discovery**: During `sakthai run`, the registry reads `~/.sakthai/mcp.json` and connects to all active servers.
2. **Namespacing**: To avoid tool name collisions, tools imported from an MCP server named `<server>` are exposed to the agent with the prefix `<server>__`.
   * For example, the `query` tool in the `sqlite-explorer` server becomes `sqlite-explorer__query`.
3. **Graceful Failures**: If an MCP server fails to start, its errors are logged, and the agent loop continues with the remaining tools.
4. **Disabling MCP**: Pass the `--no-mcp` flag to `sakthai run` to run the loop with only built-in tools.

---

## 📜 Custom Skills

A *skill* in SakThai is a markdown file (`SKILL.md`) that defines system prompt instructions.

### Locations

SakThai scans the following directories for skills:
1. `sakthai/skills/` (bundled default skills)
2. `library/` (supplementary local skills)
3. `~/.sakthai/extensions/` (installed third-party extensions/skills)

### Structure of a Skill

Each skill is a directory containing a `SKILL.md` file. It must begin with YAML frontmatter specifying its name and description:

```markdown
---
name: python-expert
description: Instructs the agent to prefer idiomatic, typed Python 3.11+.
---

# Python Expert Skill

When writing Python code:
- Always use type hints.
- Favor list comprehensions over loops when readable.
- Adhere strictly to PEP 8 standards.
```

### Validation & Injection

* **List available skills**: Run `sakthai skills list`.
* **Validate skill metadata**: Run `sakthai skills validate` to check frontmatter correctness.
* **Inject into a run**: Pass `--with-skills <skill-name>` to `sakthai run`. You can specify this option multiple times:
  ```bash
  sakthai run "refactor this script" --with-skills python-expert
  ```

---

## 🔁 Syncing skills Hermes has learned

SakThai can run on the [Hermes](https://github.com/) agent runtime (`~/.hermes`),
which ships *bundled* skills and accumulates *learned* (agent-created) ones over
time. To pull the skills Hermes has **learned** into this repo as first-class
`sakthai-` skills:

```bash
sakthai skills sync-hermes            # import learned skills into skills/
sakthai skills sync-hermes --dry-run  # preview what would change
sakthai skills sync-hermes --hermes-home /custom/.hermes/skills
```

What counts as "learned": any `SKILL.md` under the Hermes skills dir whose slug is
**not** in `skills/.bundled_manifest` (and is not a Hermes-internal `hermes-*`
skill). Each imported skill is:

* renamed with a `sakthai-` prefix (`cron-watchdog` → `sakthai-cron-watchdog`),
* rewritten with this repo's canonical YAML frontmatter (so it round-trips
  through `sakthai skills validate`), with provenance recorded under
  `metadata.sakthai.source: hermes:<original-slug>`,
* given a category from its Hermes nesting (e.g. `devops`, `mlops`) or `hermes`.

The sync is **idempotent**: re-running rewrites only the skills whose rendered
content changed and reports created / updated / unchanged. Hermes' learned skills
do not always carry frontmatter, so the importer tolerates a missing or malformed
block and derives a title/description from the Markdown body. Override the Hermes
location with `--hermes-home` or the `HERMES_HOME` environment variable.
