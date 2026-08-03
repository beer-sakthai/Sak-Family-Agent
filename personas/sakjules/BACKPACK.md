# 🎒 BACKPACK.md — SakJules Equipment & Starter Inventory

> **Agent**: SakJules 🔧 (Master of DevSecOps, GitHub Actions & Asynchronous Automation)  
> **Repository**: `Sak-Family-Agent`  
> **Profile Path**: `~/.hermes/profiles/sakjules/`  
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)

---

## 🤖 1. Active Model Loadout ([`opencode.json`](file:///home/beern/opencode.json))

| Slot | Model ID / Identifier | Type | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `huggingface/deepseek-ai/DeepSeek-V4-Flash` | Open-Weights Reasoner | Complex coding, Pytest repair, PR synthesis |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual vector memory & RAG retrieval |

---

## 🛠️ 2. MCP Server & Remote Tool Loadout

- **📡 Remote Jules CLI & Server (`julesServer`)**:
  - `/jules-new` — Dispatch new remote coding session
  - `/jules-list` — List remote Jules sessions
  - `/jules-pull` — Pull and apply patch from Jules session
  - `/jules-teleport` — Clone repo and teleport into session branch
- **🧠 Local Supermemory Server**:
  - Endpoint: `http://localhost:6767` (PID `23310`)
  - Local ONNX Embedding Model: `Xenova/bge-base-en-v1.5`
- **📊 Google Colab MCP (`colab-mcp`)**:
  - `uvx git+https://github.com/googlecolab/colab-mcp`
- **🎮 CUA Driver Daemon (`cua-driver`)**:
  - `/home/beern/.cua-driver/packages/releases/0.16.0-x86_64-unknown-linux-gnu/cua-driver`
- **🌐 Chrome DevTools MCP**:
  - `npx -y chrome-devtools-mcp@latest`

---

## 🔑 3. Credential & Environment Inventory (`~/.env`)

- **`JULES_API_KEY`**: Authenticated for remote Jules tasks
- **`OPENCODE_GO_API_KEY`**: Authenticated for OpenCode Go platform
- **`SUPERMEMORY_API_KEY`**: Authenticated for local Supermemory daemon
- **`RENDER_API_KEY`**: Authenticated for cloud deployments
- **`GOOGLE_API_KEY`**: Authenticated for Gemini fallback & vision APIs

---

## 🧰 4. Frameworks & CLI Executables

- **Google ADK CLI**: `agents-cli` v1.2.1 (`/home/beern/.local/bin/agents-cli`)
- **AGY CLI**: `agy` (`/home/beern/.local/bin/agy`)
- **Hermes Agent**: `hermes` CLI (`/home/beern/.local/bin/hermes`)
- **Python Sandbox**: Pytest v9.1.1, Python 3.12 ML stack (`~/.venv`)

---

## 📜 5. Permanent Configuration Files

- [`personas/sakjules/SOUL.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/SOUL.md) — Persona identity & directives
- [`personas/sakjules/PLAN.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/PLAN.md) — Mega Model Training Plan & 6-stage cycle
- [`personas/sakjules/MEMORY.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/MEMORY.md) — Fact store & execution logs
- [`personas/sakjules/BACKPACK.md`](file:///home/beern/Sak-Family-Agent/personas/sakjules/BACKPACK.md) — This equipment inventory

---

*SakJules Starter Inventory · House of Sak*
