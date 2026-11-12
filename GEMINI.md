# GEMINI.md - House of Sak / Sak-Family-Agent Instructions

This document serves as the foundational context and instructional guide for operating within the **House of Sak (Sak-Family-Agent)** workspace.

---

## 1. Project Overview
**House of Sak** is a local-first, provider-agnostic AI agent workspace built with Python (core agent/loop/memory), Next.js (dashboard), and Model Context Protocol (MCP). It revolves around six distinct personas sharing a common core architecture.

### Key Architecture & Technologies
- **Core Package**: Python 3.11+, using `uv` for environment & package management.
- **Agent Architecture**: Tool-using agent loop (`agent/loop.py`), retries, dry-run preflight, and Model Context Protocol (MCP) support.
- **Personas (6)**: 
  - `SakThai` (lead / HF Master)
  - `SakSee` (web / browser specialist)
  - `SakJules` (GitHub / CI/CD master)
  - `SakKing` (general assistant / runner)
  - `SakSit` (social / content specialist)
  - `SakTan` (daily ops / rhythm, local Ollama)
- **Memory Store**: SQLite-backed persistent memory per persona under `~/.sakthai/` (or `$SAKTHAI_HOME`).
- **Dashboard**: Next.js app in `apps/sak_agent_dashboard/`.
- **Integrations**: Support for Anthropic, Gemini, OpenAI-compatible APIs, Ollama, and Hugging Face router models.

---

## 2. Building, Running, and Testing

### Setup & Requirements
- **Python**: 3.11+ (managed via `uv`)
- **Node.js**: 22+ (for Next.js dashboard)
- Ensure `.env` is configured (copy from `.env.example`).

### Essential CLI Commands

#### Python Core & CLI (`sakthai`)
- **Install Dependencies**: `uv sync --all-extras`
- **Run Tests**: `uv run pytest` or `make test`
- **Check Environment / Status**: 
  - `uv run sakthai status`
  - `uv run sakthai doctor --json`
- **Run Agent Loop**:
  - `uv run sakthai run "your instruction prompt"`
  - `uv run sakthai run "your prompt" --persona sakking`
- **Interactive Chat**: `uv run sakthai chat --persona <name>`
- **Memory Inspection**: `uv run sakthai memory family --tag <tag>`
- **Run MCP Stdio Server**: `uv run sakthai mcp`

#### Dashboard (`apps/sak_agent_dashboard`)
- **Install**: `cd apps/sak_agent_dashboard && npm install`
- **Development**: `npm run dev`
- **Build**: `npm run build`
- **Test**: `npm test`

---

## 3. Development Conventions & Guidelines

- **Python Standards**:
  - Code formatting: Follow standard `black`/`ruff` patterns.
  - Type Hinting: Enforce strict typing where applicable.
  - Test Coverage: Minimum 96% coverage is strictly enforced by CI. All new features require matching `pytest` unit tests.
- **Personas & Configuration**:
  - Personas reside in `personas/<persona_name>/`.
  - Individual settings are in `personas/<persona_name>/config/config.yaml`.
  - Personas use distinct `SOUL.md` system prompts to drive identity.
- **Memory Management**:
  - Do not edit raw SQLite databases directly. Use `MemoryStore` or `sakthai memory` CLI commands.
- **Safety & Security**:
  - Never check in API keys or secrets (`HF_TOKEN`, `ANTHROPIC_API_KEY`).
  - Follow security guidelines provided by `SECURITY.md` and GitHub security workflows.
