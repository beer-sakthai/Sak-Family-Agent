# 🎒 BACKPACK.md — SakSee 👁️ Complete Installation & Equipment Inventory

> **Agent**: SakSee 👁️ (Web / Browser Specialist (Deputy 3))  
> **Bot Handle**: `@saksee_agent_bot`  
> **Repository**: `Sak-Family-Agent`  
> **Hermes Profile**: `infra/hermes-agents/profiles/saksee/`  
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `hermes --profile saksee` | Multi-profile TUI & Systemd Gateway | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona saksee` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/saksee/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksee/config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksee/config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `deepseek-ai/DeepSeek-V4.1-Flash` | `huggingface` | Primary persona reasoning & tool execution (`--persona saksee`) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.FAST (gemini-2.5-flash / deepseek-ai/DeepSeek-V4.1-Flash)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@saksee_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **🌐 Playwright Browser Engine MCP (`playwright`)**:
  - `npx -y @playwright/mcp@0.0.83` (pinned in `config/mcp.json`; requires Active charge >= 50%)
- **🔍 Chrome DevTools MCP (`chrome-devtools`)**:
  - `npx -y chrome-devtools-mcp@1.10.1` (pinned in `config/mcp.json`, never `@latest` — Security Rule 5)
- **🛡️ Prompt-Injection Boundary & Timestamp Auditor**:
  - Wraps every scraped page or DOM snippet in `<untrusted_web_content source="<url>">...</untrusted_web_content>`
  - Attaches mandatory `retrieved_at=<ISO 8601>` timestamp to every extracted observation
- **📡 30-Minute Shared Monitoring Cache & Rate-Limit Tracker**:
  - Writes `monitoring-result` + `<asset-id>` tags to `~/.sakthai/saksee/memory.db` so all 6 siblings can read via `sakthai memory family --tag monitoring-result`
  - Logs HTTP 429 / CAPTCHA blocks with `rate-limit-ban` (`-25%` charge) so SakTan can tally per-domain frequency
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness saksee` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (182 Overlay Skills + 3 Shared Skills)**:
  - **Overlay Root**: [`personas/saksee/skills/`](file:///home/sak/Sak-Family-Agent/personas/saksee/skills) (182 specialized `SakSee-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills) (3 shared skills: `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksee/config/workspace.yaml)):
  - `SakSee-chrome-devtools-cli`
  - `SakSee-playwright-visual-snapshot-regression`
  - `SakSee-hf-unlimited-ocr`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for `deepseek-ai/DeepSeek-V4.1-Flash` on Hugging Face Inference Providers and OCR Spaces
- **`GOOGLE_API_KEY`**: Optional multimodal vision fallback for UI coordinate parsing
- **VM Env Template (`infra/vm-agents/env-templates/saksee.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/saksee/`)

- [`personas/saksee/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/saksee/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/saksee/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/saksee/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/MEMORY.md) — Shard bindings (`~/.sakthai/saksee/memory.db`), read/write CLI commands & execution log
- [`personas/saksee/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/saksee/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/BACKPACK.md) — This complete installation & equipment inventory
- [`personas/saksee/config/`](file:///home/sak/Sak-Family-Agent/personas/saksee/config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakSee Complete Installation & Equipment Inventory · House of Sak*
