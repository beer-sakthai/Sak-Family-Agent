"""Tests for scripts/hf-portfolio-health.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "hf-portfolio-health.py"


@pytest.fixture
def hf_health() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hf_portfolio_health", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fetch_json_valid_url(hf_health: ModuleType) -> None:
    mock_data = {"key": "value"}
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = hf_health.fetch_json("https://huggingface.co/api/models")
        assert result == mock_data
        assert mock_urlopen.called


def test_fetch_json_rejects_non_http_schemes(hf_health: ModuleType) -> None:
    with pytest.raises(ValueError, match="Unsupported URL scheme: file"):
        hf_health.fetch_json("file:///etc/passwd")

    with pytest.raises(ValueError, match="Unsupported URL scheme: ftp"):
        hf_health.fetch_json("ftp://example.com/file")

    with pytest.raises(ValueError, match="Unsupported URL scheme: javascript"):
        hf_health.fetch_json("javascript:alert(1)")


def test_fetch_json_rejects_untrusted_hosts(hf_health: ModuleType) -> None:
    with pytest.raises(ValueError, match="Untrusted host: evil.com"):
        hf_health.fetch_json("https://evil.com/api/steal")

    with pytest.raises(ValueError, match="Untrusted host: attacker.org"):
        hf_health.fetch_json("http://attacker.org/test")


def test_main_healthy_portfolio(hf_health: ModuleType) -> None:
    models = [
        {
            "id": f"{hf_health.AUTHOR}/model-1",
            "tags": ["license:apache-2.0"],
            "pipeline_tag": "text-generation",
            "downloads": 100,
            "likes": 5,
        }
    ]
    spaces = [{"id": f"{hf_health.AUTHOR}/space-1", "sdk": "gradio"}]
    collection = {"title": "Test Collection", "items": [{"id": "item-1"}]}

    def mock_fetch(url: str, timeout: int = 30) -> list[dict[str, object]] | dict[str, object]:
        if "api/models" in url:
            return models
        if "api/spaces" in url:
            return spaces
        if "api/collections" in url:
            return collection
        return []

    with patch.object(hf_health, "fetch_json", side_effect=mock_fetch):
        exit_code = hf_health.main()
        assert exit_code == 0


def test_main_with_issues(hf_health: ModuleType) -> None:
    models = [
        {
            "id": f"{hf_health.AUTHOR}/model-missing-tags",
            "tags": [],
            "pipeline_tag": None,
            "downloads": 10,
            "likes": 1,
        }
    ]

    def mock_fetch(url: str, timeout: int = 30) -> list[dict[str, object]] | dict[str, object]:
        if "api/models" in url:
            return models
        return []

    with patch.object(hf_health, "fetch_json", side_effect=mock_fetch):
        exit_code = hf_health.main()
        assert exit_code == 1
