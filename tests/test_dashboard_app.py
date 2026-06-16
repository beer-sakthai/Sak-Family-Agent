"""Smoke tests for the Streamlit dashboard app (sakthai/dashboard/app.py).

The module is pure Streamlit/plotly presentation glue; the data logic it renders
lives in dashboard/data.py (covered by test_dashboard_data.py) and app.py is
excluded from coverage/mypy in pyproject.toml. These tests run only where the
``dashboard`` extra is installed — they skip under CI's dev-only install — and
verify the module imports cleanly and its figure/helper builders work without a
live Streamlit runtime (``st`` side effects are stubbed).
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
pytest.importorskip("pandas")

from sakthai.dashboard import app  # noqa: E402  (guarded import after importorskip)
from sakthai.dashboard.data import DEMO_DATA  # noqa: E402


def test_main_is_callable() -> None:
    assert callable(app.main)


def test_token_fingerprint_anonymous_when_empty() -> None:
    assert app._token_fingerprint("") == "anonymous"


def test_token_fingerprint_is_stable_and_non_reversible() -> None:
    fp = app._token_fingerprint("ghp_secret_token")
    assert fp == app._token_fingerprint("ghp_secret_token")  # deterministic
    assert "ghp_secret_token" not in fp  # never leaks the secret
    assert len(fp) == 12


def test_knowledge_graph_builds(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(app.st, "plotly_chart", lambda fig, **k: captured.setdefault("fig", fig))
    app._render_knowledge_graph(DEMO_DATA["graph"])
    # One trace per spoke edge plus one node-marker trace → at least 2 traces.
    assert len(captured["fig"].data) >= 2


def test_knowledge_graph_handles_no_categories(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(app.st, "plotly_chart", lambda fig, **k: captured.setdefault("fig", fig))
    app._render_knowledge_graph({"categories": [], "total_nodes": 0, "connections": 0})
    assert captured["fig"].data  # the central "Core" node is always present


def test_notify_appends_and_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app.st, "session_state", {}, raising=False)
    for i in range(25):
        app._notify(f"event {i}")
    notes = app.st.session_state["notifications"]
    assert len(notes) == 20  # capped
    assert notes[-1]["msg"] == "event 24"
