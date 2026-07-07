---
name: SakThai-coding-testing
category: coding
description: Write hermetic pytest tests for sakthai-agent-v2 — no network, no GCP, injected stores/clients. Use when adding tests, building fixtures, mocking the agent loop or MCP, or gating integration tests.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - python
      - testing
      - pytest
      - hermetic
    related_skills:
      - sakthai-coding-uv
      - sakthai-coding-type-safety
      - sakthai-coding-skill-authoring
---

# sakthai-coding-testing

`sakthai-agent-v2`'s suite is **hermetic by contract**: tests assume *no network*
and *no GCP credentials*, and they exercise behavior through injected `store` /
client objects rather than reaching out. Real-endpoint tests are quarantined
behind the `integration` marker and excluded from CI.

## When to use this skill

- Adding a unit test under `tests/`
- Designing a fixture (e.g. an in-memory `MemoryStore`)
- Testing the agent loop or MCP server without a live model/process
- Deciding whether a test belongs under the `integration` marker
- Reproducing a CI failure locally

## The hermetic contract

1. **No network, no GCP.** Inject a fake/real-but-local collaborator; never call
   a live endpoint in the default suite.
2. **Inject the seam, don't patch the world.** v2 makes `store` and the client
   injectable precisely so tests pass a test double in. Use that — prefer
   constructor injection over `monkeypatch` of globals.
3. **The store is the seam.** Anything touching SQLite goes through
   `MemoryStore`; tests get a fresh one per test (temp DB) for isolation.

Run the suite exactly as CI does:

```bash
uv run pytest tests/ -q                 # default: integration excluded via -m 'not integration'
uv run pytest tests/test_memory_store.py -q
uv run pytest -m integration            # opt in locally (self-skips if endpoint/cred absent)
```

## Fixtures: a fresh isolated store

The suite passes a `store` fixture into tests. Build it against a temp path so
each test is independent and nothing touches `~/.sakthai`:

```python
# conftest.py
import pytest
from sakthai.memory.store import MemoryStore

@pytest.fixture
def store(tmp_path) -> MemoryStore:
    return MemoryStore(tmp_path / "memory.db")
```

```python
def test_add_and_list_facts(store: MemoryStore) -> None:   # AAA, typed signature
    fid = store.add_fact("likes tea", kind="pref", key="drink")   # Arrange/Act
    facts = store.list_facts()                                    # Act
    assert facts[0].value == "likes tea"                          # Assert
```

Note the conventions visible in the real suite: `from __future__ import
annotations`, fully typed `-> None` test signatures (strict mypy also covers
intent here), and the AAA shape.

## Testing the agent loop without a live model

`run_agent` takes an injectable client and store. Pass a stub client that returns
canned tool-call/response turns — assert on dispatched tool calls and the written
session log, not on a real API:

```python
class FakeClient:
    def __init__(self, turns): self._turns = iter(turns)
    def create(self, **_): return next(self._turns)

def test_loop_dispatches_tool(store, tmp_path):
    client = FakeClient([...])      # canned turns
    run_agent("do X", client=client, store=store)
    # assert tool was called / fact written via store
```

## Testing the MCP server (pure function)

`mcp/server.py`'s `handle_request` is a **pure function** — test the JSON-RPC
protocol with plain dicts, no subprocess:

```python
def test_mcp_lists_tools():
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert resp["id"] == 1
    assert "tools" in resp["result"]
```

## The integration marker

Tag any test that *may* hit a real external endpoint (Ollama/Anthropic):

```python
@pytest.mark.integration
def test_real_ollama_roundtrip():
    # self-skip if the endpoint/credential is absent
    ...
```

CI runs `-m 'not integration'`; these never block `main`. They should also
self-skip when their endpoint or credential is missing, so an opt-in local run
degrades gracefully.

## Common pitfalls

1. **Don't hit the network in the default suite.** No live Anthropic/Ollama/GCP
   calls outside the `integration` marker.
2. **Don't write to `~/.sakthai`.** Use `tmp_path`; set `SAKTHAI_HOME` if a code
   path resolves the home root.
3. **Don't share state between tests.** Fresh store per test; no module-level
   mutable singletons.
4. **Don't bypass the seam.** Drive behavior through `MemoryStore` and the tool
   registry, mirroring production paths — don't poke SQLite directly.
5. **Don't forget to mark integration tests** — an unmarked live test breaks the
   hermetic guarantee and flakes CI.
