---
name: run-sakthai-chat-cli
description: Build, run, and drive the sakthai chat CLI. Use when asked to start or run sakthai, open the chat REPL, smoke-test the CLI/MCP server, run its tests, or interact with (or screenshot) the running TUI.
---

The `sakthai` CLI (Click + rich/prompt_toolkit) — a chat REPL, one-shot agent
loop, memory commands, and an MCP stdio server. Drive it via
`.claude/skills/run-sakthai-chat-cli/driver.py`: its `smoke` subcommand
exercises every offline surface end-to-end, and its built-in **stub
OpenAI-compatible server** lets the interactive chat REPL do a real
model round trip with **no credentials, no Ollama, no network**.

All paths are relative to the repo root. All commands below were run and
verified on Ubuntu (headless).

## Prerequisites

`uv`, `python3` (3.11+), and `tmux` — all pre-installed in the standard
container. If tmux is missing: `apt-get install -y tmux`.

## Setup

```bash
uv sync --all-extras
```

No env vars are required for anything below. Always point `SAKTHAI_HOME`
at a throwaway dir so you never touch the real `~/.sakthai` memory DB
(the driver does this automatically).

## Run (agent path)

**Full offline smoke — start here.** Verifies CLI, memory, MCP server,
and a real chat REPL round trip against the stub model (7 steps, ~1–2 min,
exits non-zero on failure):

```bash
python3 .claude/skills/run-sakthai-chat-cli/driver.py smoke
```

**Drive the chat REPL interactively.** Starts the stub model server and a
tmux session `sakchat` running `sakthai chat` against it; the process
stays in the foreground keeping the stub alive, so background it:

```bash
python3 .claude/skills/run-sakthai-chat-cli/driver.py chat &   # stub + tmux session "sakchat"
timeout 30 bash -c 'until tmux capture-pane -t sakchat -p | grep -q "SAK FAMILY TERMINAL"; do sleep 0.5; done'
tmux send-keys -t sakchat 'hello SakThai' Enter
sleep 8                                    # uv + REPL turn latency; poll for "STUB-REPLY" to be exact
tmux capture-pane -t sakchat -p            # ← the "screenshot": banner, your message, STUB-REPLY panel
tmux send-keys -t sakchat '/exit' Enter && tmux kill-session -t sakchat
```

Every model reply reads `STUB-REPLY: you said '<your message>'` — proof
the full REPL → provider → renderer path worked. To chat against a
*real* backend instead, skip the driver and set one of:
`OLLAMA_HOST=http://127.0.0.1:11434` (local Ollama),
`ANTHROPIC_API_KEY` + `--provider anthropic`, or `OPENAI_BASE_URL`/`OPENAI_API_KEY`.

**MCP stdio server** — newline-delimited JSON-RPC on stdin/stdout, no tmux
needed (the smoke does this too):

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"recall","arguments":{"query":"alpha"}}}' \
  | SAKTHAI_HOME=$(mktemp -d) uv run sakthai mcp
```

**Direct invocation** (for PRs touching internals — no REPL needed):
memory, tools, and skills are plain commands:

```bash
export SAKTHAI_HOME=$(mktemp -d)
uv run sakthai learn "a fact" --kind note --tag smoke   # → "learned (id=1)"
uv run sakthai recall "fact"
uv run sakthai tools          # the 10 BUILTIN_TOOLS
uv run sakthai skills list    # 31 skills from library/
uv run sakthai doctor         # env/paths/credentials report
```

| driver command | what it does |
|---|---|
| `smoke` | 7-step offline verification, PASS/FAIL per step |
| `chat [--port N]` | stub server + tmux session `sakchat` for interactive poking |
| `stub [--port N]` | stub `/v1/chat/completions` server alone (default port 8765) |

## Run (human path)

```bash
uv run sakthai chat   # → full-screen REPL (clears screen, boxed input, bottom toolbar, tab-completed
                      #   slash commands); needs Ollama or API keys to answer.
                      #   In-REPL: /help /tools /skills /memory /goal /clear /exit.
```

## Test

```bash
uv run python -m pytest tests/ -q   # hermetic; 1330 tests, exits 0 (integration tests self-skip offline), ~5 min with coverage
```

## Gotchas

- **`sakthai chat` opens fine with zero credentials, then errors per
  turn** (`No OpenAI credentials found…`). The provider is only resolved
  when a message is sent. The driver's stub fixes this for testing; the
  REPL banner alone is not proof the app works.
- **`OLLAMA_HOST` doubles as a generic OpenAI-compatible override** —
  the code appends `/v1` to it. That's how the driver injects its stub
  (`OLLAMA_HOST=http://127.0.0.1:8765`); no Ollama involved.
- **The provider streams SSE by default** (`POST /chat/completions` with
  `stream:true`). Any stub must answer with `data: {chunk}\n\n` lines +
  `data: [DONE]`, not a plain JSON body — the driver's stub does both.
- **`learn` flags are `--kind`/`--key`/`--tag`**. `--topic` and
  `--category` don't exist and Click exits 2.
- **Always set `SAKTHAI_HOME`** or you'll write facts into the real
  `~/.sakthai/memory.db`.
- **First `uv run` after `uv sync` is slow** (~10 s venv warm-up); budget
  for it in tmux wait loops.

## Troubleshooting

- **`✗ error: No OpenAI credentials found. Please set OPENAI_API_KEY, OPENAI_BASE_URL, or OLLAMA_HOST.`**
  inside the REPL: no backend configured. Use the driver's stub
  (`driver.py chat`) or set one of those vars.
- **tmux pane shows only the banner, no reply panel**: the stub isn't
  reachable on the port the REPL was given — confirm the driver process
  backing the stub is still alive (`driver.py chat` foregrounds; if you
  `&`-ed it, check it wasn't reaped).
