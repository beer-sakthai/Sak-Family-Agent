"""Tests for `sakthai train` commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import sakthai.cli.train as train_mod
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_train_list_text_and_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "list"])
    assert result.exit_code == 0
    assert "Model Training Runs & Recipes" in result.output
    assert "sakthai-1.5b-lora" in result.output

    result_json = runner.invoke(main, ["train", "list", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.output)
    assert isinstance(data, list)
    assert any(item["name"] == "sakthai-1.5b-lora" for item in data)


def test_train_read_title_helper(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# My Awesome Recipe\nDetails here")
    assert train_mod._read_title(readme) == "My Awesome Recipe"

    meta_readme = tmp_path / "meta.md"
    meta_readme.write_text("---\npretty_name: Sample Dataset Name\n---\n")
    assert train_mod._read_title(meta_readme) == "Sample Dataset Name"

    assert train_mod._read_title(tmp_path / "missing.md") == ""


def test_train_sft_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "sft", "--dry-run", "--", "--epochs", "3"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/train/sft_qlora.py" in result.output
    assert "--epochs 3" in result.output


def test_train_dataset_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "dataset", "--dry-run", "--", "--limit", "100"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/dataset_prep/build_v12.py" in result.output
    assert "--limit 100" in result.output


def test_train_read_title_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# title")
    monkeypatch.setattr(
        Path, "read_text", lambda self, *a, **kw: (_ for _ in ()).throw(OSError("boom"))
    )
    assert train_mod._read_title(readme) == ""


def test_train_list_empty_or_missing_root(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, tmp_path: Path
) -> None:
    monkeypatch.setattr(train_mod.config, "REPO_ROOT", tmp_path)
    res = runner.invoke(main, ["train", "list"])
    assert res.exit_code == 0


def test_train_exit_code_propagation(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setattr(train_mod, "run_repo_argv", lambda argv, **kw: 11)
    assert runner.invoke(main, ["train", "sft"]).exit_code == 11
    assert runner.invoke(main, ["train", "dataset"]).exit_code == 11
