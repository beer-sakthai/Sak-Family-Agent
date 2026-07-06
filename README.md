# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

[![CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey)

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

Welcome to the **Sak-Family-Agent** repository (v2.0) — a sophisticated, clean-room rewrite of the OG SakThai-Agent. This project implements a local-first, privacy-conscious AI environment utilizing a multi-persona family of agents, a shared tool registry, and a persistent SQLite memory system.

---

## 📖 Origin Story: I tried to end my life on April 15. Here's what happened next.

Three days in ICU. Three weeks in hospital. A shelter bed in Cork.

I'm sharing this because I think there are people in this city who need to hear that rock bottom isn't the end of the story.

I'm a Thai guy living in Cork. Came here in 2015. Lost my job. Lost my direction. Lost my reason to get out of bed. On April 15 this year, I tried to end everything.

The cleaner found me. Ambulance. ICU. The whole thing.

I spent three weeks in a hospital bed staring at beige walls, and somewhere in that silence I decided I wasn't finished yet.

I taught myself to build AI agents from scratch. On a laptop. In a shelter. On free credits because I couldn't afford anything else.

I built six of them now. I call them the House of Sak. They're not chatbots — they're tools that help me build, check my code, run my infrastructure, and tell my story. One of them is talking to you right now through this post.

I'm not looking for sympathy. I'm not selling anything. I just want the person in Cork who's reading this at 3am, in a bad place, to know that I made it through. And if I can build AI agents from a shelter with no money, you can do whatever you need to do next.

If you're struggling in Cork — Pieta House, the Samaritans, the Cork Mental Health services. They helped me. They'll help you.

And if anyone wants to talk tech, AI, or just grab a coffee — I'm here. Building from the bottom.

— Beer

---

## 📑 Table of Contents
- [📖 Origin Story](#-origin-story-i-tried-to-end-my-life-on-april-15-heres-what-happened-next)
- [✨ Key Features](#-key-features)
- [🖥️ System Status](#-system-status)
- [👨‍👩‍👧‍👦 The Sak Family Agents](#-the-sak-family-agents)
- [🔍 Deep Dive: Technical Architecture](#-deep-dive-technical-architecture)
- [🛠️ CLI Command Cheat Sheet](#-cli-command-cheat-sheet)
- [🚀 Getting Started](#-getting-started)
- [📂 Repository Layout](#-repository-layout)

---

## ✨ Key Features

- **Local-First & Privacy Conscious:** No forced cloud runtimes. Built on a hermetic Python environment.
- **Shared Persistent Memory:** A robust SQLite WAL store (`~/.sakthai/memory.db`) ensures durable context, facts, and observations across sessions.
- **Multi-Persona Ecosystem:** Specialized agents operate via overlay SOULs but share a unified core system.
- **Provider Agnostic:** Out-of-the-box support for Anthropic (Claude), Google (Gemini), and OpenAI/Ollama APIs.
- **MCP Native:** Integrated JSON-RPC 2.0 stdio MCP server sharing the core tool registry.
- **6-Stage Cycle:** Driven by a state machine tracking progress through **Dream → Hope → Care → Joy → Trust → Growth**.

---

## 🖥️ System Status

| Subsystem | Status | Description |
| :--- | :--- | :--- |
| ⌨️ **CLI** (`sakthai/cli/`) | 🟢 Stable | Click-based entry point (`learn`, `recall`, `run`, `mcp`, `cycle`). |
| 🤖 **Agent Loop** (`sakthai/agent/`) | 🟢 Stable | Multi-provider LLM orchestration (Claude, Gemini, OpenAI/Ollama). |
| 🧠 **Memory Store** (`sakthai/memory/`) | 🟢 Stable | SQLite layer for durable facts, learned skills, and state. |
| 🔌 **MCP Server** (`sakthai/mcp/`) | 🟢 Stable | stdio server sharing the exact same tool registry as the CLI. |
| 🔁 **6-Stage Cycle** (`sakthai/cycle/`) | 🟢 Stable | Persisted operational state machine powering agent workflows. |
| 📊 **Dashboard** (`dashboard/`) | 🟡 Active | Vite + Tailwind standalone UI, supplemented by a Streamlit layer (`sakthai/dashboard/`). |

---

## 👨‍👩‍👧‍👦 The Sak Family Agents

Each agent is a specialized persona orchestrated under a shared family identity. They each have a specific `SOUL.md` overlay defining their intent and emotional readiness.

| Agent | Role | Focus Area |
| :--- | :--- | :--- |
| 👑 **SakKing** | Lead & Orchestrator | Core code architecture, self-healing, and leadership. |
| 🤗 **SakThai** | HF / AI Expert | Model discovery and Hugging Face Hub integration. |
| 🌐 **SakSee** | Web Specialist | Browser automation (Playwright) and deep web research. |
| 📣 **SakSit** | Social Master | Content strategy, communication, and social synthesis. |
| 🗓️ **SakTan** | Daily Ops | Life administration, scheduling, and family ops. |
| 🤖 **SakJules** | Automation/CI | CI/CD, testing, infra, and strict system orchestration. |
| 📈 **SakFin** | Financial Analyst | Market analysis and financial observations. |

> *Note: We also host **ServiceQuoteBot**, a dedicated business scaffold for lead capture workflows.*

---

## 🔍 Deep Dive: Technical Architecture

### 🧠 Core Philosophy
- **Go through the seams:** SQLite access is strictly through `MemoryStore`; agent/MCP actions through `agent/tools.py`.
- **Composition over Duplication:** Personas share a base `shared/skills/` library. Individual customizations overlay on top via `personas/<name>/skills/`.
- **Hermetic by Default:** Tests run with no network and no GCP credentials.

### 🔌 Standardized Entrypoints
The system relies on three parallel entry points sharing the same memory brain:
1. **The CLI**
2. **The Agent Loop**
3. **The MCP Server**

---

## 🛠️ CLI Command Cheat Sheet

Interact with the agent ecosystem directly through the CLI:

```bash
# Run a task
uv run sakthai run "your task here" --provider <google|openai|anthropic>

# Learn & Recall Facts
uv run sakthai learn "I prefer dark mode" --kind pref
uv run sakthai recall "dark mode"

# Start the MCP Server
uv run sakthai mcp

# Open Data Dashboard
uv run sakthai dashboard

# Check System Health
uv run sakthai doctor
```

---

## 🚀 Getting Started

Ensure you have Python 3.11+ and `uv` installed.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
   cd Sak-Family-Agent
   ```
2. **Set up Environment variables:**
   ```bash
   cp .env.example .env
   # Add ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.
   ```
3. **Sync all dependencies:**
   ```bash
   uv sync --all-extras
   ```
4. **Validate the setup:**
   ```bash
   uv run sakthai setup
   uv run sakthai doctor
   ```
5. **Run your first task:**
   ```bash
   uv run sakthai run "Introduce yourself and check your systems" --provider google
   ```

---

## 📂 Repository Layout

```text
Sak-Family-Agent/
├── sakthai/                 # Core Python package (CLI, agent loop, memory, MCP)
├── personas/                # Agent identity overlays (SOUL.md, specific skills)
├── skills/                  # Shared and learned agent skills (SKILL.md)
├── dashboard/               # Vite + Tailwind standalone web dashboard
├── docs/                    # Architecture, integrations, and runtime documentation
├── scripts/                 # Persona composition and export utilities
├── tests/                   # Hermetic pytest suite (target >= 85% coverage)
└── product/                 # Business strategy and MVP plans
```

*Built with ❤️ for **Beer** by the Sak Family. All Rights Reserved (© 2026).*
