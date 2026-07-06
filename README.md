# Sak-Family-Agent 🤖👨‍👩‍👧‍👦

> **Your Personal AI Ecosystem for Real-Life Growth and Productivity**

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)
![Last Commit](https://img.shields.io/github/last-commit/beer-sakthai/Sak-Family-Agent)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

## ✨ Vision: Imagine a Smarter Family Life

Imagine a world where your daily tasks are effortlessly managed, your learning is accelerated, and your personal growth is supercharged by a team of intelligent AI companions. The **Sak-Family-Agent** is that vision brought to life — a dynamic, multi-agent AI ecosystem designed to streamline your life, empower your decisions, and foster continuous learning. It's a personal sandbox for real-life growth, where AI assistants collaborate to make your digital and physical world more efficient and enjoyable. This project emphasizes a local-first approach, focusing on CLI operations, robust agent loops, and seamless MCP server functionalities [1].

## 💡 Why Was This Made? (Motivation)

This project was born from **Beer's** (`beer-sakthai`) passion for AI, productivity, and continuous learning. It serves as a personal laboratory to experiment with cutting-edge AI models and build practical solutions for everyday challenges. The primary motivations include:

- **Personal Growth**: A platform for Beer to deepen AI knowledge and build efficient workflows.
- **Family Productivity**: Automating routine tasks and providing intelligent assistance for family members.
- **No-Cost Innovation**: Leveraging free and open-source AI tools to create powerful solutions without significant financial investment.
- **Learning & Experimentation**: A sandbox to explore multi-agent systems, persistent memory, and tool integration in a real-world context.

## 🎯 Who Is It For?

The Sak-Family-Agent is primarily built for **Beer** (`beer-sakthai`) as a personal sandbox for real-life growth and continuous learning. It is also a valuable resource for:

- **AI Enthusiasts**: Individuals interested in building and experimenting with multi-agent AI systems.
- **Developers**: Those looking for a practical example of integrating various AI models and tools into a cohesive agent framework.
- **Learners**: Anyone keen on understanding how persistent memory, tool registries, and inter-agent communication can be implemented in AI applications.

## 💰 No-Cost Tools & Support

This project is committed to utilizing **no-cost or low-cost options** wherever possible, making advanced AI capabilities accessible. The core of the Sak-Family-Agent is powered by a combination of free-tier AI services and open-source tools:

| Tool | Purpose | Free Tier / Open Source | Link |
|:-----|:------------------------------------|:------------------------|:-----|
| **Claude (Anthropic)** | Advanced AI reasoning & writing | Free tier available | [claude.ai](https://claude.ai/) |
| **Gemini (Google)** | Multimodal AI capabilities | Free tier available | [gemini.google.com](https://gemini.google.com/) |
| **Jules (Google)** | Asynchronous coding agent | Free beta | [jules.google](https://jules.google/) |
| **Antigravity CLI** | AI-powered command-line interface | Free & Open Source | - |
| **Manus** | Agentic AI assistant platform | Free tier available | [manus.im](https://manus.im/) |
| **GitHub** | Version control & CI/CD | Free for public repositories | [github.com](https://github.com/) |
| **Ollama** | Run large language models locally | Free & Open Source | [ollama.com](https://ollama.com/) |
| **SQLite** | Lightweight database for persistent memory | Free & Open Source | [sqlite.org](https://sqlite.org/) |

## 👨‍👩‍👧‍👦 The Sak Family Members

The Sak-Family-Agent ecosystem comprises six distinct AI personas, with **SakKing** acting as the lead and orchestrator. All are deployed as always-on Telegram bots on a single Azure VM, sharing one Azure AI Foundry backend (`sakthai-resource`) via the OpenAI-compatible `/openai/v1` API — each persona just points at a different deployed model [1].

| Agent | Handle | Role | Model (on `sakthai-resource`) | State |
|:------|:-------|:----------------------------------------------------|:-------------------------------------------------|:------|
| 👑 **SakKing** | `@SakKing_Agent_bot` | Lead & Orchestrator · Master of Code & Self-Healing (owns all skills) | `model-router` (Ollama Cloud `qwen3-coder:480b` → `gpt-oss:120b` fallback; CLI coding: Claude) | ✅ deployed |
| 🤗 **SakThai** | `@SakThai_Agent_bot` | Master of Hugging Face (mastery via Hub/MCP tools) | Anthropic `claude-opus-4-8` → Ollama Cloud `gpt-oss:120b` fallback | ✅ deployed |
| 🌐 **SakSee** | `@SakSee_Agent_bot` | Master of Web (Playwright + Chrome DevTools) | local Ollama `llama3` → `qwen` fallback | 🚧 pending |
| 📣 **SakSit** | `@SakSit_Agent_bot` | Master of Social Media (IG image/video) | local Ollama `llama3` → `qwen` fallback (Modal sandbox) | ✅ deployed |
| 🗓️ **SakTan** | `@SakTan_Agent_bot` | Daily Ops Helper (calendar, email, life admin) | `gemini-1.5-flash-lite` | ✅ deployed |
| 🤖 **SakJules** | `@SakJules_Agent_bot` | Master of Automation & CI/CD | `gemini-1.5-pro-latest` | 🚧 pending |

**Secrets:** Each bot's Telegram token and the shared Azure OpenAI key live in Azure Key Vault, fetched at process start via the VM's managed identity (see `infra/vm-agents/sakthai-agent-run.sh`) — no static secret files on the host.

## ✨ What Can It Do? (Key Features)

The Sak-Family-Agent provides a rich set of capabilities through its CLI, agent loop, and MCP server, all sharing a persistent SQLite memory (`~/.sakthai/memory.db`). Key functionalities include:

- 🧠 **Persistent Memory**: Agents can `learn`, `recall`, `search`, and `forget` facts, observations, and preferences across sessions, ensuring continuous learning and context retention [1, 3].
- 🛠️ **Tool Usage**: A shared tool registry allows agents to perform actions like reading files (`read_file`), running commands (`run_command`), sending Telegram messages (`send_telegram_message`), and even running nested agent loops (`run_agent_loop`) [1, 3].
- 🤝 **Multi-Agent Coordination**: SakKing orchestrates the other agents, leveraging their specialized skills for complex tasks. Agents communicate and share information through shared memory and GitHub-backed artifacts [1].
- 🚀 **Extensible Skills**: The system supports a wide range of skills, which are parsed, cataloged, and validated from `SKILL.md` files. These skills are injected into the agent's system prompt, enhancing their capabilities [2].
- 🤖 **Flexible AI Model Integration**: The agent loop is provider-agnostic, supporting Claude, Gemini, OpenAI-compatible APIs, and Ollama endpoints [2].
- 📊 **Dashboard & Sessions Management**: CLI commands allow for managing memory, viewing agent sessions, and interacting with a React-based dashboard for insights [2].
- 🫂 **Hugging Face Integration**: Tools for interacting with the Hugging Face Hub, including `hf info` and `hf download` [2].
- 🚨 **Asset Monitoring**: A built-in skill (`asset-monitor`) to monitor a list of public URLs and send a Telegram alert if any of them become unavailable [4].
- 🌱 **Self-Evolution (Experimental)**: An experimental `agent-self-evolution` package explores DSPy/GEPA for agent self-improvement [2].
- 🔒 **Continuous Security & Self-Healing**: A nightly GitHub Actions workflow runs the `devsecops` skill to proactively scan the codebase with `ruff` and `bandit`. When vulnerabilities are found, it triggers an automated patching pipeline to generate, test, and open pull requests with proposed fixes, creating an "intelligent digital immune system" [5].
- 🧪 **Model Evaluation**: Custom tasks for `lm-evaluation-harness` defined in `evaluation_tasks/` validate the agent's structured outputs (JSON, YAML) and reasoning constraints.

## 🛠️ Tech Stack

The project is built primarily with Python and leverages several key libraries and AI models:

- **Python**: Version 3.11 and above [3].
- **AI Models**: Anthropic Claude, Google Gemini, OpenAI-compatible models, Ollama [1, 3].
- **Memory**: SQLite for persistent memory storage [2].
- **Dependency Management**: `uv` for fast and efficient dependency resolution [3].

## 🚀 Getting Started

To get started with the Sak-Family-Agent, follow these steps:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
    cd Sak-Family-Agent
    ```
2.  **Setup Environment Variables**:
    Copy the example environment file and fill in your API keys (e.g., `ANTHROPIC_API_KEY`):
    ```bash
    cp .env.example .env
    # Open .env and add your API keys
    ```
3.  **Install Dependencies**:
    The project uses `uv` for dependency management. Ensure you have Python 3.11+ installed.
    ```bash
    uv sync --all-extras
    ```
4.  **Run Commands**:
    You can now use the `sakthai` CLI. For example:
    - Run an agent: `sakthai run "your task here" --provider anthropic --model claude-3-opus-20240229`
    - Learn a fact: `sakthai learn "My favorite color is blue" --kind pref --key color`
    - Show memory: `sakthai memory show`
    - Start the dashboard: `sakthai dashboard`
    Refer to the `CLAUDE.md` file for a comprehensive list of commands and usage examples [2].

## 🗺️ Roadmap & Status

The Sak-Family-Agent is a continuously evolving project, operating on a six-stage cycle: Dream → Hope → Care → Joy → Trust → Growth. This ensures iterative development and improvement, always prioritizing no-cost, low-risk, and practical solutions that benefit Beer [1].

🟩🟩🟩🟩🟩🟩🟩🟨🟨⬜ 70% — Core Agent Setup
🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% — Family Workflows
🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ 30% — Documentation

## 🤝 Contributing

While this is primarily a personal project, contributions are welcome. Please refer to the `CLAUDE.md` for development guidelines and the `CODE_OF_CONDUCT.md` for community standards.

## 📄 License

This project is **All Rights Reserved (© 2026 beer-sakthai)**. The source code is available for reading and learning, but no license to use, copy, modify, or redistribute it is granted. See `CODE_OF_CONDUCT.md` for details.

## ✍️ Author

Built with ❤️ for Beer by the Sak Family.

---

## References

[1] `docs/SOUL.md` from `beer-sakthai/Sak-Family-Agent`
[2] `README.md` (existing) from `beer-sakthai/Sak-Family-Agent`
[3] `pyproject.toml` from `beer-sakthai/Sak-Family-Agent`
[4] `.github/workflows/SKILL.md` from `beer-sakthai/Sak-Family-Agent`
[5] `.github/workflows/continuous-security.yml` from `beer-sakthai/Sak-Family-Agent`
