# Handoff Report — Runtime Data Schema & `~/.sakthai/` Investigation

**Agent:** Explorer 2 (Runtime Data Schema & `~/.sakthai/` Investigator)  
**Working Directory:** `/home/beern/teamwork_projects/sak_agent_dashboard/.agents/teamwork_preview_explorer_survey_2`  
**Target State Directory:** `/home/beern/.sakthai/`  
**Date:** 2026-08-02  

---

## 1. Observation

Direct observations made during inspection of `/home/beern/.sakthai/`:

### 1.1 Directory Contents & Sizes
* `list_dir` on `/home/beern/.sakthai/` revealed:
  - `eval.jsonl`: 199,327 bytes, 761 lines.
  - `audit.log`: 11,296 bytes, 60 lines.
  - `memory.db`: 32,768 bytes.
  - `sessions/`: directory containing 761 `.json` files.

### 1.2 `eval.jsonl` Log Format & Fields
* **Command:** `python3 -c "import json; ..."`
* **Observation:** 761 JSON lines. Every line contains exactly 11 fields:
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
* **Distinct Models & Counts:**
  - `claude-opus-4-8`: 590
  - `gpt-4o`: 114
  - `gemini-2.5-flash`: 19
  - `meta-llama/Llama-3.1-8B-Instruct`: 19
  - `qwen2.5-coder:7b`: 19

### 1.3 `audit.log` Security Log Format
* **Observation:** 60 JSON lines with fields: `timestamp`, `type`, `severity`, `message`, `details`.
* **Sample Line:**
  ```json
  {"timestamp": 1785598568.400509, "type": "symlink_traversal", "severity": "high", "message": "Symlink /tmp/pytest-of-beern/pytest-0/test_symlink_to_dangerous_loca0/dangerous_link resolves to critical directory: /root", "details": {"target": "/tmp/pytest-of-beern/pytest-0/test_symlink_to_dangerous_loca0/dangerous_link", "resolves_to": "/root"}}
  ```
* **Severities Breakdown:** `high` (20), `critical` (20), `medium` (20).

### 1.4 `memory.db` SQLite Schema
* **Command:** `python3 -c "import sqlite3; ... SELECT type, name, sql FROM sqlite_master;"`
* **Observation:** 3 Tables & 3 Indices:
  1. `schema_version`: `(version INTEGER PRIMARY KEY, migrated_at INTEGER NOT NULL)` — 3 rows (`version` 1, 2, 3 at timestamp `1785598657`).
  2. `facts`: `(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL DEFAULT 'note', key TEXT, value TEXT NOT NULL, source_session TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, tags TEXT)`. Indices: `idx_facts_kind`, `idx_facts_updated`. (0 rows).
  3. `observations`: `(id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT NOT NULL, evidence_session_id TEXT, weight REAL NOT NULL DEFAULT 1.0, confidence REAL NOT NULL DEFAULT 0.5, created_at INTEGER NOT NULL)`. Index: `idx_obs_weight`. (0 rows).

### 1.5 `sessions/*.json` Transcript Files
* **Observation:** 761 files formatted `<timestamp>_<uuid>.json`.
* **Sample File (`1785599456_66f54942f0444d1982eac658e5762bad.json`):**
  ```json
  {
    "timestamp": 1785599456,
    "task": "x",
    "model": "claude-opus-4-8",
    "messages": [{"role": "user", "content": "x"}],
    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    "result": {"text": "hi", "iterations": 1, "stop_reason": "end_turn", "tool_calls": []}
  }
  ```

### 1.6 Persona Profiles in `Sak-Family-Agent/infra/hermes-agents/profiles/`
* **Observation:** 5 SOUL.md persona profiles found:
  - `sakthai`: Main Lead of the House & Hugging Face Master (`claude-opus-4-8`)
  - `sakking`: Executive Runner & Commander (`gpt-4o`)
  - `saksee`: Visual Perception & Browser Learning (`gemini-2.5-flash`)
  - `saksit`: Social Storyteller & Media (`meta-llama/Llama-3.1-8B-Instruct`)
  - `sakjules`: Autonomous Coder & CI/CD (`qwen2.5-coder:7b`)

---

## 2. Logic Chain

