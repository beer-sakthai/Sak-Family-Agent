"""QLoRA SFT launcher for the sakthai-context retrain round.

Heavy ML imports (trl/transformers/peft) are lazy: this module imports and
tests with only the stdlib + pyyaml.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

CONFIG_KEYS = {
    "base_model",
    "output_repo",
    "lora_r",
    "lora_alpha",
    "seq_len",
    "epochs",
    "lr",
    "data_path",
    "merge",
}
REQUIRED_KEYS = CONFIG_KEYS


def load_config(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text())
    unknown = set(cfg) - CONFIG_KEYS
    if unknown:
        raise ValueError(f"unknown config keys: {', '.join(sorted(unknown))}")
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise ValueError("missing config keys: " + ", ".join(sorted(missing)))


def repo_id(cfg: dict) -> str:
    if not cfg["output_repo"].endswith("-r2"):
        raise ValueError("output_repo must use the -r2 suffix")
    return cfg["output_repo"]


def dry_run(cfg: dict) -> str:
    repo_id(cfg)
    return (
        f"plan: base={cfg['base_model']} data={cfg['data_path']} "
        f"epochs={cfg['epochs']} lora_r={cfg['lora_r']} seq_len={cfg['seq_len']} "
        f"-> {cfg['output_repo']}"
    )


def train(cfg: dict) -> None:
    try:
        import peft  # noqa: F401
        import transformers  # noqa: F401
        import trl  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("trl/transformers not installed; install the training extra") from exc
    raise NotImplementedError("run-time training dispatch: see the retrain round runbook")


def main() -> None:
    parser = argparse.ArgumentParser(description="SakThai QLoRA SFT launcher")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="validate config, no training")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.dry_run:
        print(dry_run(cfg))
        return
    train(cfg)


if __name__ == "__main__":
    main()
