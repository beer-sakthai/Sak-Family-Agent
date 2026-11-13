# 🎒 BACKPACK.md — SakTan 📗 Complete Installation & Equipment Inventory

> **Agent**: SakTan 📗 (Daily Ops & Rhythm (Deputy 2))  
> **Bot Handle**: `@saktan_agent_bot`  
> **Repository**: `Sak-Family-Agent`  
> **Hermes Profile**: `infra/hermes-agents/profiles/saktan/`  
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `hermes --profile saktan` | Multi-profile TUI & Systemd Gateway | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona saktan` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/saktan/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saktan/config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saktan/config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `sakthai` | `ollama` | Primary persona reasoning & tool execution (`--persona saktan`) |
| **Fallback Engine** | `Local Ollama (`http://127.0.0.1:11434`)` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.LOCAL (ollama/sakthai — $0.00 Local Execution)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@saktan_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **🏠 100% Local Zero-Cost Execution (`config/mcp.json`: `{}`)**:
  - Runs on local Ollama (`sakthai` model) with zero external MCP servers and zero API token spend
  - Uses built-in memory, calendar, and mail tools (`list_calendar_events`, `create_calendar_event`, `read_outlook_mail`, `send_telegram_message`)
- **⏰ Household Rhythm & Cron Proposal Engine (`schedule-request`)**:
  - Drives Beer's daily rhythm (`SakTan-daily-briefing`, `SakTan-close-the-day`, `SakTan-weekly-review`) with strict token economy (one clear next action)
  - Proposes cron schedules via `schedule-request` for SakJules to implement (`schedule-confirmed`)
- **🛡️ Family Health Watchdog (Ban Tally & Stalled Joy Monitor)**:
  - Counts SakSee's `rate-limit-ban` tags per domain so repeatedly banning domains are retired rather than retried
  - Monitors SakSit's `cycle-paused` + `awaiting-beer` Joy stages and notifies Beer when a draft waits > 7 days
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness saktan` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (13 Overlay Skills + 3 Shared Skills)**:
  - **Overlay Root**: [`personas/saktan/skills/`](file:///home/sak/Sak-Family-Agent/personas/saktan/skills) (13 specialized `SakTan-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills) (3 shared skills: `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](file:///home/sak/Sak-Family-Agent/personas/saktan/config/workspace.yaml)):
  - `SakTan-daily-briefing`
  - `SakTan-close-the-day`
  - `SakTan-weekly-review`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`OLLAMA_HOST`**: Local Ollama endpoint (`http://127.0.0.1:11434`, requires zero API key)
- **`MS_GRAPH_REFRESH_TOKEN`**: Optional credential for calendar and mail reminders (`~/.sakthai/graph_token.json`)
- **VM Env Template (`infra/vm-agents/env-templates/saktan.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/saktan/`)

- [`personas/saktan/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/saktan/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/saktan/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/saktan/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/MEMORY.md) — Shard bindings (`~/.sakthai/saktan/memory.db`), read/write CLI commands & execution log
- [`personas/saktan/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/saktan/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/BACKPACK.md) — This complete installation & equipment inventory
- [`personas/saktan/config/`](file:///home/sak/Sak-Family-Agent/personas/saktan/config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakTan Complete Installation & Equipment Inventory · House of Sak*
