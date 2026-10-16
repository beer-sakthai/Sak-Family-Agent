# 🎒 BACKPACK.md — SakTan 📗

> **Agent**: SakTan 📗 — Daily Ops & Rhythm (Deputy 2)\
> **Repository**: `Sak-Family-Agent`\
> **Hermes Profile**: `infra/hermes-agents/profiles/saktan/`\
> **Cost Policy**: Token economy — every output token is real money against a small budget (SOUL, Tone).

---

## 🖥️ 1. How to Run Me

| Command | What it does |
|:---|:---|
| `sakthai run "<task>" --persona saktan` | One task through the agent loop, with my SOUL, skills, MCP config and model |
| `sakthai chat --persona saktan` | Interactive chat with the same setup |
| `SAKTHAI_HOME=$(mktemp -d) sakthai run "<task>" --persona saktan --no-mcp --dry-run` | Check provider, model, credentials and skills without a model call |
| `sakthai memory --persona saktan stats` | My memory shard at a glance |
| Telegram `@saktan_agent_bot` | The VM deployment, started by `infra/vm-agents/sakthai-agent-run.sh saktan` |

---

## 🤖 2. Model Loadout

| Where | Provider | Model | Set in |
|:---|:---|:---|:---|
| Local CLI (`--persona saktan`) | `ollama` | `sakthai` | `config/config.yaml` |
| VM Telegram bot | `openai` (Azure OpenAI) | `gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` |

---

## 🛠️ 3. MCP Servers (`config/mcp.json`)

None — `config/mcp.json` lists no servers.

---

## 🧰 4. Skills

- **My overlay**: 13 skills in `personas/saktan/skills/`
- **Shared**: the `Sak-*` skills in `personas/shared/skills/`, composed into every persona
- **Primary** (`config/workspace.yaml`):
  - `SakTan-daily-briefing`
  - `SakTan-close-the-day`
  - `SakTan-weekly-review`

---

## 🔑 5. Credentials & Environment (names only — never print a value)

- **Model provider**: None — `ollama` needs a local server at `http://127.0.0.1:11434` (`OLLAMA_HOST`), not a key.
- **VM env template** (`infra/vm-agents/env-templates/saktan.env.example`): `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Approvals**: `mode: manual` · `cron_mode: deny` · `command_allowlist: []` (`config/config.yaml`)

---

## 📜 6. Permanent Files (`personas/saktan/`)

- `SOUL.md` — identity, cycle and security rules
- `PLAN.md` — task-by-task roadmap
- `CYCLE.md` — six-stage cycle record
- `MEMORY.md` — where memory lives and how to read and write it
- `HANDOFF.md` — what I receive from and hand to each sibling
- `BACKPACK.md` — this inventory
- `config/` — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakTan Equipment Inventory · House of Sak*
