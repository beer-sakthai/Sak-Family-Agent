# 🎒 BACKPACK.md — SakJules Complete Installation & Equipment Inventory

> **Agent**: SakJules 🔧 (Master of DevSecOps, GitHub Actions & Asynchronous Automation)  
> **Repository**: `Sak-Family-Agent`  
> **Hermes Profile**: `~/.hermes/profiles/sakjules/`  
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI** | `/home/beern/.local/bin/agy` | v2.0 Stdio & MCP | ✅ Active |
| **Google ADK CLI** | `/home/beern/.local/bin/agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `/home/beern/.local/bin/hermes` | Multi-profile TUI (`--profile sakjules`) | ✅ Active |
| **Supermemory Server Daemon** | `/home/beern/.supermemory/bin/supermemory-server` | v0.0.6 Daemon (`http://localhost:6767`) | ✅ Active (PID 23310) |
| **OpenCode CLI** | `opencode` | Configured via `opencode.json` | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`opencode.json`](file:///home/beern/opencode.json))

| Slot | Model ID / Identifier | Type | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `opencode-go/DeepSeek-V4-Flash` | OpenCode Go Reasoner | Complex coding, Pytest repair, PR synthesis |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual vector memory & RAG retrieval |

---

## 🛠️ 3. MCP Server & Remote Tool Loadout

- **📡 Remote Jules CLI & REST API Server (`julesServer` & REST Hook)**:
  - Webhook Endpoint: `http://localhost:8787/api/jules/webhook` (Auto-pull on COMPLETED)
  - REST Dispatch: `POST http://localhost:8787/api/jules/dispatch`
  - REST Status: `GET http://localhost:8787/api/jules/status`
  - `/jules-new` — Dispatch new remote coding session
  - `/jules-list` — List remote Jules sessions
  - `/jules-pull` — Pull and apply patch from Jules session
  - `/jules-teleport` — Clone repo and teleport into session branch
- **🧠 Local Supermemory Server**:
  - Endpoint: `http://localhost:6767` (PID `23310`)
  - Local ONNX Embedding Model: `Xenova/bge-base-en-v1.5`
- **📊 Google Colab MCP (`colab-mcp`)**:
  - `uvx git+https://github.com/googlecolab/colab-mcp`
- **⚡ Composio MCP (`composio`)**:
  - `npx -y composio-core@latest mcp start` (Integrates 250+ SaaS tools: GitHub, Slack, Gmail, Jira)
- **🎮 CUA Driver Daemon (`cua-driver`)**:
  - `/home/beern/.cua-driver/packages/releases/0.16.0-x86_64-unknown-linux-gnu/cua-driver`
- **🌐 Chrome DevTools MCP**:
  - `npx -y chrome-devtools-mcp@latest`

---

## 🔑 4. Credential & Environment Inventory (`~/.env`)

- **`JULES_API_KEY`**: Authenticated for remote Jules tasks
- **`OPENCODE_GO_API_KEY`**: Authenticated for OpenCode Go platform
- **`SUPERMEMORY_API_KEY`**: Authenticated for local Supermemory daemon
- **`RENDER_API_KEY`**: Authenticated for cloud deployments
- **`GOOGLE_API_KEY`**: Authenticated for Gemini fallback & vision APIs

---

## 📜 5. Permanent Configuration Files

- [`personas/sakjules/SOUL.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/SOUL.md) — Persona identity & directives
- [`personas/sakjules/PLAN.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/PLAN.md) — Mega Model Training Plan & 6-stage cycle
- [`personas/sakjules/MEMORY.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/MEMORY.md) — Fact store & execution logs
- [`personas/sakjules/BACKPACK.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/BACKPACK.md) — Complete installation & equipment inventory
- [`/.agents-cli-spec.md`](file:///home/beern/.agents-cli-spec.md) — Google ADK $0.00 zero-cost specification

---

*SakJules Complete Installation Inventory · House of Sak*
