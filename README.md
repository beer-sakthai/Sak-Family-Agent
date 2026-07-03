# Sak-Family-Agent: Your Personal AI Agent Ecosystem

<div align="center">

![House of Sak](./assets/house_of_sak_v2.png)

**A local-first personal learning agent with persistent memory.**
One package, three ways in — a CLI, a tool-using agent loop, and an MCP stdio server.

<!-- 📡 Live status bar. Note: The repo name in badge URLs is hardcoded to the main repo, not the fork name. -->
[![CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml)
[![Lint Code Base](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/super-linter.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/super-linter.yml)
[![Codecov](https://codecov.io/gh/beer-sakthai/Sak-Family-Agent/branch/main/graph/badge.svg)](https://codecov.io/gh/beer-sakthai/Sak-Family-Agent)

[![Python](https://img.shields.io/badge/python-3.11_|_3.12_|_3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-8A2BE2)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/beer-sakthai/sakthai-agent-v2/main?logo=git&logoColor=white)](https://github.com/beer-sakthai/sakthai-agent-v2/commits/main)

</div>

> SakThai gives a **Claude**, **Gemini**, or **local (Ollama / OpenAI-compatible)** model a
> durable **SQLite memory** it reads and writes across sessions, a shared **tool registry**,
> a curated **skills catalog**, and a two-way **MCP** bridge — so the same memory and tools
> are reachable from other agents and editors. **Local-first**, with a fully **no-cost** local run.

---

## 📑 Table of Contents

- [🚀 What is Sak-Family-Agent?](#-what-is-sak-family-agent)
- [🎯 Who is it for?](#-who-is-it-for)
- [👨‍👩‍👧‍👦 The Sak Family Members](#-the-sak-family-members)
- [✨ What Can It Do?](#-what-can-it-do)
- [🛠️ Tech Stack](#️-tech-stack)
- [📂 Project Structure](#-project-structure)
- [🚀 How to Use / Get Started](#-how-to-use--get-started)
- [🗺️ Roadmap & Status](#️-roadmap--status)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [✍️ Author](#️-author)
- [References](#references)

---

## 🚀 What is Sak-Family-Agent?

**Sak-Family-Agent** is a personal AI agent ecosystem designed for real-life growth and learning.
It provides a robust framework for AI assistants (like Claude, Gemini, and others) to operate with
persistent memory, a shared tool registry, and an MCP (Model Context Protocol) stdio server. This
setup allows for seamless interaction and knowledge sharing across multiple AI agents, all working
towards enhancing personal productivity and learning for Beer [1].

This repository serves as the shared workspace for the entire Sak family of agents, enabling them to coordinate, learn, and evolve together. It emphasizes a local-first approach, focusing on CLI operations, agent loops, and MCP server functionalities [2].

## 🎯 Who is it for?

This project is primarily built for **Beer** (`beer-sakthai`) as a personal sandbox for real-life growth and continuous learning. It is also a valuable resource for:

- **AI Enthusiasts**: Individuals interested in building and experimenting with multi-agent AI systems.
- **Developers**: Those looking for a practical example of integrating various AI models and tools into a cohesive agent framework.
- **Learners**: Anyone keen on understanding how persistent memory, tool registries, and inter-agent communication can be implemented in AI applications.

## 👨‍👩‍👧‍👦 The Sak Family Members

The Sak-Family-Agent ecosystem comprises six distinct AI personas, with **SakKing** acting as the lead and orchestrator. All are deployed as always-on Telegram bots on a single Azure VM, sharing one Azure AI Foundry backend (`sakthai-resource`) via the OpenAI-compatible `/openai/v1` API — each persona just points at a different deployed model [1].

| Agent | Handle | Role | Model (on `sakthai-resource`) | State |
| :---- | :----- | :--- | :----------------------------- | :---- |
| 👑 **SakKing**  | `@SakKing_Agent_bot`  | Lead & Orchestrator · Master of Code & Self-Healing (owns all skills) | `model-router` (auto-routes across deployed models) | ✅ deployed |
| 🤗 **SakThai**  | `@SakThai_Agent_bot`  | Master of Hugging Face (mastery via Hub/MCP tools)                    | `gpt-4o-mini` | ✅ deployed |
| 🌐 **SakSee**   | `@SakSee_Agent_bot`   | Master of Web (Playwright + Chrome DevTools)                          | `gpt-5.4-mini` | 🚧 pending |
| 📣 **SakSit**   | `@SakSit_Agent_bot`   | Master of Social Media (IG image/video)                               | `Phi-4-mini-reasoning` | ✅ deployed |
| 🗓️ **SakTan**   | `@SakTan_Agent_bot`   | Daily Ops Helper (calendar, email, life admin)                        | `gpt-4o-mini` | ✅ deployed |
| 🤖 **SakJules** | `@SakJules_Agent_bot` | Master of Automation & CI/CD                                          | `gpt-4o-mini` | 🚧 pending |

**Secrets:** each bot's Telegram token and the shared Azure OpenAI key live in Azure Key Vault, fetched at process start via the VM's managed identity (see `infra/vm-agents/sakthai-agent-run.sh`) — no static secret files on the host.

## ✨ What Can It Do?

The Sak-Family-Agent provides a rich set of capabilities through its CLI, agent loop, and MCP server, all sharing a persistent SQLite memory (`~/.sakthai/memory.db`). Key functionalities include:

- **Persistent Memory**: Agents can `learn`, `recall`, `search`, and `forget` facts, observations, and preferences across sessions, ensuring continuous learning and context retention [1, 3].
- **Tool Usage**: A shared tool registry allows agents to perform actions like reading files (`read_file`), running commands (`run_command`), sending Telegram messages (`send_telegram_message`), and even running nested agent loops (`run_agent_loop`) [1, 3].
- **Multi-Agent Coordination**: SakKing orchestrates the other agents, leveraging their specialized skills for complex tasks. Agents communicate and share information through shared memory and GitHub-backed artifacts [1].
- **Extensible Skills**: The system supports a wide range of skills, which are parsed, cataloged, and validated from `SKILL.md` files. These skills are injected into the agent's system prompt, enhancing their capabilities [2].
- **Flexible AI Model Integration**: The agent loop is provider-agnostic, supporting Claude, Gemini, OpenAI-compatible APIs, and Ollama endpoints [2].
- **Dashboard & Sessions Management**: CLI commands allow for managing memory, viewing agent sessions, and interacting with a React-based dashboard for insights [2].
- **Hugging Face Integration**: Tools for interacting with the Hugging Face Hub, including `hf info` and `hf download` [2].
- **Asset Monitoring**: A built-in skill (`asset-monitor`) to monitor a list of public URLs and send a Telegram alert if any of them become unavailable [4].
- **Self-Evolution (Experimental)**: An experimental `agent-self-evolution` package explores DSPy/GEPA for agent self-improvement [2].
- **Continuous Security & Self-Healing**: A nightly GitHub Actions workflow runs the `devsecops` skill to proactively scan the codebase with `ruff` and `bandit`. When vulnerabilities are found, it triggers an automated patching pipeline to generate, test, and open pull requests with proposed fixes, creating an "intelligent digital immune system" [5].

## 🛠️ Tech Stack

The project is built primarily with Python and leverages several key libraries and AI models:

- **Python**: Version 3.11 and above [3].
- **AI Models**: Anthropic Claude, Google Gemini, OpenAI-compatible models, Ollama [1, 3].
- **Memory**: SQLite for persistent memory storage [2].
- **CLI**: `click` for command-line interface development [3].
- **Dependencies**: `pyyaml`, `anthropic`, `httpx`, `google-genai`, `tenacity`, `python-telegram-bot` [3].
- **Development Tools**: `pytest`, `ruff`, `mypy`, `bandit`, `mutmut` for testing, linting, type-checking, security, and mutation testing [3].
- **Frontend (Dashboard)**: React/Vite (located in the `dashboard/` directory, served by the `sakthai dashboard` command) [2].

## 📂 Project Structure

This repository is structured as a monorepo, with `sakthai-agent` as the core package at the root. Other components are organized into logical directories [2].

```text
Sak-Family-Agent/
├── .github/                # GitHub Actions workflows (CI/CD)
├── docs/                   # Documentation (architecture, cycle stages, SOUL files)
├── infra/                  # Infrastructure configurations (VM agents, Playwright PoC)
├── library/                # Curated skills library
├── packages/               # Other standalone Python packages (e.g., agent-self-evolution)
├── personas/               # Agent persona definitions (SOUL.md, config, skill overlays)
├── scripts/                # Utility scripts (e.g., export_agent_repo.py, compose_persona.py)
├── services/               # Service pitches/specs
├── sakthai/                # Main Python package for SakThai agent
│   ├── agent/              # Agent loop, tools, registry, providers
│   ├── cli/                # CLI commands
│   ├── config.py           # Centralized configuration
│   ├── cycle/              # Six-stage state machine
│   ├── dashboard/          # Dashboard data generation
│   ├── extensions/         # Git-based skill/MCP bundle installer
│   ├── hf.py               # Hugging Face operations
│   ├── learn/              # One-shot fact capture
│   ├── mcp/                # Model Context Protocol (server, client, manager)
│   ├── memory/             # Memory store, provider, backup, sync
│   ├── sakking_skills.py   # SakKing-specific skill mirroring
│   ├── sandbox.py          # Docker sandbox integration
│   ├── skills.py           # Skill discovery and management
│   ├── telegram/           # Telegram bot prototype
│   └── web/                # Web server stub
├── skills/                 # User/extension skills
├── tests/                  # Unit and integration tests
├── training/               # Hugging Face Jobs fine-tune + model-serving scripts
├── .env.example            # Example environment variables
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # This file
├── CLAUDE.md               # Guidance for Claude Code
└── uv.lock                 # uv dependency lock file
```

## 🚀 How to Use / Get Started

To get started with the Sak-Family-Agent, follow these steps:

1. **Clone the repository**:

    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```

2. **Setup Environment Variables**:
    Copy the example environment file and fill in your API keys (e.g., `ANTHROPIC_API_KEY`):

    ```bash
    cp .env.example .env
    # Open .env and add your API keys
    ```

3. **Install Dependencies**:
    The project uses `uv` for dependency management. Ensure you have Python 3.11+ installed.

    ```bash
    uv sync --all-extras
    ```

4. **Run Commands**:
    You can now use the `sakthai` CLI. For example:
    - Run an agent: `sakthai run "your task here" --provider anthropic --model claude-3-opus-20240229`
    - Learn a fact: `sakthai learn "My favorite color is blue" --kind pref --key color`
    - Show memory: `sakthai memory show`
    - Start the dashboard: `sakthai dashboard`

    Refer to the `CLAUDE.md` file for a comprehensive list of commands and usage examples [2].

## 🗺️ Roadmap & Status

The Sak-Family-Agent is a continuously evolving project. It operates on a six-stage cycle: Dream → Hope → Care → Joy → Trust → Growth, ensuring iterative development and improvement. The project prioritizes no-cost, low-risk, and practical solutions, always focusing on benefiting Beer [1].

## 🤝 Contributing

While this is primarily a personal project, contributions are welcome. Please refer to the `CLAUDE.md` for development guidelines and the `CODE_OF_CONDUCT.md` for community standards.

## 📄 License

This project is **All Rights Reserved (© 2026 beer-sakthai)**. The source code is available for reading and learning, but no license to use, copy, modify, or redistribute it is granted. See `CODE_OF_CONDUCT.md` for details.

## ✍️ Author

Built with ❤️ for Beer by the Sak Family.

---

## References

[1] `docs/SOUL.md` from `beer-sakthai/Sak-Family-Agent`
[2] `CLAUDE.md` from `beer-sakthai/Sak-Family-Agent`
[3] `pyproject.toml` from `beer-sakthai/Sak-Family-Agent`
[4] `.github/workflows/SKILL.md` from `beer-sakthai/Sak-Family-Agent`
[5] `.github/workflows/continuous-security.yml` from `beer-sakthai/Sak-Family-Agent`
