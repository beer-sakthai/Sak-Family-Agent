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
