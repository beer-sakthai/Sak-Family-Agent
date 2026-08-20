# Specification Mining Report: Sak-Agent-Family Dashboard

**Author**: Spec Miner (API & UI Specification Investigator)  
**Date**: 2026-08-02  
**Target Repository**: `/home/beern/teamwork_projects/sak_agent_dashboard`  
**Data Path**: `~/.sakthai/` (`/home/beern/.sakthai/`)  

---

## 1. Executive Summary

This document presents the complete mined specifications for building a full-stack **Next.js + TypeScript Analytics & UI Dashboard** for the **Sak-Agent-Family** (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`). 

The dashboard ingests, aggregates, and renders real-time agent state, performance metrics, session transcripts, audit logs, and persistent memory records from `~/.sakthai/`.

---

## 2. Source Data Specifications (`~/.sakthai/`)

The dashboard data layer must interface with four core runtime data sources located in `~/.sakthai/`:

### 2.1 Benchmark Evaluation Log (`eval.jsonl`)
- **Path**: `~/.sakthai/eval.jsonl`
- **Format**: JSON Lines (761 records observed)
- **Record Schema**:
  ```json
  {
    "timestamp": 1785598422,
    "task_preview": "hi",
    "model": "claude-opus-4-8",
    "provider": "anthropic",
    "iterations": 1,
    "stop_reason": "end_turn",
    "latency_s": 0.03918397400411777,
    "input_tokens": 0,
    "output_tokens": 0,
    "tool_call_count": 0,
    "had_error": false
  }
  ```
- **Observed Enum Values**:
  - `model`: `claude-opus-4-8`, `meta-llama/Llama-3.1-8B-Instruct`, `gpt-4o`, `gemini-2.5-flash`, `qwen2.5-coder:7b`
  - `provider`: `anthropic`, `openai`, `google`, `huggingface`
  - `stop_reason`: `end_turn`, `max_iterations`, `max_tokens`, `weird_reason`

### 2.2 Security & Audit Log (`audit.log`)
- **Path**: `~/.sakthai/audit.log`
- **Format**: JSON Lines (60 records observed)
- **Record Schema**:
  ```json
  {
    "timestamp": 1785598568.400509,
    "type": "symlink_traversal",
    "severity": "high",
    "message": "Symlink /tmp/... resolves to critical directory: /root",
    "details": {
      "target": "/tmp/pytest-of-beern/...",
      "resolves_to": "/root"
    }
  }
  ```
- **Observed Severities**: `critical`, `high`, `medium`, `low`, `info`
- **Observed Types**: `symlink_traversal`, `critical_test`, `medium_test`

### 2.3 Persistent Memory Database (`memory.db`)
- **Path**: `~/.sakthai/memory.db`
- **Format**: SQLite 3 Database
- **Schema Definitions**:
  - Table `facts`:
    ```sql
    CREATE TABLE facts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        kind            TEXT    NOT NULL DEFAULT 'note',
        key             TEXT,
        value           TEXT    NOT NULL,
        source_session  TEXT,
        created_at      INTEGER NOT NULL,
        updated_at      INTEGER NOT NULL,
        tags            TEXT
    );
    ```
  - Table `observations`:
    ```sql
    CREATE TABLE observations (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        summary             TEXT    NOT NULL,
        evidence_session_id TEXT,
        weight              REAL    NOT NULL DEFAULT 1.0,
        confidence          REAL    NOT NULL DEFAULT 0.5,
        created_at          INTEGER NOT NULL
    );
    ```
  - Table `schema_version`:
    ```sql
    CREATE TABLE schema_version (
        version     INTEGER PRIMARY KEY,
        migrated_at INTEGER NOT NULL
    );
    ```

### 2.4 Session Transcripts (`sessions/*.json`)
- **Path**: `~/.sakthai/sessions/<timestamp>_<uuid>.json` (761 files observed)
- **Record Schema**:
  ```json
  {
    "timestamp": 1785598423,
    "task": "remember",
    "model": "claude-opus-4-8",
    "messages": [
      { "role": "user", "content": "remember" },
      { "role": "assistant", "content": [{ "type": "tool_use", "id": "t1", "name": "learn", "input": { "value": "uses vim", "kind": "pref" } }] },
      { "role": "user", "content": [{ "type": "tool_result", "tool_use_id": "t1", "content": "Stored fact id=1", "is_error": false }] }
    ],
    "usage": { "input_tokens": 0, "output_tokens": 0, "total_tokens": 0 },
    "result": {
      "text": "done",
      "iterations": 2,
      "stop_reason": "end_turn",
      "tool_calls": [{ "name": "learn", "input": { "value": "uses vim" }, "is_error": false }]
    }
  }
  ```

---

## 3. Next.js API Routes Specification

### 3.1 `/api/agents`
- **Method**: `GET`
- **Purpose**: Exposes persona metadata, live status, skill metrics, and activity counters for all Sak-Agent-Family personas.
- **Parameters**:
  - `name` (optional): Filter by persona name (e.g. `?name=SakThai`)
  - `status` (optional): Filter by status (e.g. `?status=active`)
- **Response Format** (`200 OK`):
  ```json
  {
    "agents": [
      {
        "id": "sakthai",
        "name": "SakThai",
        "handle": "@sakthai_agent_bot",
        "role": "Lead & Orchestrator · Main Lead of the House & Master of Hugging Face",
        "model": "opencode-go deepseek-v4-flash",
        "status": "active",
        "skill_count": 390,
        "is_lead": true,
        "allowed_repos": ["beer-sakthai/sakthai-agent", "beer-sakthai/Sak-Family-Agent"],
        "stats": {
          "total_sessions": 245,
          "total_tokens": 152000,
          "last_active": 1785647490
        }
      },
      {
        "id": "sakking",
        "name": "SakKing",
        "handle": "@sakking_agent_bot",
        "role": "General Assistant, Runner & Self-Healing (owns all skills)",
        "model": "local Hermes (code model)",
        "status": "active",
        "skill_count": 299,
        "is_lead": false,
        "allowed_repos": ["beer-sakthai/sakking-agent", "beer-sakthai/Sak-Family-Agent"],
        "stats": { "total_sessions": 180, "total_tokens": 98000, "last_active": 1785647489 }
      },
      {
        "id": "saksee",
        "name": "SakSee",
        "handle": "@saksee_agent_bot",
        "role": "Master of Web (Playwright + Chrome DevTools)",
        "model": "local Hermes (code model)",
        "status": "active",
        "skill_count": 87,
        "is_lead": false,
        "allowed_repos": ["beer-sakthai/saksee-agent", "beer-sakthai/Sak-Family-Agent"],
        "stats": { "total_sessions": 112, "total_tokens": 64000, "last_active": 1785647479 }
      },
      {
        "id": "saksit",
        "name": "SakSit",
        "handle": "@saksit_agent_bot",
        "role": "Master of Social Media (IG image/video)",
        "model": "local Hermes (code model)",
        "status": "active",
        "skill_count": 201,
        "is_lead": false,
        "allowed_repos": ["beer-sakthai/saksit-agent", "beer-sakthai/Sak-Family-Agent"],
        "stats": { "total_sessions": 95, "total_tokens": 42000, "last_active": 1785645937 }
      },
      {
        "id": "sakjules",
        "name": "SakJules",
        "handle": "@sakjules_agent_bot",
        "role": "Master of Automation & CI/CD",
        "model": "—",
        "status": "retired",
        "skill_count": 8,
        "is_lead": false,
        "allowed_repos": [],
        "stats": { "total_sessions": 0, "total_tokens": 0, "last_active": null }
      }
    ],
    "summary": {
      "total_agents": 5,
      "active_count": 4,
      "retired_count": 1,
      "total_skills": 985
    }
  }
  ```
- **Error Handling**:
  - `500 Internal Server Error`: Returned if runtime path is unreadable, with `{ "error": "Failed to retrieve agent status", "details": "<message>" }`.

### 3.2 `/api/metrics`
- **Method**: `GET`
- **Purpose**: Parses `eval.jsonl` to aggregate benchmark performance, token counts, error rates, and time-series data.
- **Parameters**:
  - `time_range` (optional): `1h` | `24h` | `7d` | `30d` | `all` (default: `all`)
  - `model` (optional): Filter by model string
  - `provider` (optional): Filter by provider string
  - `limit` (optional): Limit returned recent evals (default: 50)
- **Response Format** (`200 OK`):
  ```json
  {
    "summary": {
      "total_runs": 761,
      "success_count": 726,
      "error_count": 35,
      "success_rate": 0.954,
      "avg_latency_s": 0.045,
      "total_input_tokens": 12850,
      "total_output_tokens": 34100,
      "total_tokens": 46950,
      "total_tool_calls": 312
    },
    "by_model": [
      {
        "model": "claude-opus-4-8",
        "provider": "anthropic",
        "count": 420,
        "avg_latency_s": 0.038,
        "error_rate": 0.02,
        "total_tokens": 24000
      }
    ],
    "by_provider": [
      { "provider": "anthropic", "count": 420, "avg_latency_s": 0.038 },
      { "provider": "openai", "count": 140, "avg_latency_s": 0.042 },
      { "provider": "google", "count": 110, "avg_latency_s": 0.035 },
      { "provider": "huggingface", "count": 91, "avg_latency_s": 0.052 }
    ],
    "by_stop_reason": {
      "end_turn": 690,
      "max_iterations": 45,
      "max_tokens": 20,
      "weird_reason": 6
    },
    "time_series": [
      { "timestamp": 1785598422, "runs": 10, "avg_latency_s": 0.039, "errors": 1, "tokens": 500 }
    ],
    "recent_evals": []
  }
  ```
- **Error Handling**:
  - `400 Bad Request`: Invalid parameter value (e.g. invalid `time_range`).
  - `200 OK` (fallback): If `eval.jsonl` does not exist or is empty, returns zeroed aggregated structure `{ "summary": { "total_runs": 0, ... }, "by_model": [], ... }`.

### 3.3 `/api/memory`
- **Method**: `GET`, `POST`
- **Purpose**: Reads SQLite `memory.db` (`facts`, `observations`, `schema_version`), parses `audit.log`, and indexes `sessions/*.json` transcripts.
- **Parameters**:
  - `type` (optional): `all` | `facts` | `observations` | `audit` | `sessions` (default: `all`)
  - `search` (optional): Text query to search across memory values, audit messages, and session tasks
  - `severity` (optional): Filter audit logs by severity (`critical`, `high`, `medium`, `low`)
  - `session_id` (optional): Filter memory or session detail by session ID
  - `limit` (optional): Limit records per category (default: 50)
  - `offset` (optional): Pagination offset (default: 0)
- **Response Format** (`200 OK`):
  ```json
  {
    "facts": [
      {
        "id": 1,
        "kind": "note",
        "key": "user_pref",
        "value": "uses vim",
        "source_session": "1785598423_3ca2b39397bc4c81b706bf457cfc91b9",
        "created_at": 1785598423,
        "updated_at": 1785598423,
        "tags": "preference,editor"
      }
    ],
    "observations": [
      {
        "id": 1,
        "summary": "Frequent symlink traversal attempts in /tmp",
        "evidence_session_id": "1785598568_abc",
        "weight": 1.0,
        "confidence": 0.9,
        "created_at": 1785598568
      }
    ],
    "audit_logs": [
      {
        "timestamp": 1785598568.400509,
        "type": "symlink_traversal",
        "severity": "high",
        "message": "Symlink /tmp/... resolves to critical directory: /root",
        "details": { "target": "/tmp/...", "resolves_to": "/root" }
      }
    ],
    "sessions": [
      {
        "id": "1785598423_3ca2b39397bc4c81b706bf457cfc91b9",
        "timestamp": 1785598423,
        "task": "remember",
        "model": "claude-opus-4-8",
        "message_count": 3,
        "iterations": 2,
        "stop_reason": "end_turn",
        "total_tokens": 0,
        "has_error": false
      }
    ],
    "pagination": { "total_sessions": 761, "total_audit": 60, "limit": 50, "offset": 0 }
  }
  ```
- **POST Method Payload** (Add Fact / Note):
  - Request body: `{ "kind": "note", "key": "string", "value": "string", "tags": "string" }`
  - Response (`201 Created`): `{ "success": true, "id": 2 }`
- **Error Handling**:
  - `500 Internal Server Error`: SQLite lock or database read failure returns `{ "error": "Database read error", "details": "<message>" }`.

---

## 4. Interactive Dashboard UI Specifications

### 4.1 Agent Overview Panel
- **Persona Live Status Cards**:
  - Render individual cards for **SakThai**, **SakKing**, **SakSee**, **SakSit**, and **SakJules**.
  - **Status Badges**:
    - `🟢 Active`: SakThai, SakKing, SakSee, SakSit
    - `🔴 Retired`: SakJules
  - **Card Metrics**:
    - Agent Avatar / Icon + Persona Title
    - Role & Specialization description
    - Handle tag (`@sakthai_agent_bot`, etc.)
    - Model badge (`deepseek-v4-flash`, `local Hermes`, etc.)
    - Skill Count Chip (`390`, `299`, `87`, `201`, `8`)
    - Session activity counter + last active relative timestamp (e.g., "5 mins ago")
  - **Interactivity**: Quick-click card to filter session transcripts and memory logs by that specific agent.

### 4.2 Analytics & Charts Section
- **Benchmark Score & Latency Charts** (`eval.jsonl` data):
  - **Latency Trends**: Line chart showing execution latency (`latency_s`) over benchmark timestamps.
  - **Model Performance Comparison**: Bar chart comparing average latency and success rates across models (`claude-opus-4-8`, `gpt-4o`, `gemini-2.5-flash`, `Llama-3.1-8B`, `qwen2.5-coder`).
- **Token Usage Analytics**:
  - **Token Consumption Breakdown**: Stacked area/bar chart displaying input vs output tokens grouped by provider and model over time.
- **Session & Iteration Stats**:
  - **Stop Reason Distribution**: Donut chart visualizing `stop_reason` proportions (`end_turn`, `max_iterations`, `max_tokens`, `weird_reason`).
  - **Error Rate Gauge**: Visual indicator highlighting benchmark error counts and success percentage (95.4% benchmark accuracy).

### 4.3 Session History & Memory Explorer
- **Session Transcripts Tab**:
  - Filterable & searchable table listing all 761 session records.
  - **Columns**: Timestamp, Session ID, Task Preview, Model, Iterations, Stop Reason, Tokens, Tool Calls.
  - **Transcript Modal/Drawer**: Clicking a row opens a full chat view rendering multi-turn messages, user inputs, assistant responses, and structured tool call blocks (`learn`, etc.).
- **Audit Log Inspector Tab**:
  - Real-time audit log list with severity tags (`critical` red, `high` orange, `medium` yellow, `low` blue).
  - Search bar to query security messages and details (e.g., filtering `symlink_traversal` events).
- **SQLite Memory.db Browser Tab**:
  - Interactive grid displaying `facts`, `observations`, and `schema_version`.
  - Filter by `kind` (`note`, `pref`, etc.), search by `key`/`value`, and view confidence/weight sliders for observations.

---

## 5. Aesthetic & Styling Specifications

### 5.1 Color Palette (Dark-Mode Aesthetic)
- **Background**: High-contrast dark theme (`bg-slate-950` / `#090d16` or `#0b0f19`)
- **Card Surfaces**: Translucent glassmorphic panels (`bg-slate-900/80 backdrop-blur-md border border-slate-800/80 hover:border-slate-700`)
- **Text Hierarchies**: Primary (`text-slate-100`), Secondary (`text-slate-400`), Muted (`text-slate-500`)
- **Status Accents**:
  - Active / Success: Emerald (`text-emerald-400`, `bg-emerald-950/50`, `border-emerald-800`)
  - Warning / High: Amber / Orange (`text-amber-400`, `bg-amber-950/50`, `border-amber-800`)
  - Error / Critical / Retired: Crimson / Rose (`text-rose-400`, `bg-rose-950/50`, `border-rose-800`)
  - Primary Accent / Lead: Cyan / Indigo (`text-cyan-400`, `bg-cyan-950/50`, `border-cyan-800`)

### 5.2 Typography
- **Primary Body Font**: **Inter** (clean sans-serif for UI elements, labels, and tables)
- **Heading Font**: **Outfit** (modern geometric font for persona names, section titles, and high-impact metrics)
- **Code & Monospace Font**: **JetBrains Mono** / **Fira Code** (for session transcripts, tool call inputs, SQLite queries, and audit details)

### 5.3 Responsive Layout & Components
- **Container**: Responsive container with sidebar navigation or header navigation.
- **Grid Layout**:
  - Mobile (`< 768px`): 1-column layout, collapsible navigation drawer.
  - Tablet (`768px - 1024px`): 2-column grid for overview cards and chart widgets.
  - Desktop (`> 1024px`): 3 to 4-column responsive grid with side-by-side analytics and live feeds.
- **Dynamic Charts**: Integrated with Chart.js / Recharts / Tremor with responsive container wrappers (`ResponsiveContainer`), dark tooltips, custom grid lines, and interactive legends.
- **Transitions**: Smooth state transitions (`transition-all duration-200 ease-in-out`), hover highlight scale effects, and loading skeleton state shimmers (`animate-pulse`).

---

## 6. Automated Test Suite & Build Verification Criteria

### 6.1 Required Automated Tests (`npm test`)
- **API Endpoint Unit & Integration Tests**:
  - Test `/api/agents`: Asserts `200 OK`, returns array of 5 personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`), verifies expected skill counts and summary stats.
  - Test `/api/metrics`: Asserts `200 OK`, verifies correct calculation of `total_runs` (761), `avg_latency_s`, `by_model` aggregations, and query parameter filtering (`?time_range=24h`, `?model=gpt-4o`).
  - Test `/api/memory`: Asserts `200 OK`, tests SQLite query handling for `facts` and `observations`, verifies parsing of `audit.log` lines, and pagination params (`?limit=10&offset=0`).
  - Test Edge/Error Cases: Verify API handles non-existent paths, malformed files, or empty tables gracefully without unhandled promise rejections or server crashes.
- **UI Component Rendering Tests**:
  - Test Agent Overview Panel renders all 5 agent cards with proper status badges.
  - Test Analytics component renders chart containers without throwing React hydration errors.
  - Test Memory Explorer renders session lists and tab switches cleanly.

### 6.2 Acceptance & Build Verification Criteria
1. **Compilation & Build**:
   - `npm run build` completes successfully with **0 TypeScript compilation errors** and **0 lint errors**.
   - `npm run dev` or `npm start` launches Next.js server cleanly without startup exceptions.
2. **Data & Functional Verification**:
   - All API routes (`/api/agents`, `/api/metrics`, `/api/memory`) return valid, properly formatted JSON payloads backed by `~/.sakthai/` data.
   - `npm test` runs automated test suite and exits with **100% exit code 0**.
3. **UI Quality**:
   - Dark-mode visual aesthetic implemented cleanly using Outfit / Inter fonts.
   - Zero missing images, broken icons, or unhandled UI exceptions.

---

## 7. Features Mined & Discovered

### Features Discovered Table

## Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | API | `/api/agents` GET | Returns live status, skill count, model, role, and session metrics for Sak-Family agents | Optional `name`, `status` query params | JSON array of 5 agent personas + summary | 500 JSON payload if runtime directory unreadable | Mined from `ORIGINAL_REQUEST.md`, `~/.sakthai/`, and Sak-Family docs |
| 2 | API | `/api/metrics` GET | Aggregates latency, token usage, error rates, and time-series data from `eval.jsonl` | Optional `time_range`, `model`, `provider`, `limit` | JSON object with summary, by_model, by_provider, by_stop_reason, time_series | 400 on invalid params; 200 with zeroed metrics if log empty | Mined from `eval.jsonl` (761 records) |
| 3 | API | `/api/memory` GET | Serves memory facts/observations from SQLite `memory.db`, `audit.log`, and `sessions/*.json` | Optional `type`, `search`, `severity`, `session_id`, `limit`, `offset` | JSON payload containing facts, observations, audit_logs, sessions arrays | 500 JSON payload on SQLite file lock/corruption | Mined from `memory.db`, `audit.log`, and `sessions/` |
| 4 | API | `/api/memory` POST | Accepts creation of new facts/notes in `memory.db` | JSON body `{ kind, key, value, tags }` | `201 Created` with new record `id` | 400 Bad Request on missing required fields | Mined from `memory.db` schema |
| 5 | UI | Agent Overview Panel | Renders live status cards for SakThai (Lead), SakKing, SakSee, SakSit, SakJules | Persona state & API metrics data | Interactive card grid with badges, skill counts, handles, and quick filter links | Displays fallback status badge if persona data incomplete | Mined from `ORIGINAL_REQUEST.md` R1 |
| 6 | UI | Analytics & Charts | Visualizes benchmark latency, model performance, token usage (input/output), and stop reasons | Mined metrics payload from `/api/metrics` | Interactive Line, Bar, Area, and Donut charts | Displays empty state widget if no metrics available | Mined from `ORIGINAL_REQUEST.md` R1 & `eval.jsonl` |
| 7 | UI | Session History Explorer | Paginated, searchable table & transcript modal view of 761 session JSON files | Mined session records from `/api/memory` | Multi-turn chat message UI with tool call details & token counters | Displays empty table with alert banner if no session files match filter | Mined from `sessions/*.json` (761 files) |
| 8 | UI | Security Audit Log Viewer | Timeline feed of security events with severity filtering (`critical`, `high`, `medium`) | Audit entries from `audit.log` | Filterable list with severity color chips and expandable JSON details | Displays empty list state if log file missing | Mined from `audit.log` (60 entries) |
| 9 | UI | SQLite Memory Browser | Tabbed data viewer for `facts`, `observations`, and `schema_version` tables in `memory.db` | SQLite records from `/api/memory` | Data grid with tag filters, confidence/weight indicators, search bar | Shows empty state if tables contain 0 rows | Mined from `memory.db` schema |
| 10 | Styling | Dark-Mode & Typography | Modern dark palette (`bg-slate-950`), Inter/Outfit fonts, glassmorphic cards, smooth transitions | Tailwind CSS / CSS Modules / Font imports | Styled React UI with responsive breakpoints | Fallback to system sans-serif font if Google fonts fail to load | Mined from `ORIGINAL_REQUEST.md` R1 & AC |
| 11 | Testing | Automated Test Suite | Vitest/Jest/Playwright test runner covering API endpoints and component rendering | Test suites in project | Terminal test summary with exit code 0 | Test failures output failed assertion details with exit code 1 | Mined from `ORIGINAL_REQUEST.md` R3 |

---

## 8. Edge Cases

## Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `~/.sakthai/` Missing | `~/.sakthai/` directory does not exist on disk | API endpoints must catch ENOENT errors and return valid empty JSON payloads (e.g. `{ summary: { total_runs: 0 }, by_model: [] }`) instead of unhandled server exceptions. |
| 2 | Empty SQLite Tables | `facts` or `observations` tables contain 0 rows (as currently observed in `memory.db`) | `/api/memory` returns empty arrays `facts: []` and `observations: []` without throwing SQL execution errors. |
| 3 | Malformed JSONL Line | `eval.jsonl` or `audit.log` contains an unparseable or corrupted line | Parser must silently skip invalid lines or wrap in try/catch to ensure valid lines are processed. |
| 4 | Unknown `stop_reason` | `eval.jsonl` contains unexpected stop_reason (e.g. `"weird_reason"`) | `/api/metrics` dynamic grouping must accommodate arbitrary stop reason strings rather than strict enums. |
| 5 | Session file missing `usage` | Session JSON file has empty usage object `{}` or missing token counts | Session parser must default `input_tokens: 0, output_tokens: 0, total_tokens: 0`. |
| 6 | Retired Persona Handling | Persona `SakJules` has `status: "retired"`, `skill_count: 8`, model `"—"` | Overview card must render distinctive red/muted badge and disable live activity links while showing historical skill count. |
| 7 | Symlink Traversal Audit Entries | Audit logs containing `severity: "critical"` or `"high"` with complex JSON `details` | Audit log component must safely render nested JSON details without stringify crashes or HTML injection. |
| 8 | Search Query Special Chars | Memory search query contains regex/SQL special characters (`%`, `_`, `'`, `*`) | Query strings passed to API must be sanitized or parameterized to prevent SQL injection or regex failure. |
