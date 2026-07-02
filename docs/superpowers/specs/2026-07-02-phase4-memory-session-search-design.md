# Phase 4: Memory Architecture & Session Search — Design

**Status:** Approved, ready for implementation planning
**Roadmap:** Hermes Runtime Roadmap, Phase 4 (`PLAN.md`, `product/todo.md`)
**Predecessor:** Phase 3 dependency inventory (`docs/agent-diagnosis.md`)

## Goal

Close the gap the roadmap names "memory architecture and session search": there
is currently no way to search across past session content. Do this in two
parts, mirroring the diagnosis-first style Phase 3 used:

1. **Audit** the current memory/session architecture and document the gap.
2. **Targeted fix**: add session search as a CLI command and an agent tool,
   without changing `MemoryStore`'s schema or scope.

## Part A: Memory & Session Architecture Audit

A short "Memory & Session Architecture" write-up (folded into this spec rather
than a separate diagnosis doc, since the finding is simple) covering:

- **`MemoryStore` (SQLite, `memory/store.py`)** — holds `facts` and
  `observations` only. WAL concurrency, additive migrations, snapshot
  export/import, dedupe/consolidate. Already has `search_memory()` (LIKE-based)
  over facts/observations. This part of the architecture is sound and is
  **not** changed by this phase.
- **Session logs (`~/.sakthai/sessions/*.json`)** — written by
  `agent/loop.py`, one flat JSON file per session (iterations, tool calls,
  usage, task text). Fully separate from `MemoryStore`; `sessions list/show`
  only read file metadata / a single file by ID.
- **The gap:** no way to search *across* session content (task text, tool
  calls, results) by query. `search_memory()` doesn't cover sessions because
  sessions were never ingested into the store, and nothing else fills that
  role.
- **Why on-demand scan, not an index:** current scale is 1,070 session files /
  4.3 MB on the primary dev machine. A scan-per-query is well under a second
  at this volume. Revisit (e.g. SQLite FTS5) only if session count grows an
  order of magnitude and scan latency becomes noticeable — not speculatively
  now.
- **Why this doesn't touch `MemoryStore`:** sessions are flat JSON, not SQLite
  rows. Folding them into the store would blur its single responsibility
  ("the memory store is the seam" for SQLite, per `CLAUDE.md`) for no benefit
  at this scale.

## Part B: Session Search

### `search_sessions()` — shared function

New module: `sakthai/memory/session_search.py`.

```python
@dataclass
class SessionMatch:
    session_id: str
    timestamp: float | None
    task: str
    matched_snippet: str

def search_sessions(
    query: str,
    limit: int = 20,
    sessions_dir: Path | None = None,
) -> list[SessionMatch]:
    ...
```

- `sessions_dir` is injectable (defaults to `config.sessions_dir()`), matching
  this repo's dependency-injection convention for testability.
