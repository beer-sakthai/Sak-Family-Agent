# Technical Stack: Sak-Family-Agent

## 1. Runtime & Languages
- **Python**: 3.11 / 3.12 (Primary backend runtime, agent loops, CLI, recovery engines).
- **TypeScript / Node.js**: TypeScript 5.7+ / Node.js 22 LTS (Dashboard, MCP bridge, frontend).
- **Package Managers**:
  - Python: `uv` (Fast dependency resolution, workspace virtual environments).
  - TypeScript: `pnpm` 9.15+ (Workspaces, monorepo package hoisting).

---

## 2. Frameworks & Libraries
- **CLI & Core Agent Engine**: `sakthai` (custom provider-agnostic loop, tool dispatch, guardrail policies).
- **Web Frontend & Dashboard**: Next.js 15 (App Router, Server Actions, SSE endpoints), React 19, Tailwind CSS v3/v4.
- **Testing & Verification**:
  - `pytest` (Hermetic unit & integration tests, hypothesis property tests, pytest-asyncio).
  - `mypy` (Strict typechecking).
  - `ruff` (Fast formatting and linting).
  - `vitest` / `playwright` (Component & end-to-end browser tests).

---

## 3. Storage & Database Architecture
- **Primary State & Episodic Memory**: SQLite3 in WAL (`Write-Ahead Logging`) mode.
- **Dead-Letter Queue & Recovery**: `recovery.db` (Isolated, thread-safe DLQ store).
- **Vector & Embeddings Mesh**: In-memory dense cosine indexing + pgvector/DuckDB bindings for scale.

---

## 4. Protocols & Integration
- **Model Context Protocol (MCP)**: JSON-RPC 2.0 stdio server (`sakthai mcp`).
- **A2A Streaming Protocol**: Server-Sent Events (SSE) with structured chunk envelopes (`seq`, `chunk_type`, `delta`).
- **LLM Providers Supported**: Anthropic (Claude 3.7/Opus/Sonnet), Google (Gemini 2.5 Flash/Pro), OpenAI (GPT-4o/o3), Ollama, Hugging Face Hub Inference API.
