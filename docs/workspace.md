# SakThai v2 Workspace Layout

This document describes the directories, testing setup, and MCP details for the `sakthai-agent-v2` repository.

---

## 📂 Repository Layout

The active rewrite repository contains the following:

| Path | Description |
| :--- | :--- |
| `sakthai/` | Core Python package source (agent, memory, CLI, utilities) |
| `library/` | Corpus of default skills and instructional files |
| `skills/` | Curated prompts injected into agent loop |
| `tests/` | Unit and CLI integration test suite |
| `docs/` | Architecture, plugins, replication, and workspace documentation |
| `dashboard/` | Source code for the Streamlit memory/activity dashboard |

---

## ⚡ Development & Testing Commands

SakThai v2 uses `uv` for package management and testing:

```bash
# Install package in editable development mode
uv pip install -e ".[dev]"

# Run all non-integration tests (used in CI)
uv run pytest -q -m "not integration"

# Run integration tests (requires provider API keys/endpoints)
uv run pytest -q -m "integration"

# Check code style and formatting
uv run ruff check sakthai/ tests/
uv run ruff format sakthai/ tests/
```

---

## 🔌 Configured MCP Servers

MCP configurations are stored in `~/.sakthai/mcp.json`. External stdio servers can be registered there or dynamically loaded from Gemini CLI directories (`~/.gemini/extensions/`).

During runtime, tools are automatically discovered and prefixed with `<server_name>__` to prevent namespace collisions.
