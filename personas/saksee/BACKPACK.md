# 🎒 BACKPACK.md — SakSee Equipment & Starter Inventory

> **Agent**: SakSee 👁️ (Master of Web Scraping, Playwright, DevTools & Computer Use Vision)  
> **Repository**: `Sak-Family-Agent`  
> **Hermes Profile**: `~/.hermes/profiles/saksee/`  
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **AGY CLI** | `/home/beern/.local/bin/agy` | v2.0 Stdio & MCP | ✅ Active |
| **Google ADK CLI** | `/home/beern/.local/bin/agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **Hermes Agent CLI** | `/home/beern/.local/bin/hermes` | Multi-profile TUI (`--profile saksee`) | ✅ Active |
| **Supermemory Server Daemon** | `/home/beern/.supermemory/bin/supermemory-server` | v0.0.6 Daemon (`http://localhost:6767`) | ✅ Active (PID 23310) |
| **OpenCode CLI** | `opencode` | Configured via `opencode.json` | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`opencode.json`](file:///home/beern/opencode.json))

| Slot | Model ID / Identifier | Type | Role |
|:---|:---|:---|:---|
| **Local Browser Engine** | `hf.co/Nanthasit/sakthai-coder-browser-gguf` | Custom 7.1 GB GGUF | Sub-100ms local Playwright & DOM automation |
| **Vision Computer Use** | `google/gemini-3.5-flash` / `gemini-2.5-flash` | Multimodal Vision API | High-res UI screenshot parsing & bounding box coordinates `click(x, y)` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B | Ultra-fast triage & web selector routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual vector memory & RAG retrieval |

---

## 🛠️ 3. Web & Vision Tool Loadout

- **🌐 Playwright Browser Engine**:
  - Chromium Version: `v1.62.1` (`~/.cache/ms-playwright/chromium-1155`)
- **🚀 Desktop Executable**:
  - Perplexity Comet: `/mnt/c/Program Files/Perplexity/Comet/Application/comet.exe` (`COMET_EXE_PATH` in `.env`)
- **📡 Automated Web Monitor Hook (`saksee-auto-monitor.sh`)**:
  - Script: `.opencode/scripts/saksee-auto-monitor.sh` (Monitors Beer's 6 HF Spaces, records `monitoring-result` to `~/.sakthai/memory.db`)
- **⚡ Composio MCP (`composio`)**:
  - `npx -y composio-core@latest mcp start` (Integrates 250+ SaaS tools: GitHub, Slack, Gmail, Jira)
- **🎮 CUA Driver Daemon (`cua-driver`)**:
  - Path: `/home/beern/.cua-driver/packages/releases/0.16.0-x86_64-unknown-linux-gnu/cua-driver`
  - Capabilities: `browser_click`, `browser_type`, `browser_scroll`, pixel-coordinate targeting
- **🌐 Chrome DevTools MCP**:
  - `npx -y chrome-devtools-mcp@latest`
- **🎨 Google Stitch MCP (`stitch`)**:
  - Endpoint: `https://stitch.googleapis.com/mcp`
  - Headers: `X-Goog-Api-Key`
- **🧠 Local Supermemory Server**:
  - Endpoint: `http://localhost:6767` (PID `23310`)
  - Local ONNX Embedding Model: `Xenova/bge-base-en-v1.5`

---

## 🔑 4. Credential & Environment Inventory (`~/.env`)

- **`COMET_EXE_PATH`**: `/mnt/c/Program Files/Perplexity/Comet/Application/comet.exe`
- **`GOOGLE_API_KEY`**: Authenticated for Gemini 3.5 Flash vision computer use
- **`OPENCODE_GO_API_KEY`**: Authenticated for OpenCode Go platform
- **`SUPERMEMORY_API_KEY`**: Authenticated for local Supermemory daemon

---

## 📜 5. Permanent Configuration Files

- [`personas/saksee/SOUL.md`](file:///home/beern/Sak-Family-Agent/personas/saksee/SOUL.md) — Persona identity & directives
- [`personas/saksee/PLAN.md`](file:///home/beern/Sak-Family-Agent/personas/saksee/PLAN.md) — Web vision & Playwright roadmap
- [`personas/saksee/MEMORY.md`](file:///home/beern/Sak-Family-Agent/personas/saksee/MEMORY.md) — Fact store & selector registry
- [`personas/saksee/BACKPACK.md`](file:///home/beern/Sak-Family-Agent/personas/saksee/BACKPACK.md) — Complete installation & equipment inventory
- [`personas/saksee/CYCLE.md`](file:///home/beern/Sak-Family-Agent/personas/saksee/CYCLE.md) — 6-Stage Growth Cycle Workflow record

---

*SakSee Complete Equipment Inventory · House of Sak*
