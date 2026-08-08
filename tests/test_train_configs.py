import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root (AGENTS.md convention)

from scripts.train.sft_qlora import dry_run, load_config, repo_id, validate_config  # noqa: E402

BASE = {
    "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
    "output_repo": "Nanthasit/sakthai-context-0.5b-tools-r2",
    "lora_r": 16,
    "lora_alpha": 32,
    "seq_len": 2048,
    "epochs": 3,
    "lr": 0.0002,
    "data_path": "data/v12.jsonl",
    "merge": True,
}


def test_load_config_rejects_unknown_keys(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("base_model: x\nnot_a_key: 1\n")
    with pytest.raises(ValueError, match="not_a_key"):
        load_config(p)


def test_validate_config_requires_all_keys(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("base_model: x\n")
    with pytest.raises(ValueError, match="lora_r"):
        validate_config(load_config(p))


def test_repo_id_must_be_r2_suffixed():
    assert repo_id(BASE) == "Nanthasit/sakthai-context-0.5b-tools-r2"


def test_dry_run_renders_plan_without_importing_trl():
    out = dry_run(BASE)
    assert "Qwen/Qwen2.5-0.5B-Instruct" in out
    assert "lora_r=16" in out
    assert "epochs=3" in out
