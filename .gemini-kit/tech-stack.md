# Tech Stack: Sak-Family-Agent

## Languages & Runtimes
- **Python**: 3.11 / 3.12 (Primary core backend, agent loops, CLI tools, recovery supervisor)
- **TypeScript / Node.js**: TypeScript 5.7+ / Node.js 22 LTS (Dashboard, MCP bridge, frontend UI)

## Package Managers & Tools
- **Python Package Manager**: `uv` (Virtual environment management, dependency locking)
- **Node Package Manager**: `pnpm` 9.15+ (Monorepo workspaces)
- **Linters & Formatters**: `ruff` (Python), `eslint` / `prettier` (TypeScript)
- **Type Checkers**: `mypy` (strict mode), `tsc` (`--noEmit`)

## Frameworks & Architecture
- **Agent Framework**: Custom lightweight provider-agnostic engine (`personas/sakthai/sakthai/agent/loop.py`)
- **Web UI & Dashboard**: Next.js 15 (App Router, Server Actions, SSE endpoints), React 19, Tailwind CSS
- **Inter-Process & Protocol**: Model Context Protocol (MCP stdio), JSON-RPC 2.0, Server-Sent Events (SSE)
- **Database**: SQLite3 (WAL mode, parameterized queries, online backup API)
- **Testing**: `pytest` (Hermetic tests, hypothesis, pytest-asyncio), `vitest`, `playwright`
