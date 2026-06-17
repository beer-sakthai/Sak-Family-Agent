# SakThai Agent — persistent memory & tools

You are an agent (Claude, Gemini, or any OpenAI-compatible/Ollama model) running
with SakThai's persistent memory and a shared tool registry active. The same
tools are exposed three ways — the `sakthai` CLI, the `sakthai run` agent loop,
and the `sakthai mcp` stdio server — and all of them read and write one SQLite
store at `~/.sakthai/memory.db` (override the root with `SAKTHAI_HOME`).

## What SakThai adds

| Tool | What it does |
|------|-------------|
| `learn` | Save a fact to persistent memory (`kind`: note/pref/project, optional `key`) |
| `recall` | List facts and observations currently in memory |
| `search` | Substring search across stored facts and observations |
| `forget` | Delete a fact by its integer id |
| `read_file` | Read a local text file within the allowed roots (output capped at 20,000 chars) |
| `run_command` | Run a CLI command — **disabled unless `SAKTHAI_SHELL_ALLOW=1`** |
| `send_telegram_message` | Send a Telegram message (needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`) |
| `run_agent_loop` | Run a high-level task through a nested SakThai agent loop |

## How to use memory

- Save things worth keeping across sessions: `learn "user prefers Python 3.11" --kind pref`.
- Check what is already known before answering a context-dependent question: `recall`.
- Find specific entries on a topic rather than dumping everything: `search "<term>"`.
- Delete facts that are outdated or wrong: `forget <id>`.

## How to run shell commands

`run_command` is off by default. The user must set `SAKTHAI_SHELL_ALLOW=1` to
enable it. When active, use it to run tests, check git status, install packages,
or perform any CLI task the user asks for — rather than asking them to run it
themselves. It runs with `shell=False`, so pipes and redirection are not
supported; the timeout is bounded 1–120 s.

## Memory schema

Facts carry a `kind` (note/pref/project) and an optional `key`. Observations are
agent-curated summaries weighted by confidence. Both are rendered into the
system prompt at the start of each run via `store.render_prompt_block()`, so you
begin every session already aware of what is known.

## Guiding principles

- Read memory before answering anything that might depend on prior context.
- Save a fact only when the user shares something worth recalling in a future
  session — not transient conversational detail.
- Honor stored preferences silently; do not narrate that you are following them.
- Surface contradictions between memory and current input rather than silently
  choosing one.
# SakThai Agent v2 — Persistent Memory & Standalone Agent

SakThai v2 is a personal, learning agent layer built to persist facts, preferences, and activity across sessions. It features a standalone agent loop, standard Model Context Protocol (MCP) server support, streaming execution, and local SQLite memory.

---

## 🛠️ Unified Tooling

SakThai v2 exposes the following core tools to the LLM agent:

| Tool | Capability | Description |
| :--- | :--- | :--- |
| `learn` | SQLite Memory Write | Store permanent user facts/preferences |
| `recall` | SQLite Memory Read | Retrieve stored facts and observations |
| `search` | Full-Text Search | Search across facts and observation indices |
| `forget` | SQLite Memory Delete | Remove a fact by ID |
| `read_file` | File System Read | View local file content securely |
| `run_command` | Shell Execution | Propose shell commands to run on user terminal |

---

## ⚡ Key Runtime Capabilities in v2

* **Stdio MCP Client**: Spawns and connects to external MCP servers dynamically over stdio (defined in `~/.sakthai/mcp.json` or discovered via extensions).
* **Skill Injection**: Dynamically parses and injects `SKILL.md` prompts (via `--with-skills`) from local library, bundled, and Gemini CLI directories.
* **Namespaced Slash Commands**: Executes extension workflows via namespaced commands (`/<plugin>:<command>`).
* **Streaming & Fast-Track Modes**: Supports `--stream` for token-by-token output and `--fast` to bypass structural loops.
* **Caveman Mode**: Dynamic output compression toggle (`--caveman [lite|full|ultra]`).

---

## 🧠 Memory Rules & Governance

1. **Prioritize Recall**: Check memory before answering context-dependent questions.
2. **Silent Compliance**: Honor stated user preferences silently without announcement.
3. **Contradiction Resolution**: Proactively surface contradictions between stored memory and current task inputs.
