# 🎒 BACKPACK.md — SakJules 🔧 Complete Installation & Equipment Inventory

> **Agent**: SakJules 🔧 (Master of GitHub, CI/CD & Automation)
> **Bot Handle**: `@sakjules_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Hermes Profile**: `infra/hermes-agents/profiles/sakjules/`
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `hermes --profile sakjules` | Multi-profile TUI & Systemd Gateway | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona sakjules` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/sakjules/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakjules/config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakjules/config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `deepseek-ai/DeepSeek-V4.1-Flash` | `huggingface` | Primary persona reasoning & tool execution (`--persona sakjules`) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.REASONING (gemini-2.5-pro / deepseek-ai/DeepSeek-V4.1-Flash)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@sakjules_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **📡 Jules Remote Asynchronous Delegation (`sakthai.agent_platform.jules_worker`)**:
  - GitHub remote resolution, asynchronous patch planning, session formatting, and patch validation (`tests/test_jules_worker.py`)
  - `config/mcp.json` lists `{}` (no unpinned runtime npx installs — Security Rule 5)
- **🏗️ Harness v1 AI Agent & Pipeline Exporter (`sakthai platform export-harness`)**:
  - Deterministic canonical identifier generation (`ca_<slug>`) and declarative Harness v1 agent template & pipeline step export (`sakthai/agent_platform/harness_exporter.py`)
- **🔒 Full Quality & DevSecOps Gate Suite (`.github/workflows/ci.yml`)**:
  - `uv run ruff check personas/sakthai/sakthai tests` & `uv run ruff format --check personas/sakthai/sakthai tests`
  - `uv run mypy personas/sakthai/sakthai` (strict type checking)
  - `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` (AST security scan)
  - `uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-fail-under=96` (96.21% coverage floor)
  - Parity enforcement: `tests/test_persona_guardrails_parity.py` & `tests/test_persona_web_server_parity.py`
- **⏰ Cron Schedule Implementation (`schedule-request` → `schedule-confirmed`)**:
  - Implements schedules proposed by SakTan and confirms them in family memory
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness sakjules` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (180 Overlay Skills + 3 Shared Skills)**:
  - **Overlay Root**: [`personas/sakjules/skills/`](file:///home/sak/Sak-Family-Agent/personas/sakjules/skills) (180 specialized `SakJules-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills) (3 shared skills: `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](file:///home/sak/Sak-Family-Agent/personas/sakjules/config/workspace.yaml)):
  - `SakJules-github-ci-fix`
  - `SakJules-triage-issues`
  - `SakJules-workflow`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for `deepseek-ai/DeepSeek-V4.1-Flash` on Hugging Face Inference Providers
- **`GH_TOKEN` / `GITHUB_TOKEN`**: Authenticated for `gh pr list`, workflow inspection, and PR hygiene checks
- **`JULES_API_KEY`**: Optional credential for remote asynchronous Jules task dispatch
- **VM Env Template (`infra/vm-agents/env-templates/sakjules.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/sakjules/`)

- [`personas/sakjules/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/sakjules/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/sakjules/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/sakjules/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/MEMORY.md) — Shard bindings (`~/.sakthai/sakjules/memory.db`), read/write CLI commands & execution log
- [`personas/sakjules/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/sakjules/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/BACKPACK.md) — This complete installation & equipment inventory
- [`personas/sakjules/config/`](file:///home/sak/Sak-Family-Agent/personas/sakjules/config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakJules Complete Installation & Equipment Inventory · House of Sak*
