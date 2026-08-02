# Runtime Data Schema & `~/.sakthai/` Investigation Analysis

**Author:** Explorer 2 (Runtime Data Schema & `~/.sakthai/` Investigator)  
**Target Path:** `/home/beern/.sakthai/`  
**Date:** 2026-08-02  
**Working Directory:** `/home/beern/teamwork_projects/sak_agent_dashboard/.agents/teamwork_preview_explorer_survey_2`  

---

## 1. Executive Summary

This report provides a complete, empirical analysis of the runtime state directory `~/.sakthai/` (`/home/beern/.sakthai/`) used by the **Sak-Agent-Family** platform. The runtime directory serves as the persistence layer for agent benchmarks, security audit events, long-term SQLite memory, and per-session transcript histories.

### Key Discoveries:
1. **Persona Mapping:** The 5 Sak-Agent-Family personas (**SakThai**, **SakKing**, **SakSee**, **SakSit**, **SakJules**) correspond directly 1-to-1 with the 5 LLM models recorded in `eval.jsonl` and `sessions/*.json`:
   - **SakThai**: `claude-opus-4-8` / `claude-sonnet-4-6` (Main Lead & Hugging Face Master) — 590 runs
   - **SakKing**: `gpt-4o` (Executive Runner & Commander) — 114 runs
   - **SakSee**: `gemini-2.5-flash` (Visual Perception & Browser Learning) — 19 runs
   - **SakSit**: `meta-llama/Llama-3.1-8B-Instruct` (Social Storyteller & Media) — 19 runs
   - **SakJules**: `qwen2.5-coder:7b` (Autonomous Coder & CI/CD) — 19 runs
2. **File Consistency:** `eval.jsonl` contains 761 evaluation records, exactly matching the 761 JSON files in the `sessions/` directory.
3. **Storage Engine Types:**
   - `eval.jsonl`: JSON Lines log file (199 KB, 761 lines)
   - `audit.log`: JSON Lines security log file (11.2 KB, 60 lines)
   - `memory.db`: SQLite 3 database (32 KB, 3 tables, 3 indices)
   - `sessions/*.json`: Individual session transcript files (761 JSON files)

---

## 2. Directory Inventory (`/home/beern/.sakthai/`)

| Path | Type | Size | Count | Purpose |
|------|------|------|-------|---------|
| `/home/beern/.sakthai/eval.jsonl` | File (JSONL) | 199,327 B | 761 records | Evaluation benchmark results and execution metrics |
| `/home/beern/.sakthai/audit.log` | File (JSONL) | 11,296 B | 60 records | Security audit trail & threat detection logs |
| `/home/beern/.sakthai/memory.db` | SQLite 3 DB | 32,768 B | 3 tables | Long-term memory store (facts, observations, schema versioning) |
| `/home/beern/.sakthai/sessions/` | Directory | N/A | 761 files | Per-session execution transcripts and tool output logs |

---

## 3. Detailed Schema Specifications

### 3.1 Benchmark Log (`eval.jsonl`)

* **Path:** `/home/beern/.sakthai/eval.jsonl`
* **Format:** Line-delimited JSON (JSONL).
* **Record Count:** 761 records.
* **Coverage Window:** `1785598422` (2026-08-01 15:33:42 UTC) to `1785665441` (2026-08-02 10:10:41 UTC).

#### JSON Field Schema:

```typescript
interface EvalRecord {
  timestamp: number;       // Unix epoch timestamp in seconds (e.g. 1785598422)
  task_preview: string;    // Brief task description / prompt excerpt (e.g. "hi", "remember")
  model: string;           // LLM model identifier string (e.g. "claude-opus-4-8")
  provider: string;        // Model provider ("anthropic", "openai", "google", "huggingface")
  iterations: number;      // Loop iterations executed (e.g. 1, 2)
  stop_reason: string;     // Termination status ("end_turn", "max_iterations", "max_tokens", "weird_reason")
  latency_s: number;       // Total execution duration in seconds (float)
  input_tokens: number;    // Count of prompt input tokens
  output_tokens: number;   // Count of completion output tokens
  tool_call_count: number; // Number of tool calls invoked in session
  had_error: boolean;      // True if execution encountered an unhandled error
}
```

#### Verbatim Sample Entry:
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

#### Statistical Breakdown by Model / Persona:

