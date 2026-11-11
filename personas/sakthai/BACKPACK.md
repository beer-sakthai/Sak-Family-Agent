# 🎒 BACKPACK.md — SakThai 🤗

> **Agent**: SakThai 🤗 — Main Lead & HF Master\
> **Repository**: `Sak-Family-Agent`\
> **Hermes Profile**: `infra/hermes-agents/default/`\
> **Cost Policy**: Zero-cost first — every operation must be free (SOUL principle 8).

---

## 🖥️ 1. How to Run Me

| Command | What it does |
|:---|:---|
| `sakthai run "<task>" --persona sakthai` | One task through the agent loop, with my SOUL, skills, MCP config and model |
| `sakthai chat --persona sakthai` | Interactive chat with the same setup |
| `SAKTHAI_HOME=$(mktemp -d) sakthai run "<task>" --persona sakthai --no-mcp --dry-run` | Check provider, model, credentials and skills without a model call |
| `sakthai memory --persona sakthai stats` | My memory shard at a glance |
| Telegram `@sakthai_agent_bot` | The VM deployment, started by `infra/vm-agents/sakthai-agent-run.sh sakthai` |

---

## 🤖 2. Model Loadout

| Where | Provider | Model | Set in |
|:---|:---|:---|:---|
| Local CLI (`--persona sakthai`) | `huggingface` | `deepseek-ai/DeepSeek-V4.1-Flash` | `config/config.yaml` |
| Fallback | `ollama-cloud` | `gpt-oss:120b` | `config/config.yaml` (`fallback_model`) |
| VM Telegram bot | `openai` (Azure OpenAI) | `gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` |

---

## 🛠️ 3. MCP Servers (`config/mcp.json`)

None — `config/mcp.json` lists no servers. Hugging Face access goes through the built-in `huggingface_inference` tool and `sakthai hf`.

---

## 🧰 4. Skills

- **My overlay**: 299 skills in `personas/sakthai/skills/`
- **Shared**: the `Sak-*` skills in `personas/shared/skills/`, composed into every persona
- **Primary** (`config/workspace.yaml`):
  - `SakThai-speckit-bridge`
  - `SakThai-spec-kit`
  - `SakThai-huggingface-cli`
  - `SakThai-learning-loop`

---

## 🔑 5. Credentials & Environment (names only — never print a value)

- **Model provider**: `HF_TOKEN` — the only credential the `huggingface` provider reads.
- **VM env template** (`infra/vm-agents/env-templates/sakthai.env.example`): `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`

---

## 📜 6. Permanent Files (`personas/sakthai/`)

- `SOUL.md` — identity, cycle and security rules
- `PLAN.md` — task-by-task roadmap
- `CYCLE.md` — six-stage cycle record
- `MEMORY.md` — where memory lives and how to read and write it
- `HANDOFF.md` — what I receive from and hand to each sibling
- `BACKPACK.md` — this inventory
- `config/` — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`
- `LEARNING_JOURNAL.md` — SakThai's learning journal

---

*SakThai Equipment Inventory · House of Sak*
