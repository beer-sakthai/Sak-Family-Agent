![Sak Family Agent Banner](assets/sak_family_banner.png)

# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)
![Last Commit](https://img.shields.io/github/last-commit/beer-sakthai/Sak-Family-Agent)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-%E2%89%A585%25-success)

---

**SakJules · Master of Automation & CI/CD.**

Welcome to the heart of the Sak Family's digital operations. This repository houses a sophisticated multi-agent ecosystem designed to automate, analyze, and accelerate every aspect of our daily lives.

## 🌟 Vision
The **Sak-Family-Agent** is a local-first, privacy-conscious AI workspace. It leverages persistent memory and specialized personas to provide a seamless bridge between digital intelligence and real-world productivity.

## 📊 Roadmap & System Status
We are currently in the **Trust → Growth** transition phase.

| Area | Progress | Status |
| :--- | :--- | :--- |
| **Core Agent Framework** | 🟩🟩🟩🟩🟩🟩🟩🟩🟨⬜ 85% | Stable |
| **Persona SOULs** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Completed |
| **Family Workflows** | 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ 60% | Active Development |
| **ServiceQuoteBot (MVP)** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | Deployed |
| **Model Evaluation** | 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70% | In Progress |

## 👨‍👩‍👧‍👦 The Sak Family Agents
Our ecosystem is powered by specialized personas, each a master of their domain, orchestrated by **SakKing**.

| Agent | Role | Specialized Skill |
| :--- | :--- | :--- |
| 👑 **SakKing** | Lead & Orchestrator | Master of Code & Architecture |
| 🤗 **SakThai** | Hugging Face Expert | Model Discovery & Integration |
| 🌐 **SakSee** | Web Specialist | Playwright, Scraping & Browsing |
| 📣 **SakSit** | Social Media Master | Content Strategy & Engagement |
| 🗓️ **SakTan** | Daily Ops Helper | Calendar, Email & Scheduling |
| 🤖 **SakJules** | Automation & CI/CD | Infrastructure, Testing & Deployment |
| 📈 **SakFin** | Financial Analyst | Market Trends & Quantitative Analysis |

## 🚀 Key Features
*   🧠 **Persistent Memory**: Shared SQLite backend (`~/.sakthai/memory.db`) allowing agents to learn and recall context across sessions.
*   🛠️ **Unified Tool Registry**: A robust set of tools for file I/O, terminal execution, and Telegram communication.
*   🤝 **Multi-Agent Swarms**: Agents can delegate tasks, share artifacts, and collaborate on complex objectives.
*   🧪 **Automated Evaluation**: Integrated `lm-evaluation-harness` to ensure high-quality, structured AI outputs.
*   🔒 **Self-Healing Infrastructure**: Nightly security scans and automated patching via the `devsecops` skill.

## 💻 Quick Start
This project requires **Python 3.11+** and uses **uv** for lightning-fast dependency management.

1.  **Clone & Enter**:
    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```
2.  **Environment Setup**:
    ```bash
    cp .env.example .env
    # Add your API keys (Anthropic, OpenAI, Gemini, etc.)
    ```
3.  **Install Everything**:
    ```bash
    uv sync --all-extras
    ```
4.  **Engage the Agent**:
    ```bash
    # Ask SakKing to perform a task
    uv run sakthai run "Analyze the current repository structure" --provider anthropic
    ```

## 📂 Repository Structure
*   `sakthai/`: Core Python package (agent, memory, mcp, cli).
*   `personas/`: Identity definitions and SOUL files for each agent.
*   `skills/`: A library of 69+ specialized agent capabilities.
*   `scripts/`: Automation and utility scripts for maintenance.
*   `tests/`: Comprehensive test suite (Unit & Integration).

---

*Built with ❤️ for **Beer** by the Sak Family. All Rights Reserved (© 2026 beer-sakthai).*
