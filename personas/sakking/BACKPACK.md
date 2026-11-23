# 🎒 BACKPACK.md — SakKing 👑 Complete Installation & Equipment Inventory

> **Agent**: SakKing 👑 (General Assistant & Runner (Deputy 1))
> **Bot Handle**: `@sakking_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Runtime**: Standalone sakthai (Base: ~/.sakthai · Shard: ~/.sakthai/sakking/memory.db)
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)
> **Fleet Comparison**: See [Fleet-Wide Comparison Matrix](../../docs/capabilities.md#fleet-wide-persona-comparison-matrix)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **Extensions Runtime** | `~/.sakthai/sakking/extensions` · `sakthai extensions` | 8-Factor Rubric (`sakthai eval extensions`) | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona sakking` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/sakking/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](./config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](./config/config.yaml))

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

- **⚡ Firebase Genkit MCP (`genkit`)**:
  - `npx -y genkit mcp` (stdio transport with graceful fallback when unconfigured)
- **📚 Google Developer Knowledge MCP (`google_dev_knowledge`)**:
  - `https://developerknowledge.googleapis.com/mcp` with preset search scopes for `antigravity.google`, `adk.dev`, `developers.google.com`
- **🌐 Playwright Browser MCP (`playwright`)**:
  - `npx -y @playwright/mcp@0.0.83` (pinned in `config/mcp.json`, never `@latest`)
- **🔍 Chrome DevTools MCP (`chrome-devtools`)**:
  - `npx -y chrome-devtools-mcp@1.10.1` (pinned in `config/mcp.json`, never `@latest`)
- **🎨 Hugging Face Media Spaces MCP (`hf-media`)**:
  - `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video` (pinned in `config/mcp.json`)
- **🔒 StepSecurity Agent MCP (`stepsecurity`)**:
  - `https://agent.api.stepsecurity.io/v1/mcp?customer=beer-sakthai` (remote SSE endpoint configured in `config/mcp.json`)
- **📧 Microsoft 365 MCP (`microsoft365`)**:
  - `https://microsoft365.mcp.claude.com/mcp` (remote endpoint in `config/mcp.json`; read-only allowlist: mail/calendar/SharePoint/Teams search, no send or delete)
- **📚 Microsoft Learn MCP (`microsoft-learn`)**:
  - `https://learn.microsoft.com/api/mcp` (public remote endpoint in `config/mcp.json`; docs search, code-sample search and page fetch; no token)
- **✨ Gemini API Docs MCP (`gemini-api-docs`)**:
  - `https://gemini-api-docs-mcp.dev` (public remote endpoint in `config/mcp.json`; `gemini_search_docs` and `gemini_get_doc`; no token)
- **⚡ Isolated Command & TDD Runner (`sakthai platform wrap-cmd` & `run_command`)**:
  - Opt-in via `SAKTHAI_SHELL_ALLOW`, 120s timeout, guarded by `DataLossGuardrail` (`check_data_loss_guardrail`)
  - Automatic virtualenv command wrapping via `wrap_with_isolated_runner` (`uv run ...`)
- **🔄 Cross-Persona Delegation (`delegate_to_persona` & `sakthai skills sync-sakking`)**:
  - Depth-bounded (`DEFAULT_MAX_DELEGATION_DEPTH = 2`), cycle-safe delegation in `sakthai/agent/coordinator.py`
  - Aggregates learned skills across the family (`59` overlay skills)
- **🎙️ Gateway Voice Mode (`config/gateway_voice_mode.json`)**:
  - Configured for `telegram:8618306046: "all"` via the OpenAI-compatible runtime gateway.
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Tool Schema Validation & Quality Gates**: Zero-dependency argument validation (`Tool.validate_args`), safe execution with error containment & secret redaction (`Tool.safe_call`), and 6-factor Tool Quality Rubric & benchmarks (`sakthai eval tools`)
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness sakking` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (59 Overlay Skills + 19 Shared Skills)**:
  - **Overlay Root**: [`personas/sakking/skills/`](./skills) (59 specialized `SakSakking-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](../shared/skills) (19 shared `Sak-*` skills including `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-ocr-and-documents`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](./config/workspace.yaml)):
  - `SakKing-subagent-driven-development`
  - `SakKing-coding-tdd`
  - `SakKing-executing-plans`
  - `SakKing-systematic-debugging`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for `Qwen/Qwen3-Coder-30B-A3B-Instruct` on Hugging Face Inference Providers and `hf-media` Spaces
- **`SAKTHAI_SHELL_ALLOW`**: Explicit opt-in gate required before `run_command` executes shell tasks
- **`STEP_SECURITY_API_KEY`**: Authenticated bearer token for remote StepSecurity MCP endpoint
- **`MS365_MCP_TOKEN`**: Bearer token for the remote Microsoft 365 MCP endpoint
- **VM Env Template (`infra/vm-agents/env-templates/sakking.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/sakking/`)

- [`personas/sakking/SOUL.md`](./SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/sakking/PLAN.md`](./PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/sakking/CYCLE.md`](./CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/sakking/MEMORY.md`](./MEMORY.md) — Shard bindings (`~/.sakthai/sakking/memory.db`), read/write CLI commands & execution log
- [`personas/sakking/HANDOFF.md`](./HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/sakking/BACKPACK.md`](./BACKPACK.md) — This complete installation & equipment inventory
- [`personas/sakking/config/`](./config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakKing Complete Installation & Equipment Inventory · House of Sak*
