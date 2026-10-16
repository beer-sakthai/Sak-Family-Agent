# 🎒 BACKPACK.md — SakSit 📣

> **Agent**: SakSit 📣 — Social / Content Specialist\
> **Repository**: `Sak-Family-Agent`\
> **Hermes Profile**: `infra/hermes-agents/profiles/saksit/`\
> **Cost Policy**: Zero-cost first — every operation must be free (SOUL principle 9).

---

## 🖥️ 1. How to Run Me

| Command | What it does |
|:---|:---|
| `sakthai run "<task>" --persona saksit` | One task through the agent loop, with my SOUL, skills, MCP config and model |
| `sakthai chat --persona saksit` | Interactive chat with the same setup |
| `SAKTHAI_HOME=$(mktemp -d) sakthai run "<task>" --persona saksit --no-mcp --dry-run` | Check provider, model, credentials and skills without a model call |
| `sakthai memory --persona saksit stats` | My memory shard at a glance |
| Telegram `@saksit_agent_bot` | The VM deployment, started by `infra/vm-agents/sakthai-agent-run.sh saksit` |

---

## 🤖 2. Model Loadout

| Where | Provider | Model | Set in |
|:---|:---|:---|:---|
| Local CLI (`--persona saksit`) | `huggingface` | `deepseek-ai/DeepSeek-V4-Flash` | `config/config.yaml` |
| Fallback | `ollama-cloud` | `gpt-oss:120b` | `config/config.yaml` (`fallback_model`) |
| VM Telegram bot | `openai` (Azure OpenAI) | `Phi-4-mini-reasoning` | `infra/vm-agents/sakthai-agent-run.sh` |

---

## 🛠️ 3. MCP Servers (`config/mcp.json`)

- **hf-media**: `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video`

Every package is pinned to an exact version — never `@latest` (Security Rule 5).

---

## 🧰 4. Skills

- **My overlay**: 43 skills in `personas/saksit/skills/`
- **Shared**: the `Sak-*` skills in `personas/shared/skills/`, composed into every persona
- **Primary** (`config/workspace.yaml`):
  - `SakSit-ai-seo-content-strategy-2026`
  - `SakSit-b2b-saas-brand-journalism-storytelling-2026`
  - `SakSit-hf-hub-model-card-seo-social-meta-tags`

---

## 🔑 5. Credentials & Environment (names only — never print a value)

- **Model provider**: `HF_TOKEN` — the only credential the `huggingface` provider reads.
- **VM env template** (`infra/vm-agents/env-templates/saksit.env.example`): `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`

---

## 📜 6. Permanent Files (`personas/saksit/`)

- `SOUL.md` — identity, cycle and security rules
- `PLAN.md` — task-by-task roadmap
- `CYCLE.md` — six-stage cycle record
- `MEMORY.md` — where memory lives and how to read and write it
- `HANDOFF.md` — what I receive from and hand to each sibling
- `BACKPACK.md` — this inventory
- `config/` — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`
- `README.md` — SakSit's own README

---

*SakSit Equipment Inventory · House of Sak*
