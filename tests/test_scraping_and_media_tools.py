"""Unit tests for SakSit media assets generation and SakSee resilient scraping in agent/tools.py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from sakthai.agent.scraping import DomainCircuitBreaker, ResilientWebFetcher
from sakthai.agent.tools import Tool, tool_by_name
from sakthai.memory.store import MemoryStore


def test_generate_model_card_assets_metadata() -> None:
    tool = tool_by_name("generate_model_card_assets")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "generate_model_card_assets"
    schema = tool.schema()
    assert "model_id" in schema["input_schema"]["properties"]
    assert "model_id" in schema["input_schema"]["required"]
    assert "benchmarks" in schema["input_schema"]["properties"]


def test_generate_model_card_assets_handler(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("generate_model_card_assets")
    assert tool is not None

    out_dir = str(tmp_path / "assets" / "sakthai-context")
    args = {
        "model_id": "Nanthasit/sakthai-context-1.5b-merged",
        "task_type": "text-generation",
        "tags": ["safetensors", "sakthai", "merge"],
        "benchmarks": {"MMLU": 68.4, "GSM8K": 74.2, "HumanEval": 52.0},
        "output_dir": out_dir,
    }

    out = tool.handler(args, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["model_id"] == "Nanthasit/sakthai-context-1.5b-merged"
    assert "banner_svg_path" in data
    assert Path(data["banner_svg_path"]).is_file()
    assert "model_card_markdown" in data
    assert "MMLU" in data["model_card_markdown"]
    assert "GSM8K" in data["model_card_markdown"]

    # Verify memory persistence
    facts = store.search_by_tag("model-card-assets", limit=5)
    assert len(facts) > 0


def test_domain_circuit_breaker_state_transitions() -> None:
    cb = DomainCircuitBreaker(failure_threshold=2, cooldown_seconds=0.5)
    domain = "api.huggingface.co"

    assert cb.can_request(domain) is True
    assert cb.get_state(domain) == "CLOSED"

    # 1 failure -> still closed
    cb.record_failure(domain, status_code=429)
    assert cb.can_request(domain) is True
    assert cb.get_state(domain) == "CLOSED"

    # 2nd failure -> trips OPEN
    cb.record_failure(domain, status_code=429)
    assert cb.get_state(domain) == "OPEN"
    assert cb.can_request(domain) is False

    # Force cooldown
    cb._tripped_at[domain] -= 1.0  # simulate time passed
    assert cb.get_state(domain) == "HALF_OPEN"
    assert cb.can_request(domain) is True

    # Success closes circuit
    cb.record_success(domain)
    assert cb.get_state(domain) == "CLOSED"
    assert cb.can_request(domain) is True


def test_resilient_web_fetcher_dual_engine_fallback() -> None:
    fetcher = ResilientWebFetcher()
    url = "https://example.com/test-article"

    # Simulate primary failing with 429 Too Many Requests -> fallback should kick in
    with (
        patch.object(fetcher, "_fetch_primary") as mock_primary,
        patch.object(fetcher, "_fetch_fallback") as mock_fallback,
    ):
        mock_primary.side_effect = HTTPError(url, 429, "Too Many Requests", {}, None)
        mock_fallback.return_value = {
            "status": 200,
            "engine": "reader_fallback",
            "content": "# Test Article (Reader Fallback)\nExtracted content clean.",
        }

        res = fetcher.fetch(url)
        assert res["status"] == 200
        assert res["engine"] == "reader_fallback"
        assert "Reader Fallback" in res["content"]


def test_web_fetch_resilient_tool(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("web_fetch_resilient")
    assert tool is not None

    with patch("sakthai.agent.scraping.ResilientWebFetcher.fetch") as mock_fetch:
        mock_fetch.return_value = {
            "url": "https://example.com/ai-trends",
            "status": 200,
            "engine": "primary_http",
            "content": "AI trends 2026 report summary",
            "domain_state": "CLOSED",
        }

        out = tool.handler({"url": "https://example.com/ai-trends"}, store)
        data = json.loads(out)
        assert data["status"] == 200
        assert data["engine"] == "primary_http"
        assert "AI trends" in data["content"]


def test_inspect_circuit_breaker_tool(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("inspect_circuit_breaker")
    assert tool is not None

    out = tool.handler({}, store)
    data = json.loads(out)
    assert "domains" in data
    assert "total_tracked" in data

    # Test specific domain
    out_dom = tool.handler({"domain": "example.com"}, store)
    data_dom = json.loads(out_dom)
    assert "state" in data_dom


def test_domain_circuit_breaker_status_and_schemeless() -> None:
    cb = DomainCircuitBreaker(failure_threshold=1, cooldown_seconds=100.0)
    assert cb.extract_domain("huggingface.co/models") == "huggingface.co"

    cb.record_failure("huggingface.co", status_code=503)
    status = cb.status_dict()
    assert status["total_tracked"] >= 1
    assert "huggingface.co" in status["domains"]
    assert status["domains"]["huggingface.co"]["state"] == "OPEN"
    assert status["domains"]["huggingface.co"]["cooldown_remaining_seconds"] > 0


def test_resilient_web_fetcher_primary_and_open_fallback() -> None:
    fetcher = ResilientWebFetcher()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"<html><body><h1>Hello World</h1><p>Test</p></body></html>"

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        res = fetcher.fetch("https://testsite.org/home")
        assert res["status"] == 200
        assert res["engine"] == "primary_http"
        assert "Hello World Test" in res["content"]

    # Now trip the circuit
    fetcher.cb.record_failure("testsite.org", status_code=429)
    fetcher.cb.record_failure("testsite.org", status_code=429)
    fetcher.cb.record_failure("testsite.org", status_code=429)

    # When OPEN, primary is bypassed
    with patch.object(fetcher, "_fetch_primary") as mock_prim:
        res_open = fetcher.fetch("https://testsite.org/home")
        assert res_open["engine"] == "reader_fallback"
        mock_prim.assert_not_called()


def test_generate_model_card_assets_default_benchmarks(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("generate_model_card_assets")
    assert tool is not None

    out = tool.handler(
        {
            "model_id": "Nanthasit/default-model",
            "output_dir": str(tmp_path / "default_assets"),
        },
        store,
    )
    data = json.loads(out)
    assert "MMLU" in data["model_card_markdown"]
    assert "Frontier" in data["model_card_markdown"]


def test_web_fetch_resilient_tool_validation(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("web_fetch_resilient")
    assert tool is not None

    import pytest

    with pytest.raises(ValueError, match="`url` is required"):
        tool.handler({"url": "  "}, store)
