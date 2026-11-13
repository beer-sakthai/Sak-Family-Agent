# 🎒 BACKPACK.md — SakSit 📣 Complete Installation & Equipment Inventory

> **Agent**: SakSit 📣 (Social / Content Specialist)
> **Bot Handle**: `@saksit_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Hermes Profile**: `infra/hermes-agents/profiles/saksit/`
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `hermes --profile saksit` | Multi-profile TUI & Systemd Gateway | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona saksit` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/saksit/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksit/config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksit/config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `deepseek-ai/DeepSeek-V4-Flash` | `huggingface` | Primary persona reasoning & tool execution (`--persona saksit`) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.FAST (gemini-2.5-flash / deepseek-ai/DeepSeek-V4-Flash)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / Phi-4-mini-reasoning` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@saksit_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **🎨 Hugging Face Media Spaces MCP (`hf-media`)**:
  - `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video` (pinned in `config/mcp.json`, never `@latest` — Security Rule 5)
- **📝 Two-Gate Content & Model Card Pipeline**:
  - **Gate 1 (Before Writing)**: Requires live card state from SakThai (`sakthai hf info <repo_id>`); pauses with `gate1-unavailable` if SakThai is Critical
  - **Gate 2 (Before Publishing)**: Saves drafts with `hub-draft` + `awaiting-review`; never publishes without Beer's `hub-approved` tag
- **📊 Zero-Scrape Data Request Protocol (`data-request`)**:
  - SakSit never scrapes the web directly; writes `data-request` for SakSee and cites SakSee's `monitoring-result` (`retrieved_at`)
  - Marks any unverified claim with explicit `[PENDING VERIFICATION]` (`-15` eval penalty if omitted)
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness saksit` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (43 Overlay Skills + 3 Shared Skills)**:
  - **Overlay Root**: [`personas/saksit/skills/`](file:///home/sak/Sak-Family-Agent/personas/saksit/skills) (43 specialized `SakSit-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills) (3 shared skills: `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksit/config/workspace.yaml)):
  - `SakSit-ai-seo-content-strategy-2026`
  - `SakSit-b2b-saas-brand-journalism-storytelling-2026`
  - `SakSit-hf-hub-model-card-seo-social-meta-tags`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for `deepseek-ai/DeepSeek-V4-Flash` on Hugging Face Inference Providers and `FLUX.1-schnell` / `LTX-Video` Spaces
- **VM Env Template (`infra/vm-agents/env-templates/saksit.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/saksit/`)

- [`personas/saksit/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/saksit/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/saksit/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/saksit/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/MEMORY.md) — Shard bindings (`~/.sakthai/saksit/memory.db`), read/write CLI commands & execution log
- [`personas/saksit/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/saksit/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/BACKPACK.md) — This complete installation & equipment inventory
- [`personas/saksit/config/`](file:///home/sak/Sak-Family-Agent/personas/saksit/config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakSit Complete Installation & Equipment Inventory · House of Sak*
