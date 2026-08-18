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


def test_hub_missing_dependency_raises_click_exception(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_hf_download_targets_sakthai_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    with patch("sakthai.cli.hf.hf_download", return_value="/tmp/cache/org/model") as mock_dl:
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
        model_info=lambda repo_id: SimpleNamespace(id=repo_id, downloads=0, likes=0, tags=None)
    )
    with patch("sakthai.hf._hub", return_value=fake):
        out = hf_info("org/model")
    assert "tags:      " in out
    assert "tags:      ," not in out


def test_hf_download_blocks_path_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that hf_download raises ValueError when repo_id contains path traversal."""
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))

    # A repo_id that tries to escape ~/.sakthai/hf
    with pytest.raises(ValueError, match="path traversal detected"):
        hf_download("../../etc/passwd")

    # Another one trying to target the root
    with pytest.raises(ValueError, match="path traversal detected"):
        hf_download("/etc/passwd")


def _load_workbench_get_hf_token(filepath: str) -> Any:
    import ast

    with open(filepath) as f:
        tree = ast.parse(f.read())
    import_nodes = [n for n in tree.body if isinstance(n, ast.Import)]
    func_node = [
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_get_hf_token"
    ][0]
    module_node = ast.Module(body=import_nodes + [func_node], type_ignores=[])
    code = compile(module_node, filename=filepath, mode="exec")
    ns: dict[str, Any] = {}
    exec(code, ns)
    return ns["_get_hf_token"]


@pytest.mark.parametrize(
    "script_path",
    [
        "scripts/workbench/workbench-1.5b-api.py",
        "sakthai-chat-cli/scripts/workbench/workbench-1.5b-api.py",
    ],
)
def test_workbench_get_hf_token_resolution(
    script_path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    get_token = _load_workbench_get_hf_token(script_path)

    # 1. HF_TOKEN env var
    monkeypatch.setenv("HF_TOKEN", "token_from_hf_token_env")
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    monkeypatch.delenv("HF_TOKEN_PATH", raising=False)
    assert get_token() == "token_from_hf_token_env"

    # 2. HUGGING_FACE_HUB_TOKEN env var
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "token_from_hf_hub_token_env")
    assert get_token() == "token_from_hf_hub_token_env"

    # 3. HF_TOKEN_PATH env var
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    custom_token_file = tmp_path / "custom_token"
    custom_token_file.write_text("token_from_custom_path")
    monkeypatch.setenv("HF_TOKEN_PATH", str(custom_token_file))
    assert get_token() == "token_from_custom_path"

    # 4. ~/.cache/huggingface/token default path
    monkeypatch.delenv("HF_TOKEN_PATH", raising=False)
    fake_home = tmp_path / "home"
    hf_cache_dir = fake_home / ".cache" / "huggingface"
    hf_cache_dir.mkdir(parents=True)
    default_token_file = hf_cache_dir / "token"
    default_token_file.write_text("token_from_default_home_path")
    monkeypatch.setenv("HOME", str(fake_home))
    assert get_token() == "token_from_default_home_path"

    # 5. No token anywhere
    default_token_file.unlink()
    assert get_token() is None
