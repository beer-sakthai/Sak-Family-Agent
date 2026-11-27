# Query-Aware Memory Context Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the memory block `agent/loop.py` injects into every system prompt retrieval-relevant to the current task, instead of purely recency-based, so the existing on-demand search tools (`search`/`recall`/`family_*`) are paired with a real context provider — matching the "context providers + search tools" RAG pattern.

**Architecture:** Add an optional `query` parameter to `MemoryStore.render_prompt_block()` that ranks candidate facts/observations by keyword-token overlap against the query (falling back to today's pure-recency selection when the query is blank or nothing matches). Thread the live task through as that query from `agent/loop.py::_build_system()` and from `SakThaiMemoryProvider.prefetch()`.

**Tech Stack:** Python stdlib only (`re`), existing `MemoryStore`/SQLite. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-26-memory-rag-context-provider-design.md`

## Global Constraints

- No new third-party dependency; stdlib `re` only.
- No schema migration; purely additive, backward-compatible parameter.
- `memory/store.py`, `memory/provider.py`, `agent/loop.py` are on the persona
  package-parity surface — run `make sync-personas` after all edits, before
  the final verification task.
- Coverage floor is 96% branch coverage (`--cov-fail-under=96`); every new
  branch needs a covering test.
- mypy strict over `personas/sakthai`; keep new code fully typed.
- Every existing test that calls `render_prompt_block()`,
  `system_prompt_block()`, or `prefetch()` without a query must keep passing
  unmodified (backward compatibility).

## Review Focus

- Blank/whitespace-only query (`""`, `"   "`) must fall back to the exact
  current recency behavior, not tokenize to something that matches
  everything or crashes.
- Query that matches no candidate (the common case — most tasks aren't about
  stored facts, e.g. "hi") must produce the same block as today, in the same
  order, not an empty block.
- Case must not matter ("Blue" in a fact must match a query for "blue").
- Tied scores must preserve the existing recency/weight order, not an
  arbitrary one (stability of the sort is load-bearing).
- An empty store (no facts/observations at all) with a non-blank query must
  still return `""`, not raise.

---

### Task 1: Query-relevance ranking in `MemoryStore.render_prompt_block`

**Files:**
- Modify: `personas/sakthai/memory/store.py` (add `import re`; add
  `RELEVANCE_CANDIDATE_LIMIT` constant near `DEFAULT_FACT_LIMIT`/
  `DEFAULT_OBS_LIMIT`; add module-level `_tokenize`; modify
  `MemoryStore.render_prompt_block`)
- Test: `tests/test_memory_store.py`

**Interfaces:**
- Produces: `MemoryStore.render_prompt_block(self, *, fact_limit: int =
  DEFAULT_FACT_LIMIT, obs_limit: int = DEFAULT_OBS_LIMIT, query: str | None =
  None) -> str` — same return shape as today (the untrusted-data-delimited
  markdown block, or `""`), now relevance-ranked when `query` is given.
  Task 2 calls this with `query=<task text>`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_memory_store.py`:

```python
def test_render_prompt_block_query_ranks_relevant_fact_over_recent_one(
    store: MemoryStore,
) -> None:
    """A fact relevant to the query beats a more recent irrelevant one."""
    store.add_fact("the user's dog is named Rex", kind="preference")
    store.add_fact("the user's favorite color is blue", kind="preference")
    block = store.render_prompt_block(fact_limit=1, query="what is the dog's name")
    assert "Rex" in block
    assert "blue" not in block


def test_render_prompt_block_query_is_case_insensitive(store: MemoryStore) -> None:
    store.add_fact("the user's dog is named Rex", kind="preference")
    block = store.render_prompt_block(fact_limit=1, query="REX")
    assert "Rex" in block


def test_render_prompt_block_blank_query_matches_no_query(store: MemoryStore) -> None:
    store.add_fact("the user's dog is named Rex", kind="preference")
    store.add_fact("the user's favorite color is blue", kind="preference")
    assert store.render_prompt_block(query="   ") == store.render_prompt_block()
    assert store.render_prompt_block(query=None) == store.render_prompt_block()


def test_render_prompt_block_nonmatching_query_falls_back_to_recency(
    store: MemoryStore,
) -> None:
    """A task unrelated to any stored fact (the common case) must match
    today's plain recency output exactly, not come back empty or reordered."""
    store.add_fact("the user's dog is named Rex", kind="preference")
    store.add_fact("the user's favorite color is blue", kind="preference")
    assert store.render_prompt_block(query="hi there") == store.render_prompt_block()


def test_render_prompt_block_query_on_empty_store_returns_empty(
    store: MemoryStore,
) -> None:
    assert store.render_prompt_block(query="anything") == ""


def test_render_prompt_block_tied_scores_preserve_recency_order(
    store: MemoryStore,
) -> None:
    """Two facts that score equally keep the newest-first order."""
    store.add_fact("project alpha status: green", kind="status")
    store.add_fact("project beta status: green", kind="status")
    block = store.render_prompt_block(fact_limit=1, query="status")
    assert "beta" in block
    assert "alpha" not in block
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_memory_store.py -k render_prompt_block -v`
Expected: the six new tests FAIL (unexpected `query` keyword argument), all
pre-existing `render_prompt_block` tests still PASS.

- [ ] **Step 3: Implement the ranking in `personas/sakthai/memory/store.py`**

Add `import re` to the import block. Add near `DEFAULT_FACT_LIMIT`/
`DEFAULT_OBS_LIMIT`:

```python
RELEVANCE_CANDIDATE_LIMIT = 500
```

Add a module-level helper (placed near the other module-level helpers, e.g.
next to `_fact_from_row`):

```python
def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t}
```

Change `render_prompt_block`'s signature to add `query: str | None = None`,
and change its body so that when `query` (stripped) is non-empty it ranks
`self.list_facts(limit=RELEVANCE_CANDIDATE_LIMIT)` /
`self.top_observations(limit=RELEVANCE_CANDIDATE_LIMIT)` by
`len(query_tokens & _tokenize(candidate_text))` descending (Python's stable
sort keeps the existing recency/weight order among ties — note this in a
short comment, since it is load-bearing), drops nothing itself but falls
back to the first `fact_limit`/`obs_limit` of the unscored candidate pool
when every candidate scores zero. Candidate text for a `Fact` is
`f"{fact.kind} {fact.key or ''} {fact.value}"`; for an `Observation` it's
`observation.summary`. When `query` is blank, behavior must be exactly
today's: `self.list_facts(limit=fact_limit)` /
`self.top_observations(limit=obs_limit)`. The rest of the method (building
the markdown block with the untrusted-data delimiters) is unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_memory_store.py -v`
Expected: all PASS, including every pre-existing test in the file.

- [ ] **Step 5: Commit**

```bash
git add personas/sakthai/memory/store.py tests/test_memory_store.py
git commit -m "feat(memory): rank render_prompt_block by query relevance"
```

---

### Task 2: Wire the task/query through the loop and the provider seam

**Files:**
- Modify: `personas/sakthai/agent/loop.py:185` (`_build_system` signature +
  body), `:562` (its call site inside `run_agent`)
- Modify: `personas/sakthai/memory/provider.py:46`
  (`SakThaiMemoryProvider.prefetch`)
- Test: `tests/test_agent_loop.py`, `tests/test_memory_aux.py`

**Interfaces:**
- Consumes: `MemoryStore.render_prompt_block(..., query: str | None = None)`
  from Task 1.
- Produces: `_build_system(..., task: str = "")` — Task 3's manual
  verification exercises this through a live `run_agent` call.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_agent_loop.py` (near `test_memory_block_includes_untrusted_delimiters`):

```python
def test_build_system_forwards_task_as_memory_query(
    sakthai_home, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The live task must reach render_prompt_block as `query`, not be
    dropped — this is what makes the injected memory block retrieval-
    relevant instead of purely recency-based."""
    captured: dict[str, object] = {}
    original = store.render_prompt_block

    def _spy(*, query: str | None = None, **kwargs: object) -> str:
        captured["query"] = query
        return original(query=query, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(store, "render_prompt_block", _spy)
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    run_agent("what is the dog's name", client=client, store=store, provider="anthropic")
    assert captured["query"] == "what is the dog's name"
```

Add to `tests/test_memory_aux.py` (near the existing `prefetch` assertion at
line 46):

```python
def test_provider_prefetch_forwards_query_to_store(sakthai_home: Path) -> None:
    """prefetch's query parameter must reach the store, not be discarded —
    it is the provider's half of the retrieval-augmented context."""
    p = SakThaiMemoryProvider()
    p.initialize()
    captured: dict[str, object] = {}
    original = p._store.render_prompt_block  # type: ignore[union-attr]

    def _spy(*, query: str | None = None, **kwargs: object) -> str:
        captured["query"] = query
        return original(query=query, **kwargs)

    monkeypatch_target = p._store  # type: ignore[union-attr]
    monkeypatch_target.render_prompt_block = _spy
    p.prefetch("find the dog")
    assert captured["query"] == "find the dog"
    p.shutdown()
```

(Use `monkeypatch.setattr` instead of direct attribute assignment if that
reads more consistently with the rest of the file — follow the file's
existing style.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agent_loop.py::test_build_system_forwards_task_as_memory_query tests/test_memory_aux.py::test_provider_prefetch_forwards_query_to_store -v`
Expected: both FAIL — `captured["query"]` is `None` (today's calls carry no
query at all).

- [ ] **Step 3: Implement the wiring**

In `personas/sakthai/agent/loop.py`, add `task: str = ""` to `_build_system`'s
signature (after the existing `persona: str | None = None` parameter), and
change its body from `store.render_prompt_block()` to
`store.render_prompt_block(query=task)`. At the call site inside `run_agent`
(the `_build_system(...)` call in the iteration loop), add `task=task` to
the keyword arguments passed.

In `personas/sakthai/memory/provider.py`, change `prefetch` to:

```python
def prefetch(self, query: str, *, session_id: str = "") -> str:
    if self._store is None:
        return ""
    return self._store.render_prompt_block(query=query)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_agent_loop.py tests/test_memory_aux.py -v`
Expected: all PASS, including the pre-existing
`test_provider_renders_facts_after_initialize` (its
`p.prefetch("anything") == block` assertion still holds because "anything"
matches no fact, so `prefetch` falls back to the same recency output as
`system_prompt_block()`).

- [ ] **Step 5: Commit**

```bash
git add personas/sakthai/agent/loop.py personas/sakthai/memory/provider.py tests/test_agent_loop.py tests/test_memory_aux.py
git commit -m "feat(agent): thread the live task through as the memory retrieval query"
```

---

### Task 3: Persona sync and full verification

**Files:**
- Modify (generated): `personas/{sakking,saksee,saksit,sakjules,saktan}/memory/store.py`, `.../memory/provider.py`, `.../agent/loop.py`

**Interfaces:**
- Consumes: Tasks 1-2's finished, committed changes in
  `personas/sakthai/`.
- Produces: nothing further — this is the repo-wide verification gate.

- [ ] **Step 1: Sync the canonical package into the five persona copies**

Run: `make sync-personas`
Expected: exits 0; `git status` shows the same three files changed under
each of `personas/sakking/`, `personas/saksee/`, `personas/saksit/`,
`personas/sakjules/`, `personas/saktan/`.

- [ ] **Step 2: Verify persona parity**

Run: `python3 scripts/sync_personas.py --check`
Expected: reports no drift.

- [ ] **Step 3: Run the full suite with coverage**

Run: `uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-fail-under=96`
Expected: all tests PASS (including every new test from Tasks 1-2 and the
full pre-existing suite); coverage gate passes.

- [ ] **Step 4: Lint, format, type-check**

Run: `uv run ruff check personas/sakthai tests && uv run ruff format --check personas/sakthai tests && uv run mypy personas/sakthai`
Expected: all clean.

- [ ] **Step 5: Commit the persona sync**

```bash
git add personas/sakking personas/saksee personas/saksit personas/sakjules personas/saktan
git commit -m "chore: sync-personas for the memory RAG context-provider change"
```
