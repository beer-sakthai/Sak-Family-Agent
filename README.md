# SakThai Agent (v2)

A personal, learning agent with persistent memory. SakThai gives a Claude (or
Gemini) agent a durable SQLite memory it can write to and read from across
sessions, plus a set of tools and an MCP server so the same memory is reachable
from other agent runtimes.

> **Note on Versioning & License:** 
> This repository (`sakthai-agent-v2`) is the active, clean from-scratch rewrite of the core engine. The original `SakThai-Agent` (v1) blueprint is now deprecated and locked. 
> Please note that this code is provided under a **Proprietary — View Only** license. You may read the source code to learn how it works, but you may not use, copy, modify, or redistribute it.

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
pip install -e ".[dashboard]" # adds streamlit/plotly/pandas for `sakthai dashboard`
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
sakthai dashboard                    # Streamlit dashboard (--export data.json skips the UI)
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

## Repository layout

```
sakthai/     the package (memory, agent, mcp, cycle, skills, dashboard, cli)
tests/       unit tests
skills/      top-level skills (sakthai-personal, sakthai-cycle-*)
library/     curated library of SakThai's own skills, grouped by category
docs/        architecture and capabilities docs
scripts/     bootstrap.sh, setup-extensions.sh
web/         zero-build static dashboard (reads data.json)
data/        memory snapshot format + a sample export
```

## The cycle

`SOUL.md` describes the agent's charge model, and `Dream.md` → `Growth.md`
document the six working stages (Dream → Hope → Care → Joy → Trust → Growth),
mirrored by the `sakthai-cycle-*` skills and the `sakthai cycle` command.

## Roadmap

The Google ADK / Vertex AI cloud agent from the original project is not part of
this repo yet — it needs live GCP and is tracked separately.
