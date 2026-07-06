![Sak Family Agent Banner](assets/sak_family_banner.png)

# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)
![Last Commit](https://img.shields.io/github/last-commit/beer-sakthai/Sak-Family-Agent)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-%E2%89%A585%25-success)

## 📊 Roadmap & System Status

The Sak-Family-Agent is continuously evolving across a six-stage lifecycle: **Dream → Hope → Care → Joy → Trust → Growth**. 

| Phase | Progress | Status |
|---|---|---|
| **Core Agent Setup** | 🟩🟩🟩🟩🟩🟩🟩🟨🟨⬜ 70% | In Progress |
| **Family Workflows** | 🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% | In Progress |
| **Documentation** | 🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ 30% | Active |

## ✨ Vision: A Smarter Family Life

Imagine a world where daily tasks are effortlessly managed, learning is accelerated, and personal growth is supercharged by intelligent AI companions. The **Sak-Family-Agent** (v2.0) is a clean-room rewrite of a personal AI ecosystem that acts as a sandbox for real-life productivity. This project emphasizes a local-first approach using Python, SQLite for persistent memory, and seamless Model Context Protocol (MCP) server functionalities.

## 👨‍👩‍👧‍👦 The Sak Family Members

The ecosystem consists of six specialized AI personas (and a ServiceQuoteBot), orchestrated by **SakKing**. They communicate through shared SQLite memory and are deployed securely as Telegram bots.

| Agent | Handle | Role | Model Backend |
|:------|:-------|:----------------------------------------------------|:-------------------------------------------------|
| 👑 **SakKing** | `@SakKing_Agent_bot` | Lead & Orchestrator · Master of Code | Ollama Cloud `qwen3-coder:480b` → `gpt-oss:120b` |
| 🤗 **SakThai** | `@SakThai_Agent_bot` | Master of Hugging Face | Anthropic `claude-opus-4-8` |
| 🌐 **SakSee** | `@SakSee_Agent_bot` | Master of Web (Playwright + Chrome Dev) | local Ollama `llama3` |
| 📣 **SakSit** | `@SakSit_Agent_bot` | Master of Social Media | local Ollama `llama3` |
| 🗓️ **SakTan** | `@SakTan_Agent_bot` | Daily Ops Helper (calendar, email) | `gemini-1.5-flash-lite` |
| 🤖 **SakJules** | `@SakJules_Agent_bot` | Master of Automation & CI/CD | `gemini-1.5-pro-latest` |

## 🚀 Key Features

- 🧠 **Persistent Memory**: Agents `learn`, `recall`, `search`, and `forget` across sessions, ensuring context retention via a local SQLite database (`~/.sakthai/memory.db`).
- 🛠️ **Shared Tool Registry**: Execute terminal commands, read/write files, send Telegram messages, and trigger nested agent loops directly.
- 🤝 **Multi-Agent Coordination**: SakKing delegates tasks to specialized personas who collaborate using GitHub-backed artifacts and memory.
- 🧪 **Model Evaluation**: Custom tasks for `lm-evaluation-harness` defined in `evaluation_tasks/` validate the agent's structured outputs (JSON, YAML) and reasoning constraints.
- 🔒 **Continuous Security & Self-Healing**: A nightly GitHub Actions workflow runs the `devsecops` skill. Automated patching pipelines scan, test, and submit PRs for code vulnerabilities.
- 🫂 **Hugging Face Integration**: Built-in CLI commands (`hf info`, `hf download`) to pull models from the hub.

## 🛠️ Architecture

A highly modular, layer-separated Python package that ensures strict separation of concerns and hermetic testing:

*   **`sakthai/cli/`**: The Click-based interface powering `learn`, `run`, `mcp`, and more.
*   **`sakthai/agent/`**: Provider-agnostic execution loop supporting Claude, Gemini, OpenAI, and Ollama.
*   **`sakthai/memory/`**: The exclusive boundary for all SQLite interactions.
*   **`sakthai/mcp/`**: A JSON-RPC 2.0 stdio server sharing the core agent's tool registry.

## 💻 Getting Started

This repository requires **Python 3.11+** and uses **uv** for fast dependency management.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```
2.  **Configure Environment**:
    ```bash
    cp .env.example .env
    # Add required keys like ANTHROPIC_API_KEY
    ```
3.  **Install Dependencies**:
    ```bash
    uv sync --all-extras
    ```
4.  **Run Your First Command**:
    ```bash
    # Run an agent task
    uv run sakthai run "your task here" --provider anthropic
    
    # Store a memory fact
    uv run sakthai learn "I prefer dark mode" --kind pref
    ```

---

*Built with ❤️ for Beer by the Sak Family. This project is **All Rights Reserved (© 2026 beer-sakthai)**.*
