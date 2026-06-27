# SakThai Agent (v2)

![SakThai Agent Banner](./assets/readme_banner.png)

[![CI](https://github.com/beer-sakthai/sakthai-agent-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/beer-sakthai/sakthai-agent-v2/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen)](https://github.com/beer-sakthai/sakthai-agent-v2/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)

SakThai is a **personal learning agent with persistent memory**. It gives a
Claude, Gemini, or local (Ollama / OpenAI-compatible) model a durable SQLite
memory it reads and writes across sessions, a shared tool registry, a curated
skills catalog, and a two-way **MCP** bridge so the same memory and tools are
reachable from other agents and editors. It is **local-first** — one package,
three ways in: a CLI, a tool-using agent loop, and an MCP stdio server.

---

## Highlights

- **Persistent memory** — a SQLite store of *facts* (things you tell it) and
  *observations* (things it concludes), with substring search, tagging, WAL
  concurrency, additive migrations, dedupe/consolidation, and multi-agent sync
  (Git JSONL merge + HTTP backup). See [`docs/architecture.md`](./docs/architecture.md).
- **Provider-agnostic agent loop** — `sakthai run "<task>"` drives a tool-using
  loop over **Anthropic (Claude)**, **Google (Gemini)**, or any
  **OpenAI-compatible / Ollama** endpoint — including a fully **no-cost local run**.
- **8 built-in tools** — one registry powers both the agent loop and the MCP
  server (see [Built-in tools](#built-in-tools)).
- **Skills catalog** — **31 curated library skills** across 11 categories plus
  **65 user/extension skills**, injected into the system prompt on demand.
- **MCP, both directions** — *serve* SakThai's tools to other agents
  (`sakthai mcp`), and *consume* external MCP servers (namespaced `<server>__tool`).
- **SakKing integration (local, no cost)** — connect SakThai and the
  [SakKing](https://github.com/) agent over local MCP stdio, and mirror
  SakKing-learned skills with `sakthai skills sync-sakking`. See [SakKing integration](#sakking-integration-local-no-cost).
- **6-stage cycle** — a lightweight Dream → Hope → Care → Joy → Trust → Growth
  state machine persisted in memory and mirrored by the `sakthai-cycle-*` skills.
- **Dashboard** — `sakthai dashboard` serves a Streamlit view of the store (KPIs,
  memory explorer, sessions, cycle).

![Architecture diagram](./assets/architecture_diagram_v2.png)

---

## Quick start

```bash
# Python >=3.11. Preferred: uv (CI uses uv + uv.lock for reproducible installs).
uv sync --all-extras
# or: pip install -e ".[all]"     # dev + dashboard extras

cp .env.example .env              # fill in ANTHROPIC_API_KEY (or use a local model — see below)
sakthai doctor                    # check environment + memory health
sakthai learn "prefers dark mode" --kind pref --key ui
sakthai recall "dark"             # search facts + observations
sakthai run "summarise my notes"  # standalone tool-using agent loop
```

All runtimes share `~/.sakthai/memory.db` (override the root with `SAKTHAI_HOME`).

---

## Providers & no-cost local run

The agent loop is provider-agnostic. The provider is auto-detected from the model
name and available credentials; override with `--provider`.

| Provider | Models | Auth |
|----------|--------|------|
| `anthropic` | Claude (default `claude-opus-4-8`) | `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth |
| `google` | Gemini | `GEMINI_API_KEY` / `GOOGLE_API_KEY`, or Gemini CLI OAuth |
| `openai` | any OpenAI-compatible gateway (vLLM, LocalAI, …) | `OPENAI_API_BASE` / `OPENAI_BASE_URL` + `OPENAI_API_KEY` (defaults `nokey`) |
| `ollama` | local models via Ollama | none — `OLLAMA_HOST` (default `http://127.0.0.1:11434`) |

**No-cost local run** (no API key, nothing leaves the machine):

```bash
ollama run qwen2.5-coder:7b          # start a local model (one-time)
sakthai run "refactor this script" --provider ollama --model qwen2.5-coder:7b
```

> Ollama is reached at the IPv4 literal `127.0.0.1` on purpose — on hosts where
> `localhost` resolves to IPv6 `::1` but Ollama binds IPv4 only, `localhost`
> would give `Connection refused`.

---

## Runtimes

One package, three entry points (full detail in [`docs/runtimes.md`](./docs/runtimes.md)):

1. **CLI** — `sakthai <cmd>` (see [Commands](#commands)).
2. **Agent loop** — `sakthai run "<task>"` drives the provider-agnostic tool-using
   loop, injecting memory and any active skills into the system prompt. Useful
   flags: `--provider`, `--model`, `--with-skills <name>` (repeatable), `--no-mcp`,
   `--fast` (skip cycle overhead), `--verbose`, and `--dry-run` (preflight, **no
   API call**).
3. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio
   (protocol `2024-11-05`), so editors and other agents share one memory.

---

## MCP

SakThai speaks the Model Context Protocol **in both directions**. Deep dive:
[`docs/plugins.md`](./docs/plugins.md) and [`docs/integrations.md`](./docs/integrations.md).

### Inbound — serve SakThai to other agents

`sakthai mcp` exposes the built-in tools over JSON-RPC stdio. The MCP server
reuses the exact same `BUILTIN_TOOLS` registry as the agent loop, so behaviour is
identical on both surfaces. Register it with any MCP client, e.g. Claude CLI
(`~/.claude/config.json`) or Gemini CLI:

```json
{
  "mcpServers": {
    "sakthai": { "command": "sakthai", "args": ["mcp"] }
  }
}
```

### Outbound — consume external MCP servers

During `sakthai run`, SakThai auto-loads external MCP servers from
`~/.sakthai/mcp.json` (standard `mcpServers` shape, Claude-Desktop-compatible),
merges their tools into the registry namespaced as `<server>__<tool>`, and fails
soft if a server won't start. Pass `--no-mcp` to disable.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here" }
    }
  }
}
```

### SakKing integration (local, no cost)

SakThai and the [SakKing](https://github.com/) agent (installed at `~/.sakking`)
interoperate over **local MCP stdio** — a subprocess JSON-RPC channel with **no
network and zero API/cloud cost**.

- **SakKing → SakThai** (already wired by SakKing): SakKing registers
  `sakthai mcp` in its `~/.sakking/config.yaml` and calls SakThai's memory tools.
- **SakThai → SakKing**: add SakKing to `~/.sakthai/mcp.json` and its conversation
  / messaging tools appear in the agent loop as `sakking__*`:

  ```json
  {
    "mcpServers": {
      "sakking": { "command": "sakking", "args": ["mcp", "serve"] }
    }
  }
  ```

- **Mirror SakKing-learned skills** into this repo as first-class `sakthai-` skills:

  ```bash
  sakthai skills sync-sakking            # import learned skills into skills/
  sakthai skills sync-sakking --dry-run  # preview changes (idempotent)
  ```

> The MCP link itself is free; SakThai's own *reasoning* still uses whatever
> provider you pick — pair the SakKing link with a local Ollama model (above) for
> an end-to-end no-cost setup.

---

## Skills

A *skill* is a directory with a `SKILL.md` (YAML frontmatter + markdown body) that
gets injected into the agent's system prompt when active. SakThai ships:

- **`library/`** — **31 curated skills** across 11 categories: `agent`,
  `automation`, `coding`, `devops`, `learning`, `llm`, `memory`, `observability`,
  `research`, `safety`, `security`.
- **`skills/`** — **65 user/extension skills** (the `sakthai-*` set, including the
  `sakthai-cycle-*` stages and skills mirrored from SakKing).

```yaml
---
name: my-skill
category: coding
description: One-line summary of what this skill does
version: "1.0"
platforms: [claude, gemini]
metadata:
  sakthai:
    tags: [python, testing]
    related_skills: [other-skill]
---

Skill body goes here — injected into the system prompt when the skill is active.
```

Manage skills with `sakthai skills list|show|validate|create|sync-sakking`, and
activate them for a run with `sakthai run "<task>" --with-skills my-skill`.

---

## Built-in tools

The same 8-tool registry (`sakthai/agent/tools.py`) powers both `sakthai run` and
`sakthai mcp`. Add a tool once and it appears on both surfaces.

| Tool | What it does | Notes |
|------|--------------|-------|
| `learn` | Save a fact (value, kind, key) | The agent's write path into memory |
| `recall` | List recent facts + top observations | Read what's already known |
| `search` | Substring search over facts + observations | Targeted lookup |
| `forget` | Delete a fact by id | — |
| `read_file` | Read a local text file | Sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`; 20k-char cap |
| `run_command` | Run a CLI command (no shell) | **Opt-in** via `SAKTHAI_SHELL_ALLOW`; 20k-char cap |
| `send_telegram_message` | Send a Telegram message | Needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| `run_agent_loop` | Delegate a whole task to SakThai's agent loop | MCP-only (filtered out of the in-loop set to avoid recursion) |

---

## Commands

```bash
sakthai doctor                       # report environment + memory health
sakthai setup                        # validate .env and required env vars
sakthai status | tools               # quick status; list agent/MCP tools
sakthai learn "prefers dark mode"    # save a fact
sakthai recall "dark"                # search facts + observations
sakthai memory show|stats|search|export|import|backup|consolidate|deduplicate
sakthai run "summarise my notes"     # provider-agnostic agent loop
sakthai mcp                          # serve memory tools over MCP stdio
sakthai cycle status|next|set|list   # the 6-stage cycle
sakthai skills list|show|validate|create|sync-sakking
sakthai sessions list|show|export    # inspect session logs
sakthai dashboard                    # Streamlit view of the store
```

---

## Develop

Mirrors `.github/workflows/ci.yml` (run before pushing; green CI is the bar for
`main`). Coverage floor is **85%**.

```bash
ruff check sakthai tests                 # lint
ruff format --check sakthai tests        # format check (drop --check to apply)
mypy sakthai                             # strict type-check
bandit -c pyproject.toml -r sakthai      # security scan
python -m pytest -m "not integration" -q # the 38-file hermetic suite (no network)
```

A live end-to-end smoke test (CLI + MCP roundtrip, **no API cost**):

```bash
python .claude/skills/run-sakthai-agent-v2/driver.py
```

### Git worktree workflow

This checkout may be shared by multiple agents/developers. Use git worktrees to
isolate work so concurrent commits never collide:

```bash
git worktree add -b my-feature ../wt-my-feature origin/main  # isolated checkout off main
cd ../wt-my-feature                                          # work, commit, push independently
# ... when done:
cd -
git worktree remove ../wt-my-feature
```

---

## Repository layout

```
sakthai/     the package (config, auth, memory, agent, mcp, cycle, skills, dashboard, cli, ...)
tests/       38 hermetic unit-test files (no network, no GCP)
skills/      65 user/extension SKILL.md folders (the sakthai-* set)
library/     31 curated skills across 11 categories
docs/        architecture, capabilities, plugins, runtimes, integrations, replication, ...
assets/      banner + architecture / cycle diagrams
scripts/     dev utilities (not linted / type-checked)
data/        memory snapshot format + a sample export
training/    HF Jobs fine-tune + serving scripts (optional, off the core path)
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [CLAUDE.md](./CLAUDE.md) | Development guide + architecture for contributors |
| [docs/architecture.md](./docs/architecture.md) | Layer diagram and SQLite schema |
| [docs/capabilities.md](./docs/capabilities.md) | Tools, memory ops, providers, dashboard |
| [docs/plugins.md](./docs/plugins.md) | MCP servers + skills extensibility |
| [docs/integrations.md](./docs/integrations.md) | Connecting Hermes, Composio, and other agents |
| [docs/runtimes.md](./docs/runtimes.md) | CLI / agent loop / MCP server + local models |
| [docs/replication.md](./docs/replication.md) | Multi-agent memory sync |
| [docs/workspace.md](./docs/workspace.md) | Dev environment setup |

---

**Note on Versioning & License:**
This repository (`sakthai-agent-v2`) is the active, clean from-scratch rewrite of
the core engine. The original `SakThai-Agent` (v1) blueprint is now deprecated and
locked.

**License:** MIT License. See the [LICENSE](LICENSE) file for details.
