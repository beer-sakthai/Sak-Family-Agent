# 🎒 BACKPACK.md — SakKing 👑 Complete Installation & Equipment Inventory

> **Agent**: SakKing 👑 (General Assistant & Runner (Deputy 1))
> **Bot Handle**: `@sakking_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Hermes Profile**: `infra/hermes-agents/profiles/sakking/`
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `hermes --profile sakking` | Multi-profile TUI & Systemd Gateway | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona sakking` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/sakking/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakking/config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakking/config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | `huggingface` | Primary persona reasoning & tool execution (`--persona sakking`) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.REASONING (gemini-2.5-pro / Qwen/Qwen3-Coder-30B-A3B-Instruct)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / model-router` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@sakking_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **🌐 Playwright Browser MCP (`playwright`)**:
  - `npx -y @playwright/mcp@0.0.83` (pinned in `config/mcp.json`, never `@latest`)
- **🔍 Chrome DevTools MCP (`chrome-devtools`)**:
  - `npx -y chrome-devtools-mcp@1.10.1` (pinned in `config/mcp.json`, never `@latest`)
- **🎨 Hugging Face Media Spaces MCP (`hf-media`)**:
  - `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video` (pinned in `config/mcp.json`)
- **⚡ Isolated Command & TDD Runner (`sakthai platform wrap-cmd` & `run_command`)**:
  - Opt-in via `SAKTHAI_SHELL_ALLOW`, 120s timeout, guarded by `DataLossGuardrail` (`check_data_loss_guardrail`)
  - Automatic virtualenv command wrapping via `wrap_with_isolated_runner` (`uv run ...`)
- **🔄 Cross-Persona Delegation (`delegate_to_persona` & `sakthai skills sync-sakking`)**:
  - Depth-bounded (`DEFAULT_MAX_DELEGATION_DEPTH = 2`), cycle-safe delegation in `sakthai/agent/coordinator.py`
  - Aggregates learned skills across the family (`106` overlay skills)
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness sakking` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (106 Overlay Skills + 3 Shared Skills)**:
  - **Overlay Root**: [`personas/sakking/skills/`](file:///home/sak/Sak-Family-Agent/personas/sakking/skills) (106 specialized `SakKing-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills) (3 shared skills: `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakking/config/workspace.yaml)):
  - `SakKing-subagent-driven-development`
  - `sakthai-coding-tdd`
  - `SakKing-executing-plans`
  - `SakKing-systematic-debugging`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for `Qwen/Qwen3-Coder-30B-A3B-Instruct` on Hugging Face Inference Providers and `hf-media` Spaces
- **`SAKTHAI_SHELL_ALLOW`**: Explicit opt-in gate required before `run_command` executes shell tasks
- **VM Env Template (`infra/vm-agents/env-templates/sakking.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/sakking/`)

- [`personas/sakking/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/sakking/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/sakking/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/sakking/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/MEMORY.md) — Shard bindings (`~/.sakthai/sakking/memory.db`), read/write CLI commands & execution log
- [`personas/sakking/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/sakking/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/BACKPACK.md) — This complete installation & equipment inventory
- [`personas/sakking/config/`](file:///home/sak/Sak-Family-Agent/personas/sakking/config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakKing Complete Installation & Equipment Inventory · House of Sak*
