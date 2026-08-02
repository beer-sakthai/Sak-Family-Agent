---
name: SakKing-sakthai
description: "Drive sakthai-agent-v2 — the `sakthai` CLI with persistent SQLite memory, an agent loop, and an MCP stdio server."
version: "2.0.0"
author: Beer (beer-sakthai) + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Memory-Agent, SakThai, Persistent-Memory, MCP, CLI, SQLite, Learning-Agent]
    related_skills: [claude-code, codex, hermes-agent, opencode]
---

# SakThai — Hermes Orchestration Guide

`sakthai-agent-v2` is a personal learning agent: a Python CLI (`sakthai`) with a
**persistent SQLite memory** of *facts* and *observations*, exposed three ways
that all share one store at `~/.sakthai/memory.db` (override the root with
`SAKTHAI_HOME`):

1. **CLI** — `sakthai <cmd>` (memory, agent, cycle, skills, dashboard).
2. **Agent loop** — `sakthai run "<task>"`, a provider-agnostic tool-using loop
   (Claude / Gemini / OpenAI-compatible / Ollama).
3. **MCP stdio server** — `sakthai mcp`, the same tools over JSON-RPC stdio.

Repo on this machine: `/home/sakthai/sakthai-agent-v2`.

## When to use this skill

- Save or retrieve durable facts/preferences that should persist across sessions.
- Run the `sakthai` agent loop on a task, or smoke-test/verify the CLI.
- Drive or connect to the `sakthai mcp` server as an MCP tool source.

## Prerequisites & setup

Python ≥ 3.11. The `sakthai` binary lands on PATH after an editable install:

```bash
cd /home/sakthai/sakthai-agent-v2
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"     # or: uv sync --all-extras
sakthai --version
```

`sakthai run` (real) needs a provider credential (`ANTHROPIC_API_KEY`, etc.) and
network. `--dry-run` validates provider/creds/model/tools with **zero** API calls.

## Memory CLI (the core surface)

```bash
export SAKTHAI_HOME=$(mktemp -d)                 # isolate from real ~/.sakthai when testing
sakthai learn "prefers Python 3.11" --kind pref --key lang   # save a fact
sakthai recall                                   # list facts + observations
sakthai memory search "python"                   # substring search
sakthai memory stats                             # counts / KPIs
```

Kinds: `note` / `pref` / `project`. Save a fact only when it's worth recalling in
a future session — not transient chatter.

## Agent loop

```bash
sakthai run "<task>"                  # real loop — spends tokens, needs a credential
sakthai run "say hi" --dry-run --no-mcp   # free preflight: resolves provider/creds/model/tools
```

## MCP server

The server reads newline-delimited JSON-RPC on stdin, replies on stdout, runs
until EOF — send all requests, then close stdin:

```bash
export SAKTHAI_HOME=$(mktemp -d)
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"learn","arguments":{"value":"hi","kind":"note"}}}' \
  | sakthai mcp
```

To wire it into Hermes as an MCP tool source, register `sakthai mcp` as a stdio
MCP server (`hermes mcp ...`).

## Verify / smoke-test

A throwaway-home driver checks the CLI, the zero-cost agent preflight, the
dashboard export, and a live MCP roundtrip — no API key or network:

```bash
cd /home/sakthai/sakthai-agent-v2 && source .venv/bin/activate
python .claude/skills/run-sakthai-agent-v2/driver.py   # 11 [PASS] lines → "OK: all checks passed"
pytest -q -m "not integration"                          # hermetic test suite
```

## Gotchas

- `sakthai` is only on PATH after `source .venv/bin/activate` (or a global
  `pip install -e .`). Else pass `SAKTHAI_BIN=/abs/path/to/sakthai`.
- All runtimes share one SQLite DB. Set `SAKTHAI_HOME` to a temp dir when
  smoke-testing or you'll pollute/lock your real memory.
- `run_command` (a sakthai tool) is **opt-in** via `SAKTHAI_SHELL_ALLOW=1`;
  `read_file` is sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`.
- The MCP server runs until stdin EOF — don't leave stdin open waiting for output.