- Walks `*.json` in the sessions directory, parses each, skips
  unreadable/corrupt files (`except (JSONDecodeError, OSError): continue`,
  same as `sessions_list`'s existing pattern).
- **Searchable text** (verified against the actual payload written by
  `_save_session_log` in `agent/loop.py`, not just the general shape):
  `task`, `result.text` (the final answer), and `result.tool_calls[].name` /
  `result.tool_calls[].input` for every entry in `result.tool_calls`. Note
  `result.tool_calls` is already a **flat** `list[dict]` (`{name, input,
  is_error}`) — there is no need to walk the nested `messages[].content[]`
  blocks to find tool calls; `messages` is not parsed by this feature at all.
- **Query semantics:** split `query` on whitespace into terms; a session
  matches if **every** term appears (case-insensitive) somewhere in the
  searchable text above. AND-of-terms, not exact-substring — this is what
  "search" means colloquially and costs only a few extra lines over substring
  matching. An empty/whitespace-only query raises `ValueError` (mirrors
  `parse_duration`'s existing empty-input guard in `cli/sessions.py`).
- **Missing sessions directory:** if `sessions_dir()` doesn't exist,
  `search_sessions()` returns `[]` (mirrors `sessions_list`'s existing
  `if not dir_path.exists(): ...; return` guard — no error).
- **No matches:** the CLI prints `"No matching sessions found."` (same
  empty-state style as `sessions_list`'s `"No sessions found."`); the agent
  tool returns an empty list, same as any other zero-result tool call.
- **Result ordering:** sorted by session timestamp descending (most recent
  first), matching `sessions_list`'s existing sort order. No relevance
  ranking — an on-demand substring scan doesn't warrant one.
- **Snippet:** `matched_snippet` is a short window of text around the first
  match, for display in both the CLI and tool output.

### Sensitivity note (deliberate, not an oversight)

Session files can contain `read_file` contents and `run_command` output.
`search_sessions` as an agent tool lets an agent read back anything from any
past session, including file/command output captured in *other* sessions.
This is **not a new privilege** — an agent could already retrieve the same
data one file at a time via the existing `sessions show` flow — `search_sessions`
just makes it reachable by content instead of by ID. No additional gating
(no `SAKTHAI_*_ALLOW` env var) is introduced for this reason. This reasoning
is recorded here so it reads as a decision, not a gap, if revisited later.

### CLI surface

`sakthai sessions search <query> [--limit N]` in `cli/sessions.py`. Table
output shaped like the existing `sessions list` table, with a
matched-snippet column replacing model/tokens.

### Agent tool surface

New entry in `BUILTIN_TOOLS` (`agent/tools.py`): `search_sessions(query,
limit)`, calling the same `search_sessions()` function. Per this repo's
existing tool convention, adding it once here makes it available in both the
agent loop and `sakthai mcp` automatically — no separate wiring.

### Out of scope (deliberately deferred)

- Regex search
- Fuzzy/typo-tolerant matching
- Pagination beyond `--limit`
- A persistent search index (SQLite FTS5 or otherwise)
- Ingesting sessions into `MemoryStore`

These are not overlooked; they're excluded to keep this phase's surface
minimal (YAGNI) given current session volume.

## Testing Plan

- **`tests/test_session_search.py`** (new): inject a `tmp_path` sessions
  directory (existing fixture pattern in this repo), write a handful of fake
  session JSON files, assert: multi-term AND matching, no-match case,
  corrupt-file-is-skipped, `limit` is respected, ordering is
  timestamp-descending.
- **`tests/test_tools.py`**: extend for the new `search_sessions` tool entry,
  using an injected `MemoryStore(":memory:")` where relevant and a `tmp_path`
  sessions dir.
- **CLI test** (wherever `sessions list`/`show` are currently covered):
  extend for the new `sessions search` subcommand.

## File Changes Summary

| File | Change |
|---|---|
| `sakthai/memory/session_search.py` | New — `search_sessions()`, `SessionMatch` |
| `sakthai/cli/sessions.py` | Add `search` subcommand |
| `sakthai/agent/tools.py` | Add `search_sessions` to `BUILTIN_TOOLS` |
| `tests/test_session_search.py` | New |
| `tests/test_tools.py` | Extend |
| CLI sessions test file | Extend |

## Plan-First Workflow Linkage

Per this repo's `CLAUDE.md` ("Always read and update `PLAN.md`... mark tasks
`[ ]` → `[x] YYYY-MM-DD` once verified"), the implementation plan derived from
this spec adds a **Phase 4** section to `product/todo.md` (alongside the
existing Phase 1–3 sections) with these checklist items, each checked off
with a date once its verification step passes:

- [ ] **Architecture audit:** Part A of this spec folded into `product/todo.md`
  or linked from it.
- [ ] **`search_sessions()`:** implemented in `sakthai/memory/session_search.py`
  with the query/ordering/missing-dir semantics above.
- [ ] **CLI command:** `sakthai sessions search <query> [--limit N]`.
- [ ] **Agent tool:** `search_sessions` in `BUILTIN_TOOLS`, verified reachable
  from both `sakthai run` and `sakthai mcp`.
- [ ] **Test coverage:** all cases in the Testing Plan above passing.
- [ ] **Local verification:** `uv run pytest tests/test_session_search.py
  tests/test_tools.py -q` and a manual `sakthai sessions search` smoke run.
- [ ] **GitHub delivery:** committed, pushed, PR opened, merged after green CI
  (per `CLAUDE.md`'s commit → green CI → merge workflow).
