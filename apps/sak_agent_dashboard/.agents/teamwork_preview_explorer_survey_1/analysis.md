# Codebase & Environment Analysis Report

**Date**: 2026-08-02
**Investigator**: Explorer 1 (Codebase & Environment Investigator)
**Target Project**: `/home/beern/teamwork_projects/sak_agent_dashboard`
**Runtime Data Path**: `/home/beern/.sakthai`

---

## Executive Summary
The target project directory `/home/beern/teamwork_projects/sak_agent_dashboard` is a freshly allocated directory containing only `ORIGINAL_REQUEST.md` and the `.agents/` metadata folder. No existing configuration files (`package.json`, `tsconfig.json`, `next.config.*`, `tailwind.config.*`) or source code exist yet.

The local system environment provides **Node.js v26.5.1**, **npm v11.17.0**, and active internet connectivity to the npm registry. The runtime state directory `~/.sakthai/` contains 761 session records, 761 benchmark evaluation records (`eval.jsonl`), 60 security/audit events (`audit.log`), and a valid SQLite memory database (`memory.db`).

---

## 1. Project Directory Inventory

| Path / File | Status | Description / Size |
|---|---|---|
| `/home/beern/teamwork_projects/sak_agent_dashboard` | Directory | Root project directory |
| `ORIGINAL_REQUEST.md` | File | 2,004 bytes — Functional & technical requirements |
| `.agents/` | Directory | Metadata directory for agent tracking & reports |
| `package.json` | Missing | Needs initialization via Next.js scaffold or npm init |
| `tsconfig.json` | Missing | Needs creation for TypeScript configuration |
| `next.config.*` | Missing | Needs creation for Next.js settings |
| `tailwind.config.*` | Missing | Needs creation for styling configuration |
| `src/` or `app/` | Missing | Needs creation for Next.js App Router application code |

---

## 2. Environment & Tooling Audit

- **Node.js**: `v26.5.1` (x86_64 linux)
- **npm**: `11.17.0`
- **npm Connectivity**: Operational (`npm ping` latency 513ms)
- **Python**: Python 3 available with built-in `sqlite3` module.
- **SQLite CLI**: `sqlite3` binary is not installed in shell PATH, but SQLite database files (`memory.db`) are fully valid and accessible via Node native drivers (`better-sqlite3`, `sqlite3`, `sql.js`, or `@libsql/client`) and Python.

---

## 3. Runtime Data Audit (`~/.sakthai/`)

The application needs to serve and visualize data from `/home/beern/.sakthai/`. We inspected the structure and confirmed the following data schema:

### 3.1 Benchmark & Execution Logs (`eval.jsonl`)
- **Total Records**: 761 lines
- **Format**: JSON Lines
- **Fields**: `timestamp` (epoch sec), `task_preview`, `model`, `provider`, `iterations`, `stop_reason`, `latency_s`, `input_tokens`, `output_tokens`, `tool_call_count`, `had_error`.
- **Models Present**: `gpt-4o`, `gemini-2.5-flash`, `meta-llama/Llama-3.1-8B-Instruct`, `claude-opus-4-8`, `qwen2.5-coder:7b`.
- **Providers Present**: `openai`, `google`, `huggingface`, `anthropic`.

### 3.2 Security & Audit Logs (`audit.log`)
- **Total Records**: 60 lines
- **Format**: JSON Lines
- **Fields**: `timestamp` (float epoch sec), `type` (e.g. `symlink_traversal`, `critical_test`, `medium_test`), `severity` (`critical`, `high`, `medium`, `low`), `message`, `details` (`target`, `resolves_to`, etc.).

### 3.3 Persistent Memory Database (`memory.db`)
- **Format**: SQLite 3 database (32 KB)
- **Tables**:
  - `facts`: `id` (INTEGER PRIMARY KEY), `kind` (TEXT), `key` (TEXT), `value` (TEXT), `source_session` (TEXT), `created_at` (INTEGER), `updated_at` (INTEGER), `tags` (TEXT).
  - `observations`: `id` (INTEGER PRIMARY KEY), `summary` (TEXT), `evidence_session_id` (TEXT), `weight` (REAL), `confidence` (REAL), `created_at` (INTEGER).
  - `schema_version`: `version` (INTEGER), `migrated_at` (INTEGER).

### 3.4 Transcripts & Session State (`sessions/`)
- **Total Files**: 761 JSON files
- **File Pattern**: `<timestamp>_<session_id>.json`
- **Fields**: `timestamp`, `task`, `model`, `messages` (`role`, `content`), `usage` (`input_tokens`, `output_tokens`, `total_tokens`), `result` (`text`, `iterations`, `stop_reason`, `tool_calls`).

---

## 4. Persona Roster (Sak-Agent-Family)

The requirements specify support for 5 personas:
1. **SakThai** (Lead Agent)
2. **SakKing**
3. **SakSee**
4. **SakSit**
5. **SakJules**

The dashboard UI should feature live/interactive status cards for each of these 5 personas with key metrics (status, persona role, total sessions, model usage, error rates).

---

## 5. Architectural Recommendations for Implementation

1. **Framework & Scaffolding**: Next.js 14/15 with App Router, TypeScript, Tailwind CSS, Lucide React icons, and Recharts for interactive analytics.
2. **API Routes**:
   - `/api/agents`: Returns status and summary metrics for the 5 Sak-Family personas.
   - `/api/metrics`: Aggregates latency, token usage, error rates, and model performance from `eval.jsonl`.
   - `/api/memory`: Returns records from `memory.db` (`facts` and `observations`) and `audit.log`.
   - `/api/sessions`: Returns list of sessions and individual transcript details from `sessions/*.json`.
3. **Automated Testing**: Vitest or Jest for unit testing API route handlers and React component rendering, ensuring `npm test` completes with 100% exit code 0.
4. **Build & Quality**: Strict TypeScript types (`npm run build` zero errors) and sleek dark-mode styling with Inter / Outfit fonts.
