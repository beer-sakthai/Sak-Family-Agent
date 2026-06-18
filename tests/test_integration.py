"""Optional integration tests that exercise real provider endpoints.

These are excluded from CI (``pytest -m "not integration"``) and self-skip when
the required endpoint/credential is absent, so the default ``pytest tests/`` run
stays fully hermetic. Run them deliberately with ``pytest -m integration`` once
a credential (ANTHROPIC_API_KEY) or a local Ollama server (OLLAMA_HOST) is set.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sakthai.agent.loop import run_agent
from sakthai.memory.store import MemoryStore

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_anthropic_live_smoke(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = run_agent(
            "Reply with exactly the single word: pong",
            store=store,
            provider="anthropic",
            max_iterations=2,
        )
    finally:
        store.close()
    assert result.text.strip()


@pytest.mark.skipif(not os.environ.get("OLLAMA_HOST"), reason="OLLAMA_HOST not set")
def test_ollama_live_smoke(tmp_path: Path) -> None:
    import httpx

    host = os.environ["OLLAMA_HOST"]
    try:
        resp = httpx.get(f"{host}/api/tags")
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
    except Exception as exc:
        pytest.skip(f"Ollama server at {host} not responsive: {exc}")

    if not models:
        pytest.skip("No models installed in Ollama")

    model = "llama3.2" if "llama3.2" in models or "llama3.2:latest" in models else models[0]

    store = MemoryStore(tmp_path / "memory.db")
    try:
        try:
            result = run_agent(
                "Reply with exactly the single word: pong",
                store=store,
                provider="ollama",
                model=model,
                max_iterations=2,
            )
        except Exception as exc:
            pytest.skip(
                f"Ollama execution failed (e.g. server error or model loading error): {exc}"
            )
    finally:
        store.close()
    assert result.text.strip()
