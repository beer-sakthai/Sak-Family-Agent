# Driving this repo with Gemini CLI and OpenCode

Claude Code has been able to work in this monorepo for a long time, via
`CLAUDE.md` and `.claude/`. This page covers the other two coding-agent CLIs the
repo is now configured for — **Gemini CLI** and **OpenCode** — and what each one
reads.

Nothing here changes the Python package. These are agent-harness configs only.

## What was added

| File | Read by | Purpose |
|---|---|---|
| `GEMINI.md` | Gemini CLI | Context file. Imports `AGENTS.md`, `CLAUDE.md`, and `docs/OPERATING_CONTRACT.md` with `@` syntax, then adds Gemini-specific notes. |
| `.gemini/settings.json` | Gemini CLI | Project settings: context file name, approval mode, MCP servers. |
| `opencode.json` | OpenCode | Project config: instruction files, providers, MCP servers, and the six personas as named agents. |

`.env.example` gained `HF_TOKEN`, `SAKTHAI_HF_API_BASE`, and `OPENCODE_API_KEY`.
`.gitignore` gained the per-machine state both tools write next to their config.

## The one rule that matters

**Instructions are imported, never copied.** `GEMINI.md` and `opencode.json`
both point at `AGENTS.md` + `CLAUDE.md` rather than restating them. This repo
already carries three parallel copies of the `sakthai` package and a test
(`tests/test_shared_package_divergence.py`) whose whole job is to stop that
divergence from growing — a fourth and fifth copy of the *instructions* would be
the same mistake in a different file type. If a rule needs to change, change it
in `AGENTS.md` or `CLAUDE.md` and every agent picks it up.

`tests/test_agent_cli_configs.py` enforces the pointers actually resolve.

## Gemini CLI

```bash
npm install -g @google/gemini-cli    # or: npx @google/gemini-cli
cd /path/to/Sak-Family-Agent
gemini
```

Auth is either `GEMINI_API_KEY` / `GOOGLE_API_KEY` in `.env`, or the CLI's own
Google sign-in. Both are already documented in `.env.example`.

`.gemini/settings.json` sets:

- `context.fileName: ["GEMINI.md"]` — one composition point. The other
  instruction files arrive through `GEMINI.md`'s `@` imports, so they are not
  loaded twice.
- `context.importFormat: "tree"` — imported files are shown with their structure
  rather than flattened into one blob.
- `context.fileFiltering.respectGitIgnore: true` — the agent does not read what
  git ignores. This repo ignores `.env`, so that matters.
- `general.defaultApprovalMode: "default"` — shell commands ask first. Do not
  commit a change to `yolo`; use `--yolo` on your own invocation if you want it
  for one session.
- `privacy.usageStatisticsEnabled: false` — no telemetry from a repo whose
  guardrails exist to keep secrets in.
- `mcpServers.sakthai` — the repo's own MCP server (see below).
- `mcpServers.huggingface` — the HF MCP server, matching
  `personas/sakthai/config/mcp.json`.

## OpenCode

```bash
curl -fsSL https://opencode.ai/install | bash    # or: npm i -g opencode-ai
cd /path/to/Sak-Family-Agent
opencode
```

`opencode.json` sets:

- `instructions` — `AGENTS.md`, `CLAUDE.md`, `docs/OPERATING_CONTRACT.md`.
- `permission` — `edit: allow`, `bash: ask`, `webfetch: allow`. Shell is gated
  for the same reason the `run_command` tool is opt-in behind
  `SAKTHAI_SHELL_ALLOW`.
- `provider.huggingface` — pinned to the router base URL that
  `SAKTHAI_HF_API_BASE` defaults to, so OpenCode and `sakthai run
  --provider huggingface` hit the same endpoint.
- `provider.ollama` — a custom OpenAI-compatible provider on
  `http://127.0.0.1:11434/v1`. **IPv4, not `localhost`** — the same reason
  `openai_provider.py` does it, IPv6 resolution for `localhost` breaks some
  environments.
- `mcp.sakthai` — the repo's own MCP server, enabled.
- `mcp.huggingface` — present but `enabled: false`, so a fresh `opencode` run
  does not block on `npx` fetching a package. Flip it to `true` when you want it.

### The personas are OpenCode agents

Each of the six personas is a named agent whose system prompt is its own
`SOUL.md` and whose model is the one in its `config/config.yaml`:

| Agent | Model | Role |
|---|---|---|
| `sakthai` | `huggingface/gemini-3.1-flash-lite` | Main Lead of the House, Master of Hugging Face |
| `sakking` | `huggingface/Qwen/Qwen3-Coder-30B-A3B-Instruct` | General assistant and runner (Deputy 1) |
| `saksee` | `huggingface/gemini-3.1-flash-lite` | Web / browser specialist (Deputy 3) |
| `saksit` | `huggingface/DeepSeek-V4-Flash` | Social / content specialist |
| `sakjules` | `huggingface/gemini-2.5-flash-lite` | Master of GitHub, CI/CD and automation |
| `saktan` | `ollama/sakthai` | Keeper of operations and daily flow — fully local, no API key |

There is a seventh, `guardrail-review`: a `subagent` with `edit: deny`, for
reviewing changes under `agent/guardrails*.py` and
`agent/security_hardening.py` without being able to write them.

Switch agents in the TUI with Tab, or run one directly:

```bash
opencode run --agent sakjules "why is the dashboard lint step skipping?"
opencode run --agent saktan "summarise today's memory writes"   # local, $0
```

The model table above is duplicated from `config/config.yaml` by necessity —
OpenCode cannot read this repo's YAML. `tests/test_agent_cli_configs.py` asserts
the two stay in sync, so a persona model rotation fails CI until `opencode.json`
is updated too.

## The shared MCP server

Both tools register the same stdio server:

```
uv run --project . sakthai mcp
```

That is `mcp/server.py`, which reuses `BUILTIN_TOOLS` directly — so Gemini CLI
and OpenCode get exactly the 14 tools the agent loop has, with identical
behavior: `learn`, `ingest_document`, `capture_lead`, `recall`, `search`,
`forget`, `read_file`, `run_command`, the four Microsoft Graph tools,
`send_telegram_message`, and `run_agent_loop`.

Two consequences worth knowing:

- **Memory is shared and real.** A `learn` from Gemini CLI writes to
  `~/.sakthai/memory.db` and Claude Code will recall it. That is the point, but
  it also means a careless agent can write junk into durable memory.
- **`run_command` through MCP is still gated by `SAKTHAI_SHELL_ALLOW`**, and
  `read_file` is still restricted to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`.
  Registering the server in another harness does not widen the sandbox — the
  guardrail policy runs inside the tool handlers, not in the caller.

## Verifying the setup

```bash
uv run pytest tests/test_agent_cli_configs.py -q   # the config invariants
uv run sakthai mcp <<< '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

The second command should print a JSON-RPC response listing the tools. If it
does, both CLIs will see the same list.
