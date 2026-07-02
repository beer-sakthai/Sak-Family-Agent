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


@pytest.mark.skipif(
    not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
    reason="GEMINI_API_KEY / GOOGLE_API_KEY not set",
)
def test_gemini_live_smoke(tmp_path: Path) -> None:
    try:
        from google import genai  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on native libs
        pytest.skip(f"google-genai not importable: {exc}")

    model = os.environ.get("SAKTHAI_GEMINI_MODEL", "gemini-2.0-flash")
    store = MemoryStore(tmp_path / "memory.db")
    try:
        try:
            result = run_agent(
                "Reply with exactly the single word: pong",
                store=store,
                provider="google",
                model=model,
                max_iterations=2,
            )
        except Exception as exc:
            pytest.skip(f"Gemini execution failed (e.g. model unavailable or quota): {exc}")
    finally:
        store.close()
    assert result.text.strip()


@pytest.mark.skipif(
    not os.environ.get("SAKTHAI_GATEWAY_URL"),
    reason="SAKTHAI_GATEWAY_URL not set",
)
def test_gateway_live_smoke(tmp_path: Path) -> None:
    # The gateway provider is OpenAI-compatible; the model name is whatever the
    # configured gateway routes (e.g. an OpenRouter/LiteLLM slug). Callers point
    # SAKTHAI_GATEWAY_MODEL at a model their gateway actually serves.
    model = os.environ.get("SAKTHAI_GATEWAY_MODEL", "gateway")
    store = MemoryStore(tmp_path / "memory.db")
    try:
        try:
            result = run_agent(
                "Reply with exactly the single word: pong",
                store=store,
                provider="gateway",
                model=model,
                max_iterations=2,
            )
        except Exception as exc:
            pytest.skip(f"Gateway execution failed (e.g. bad route or auth): {exc}")
    finally:
        store.close()
    assert result.text.strip()


@pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_BASE") or os.environ.get("OPENAI_BASE_URL")),
    reason="OPENAI_API_BASE / OPENAI_BASE_URL not set",
)
def test_openai_compat_live_smoke(tmp_path: Path) -> None:
    # Exercises the OpenAI-compatible HTTP path against any self-hosted or
    # third-party endpoint the operator points OPENAI_API_BASE at.
    model = os.environ.get("SAKTHAI_OPENAI_MODEL", "gpt-4o-mini")
    store = MemoryStore(tmp_path / "memory.db")
    try:
        try:
            result = run_agent(
                "Reply with exactly the single word: pong",
                store=store,
                provider="openai",
                model=model,
                max_iterations=2,
            )
        except Exception as exc:
            pytest.skip(f"OpenAI-compatible execution failed: {exc}")
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
                provider="openai",
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


@pytest.mark.skipif(not os.environ.get("LOCAL_API_BASE"), reason="LOCAL_API_BASE not set")
def test_local_live_smoke(tmp_path: Path) -> None:
    """Exercises the `local` provider against a custom OpenAI-compatible endpoint."""
    # The model name must start with "local/" to be auto-detected, or the
    # provider must be set explicitly. The part after the slash is the model
    # identifier the local server expects.
    model = os.environ.get("SAKTHAI_LOCAL_MODEL", "local/local-model")
    store = MemoryStore(tmp_path / "memory.db")
    try:
        try:
            result = run_agent(
                "Reply with exactly the single word: pong",
                store=store,
                model=model,
                max_iterations=2,
            )
        except Exception as exc:
            pytest.skip(
                f"Local provider execution failed (e.g. server not running or bad auth): {exc}"
            )
    finally:
        store.close()
    assert result.text.strip()
