---
name: run-sakthai-agent-v2
description: Build, run, drive, and test sakthai-agent-v2 — the `sakthai` CLI, its agent loop, and its MCP stdio server. Use when asked to run sakthai, start the sakthai agent, smoke-test it, drive the MCP server, export the dashboard, or verify the CLI works.
---

`sakthai-agent-v2` is a Python CLI (`sakthai`) — a personal agent with a
persistent SQLite memory exposed three ways: the CLI itself, a tool-using
**agent loop** (`sakthai run`), and an **MCP stdio JSON-RPC server**
(`sakthai mcp`). Drive all of it with
`.claude/skills/run-sakthai-agent-v2/driver.py`, which smoke-tests the CLI,
the zero-cost agent preflight, the dashboard export, and a live MCP roundtrip
in a throwaway home — no API key or network needed.

All paths below are relative to `sakthai-agent-v2/`.

## Prerequisites

Python ≥ 3.11. No system packages beyond Python itself are required (pure-Python
CLI; SQLite ships with CPython).

```bash
python3 --version   # need >= 3.11
```

## Setup

One-time, from a clean checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"        # puts `sakthai` on PATH; enough for the driver + tests
# pip install -e ".[dev,dashboard]"   # also installs streamlit/plotly/pandas to *serve* the UI
```

Verify:

```bash
sakthai --version
```

### Environment

| Variable | Required | Notes |
|---|---|---|
| `SAKTHAI_HOME` | No | Data dir (memory DB, sessions). Defaults to `~/.sakthai`. The driver sets this to a temp dir so it never touches real memory. |
| `ANTHROPIC_API_KEY` | Only for a *real* `sakthai run` | Or `ANTHROPIC_AUTH_TOKEN`, or a Claude CLI OAuth login. **Not** needed for `--dry-run` or anything the driver does. |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` / `OLLAMA_HOST` | No | Alternative providers for the agent loop. |

## Run (agent path)

Activate the venv first, then run the driver. It exits non-zero if any surface
is broken and prints a `[PASS]`/`[FAIL]` line per check:

```bash
source .venv/bin/activate
python .claude/skills/run-sakthai-agent-v2/driver.py
# → 11 [PASS] lines, then "OK: all checks passed"
```

What it drives (all in a throwaway `SAKTHAI_HOME`):

| surface | how it's checked |
|---|---|
| memory CLI | `status`, `learn`, `recall`, `memory stats`, `tools` (exit codes + output) |
| agent loop | `run "..." --dry-run --no-mcp` — resolves provider/creds/model/tools, **no API call** |
| dashboard | `dashboard --export <file>` writes valid JSON (no browser, no streamlit) |
| MCP server | spawns `sakthai mcp`, pipes JSON-RPC `initialize` → `tools/list` → `tools/call learn` → `tools/call recall`, asserts the fact round-trips through the live server |

Override the binary with `SAKTHAI_BIN=/path/to/sakthai python .../driver.py`.

### Drive the MCP server yourself

The server reads newline-delimited JSON-RPC on stdin and replies on stdout,
running until EOF — feed every request, then close stdin:

```bash
export SAKTHAI_HOME=$(mktemp -d)
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"learn","arguments":{"value":"hi","kind":"note"}}}' \
  | sakthai mcp
```

### Individual CLI commands

```bash
export SAKTHAI_HOME=$(mktemp -d)            # isolate from your real ~/.sakthai
sakthai learn "prefers dark mode" --kind pref --key ui   # → learned (id=1)
sakthai recall "dark"                                     # → [pref] ui: prefers dark mode
sakthai run "say hi" --dry-run --no-mcp                  # → preflight report, exit 0, no tokens spent
sakthai dashboard --export /tmp/snap.json               # → snapshot: /tmp/snap.json
```

## Run (human path)

- `sakthai run "<task>"` — real agent loop; needs a credential and network and
  **spends tokens**. Use `--dry-run` to validate setup for free.
- `sakthai dashboard` — serves the Streamlit UI (needs `[dashboard]` extra);
  blocks the shell and opens a browser, so it's useless headless.

## Test

```bash
pytest -q -m "not integration"   # ~546 hermetic tests (1 skipped w/o [dashboard]); this is what CI runs
```

Integration tests (`-m integration`) hit real Anthropic/Ollama endpoints and
self-skip when no credential/endpoint is set.

## Gotchas

- **`sakthai` is only on PATH after `source .venv/bin/activate`** (or a global
  `pip install -e .`). The driver invokes `sakthai` from PATH; if it's elsewhere,
  pass `SAKTHAI_BIN=/abs/path/to/sakthai`.
- **All runtimes share one SQLite DB** (`$SAKTHAI_HOME/memory.db`, default
  `~/.sakthai`). Always set `SAKTHAI_HOME` to a temp dir when smoke-testing or
  you'll pollute (or lock) your real memory. The driver does this for you.
- **`sakthai run` without `--dry-run` costs tokens and needs network.** For a
  "does it work" check, `--dry-run` resolves provider + credentials + model +
  tool count with zero API calls.
- **`dashboard --export` needs no `[dashboard]` extra** — it imports only the
  data layer. Only *serving* the live UI imports streamlit (lazily).
- **The MCP server runs until stdin EOF.** Don't leave stdin open waiting for
  more output; send all requests and close the pipe.

## Troubleshooting

- **`sakthai: command not found`**: the venv isn't active. `source .venv/bin/activate`.
- **`pytest` errors collecting `test_dashboard_app.py`**: that file `importorskip`s
  streamlit and is skipped without the `[dashboard]` extra — not a failure.
- **`sakthai run` exits with "Missing credentials …" / AuthError**: expected with
  no provider credential. Use `--dry-run`, or set `ANTHROPIC_API_KEY`.
