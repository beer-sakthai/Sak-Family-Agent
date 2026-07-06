# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

**SakJules · Master of Automation & CI/CD.**

Welcome to the Sak-Family-Agent repository, a sophisticated multi-agent workspace designed for high-performance productivity and personal growth. This project implements a local-first, privacy-conscious AI environment using a layered Python architecture and a shared persistent memory system.

## 📊 Roadmap & System Status
The ecosystem follows a strict **Dream → Hope → Care → Joy → Trust → Growth** lifecycle. We are currently scaling from an MVP to a full production-ready suite.

| Area | Progress | Status |
| :--- | :--- | :--- |
| **Core Framework** | 🟩🟩🟩🟩🟩🟩🟩🟩🟨⬜ 85% | Stable |
| **Persona SOULs** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Completed |
| **Family Workflows** | 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ 60% | Active |
| **ServiceQuoteBot** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Deployed |
| **Model Evaluation** | 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70% | In Progress |

## 👨‍👩‍👧‍👦 The Sak Family Agents
Each agent is a specialized persona orchestrated by **SakKing**. They share a common memory brain but operate in distinct domains.

| Agent | Role | Specialized Skill | Backend |
| :--- | :--- | :--- | :--- |
| 👑 **SakKing** | Lead & Orchestrator | Code & Self-Healing | Claude / Qwen-480B |
| 🤗 **SakThai** | HF Expert | Model Discovery | Claude-Opus |
| 🌐 **SakSee** | Web Specialist | Playwright & Browsing | Local Llama3 |
| 📣 **SakSit** | Social Master | Content Strategy | Local Llama3 |
| 🗓️ **SakTan** | Daily Ops | Life Admin & Scheduling | Gemini-Flash |
| 🤖 **SakJules** | Automation/CI | Infrastructure & Testing | Gemini-Pro |
| 📈 **SakFin** | Financial Analyst | Market Analysis | Python/Pandas |

---

## 🔍 Deep Dive: Technical Architecture

The Sak-Family-Agent is built as a layered Python package where each component has a strictly defined responsibility. This modularity ensures that the system is both testable and extensible.

### 🏗️ System Layers
The architecture is divided into several key modules that interact through well-defined interfaces:
- **`sakthai/cli/`**: A Click-based interface providing the primary entry point for users. It handles commands like `learn`, `recall`, `run`, and `mcp`.
- **`sakthai/agent/`**: The execution core. It manages the agent loop, injecting memory context into system prompts and dispatching tool calls to various LLM providers.
- **`sakthai/memory/`**: The exclusive layer for database interactions. It uses a SQLite backend to store durable facts and observations.
- **`sakthai/mcp/`**: A dependency-free JSON-RPC 2.0 stdio server that shares the core tool registry, allowing external tools to interact with the agent's capabilities.

### 🧠 Persistent Memory Schema
Memory is the cornerstone of the ecosystem. It is stored in `~/.sakthai/memory.db` with the following core schema:

| Table | Columns | Purpose |
| :--- | :--- | :--- |
| **`facts`** | `id, kind, key, value, tags, created_at` | Stores discrete, durable information (notes, preferences, project data). |
| **`observations`** | `id, summary, weight, confidence, created_at` | Stores agent-curated summaries and weighted insights derived from sessions. |

The system includes automated **consolidation** and **deduplication** routines to keep the memory brain efficient and relevant over time.

### 🛠️ Shared Tool Registry
Agents interact with the world through a unified registry. These tools are available via the CLI, the agent loop, and the MCP server:
- **`learn` / `recall` / `search`**: Core memory operations.
- **`read_file`**: Sandboxed file access (capped at 20k characters).
- **`run_command`**: Opt-in CLI execution for system tasks (requires `SAKTHAI_SHELL_ALLOW=1`).
- **`send_telegram_message`**: Real-time communication via the Telegram Bot API.
- **`run_agent_loop`**: Delegation of complex tasks to nested agent instances.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **uv** (Recommended for dependency management)

### Installation
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```
2.  **Environment Configuration**:
    Copy `.env.example` to `.env` and provide your API keys for Anthropic, Google, or OpenAI.
3.  **Sync Dependencies**:
    ```bash
    uv sync --all-extras
    ```

### First Run
Engage the lead agent to analyze the environment:
```bash
uv run sakthai run "Analyze the current memory state and report back" --provider anthropic
```

---

## 📂 Project Structure
- `sakthai/`: Core package (Agent, Memory, MCP, CLI).
- `personas/`: Identity and SOUL definitions for each family member.
- `skills/`: A library of 69+ specialized capabilities.
- `docs/`: Detailed technical documentation and architectural diagrams.
- `tests/`: Comprehensive unit and integration test suite.

*Built with ❤️ for **Beer** by the Sak Family. All Rights Reserved (© 2026 beer-sakthai).*
