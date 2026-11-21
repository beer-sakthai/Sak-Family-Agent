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


def test_train_sft_recipe_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(
        main, ["train", "sft", "--recipe", "toolcalling", "--dry-run", "--", "--epochs", "4"]
    )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "training/hf-jobs/train_toolcalling_lora.py" in result.output
    assert "--epochs 4" in result.output


def test_train_dataset_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "dataset", "--dry-run", "--", "--limit", "100"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/dataset_prep/build_v12.py" in result.output
    assert "--limit 100" in result.output


def test_train_dataset_synthetic_tools_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "dataset", "--synthetic-tools", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "training/hf-jobs/build_toolcalling_dataset.py" in result.output


def test_train_eval_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "eval", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "training/serving/eval_toolcalling.py" in result.output


def test_train_export_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "export", "--dry-run", "--", "--out", "./test-out"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "training/serving/export_ollama.py" in result.output
    assert "--out ./test-out" in result.output


def test_train_deploy_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["train", "deploy", "--dry-run", "--", "--repo", "test/repo"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "training/serving/deploy_hf_endpoint.py" in result.output
    assert "--repo test/repo" in result.output


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
    assert runner.invoke(main, ["train", "eval"]).exit_code == 11
    assert runner.invoke(main, ["train", "export"]).exit_code == 11
    assert runner.invoke(main, ["train", "deploy"]).exit_code == 11


def test_resolve_openenv_root_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Explicit SAKTHAI_OPENENV_ROOT override
    explicit_dir = tmp_path / "custom-openenv"
    explicit_dir.mkdir()
    monkeypatch.setenv("SAKTHAI_OPENENV_ROOT", str(explicit_dir))
    assert train_mod.config.resolve_openenv_root() == explicit_dir.resolve()

    # 2. Sibling checkout discovery
    monkeypatch.delenv("SAKTHAI_OPENENV_ROOT", raising=False)
    fake_parent = tmp_path / "workspace"
    fake_repo = fake_parent / "Sak-Family-Agent"
    fake_sibling = fake_parent / "openenv-rl-training"
    fake_repo.mkdir(parents=True)
    fake_sibling.mkdir(parents=True)
    monkeypatch.setattr(train_mod.config, "REPO_ROOT", fake_repo)
    assert train_mod.config.resolve_openenv_root() == fake_sibling.resolve()

    # 3. Fallback when no directory exists
    fake_sibling.rmdir()
    assert train_mod.config.resolve_openenv_root() == fake_sibling.resolve()


def _create_fake_openenv_root(base: Path) -> Path:
    root = base / "openenv-rl-training"
    for ws in train_mod.OPENENV_WORKSPACES:
        (root / ws).mkdir(parents=True, exist_ok=True)
    (root / "verify_grpo_contract.py").write_text("# contract")
    (root / "test_browsergym_contract.py").write_text("# test")
    (root / "openenv-custom-training" / "evaluate_baselines.py").write_text("# baselines")
    (root / "openenv-custom-training" / "train.py").write_text("# train")
    (root / "openenv-multi-catalog-training" / "train_multi_env.py").write_text("# multi")
    (root / "openenv-multi-catalog-training" / "a2a_agent").mkdir(parents=True, exist_ok=True)
    (root / "openenv-multi-catalog-training" / "a2a_agent" / "server.py").write_text("# a2a")
    (root / "sakthai-agentic-eval-train" / "scripts").mkdir(parents=True, exist_ok=True)
    (
        root / "sakthai-agentic-eval-train" / "scripts" / "benchmark_evaluation_manager_agent.py"
    ).write_text("# bench")
    return root


def test_openenv_status_text_and_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    root = _create_fake_openenv_root(tmp_path)
    monkeypatch.setenv("SAKTHAI_OPENENV_ROOT", str(root))

    res_text = runner.invoke(main, ["train", "openenv", "status"])
    assert res_text.exit_code == 0
    assert "OpenEnv RL Training Ecosystem Status" in res_text.output
    assert "READY" in res_text.output
    assert "openenv-custom-training" in res_text.output

    res_json = runner.invoke(main, ["train", "openenv", "status", "--json"])
    assert res_json.exit_code == 0
    payload = json.loads(res_json.output)
    assert payload["exists"] is True
    assert payload["ready"] is True
    assert len(payload["workspaces"]) == 5


def test_openenv_missing_root_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    missing_dir = tmp_path / "missing-openenv"
    monkeypatch.setenv("SAKTHAI_OPENENV_ROOT", str(missing_dir))

    res = runner.invoke(main, ["train", "openenv", "verify"])
    assert res.exit_code != 0
    assert "openenv-rl-training workspace not found" in res.output


def test_openenv_subcommands_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    root = _create_fake_openenv_root(tmp_path)
    monkeypatch.setenv("SAKTHAI_OPENENV_ROOT", str(root))

    res_verify = runner.invoke(main, ["train", "openenv", "verify", "--dry-run"])
    assert res_verify.exit_code == 0
    assert "verify_grpo_contract.py" in res_verify.output

    res_test = runner.invoke(
        main, ["train", "openenv", "test", "--workspace", "custom", "--dry-run", "--", "-v"]
    )
    assert res_test.exit_code == 0
    assert "openenv-custom-training/tests/" in res_test.output
    assert "-v" in res_test.output

    res_base = runner.invoke(main, ["train", "openenv", "baselines", "--dry-run"])
    assert res_base.exit_code == 0
    assert "openenv-custom-training/evaluate_baselines.py" in res_base.output

    res_bench = runner.invoke(main, ["train", "openenv", "benchmark", "--json", "--dry-run"])
    assert res_bench.exit_code == 0
    assert "benchmark_evaluation_manager_agent.py" in res_bench.output
    assert "--json" in res_bench.output

    for env_choice, expected in (
        ("mcp", "openenv-custom-training/train.py --env mcp"),
        ("multi", "openenv-custom-training/multi_env.py"),
        ("catalog", "openenv-multi-catalog-training/train_multi_env.py"),
    ):
        res_grpo = runner.invoke(
            main, ["train", "openenv", "grpo", "--env", env_choice, "--dry-run"]
        )
        assert res_grpo.exit_code == 0
        assert expected in res_grpo.output

    res_a2a = runner.invoke(main, ["train", "openenv", "a2a", "--port", "9005", "--dry-run"])
    assert res_a2a.exit_code == 0
    assert "openenv-multi-catalog-training/a2a_agent/server.py" in res_a2a.output
    assert "9005" in res_a2a.output


def test_openenv_exit_code_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    root = _create_fake_openenv_root(tmp_path)
    monkeypatch.setenv("SAKTHAI_OPENENV_ROOT", str(root))
    monkeypatch.setattr(train_mod, "run_repo_argv", lambda argv, **kw: 17)

    assert runner.invoke(main, ["train", "openenv", "verify"]).exit_code == 17
    assert runner.invoke(main, ["train", "openenv", "test"]).exit_code == 17
    assert runner.invoke(main, ["train", "openenv", "baselines"]).exit_code == 17
    assert runner.invoke(main, ["train", "openenv", "benchmark"]).exit_code == 17
    assert runner.invoke(main, ["train", "openenv", "grpo"]).exit_code == 17
    assert runner.invoke(main, ["train", "openenv", "a2a"]).exit_code == 17