| Model ID | Mapped Persona | Provider | Runs | Avg Latency (s) | Avg Iterations | Total Tool Calls | Error Count | Error Rate |
|----------|----------------|----------|------|-----------------|----------------|------------------|-------------|------------|
| `claude-opus-4-8` | **SakThai** | `anthropic` | 590 | 0.0795s | 1.39 | 190 | 19 | 3.22% |
| `gpt-4o` | **SakKing** | `openai` | 114 | 0.0271s | 1.33 | 38 | 0 | 0.00% |
| `gemini-2.5-flash` | **SakSee** | `google` | 19 | 0.0153s | 1.00 | 0 | 0 | 0.00% |
| `meta-llama/Llama-3.1-8B-Instruct` | **SakSit** | `huggingface` | 19 | 0.0180s | 1.00 | 0 | 0 | 0.00% |
| `qwen2.5-coder:7b` | **SakJules** | `huggingface` | 19 | 0.0107s | 1.00 | 0 | 0 | 0.00% |
| **TOTAL / OVERALL** | **All 5 Personas** | **4 Providers** | **761** | **0.0658s** | **1.36** | **228** | **19** | **2.50%** |

#### Stop Reasons Distribution:
- `end_turn`: 704 records (92.5%)
- `max_iterations`: 19 records (2.5%)
- `max_tokens`: 19 records (2.5%)
- `weird_reason`: 19 records (2.5%)

---

### 3.2 Security Audit Log (`audit.log`)

* **Path:** `/home/beern/.sakthai/audit.log`
* **Format:** Line-delimited JSON (JSONL).
* **Record Count:** 60 records.

#### JSON Field Schema:

```typescript
interface AuditRecord {
  timestamp: number;       // Unix epoch timestamp in seconds (float or int)
  type: string;            // Event category ("symlink_traversal", "critical_test", "medium_test")
  severity: string;        // Severity level ("critical", "high", "medium")
  message: string;         // Human-readable incident summary
  details: Record<string, any>; // Arbitrary metadata payload (e.g. { target: string, resolves_to: string })
}
```

#### Verbatim Sample Entries:
```json
{
  "timestamp": 1785598568.400509,
  "type": "symlink_traversal",
  "severity": "high",
  "message": "Symlink /tmp/pytest-of-beern/pytest-0/test_symlink_to_dangerous_loca0/dangerous_link resolves to critical directory: /root",
  "details": {
    "target": "/tmp/pytest-of-beern/pytest-0/test_symlink_to_dangerous_loca0/dangerous_link",
    "resolves_to": "/root"
  }
}
```
```json
{
  "timestamp": 0.0,
  "type": "critical_test",
  "severity": "critical",
  "message": "Critical event",
  "details": {}
}
```

#### Severity Breakdown:
- `high`: 20 events (`symlink_traversal` attempting to resolve `/root`)
- `critical`: 20 events (`critical_test` mock synthetic events)
- `medium`: 20 events (`medium_test` mock synthetic events)

---

### 3.3 Persistent Memory Store (`memory.db`)

* **Path:** `/home/beern/.sakthai/memory.db`
* **Format:** SQLite 3 Database.
* **Size:** 32,768 bytes.

#### Table DDL Statements & Indices:

1. **`schema_version`** (Tracks schema migrations)
```sql
CREATE TABLE schema_version (
    version     INTEGER PRIMARY KEY,
    migrated_at INTEGER NOT NULL
);
```
*Current Rows (3):*
- `version: 1, migrated_at: 1785598657`
- `version: 2, migrated_at: 1785598657`
- `version: 3, migrated_at: 1785598657`

