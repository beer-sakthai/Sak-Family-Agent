"""Tests for the Hugging Face CLI command group and helper functions."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.hf import _hub, hf_download, hf_info

if TYPE_CHECKING:
    from pathlib import Path


def test_hub_missing_dependency_raises_click_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A None entry in sys.modules makes `import huggingface_hub` raise ImportError.
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)
    with pytest.raises(click.ClickException, match="huggingface_hub is not installed"):
        _hub()


def test_hub_returns_module_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """_hub() must return the huggingface_hub module when the import succeeds."""
    import types as _t

    fake_module = _t.ModuleType("huggingface_hub")
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)
    result = _hub()
    assert result is fake_module


def test_hf_info_formats_model_fields() -> None:
    fake = SimpleNamespace(
        model_info=lambda repo_id: SimpleNamespace(
            id=repo_id, downloads=42, likes=7, tags=["pytorch", "llm"]
        )
    )
    with patch("sakthai.hf._hub", return_value=fake):
        out = hf_info("org/model")
    assert "id:        org/model" in out
    assert "downloads: 42" in out
    assert "likes:     7" in out
    assert "tags:      pytorch, llm" in out


def test_hf_download_targets_sakthai_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    captured: dict[str, Any] = {}

    def snapshot_download(repo_id: str, local_dir: str) -> str:
        captured["repo_id"] = repo_id
        captured["local_dir"] = local_dir
        return local_dir

    fake = SimpleNamespace(snapshot_download=snapshot_download)
    with patch("sakthai.hf._hub", return_value=fake):
        result = hf_download("org/model")

    assert captured["repo_id"] == "org/model"
    assert captured["local_dir"] == str(tmp_path / "hf" / "org/model")
    assert result == captured["local_dir"]


def test_cli_hf_info_command() -> None:
    with patch("sakthai.cli.hf.hf_info", return_value="id: org/model") as mock_info:
        r = CliRunner().invoke(main, ["hf", "info", "org/model"])
    assert r.exit_code == 0
    assert "id: org/model" in r.output
    mock_info.assert_called_once_with("org/model")


def test_cli_hf_download_command() -> None:
    with patch(
        "sakthai.cli.hf.hf_download", return_value="/tmp/cache/org/model"
    ) as mock_dl:
        r = CliRunner().invoke(main, ["hf", "download", "org/model"])
    assert r.exit_code == 0
    assert "/tmp/cache/org/model" in r.output
    mock_dl.assert_called_once_with("org/model")


def test_cli_hf_missing_dependency_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)
    r = CliRunner().invoke(main, ["hf", "info", "org/model"])
    assert r.exit_code != 0
    assert "huggingface_hub is not installed" in r.output


def test_hf_info_raises_exception_on_error() -> None:
    """Verify that hf_info propagates exceptions from the hub."""

    def mock_model_info(repo_id: str) -> Any:
        raise RuntimeError("API Error")

    fake = SimpleNamespace(model_info=mock_model_info)

    with (
        patch("sakthai.hf._hub", return_value=fake),
        pytest.raises(RuntimeError, match="API Error"),
    ):
        hf_info("org/model")


def test_hf_download_raises_exception_on_error() -> None:
    """Verify that hf_download propagates exceptions from the hub."""

    def mock_snapshot_download(repo_id: str, local_dir: str) -> Any:
        raise RuntimeError("Download failed")

    fake = SimpleNamespace(snapshot_download=mock_snapshot_download)

    with (
        patch("sakthai.hf._hub", return_value=fake),
        pytest.raises(RuntimeError, match="Download failed"),
    ):
        hf_download("org/model")


def test_hf_info_handles_missing_tags() -> None:
    """Verify that hf_info handles None tags gracefully."""
    fake = SimpleNamespace(
        model_info=lambda repo_id: SimpleNamespace(
            id=repo_id, downloads=0, likes=0, tags=None
        )
    )
    with patch("sakthai.hf._hub", return_value=fake):
        out = hf_info("org/model")
    assert "tags:      " in out
    assert "tags:      ," not in out
