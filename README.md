# SakThai Agent

A personal, learning agent with persistent memory. SakThai gives a Claude (or
Gemini) agent a durable SQLite memory it can write to and read from across
sessions, plus a set of tools and an MCP server so the same memory is reachable
from other agent runtimes.

This is a clean, from-scratch implementation of the core engine.

## What's here

- **Persistent memory** — a SQLite store of *facts* (things you tell it) and
  *observations* (things it concludes), with search, tagging, dedupe,
  consolidation, and import/export.
- **Explicit capture** — `sakthai learn "..."` records a fact directly.
- **Agent loop** — `sakthai run "<task>"` runs a tool-using Claude/Gemini loop
  that injects your memory into the system prompt.
- **MCP server** — `sakthai mcp` exposes the memory tools over MCP stdio
  (JSON-RPC) so editors and other agents can share the same memory.
- **6-stage cycle** — a lightweight Dream → Hope → Care → Joy → Trust → Growth
  state machine persisted in memory.

## Install

```bash
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
pip install -e ".[dev]"       # editable install (Python >=3.11)
```

## Usage

```bash
sakthai doctor                       # report environment + memory health
sakthai setup                        # validate .env and required env vars
sakthai learn "prefers dark mode"    # save a fact (--kind, --key, --tag)
sakthai recall "dark"                # search facts + observations
sakthai memory show|stats|search     # inspect the store
sakthai run "summarise my notes"     # standalone Claude/Gemini agent loop
sakthai mcp                          # serve memory tools over MCP stdio
sakthai cycle status|next|set|list   # the 6-stage cycle
sakthai skills list|show|validate    # skill catalog
sakthai tools                        # list agent/MCP tools
```

All runtimes share `~/.sakthai/memory.db` (override with `SAKTHAI_HOME`).

## Develop

```bash
python -m pytest tests/ -q
ruff check sakthai && ruff format --check sakthai
mypy sakthai
bandit -c pyproject.toml -r sakthai
```

## Roadmap

The Streamlit dashboard and the Google ADK / Vertex AI cloud agent are not part
of this first pass — they're coming next.