2. **`facts`** (Stores long-term key-value facts learned across agent sessions)
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
CREATE INDEX idx_facts_kind ON facts(kind);
CREATE INDEX idx_facts_updated ON facts(updated_at);
```
*Current Rows:* 0 rows (Ready for dynamic reads/writes by the dashboard and agents).

3. **`observations`** (Stores agent observations, evidence links, weights, and confidence scores)
```sql
CREATE TABLE observations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    summary             TEXT    NOT NULL,
    evidence_session_id TEXT,
    weight              REAL    NOT NULL DEFAULT 1.0,
    confidence          REAL    NOT NULL DEFAULT 0.5,
    created_at          INTEGER NOT NULL
);
CREATE INDEX idx_obs_weight ON observations(weight);
```
*Current Rows:* 0 rows.

---

### 3.4 Session Transcripts (`sessions/*.json`)

* **Directory:** `/home/beern/.sakthai/sessions/`
* **File Count:** 761 JSON files.
* **Naming Convention:** `<timestamp>_<uuid>.json` (e.g., `1785599456_66f54942f0444d1982eac658e5762bad.json`).

#### JSON Field Schema:

```typescript
interface SessionRecord {
  timestamp: number;       // Unix epoch timestamp in seconds
  task: string;            // User input task / prompt string
  model: string;           // LLM model name string
  messages: Array<{        // Array of conversation messages
    role: "user" | "assistant" | "system";
    content: string;
  }>;
  usage: {                 // Token consumption
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  result: {                // Execution output & status
    text: string;          // Assistant response text
    iterations: number;    // Iteration count
    stop_reason: string;   // Stop reason
    tool_calls: Array<any>;// List of tool call objects
  };
}
```

#### Verbatim Sample File (`1785599456_66f54942f0444d1982eac658e5762bad.json`):
```json
{
  "timestamp": 1785599456,
  "task": "x",
  "model": "claude-opus-4-8",
  "messages": [
    {
      "role": "user",
      "content": "x"
    }
  ],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  },
  "result": {
    "text": "hi",
    "iterations": 1,
    "stop_reason": "end_turn",
    "tool_calls": []
  }
}
```

---

## 4. Persona Representation & Derivation Architecture

### 4.1 Persona Profiles & Roles
In the `Sak-Family-Agent` ecosystem (defined in `infra/hermes-agents/profiles/`), each persona represents a specialized role in the family:

1. **SakThai** (`@sakthai_agent_bot`): Main Lead of the House & Master of Hugging Face / Model Registry.
   - *Default Model:* `claude-opus-4-8` / `deepseek-v4-flash`
   - *Focus:* Hugging Face models, dataset curation, house orchestration.
2. **SakKing** (`@sakking_agent_bot`): Executive Runner & Commander.
   - *Default Model:* `gpt-4o`
   - *Focus:* Execution workflow, task dispatching, general assistance.
3. **SakSee** (`@saksee_agent_bot`): Visual Perception & Browser Learning.
   - *Default Model:* `gemini-2.5-flash`
   - *Focus:* Visual inputs, web browsing, multimodal analysis.
4. **SakSit** (`@saksit_agent_bot`): Social Storyteller & Media Creator.
   - *Default Model:* `meta-llama/Llama-3.1-8B-Instruct`
   - *Focus:* Storytelling, image/video generation (Flux/Wan), media output.
5. **SakJules** (`@sakjules_agent_bot`): Autonomous Coder & CI/CD Agent.
   - *Default Model:* `qwen2.5-coder:7b`
   - *Focus:* Code generation, automated testing, benchmarking.

### 4.2 Data Mapping for Next.js API Routes

To serve `/api/agents`, `/api/metrics`, and `/api/memory`:

1. **`/api/agents` Endpoint Payload:**
   Should combine static persona metadata (name, title, description, role, primary model) with dynamic aggregations calculated from `eval.jsonl` and `sessions/`:
   - `status`: Derived from latest session timestamp and error state (`"active"`, `"idle"`, `"error"`).
   - `totalSessions`: Sum of sessions for mapped model.
   - `avgLatency`: Average latency in seconds.
   - `errorRate`: Percentage of runs with `had_error: true`.
   - `totalToolCalls`: Cumulative tool calls count.

2. **`/api/metrics` Endpoint Payload:**
   Serves time-series and aggregated benchmark metrics parsed from `eval.jsonl`:
   - Time-series benchmark scores over time.
   - Latency distributions by model/persona.
   - Token usage trends (input vs output tokens).
   - Stop reason breakdown.

3. **`/api/memory` Endpoint Payload:**
   Interrogates `memory.db` and `audit.log`:
   - Query `facts` table (filterable by `kind`, `tags`, `key`).
   - Query `observations` table (filterable by `weight`, `confidence`).
   - Query `audit.log` for recent security incidents (`type`, `severity`, `timestamp`).

---

## 5. Summary Table of Persona Metrics

| Persona | Primary Model | Provider | Total Runs | Avg Latency | Error Rate | Tool Calls | Status |
|---------|---------------|----------|------------|-------------|------------|------------|--------|
| **SakThai** | `claude-opus-4-8` | Anthropic | 590 | 79.5 ms | 3.22% | 190 | Active |
| **SakKing** | `gpt-4o` | OpenAI | 114 | 27.1 ms | 0.00% | 38 | Active |
| **SakSee** | `gemini-2.5-flash` | Google | 19 | 15.3 ms | 0.00% | 0 | Active |
| **SakSit** | `meta-llama/Llama-3.1-8B-Instruct` | HuggingFace | 19 | 18.0 ms | 0.00% | 0 | Active |
| **SakJules** | `qwen2.5-coder:7b` | HuggingFace | 19 | 10.7 ms | 0.00% | 0 | Active |

---

## 6. Recommendations for Implementers

1. **SQLite Connection:** Use Node `sqlite3` or `better-sqlite3` in read-only mode (`sqlite3.OPEN_READONLY`) when accessing `/home/beern/.sakthai/memory.db`.
2. **JSONL Parsing:** `eval.jsonl` and `audit.log` can be parsed line-by-line using standard Node `readline` / stream modules or `fs.readFileSync` for instant response.
3. **Session Reading:** Standardize session reading from `/home/beern/.sakthai/sessions/*.json` with graceful handling for missing or corrupt files.
4. **Persona Model Fallback:** Build a robust mapping utility (`MODEL_TO_PERSONA`) so any new models in future logs fall back gracefully to appropriate persona categories.
