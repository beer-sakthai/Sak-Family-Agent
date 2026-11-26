# Design: query-aware memory context provider

**Date:** 2026-11-26
**Status:** Approved

## Intent / why

Microsoft's Agent Framework describes RAG as two complementary pieces: context
providers that inject *retrieved* content before model invocation, and search
tools the model calls on demand. `sakthai-agent` already has the second half —
`search`, `recall`, `search_sessions`, `family_search`, `family_recall`
(`agent/tools.py`). The first half is weaker than it looks:
`MemoryStore.render_prompt_block()`, which `agent/loop.py` injects into every
system prompt, only ever returns the most *recent* facts/observations. It is
recency-based, not retrieval-based — the injected content has no relationship
to what the current task is actually about. This closes that gap so the
context-provider half is genuinely query-relevant, matching the pattern.

## Goals

- `MemoryStore.render_prompt_block()` accepts an optional `query`; when given,
  it ranks facts/observations by relevance to that query instead of pure
  recency.
- `agent/loop.py` passes the live task through as that query, so the memory
  block injected into every turn's system prompt is retrieval-augmented.
- `SakThaiMemoryProvider.prefetch(query, ...)` — an existing seam whose
  signature already promises query-aware retrieval but today ignores the
  argument — actually uses it.
- Fully backward compatible: every existing caller that omits `query` gets
  byte-identical output to today.

## Non-goals

- No SQLite FTS5 / BM25, no embeddings, no vector store, no new dependency,
  no network call. The personal memory store is small (tens to low hundreds
  of rows per persona); keyword-overlap scoring over existing LIKE-adjacent
  infrastructure is proportionate.
- No change to `search`/`recall`/`family_search`/`family_recall`/
  `search_sessions` — the on-demand half already works.
- No migration of `agent/loop.py` onto `ContextManager`/`SakThaiMemoryProvider`
  — that's separate, already-flagged tech debt, not part of this change.
- No change to `memory/merged.py`'s `FamilyMemoryView` (a human-facing read
  path for `sakthai memory family`, not the per-turn injection path).

## Anti-goals

- Don't make the memory block non-deterministic or reorder it for queries
  that don't actually relate to any stored fact (e.g. "hi", "what time is
  it") — those must fall back to exactly today's recency behavior.
- Don't silently drop a relevant-but-old fact just because it's outside the
  default recency window.

## Constraints

- Additive change only; no schema migration.
- No new third-party dependency (stdlib `re` only).
- Hermetic: no network, deterministic given the store's contents.
- `memory/store.py`, `memory/provider.py`, and `agent/loop.py` are on the
  whole-package persona parity surface (`tests/test_persona_package_parity.py`)
  — run `make sync-personas` after editing.
- Coverage floor is 96% branch coverage (`--cov-fail-under=96`); new branches
  need tests.
- mypy strict over `personas/sakthai`.

## Approaches considered

1. **SQLite FTS5 + BM25.** Real ranked full-text search, but needs a new
   virtual table and sync triggers, and FTS5 isn't guaranteed to be compiled
   into every Python's bundled sqlite3. Overkill for a store this small and
   adds schema/migration risk this codebase is deliberately conservative
   about.
2. **Leave the context-provider half alone.** Rejected — it's the actual gap
   the user asked to close; the search-tool half already satisfies the other
   half of the pattern.
3. **Python-side keyword-overlap scoring (chosen).** Tokenize the query and
   each candidate's text (lowercase, split on non-alphanumeric); score by the
   size of the token-set intersection; sort by score descending (Python's
   stable sort preserves the existing recency/weight order among ties); fall
   back to the current recency-only selection when the query is empty/blank
   or nothing scores above zero. No new dependency, no schema change, same
   shape as the multi-term matching `search_sessions` already does.

## Decided design

- New module-level constant in `memory/store.py`:
  `RELEVANCE_CANDIDATE_LIMIT = 500` — the candidate pool size scored when a
  query is given (independent of the final `fact_limit`/`obs_limit`, which
  remain the output size).
- New module-level helper: `_tokenize(text: str) -> set[str]` —
  `{t for t in re.split(r"[^a-z0-9]+", text.lower()) if t}`.
- `MemoryStore.render_prompt_block(self, *, fact_limit=DEFAULT_FACT_LIMIT,
  obs_limit=DEFAULT_OBS_LIMIT, query: str | None = None) -> str`:
  - If `query` is falsy/blank after `.strip()`, behavior is unchanged
    (`self.list_facts(limit=fact_limit)`, `self.top_observations(limit=obs_limit)`).
  - Otherwise, fetch up to `RELEVANCE_CANDIDATE_LIMIT` candidates (same
    recency/weight order as today), score each by
    `len(query_tokens & _tokenize(candidate_text))`, drop zero-score
    candidates, sort by score descending (stable), take the first
    `fact_limit`/`obs_limit`. If every candidate scores zero, fall back to
    the first `fact_limit`/`obs_limit` of the (recency-ordered) candidate
    pool — identical to the no-query path.
  - Candidate text for a fact: `f"{kind} {key or ''} {value}"`. For an
    observation: its `summary`.
- `SakThaiMemoryProvider.prefetch(self, query: str, *, session_id: str = "") -> str`:
  now calls `self._store.render_prompt_block(query=query)` directly (guarded
  by the existing `self._store is None` check) instead of delegating to
  `system_prompt_block()`. `system_prompt_block()` itself is unchanged (still
  query-less; it's what `ContextManager.assemble_prompt` calls, out of scope).
- `agent/loop.py`:
  - `_build_system(...)` gains a `task: str = ""` keyword parameter.
  - Its body changes `store.render_prompt_block()` to
    `store.render_prompt_block(query=task)`.
  - The one call site (inside `run_agent`'s iteration loop) passes
    `task=task`.

## What's left to the implementer

- Exact token-set intersection tie-breaking relies on Python's sort stability
  — no explicit secondary sort key needed, but say so in a comment since it's
  load-bearing.
- Test fixture/mocking style: follow this repo's existing pattern of
  constructing a real in-memory `MemoryStore(":memory:")` for store-level
  tests, and `monkeypatch.setattr` on a store instance method to capture
  forwarded arguments for the thin wiring tests (loop.py, provider.py).