1. **Premise 1:** The user request (`ORIGINAL_REQUEST.md`) requires building Next.js API routes (`/api/agents`, `/api/metrics`, `/api/memory`) for 5 personas: SakThai, SakKing, SakSee, SakSit, SakJules based on runtime state in `~/.sakthai/`.
2. **Premise 2:** Inspection of `eval.jsonl` shows 761 records across 5 distinct model strings: `claude-opus-4-8`, `gpt-4o`, `gemini-2.5-flash`, `meta-llama/Llama-3.1-8B-Instruct`, `qwen2.5-coder:7b`.
3. **Premise 3:** Inspection of `infra/hermes-agents/profiles/` in `Sak-Family-Agent` confirms these 5 models map 1-to-1 to the 5 personas:
   - `claude-opus-4-8` -> **SakThai**
   - `gpt-4o` -> **SakKing**
   - `gemini-2.5-flash` -> **SakSee**
   - `meta-llama/Llama-3.1-8B-Instruct` -> **SakSit**
   - `qwen2.5-coder:7b` -> **SakJules**
4. **Premise 4:** Inspection of `sessions/*.json` shows 761 JSON files with transcript messages, usage metrics, and result status matching the 761 `eval.jsonl` benchmark runs.
5. **Premise 5:** Inspection of `memory.db` shows 3 tables (`schema_version`, `facts`, `observations`) for persistent long-term storage, while `audit.log` contains 60 security event logs (`symlink_traversal`, `critical_test`, `medium_test`).
6. **Conclusion:** All runtime data schemas, JSON formats, SQLite table definitions, statistical distributions, and persona mapping mechanisms are fully documented and ready for API layer implementation.

---

## 3. Caveats

1. **Empty Memory Tables:** In `memory.db`, the `facts` and `observations` tables currently contain 0 rows. The Next.js `/api/memory` endpoint must safely handle empty table responses (`[]`) without crashing.
2. **Mock Audit Timestamps:** In `audit.log`, 40 of the 60 records use synthetic test timestamps (`0.0` or `1.0`). The API layer should format timestamps safely (e.g. formatting `0.0` as ISO date or relative time).
3. **Zero Token Counts in Test Runs:** Many test records in `eval.jsonl` have `input_tokens: 0` and `output_tokens: 0`. Aggregations should calculate averages safely with division-by-zero checks.

---

## 4. Conclusion

The runtime data state directory `~/.sakthai/` (`/home/beern/.sakthai/`) has been completely inspected and cataloged.
- `eval.jsonl` provides 761 benchmark metrics records.
- `audit.log` provides 60 security event logs.
- `memory.db` provides SQLite schemas for `facts`, `observations`, and `schema_version`.
- `sessions/*.json` provides 761 transcript files.
- The 5 personas map directly 1-to-1 to the 5 model IDs.

The Next.js implementation team has exact schema definitions, sample payloads, and aggregated statistics to construct `/api/agents`, `/api/metrics`, and `/api/memory` without ambiguity.

---

## 5. Verification Method

To independently verify these findings, execute the following commands from bash:

1. **Verify `eval.jsonl` Record Count & Models:**
   ```bash
   python3 -c "
   import json
   with open('/home/beern/.sakthai/eval.jsonl') as f:
       recs = [json.loads(l) for l in f if l.strip()]
   print('Count:', len(recs))
   from collections import Counter
   print('Models:', Counter(r['model'] for r in recs))
   "
   ```
   *Expected Output:* Count: 761. Models: `claude-opus-4-8`: 590, `gpt-4o`: 114, `gemini-2.5-flash`: 19, `meta-llama/Llama-3.1-8B-Instruct`: 19, `qwen2.5-coder:7b`: 19.

2. **Verify `memory.db` Schema & Tables:**
   ```bash
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('/home/beern/.sakthai/memory.db')
   cur = conn.cursor()
   cur.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
   print('Tables:', cur.fetchall())
   "
   ```
   *Expected Output:* Tables: `[('schema_version',), ('facts',), ('sqlite_sequence',), ('observations',)]`.

3. **Verify Session File Count:**
   ```bash
   ls -1 /home/beern/.sakthai/sessions/*.json | wc -l
   ```
   *Expected Output:* `761`.

4. **Verify `audit.log` Line Count & Severities:**
   ```bash
   python3 -c "
   import json
   with open('/home/beern/.sakthai/audit.log') as f:
       recs = [json.loads(l) for l in f if l.strip()]
   print('Audit Count:', len(recs))
   "
   ```
   *Expected Output:* Audit Count: 60.
