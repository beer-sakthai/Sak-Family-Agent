---
name: run-sakthai-agent-v2
description: Build, run, drive, and test sakthai-agent-v2 — the `sakthai` CLI, its agent loop, its MCP stdio server, and the web API. Use when asked to run sakthai, start the sakthai agent, smoke-test it, drive the MCP server, serve the web API, or verify the CLI works.
---

`sakthai-agent-v2` is a Python CLI (`sakthai`) — a personal agent with a
persistent SQLite memory exposed four ways: the CLI itself, a tool-using
**agent loop** (`sakthai run`), an **MCP stdio JSON-RPC server**
(`sakthai mcp`), and a **web API** (`python -m sakthai.web.server`). Drive all
of it with `.claude/skills/run-sakthai-agent-v2/driver.py`, which smoke-tests
the CLI, the zero-cost agent preflight, the web API, and a live MCP roundtrip
in a throwaway home — no API key or network needed.

All paths are relative to the repo root. **The package source lives at
`personas/sakthai/sakthai/`** (see `[tool.setuptools.packages.find]` in
`pyproject.toml`), not at a root-level `sakthai/` — edit there.

## Prerequisites

Python ≥ 3.11 and `uv`. No system packages beyond that (pure-Python CLI;
SQLite ships with CPython).

```bash
python3 --version   # need >= 3.11
uv --version
```

## Setup

One-time, from the repo root:

```bash
uv sync --all-extras     # creates .venv with `sakthai` + dev deps
```

Verify:

```bash
uv run sakthai --version   # → sakthai, version 2.0.0
```

## Run (agent path)

Run the driver. It exits non-zero if any surface is broken and prints a
`[PASS]`/`[FAIL]` line per check:

```bash
uv run python .claude/skills/run-sakthai-agent-v2/driver.py
# → 11 [PASS] lines, then "OK: all checks passed"
```

What it drives (all in a throwaway `SAKTHAI_HOME`):

| surface | how it's checked |
|---|---|
| memory CLI | `status`, `learn`, `recall`, `memory stats`, `tools` (exit codes + output) |
| agent loop | `run "..." --dry-run --no-mcp` — resolves provider/creds/model/tools, **no API call** |
| web API | spawns `python -m sakthai.web.server`, asserts `GET /api/stages` returns KPI JSON |
| MCP server | spawns `sakthai mcp`, pipes JSON-RPC `initialize` → `tools/list` → `tools/call learn` → `tools/call recall`, asserts the fact round-trips through the live server |

Override the binary with `SAKTHAI_BIN=/path/to/sakthai`.

### Drive the MCP server yourself

The server reads newline-delimited JSON-RPC on stdin and replies on stdout,
running until EOF — feed every request, then close stdin:

```bash
source .venv/bin/activate
export SAKTHAI_HOME=$(mktemp -d)
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"learn","arguments":{"value":"hi","kind":"note"}}}' \
  | sakthai mcp
```

### Individual CLI commands

```bash
source .venv/bin/activate
export SAKTHAI_HOME=$(mktemp -d)            # isolate from your real ~/.sakthai
sakthai learn "prefers dark mode" --kind pref --key ui   # → learned (id=1)
sakthai recall "dark"                                     # → [pref] ui: prefers dark mode
sakthai run "say hi" --dry-run --no-mcp                  # → preflight report, exit 0, no tokens spent
```

### Web API server

```bash
.venv/bin/python -m sakthai.web.server &   # listens on 127.0.0.1:3001
curl -s http://127.0.0.1:3001/api/stages     # → KPI/growth JSON (demo stub without live data)
curl -s http://127.0.0.1:3001/api/ecosystem  # → integration status JSON
kill %1
```

## Run (human path)

- `sakthai run "<task>"` — real agent loop; needs a credential and network and
  **spends tokens**. Use `--dry-run` to validate setup for free.

## Test

```bash
uv run pytest tests/ -q -m "not integration"   # 1190 hermetic tests, ~80s
```

Integration tests (`-m integration`) hit real Anthropic/Ollama endpoints and
self-skip when no credential/endpoint is set.

## Gotchas

- **Always scope pytest to `tests/`.** A bare `uv run pytest` from the repo
  root tries to collect the persona trees (`personas/*/agent-self-evolution`,
  skill scripts, …) whose dependencies aren't installed — 60 collection
  errors before a single test runs.
- **The `dashboard` CLI command no longer exists** (removed in 5de2c25 along
  with `sakthai/dashboard/`). The JSON surface is now
  `python -m sakthai.web.server` (`/api/stages`, `/api/ecosystem`), which
  serves a demo stub when no live data layer is present. The React UI under
  the repo-root `dashboard/` is a separate app; without its built `dist` the
  server is API-only.
- **All runtimes share one SQLite DB** (`$SAKTHAI_HOME/memory.db`, default
  `~/.sakthai`). Always set `SAKTHAI_HOME` to a temp dir when smoke-testing or
  you'll pollute (or lock) your real memory. The driver does this for you.
- **`sakthai run` without `--dry-run` costs tokens and needs network.** For a
  "does it work" check, `--dry-run` resolves provider + credentials + model +
  tool count with zero API calls.
- **The MCP server runs until stdin EOF.** Don't leave stdin open waiting for
  more output; send all requests and close the pipe.
- **`sakthai` is only on PATH inside the venv** (`uv run …` or
  `source .venv/bin/activate`). The driver invokes `sakthai` from PATH; if
  it's elsewhere, pass `SAKTHAI_BIN=/abs/path/to/sakthai`.

## Troubleshooting

- **`sakthai: command not found`**: use `uv run sakthai …` or
  `source .venv/bin/activate` first.
- **`ModuleNotFoundError: No module named 'sakthai.cli.dashboard'`**: you're
  on a stale checkout/branch where commit 5de2c25 removed the dashboard
  modules but `cli/__init__.py` still imported them (fixed since). Update, or
  remove the dangling import.
- **`FileNotFoundError: … sakthai/dashboard/dist` from the web server**: same
  era — `serve()` used to `chdir` into the removed dist unconditionally;
  fixed to skip it when absent.
- **`sakthai run` exits with "Missing credentials …" / AuthError**: expected
  with no provider credential. Use `--dry-run`, or set `ANTHROPIC_API_KEY`.
- **pytest interrupted with dozens of collection errors**: you ran it from
  the repo root without scoping. Use `uv run pytest tests/ -q`.
