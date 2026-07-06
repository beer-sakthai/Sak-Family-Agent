# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

[![CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey)

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

**SakJules · Master of Automation & CI/CD.**

Welcome to the Sak-Family-Agent repository, a sophisticated multi-agent workspace designed for high-performance productivity and personal growth. This project implements a local-first, privacy-conscious AI environment using a layered Python architecture and a shared persistent memory system.

---

## 📑 Table of Contents
- [🖥️ System Status](#system-status)
- [📊 Roadmap & System Status](#-roadmap--system-status)
- [👨‍👩‍👧‍👦 The Sak Family Agents](#-the-sak-family-agents)
- [🤝 Family Workflows](#-family-workflows)
- [🔍 Deep Dive: Technical Architecture](#-deep-dive-technical-architecture)
- [🛠️ CLI Command Cheat Sheet](#-cli-command-cheat-sheet)
- [🚀 Getting Started](#-getting-started)
- [📖 Glossary of Terms](#-glossary-of-terms)
- [📂 Project Structure](#-project-structure)

---

## 🖥️ System Status
The system inside, subsystem by subsystem — all sharing one `~/.sakthai/memory.db` brain across three runtime entry points (CLI, agent loop, MCP server).

| Subsystem | Status | Description |
| :--- | :--- | :--- |
| ⌨️ **CLI** (`sakthai/cli/`) | 🟢 Operational | `sakthai` entry point — `learn`/`recall`/`run`/`mcp`/`dashboard`/... |
| 🤖 **Agent Loop** (`sakthai/agent/`) | 🟢 Operational | Claude / Gemini / OpenAI-compatible tool-using orchestration |
| 🧠 **Memory Store** (`sakthai/memory/`) | 🟢 Operational | SQLite WAL store for durable facts + observations |
| 🔌 **MCP Server** (`sakthai/mcp/`) | 🟢 Operational | JSON-RPC 2.0 stdio server, shares the CLI's tool registry |
| 🔁 **6-Stage Cycle** (`sakthai/cycle/`) | 🟢 Operational | Dream → Hope → Care → Joy → Trust → Growth state machine |
| 📊 **Dashboard** (`dashboard/`) | 🟡 Partial | React/Vite UI served via `sakthai dashboard`; requires a build step |

---

## 📊 Roadmap & System Status
The ecosystem follows a strict **Dream → Hope → Care → Joy → Trust → Growth** lifecycle. We are currently scaling from an MVP to a full production-ready suite.

| Area | Progress | Status |
| :--- | :--- | :--- |
| **Core Framework** | 🟩🟩🟩🟩🟩🟩🟩🟩🟨⬜ 85% | Stable |
| **Persona SOULs** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Completed |
| **Family Workflows** | 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ 60% | Active |
| **ServiceQuoteBot** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Deployed |
| **Model Evaluation** | 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70% | In Progress |
| **Dashboard UI** | 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70% | In Progress |

---

## 👨‍👩‍👧‍👦 The Sak Family Agents
Each agent is a specialized persona orchestrated by **SakKing**. They share a common memory brain but operate in distinct domains.

| Agent | Role | Specialized Skill |
| :--- | :--- | :--- |
| 👑 **SakKing** | Lead & Orchestrator | Code & Self-Healing |
| 🤗 **SakThai** | HF Expert | Model Discovery |
| 🌐 **SakSee** | Web Specialist | Playwright & Browsing |
| 📣 **SakSit** | Social Master | Content Strategy |
| 🗓️ **SakTan** | Daily Ops | Life Admin & Scheduling |
| 🤖 **SakJules** | Automation/CI | Infrastructure & Testing |
| 📈 **SakFin** | Financial Analyst | Market Analysis |

---

## 🤝 Family Workflows
The power of the Sak Family lies in multi-agent coordination. Here are common collaborative patterns:

*   **The Researcher's Loop**: Ask **SakKing** to investigate a topic. He delegates web scraping to **SakSee**, technical model lookup to **SakThai**, and final content drafting to **SakSit**.
*   **The Ops Pipeline**: **SakTan** identifies an upcoming meeting. He triggers **SakJules** to ensure all CI/CD reports are ready for presentation and notifies the team via Telegram.
*   **The Financial Insight**: **SakFin** analyzes market trends and stores key facts via `learn`. **SakKing** then uses these facts to suggest architectural adjustments for the product.

---

## 🔍 Deep Dive: Technical Architecture

### 🏗️ System Layers
- **`sakthai/cli/`**: Click-based entry point for all commands (`learn`, `recall`, `run`, `mcp`).
- **`sakthai/agent/`**: The execution core managing the agent loop and LLM provider dispatching.
- **`sakthai/memory/`**: Exclusive SQLite layer for storing durable facts and observations.
- **`sakthai/mcp/`**: JSON-RPC 2.0 stdio server sharing the core tool registry.

### 🧠 Persistent Memory Schema
Stored in `~/.sakthai/memory.db`:
- **`facts`**: Discrete information (notes, preferences, project data).
- **`observations`**: Agent-curated weighted insights and summaries.

---

## 🛠️ CLI Command Cheat Sheet

| Action | Command |
| :--- | :--- |
| **Run Agent Task** | `uv run sakthai run "your task here" --provider <name>` |
| **Store Fact** | `uv run sakthai learn "I prefer dark mode" --kind pref` |
| **Recall Memory** | `uv run sakthai recall` |
| **Search Memory** | `uv run sakthai search "keyword"` |
| **Open Dashboard** | `uv run sakthai dashboard` |
| **Check Health** | `uv run sakthai memory healthcheck` |

---

## 🚀 Getting Started

1.  **Clone & Enter**:
    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```
2.  **Setup Environment**:
    `cp .env.example .env` and add your API keys.
3.  **Sync Dependencies**:
    `uv sync --all-extras`
4.  **Engage**:
    `uv run sakthai run "Analyze the environment" --provider anthropic`

---

## 📖 Glossary of Terms
*   **SOUL**: The authoritative identity, intent, and emotional readiness definition for an agent.
*   **Charge**: A measure of an agent's focus and energy (Optimal, Active, Low, Critical).
*   **6-Stage Cycle**: The operational lifecycle: **Dream → Hope → Care → Joy → Trust → Growth**.
*   **Persistent Memory**: A shared SQLite backend that allows agents to remember context across different sessions.

---

## 📂 Project Structure
- `sakthai/`: Core package (Agent, Memory, MCP, CLI).
- `personas/`: Identity and SOUL definitions.
- `skills/`: Library of 69+ specialized capabilities.
- `docs/`: Technical documentation and diagrams.
- `tests/`: Unit and integration test suite.

*Built with ❤️ for **Beer** by the Sak Family. All Rights Reserved (© 2026 beer-sakthai).*
