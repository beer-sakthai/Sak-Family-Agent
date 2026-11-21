"""The ``train`` command group: discover training runs and launch fine-tuning."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .. import config
from ._runner import run_repo_argv


def _read_title(readme_path: Path) -> str:
    if not readme_path.is_file():
        return ""
    try:
        for line in readme_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("pretty_name:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


@click.group(name="train")
def train_cmd() -> None:
    """Inspect model training runs, prepare datasets, and launch fine-tuning."""


@train_cmd.command("list")
@click.option("--json", "as_json", is_flag=True, help="Emit training runs as JSON.")
def train_list(as_json: bool) -> None:
    """List available model fine-tuning runs and datasets under training/."""
    training_root = config.REPO_ROOT / "training"
    runs: list[dict[str, str]] = []
    if training_root.is_dir():
        for path in sorted(training_root.iterdir()):
            if path.is_dir():
                title = _read_title(path / "README.md")
                runs.append(
                    {
                        "name": path.name,
                        "title": title or "(no title)",
                        "path": f"training/{path.name}",
                    }
                )

    if as_json:
        click.echo(json.dumps(runs, indent=2))
        return

    click.echo("# Model Training Runs & Recipes")
    click.echo(f"  {'RUN/RECIPE':<26} {'DESCRIPTION'}")
    click.echo("  " + "-" * 70)
    for r in runs:
        click.echo(f"  {r['name']:<26} {r['title']}")
    click.echo(
        "\nLaunch fine-tuning with `sakthai train sft` or dataset compilation with `sakthai train dataset`."
    )


_RECIPES = {
    "sft_qlora": "scripts/train/sft_qlora.py",
    "toolcalling": "training/hf-jobs/train_toolcalling_lora.py",
    "persona": "training/hf-jobs/train_persona_lora.py",
    "coder": "training/hf-jobs/train_eval_coder_lora.py",
    "7b": "training/sakthai-7b-lora/train.py",
}


@train_cmd.command("sft", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.option(
    "--recipe",
    type=click.Choice(list(_RECIPES.keys()), case_sensitive=False),
    default="sft_qlora",
    help="Target training recipe to run (default: sft_qlora).",
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def train_sft(dry_run: bool, recipe: str, extra_args: tuple[str, ...]) -> None:
    """Launch SFT QLoRA fine-tuning run using the specified recipe."""
    script = _RECIPES.get(recipe.lower(), "scripts/train/sft_qlora.py")
    argv = ["uv", "run", "python", script] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@train_cmd.command("dataset", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.option(
    "--synthetic-tools",
    is_flag=True,
    help="Build synthetic tool-calling dataset via training/hf-jobs/build_toolcalling_dataset.py.",
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def train_dataset(dry_run: bool, synthetic_tools: bool, extra_args: tuple[str, ...]) -> None:
    """Build and format fine-tuning datasets (v12 corpus or synthetic tool-calling)."""
    script = (
        "training/hf-jobs/build_toolcalling_dataset.py"
        if synthetic_tools
        else "scripts/dataset_prep/build_v12.py"
    )
    argv = ["uv", "run", "python", script] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@train_cmd.command("eval", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def train_eval(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Evaluate tool-calling fidelity on fine-tuned models via training/serving/eval_toolcalling.py."""
    argv = ["uv", "run", "python", "training/serving/eval_toolcalling.py"] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@train_cmd.command("export", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def train_export(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Merge LoRA adapter and export Ollama Modelfile via training/serving/export_ollama.py."""
    argv = ["uv", "run", "python", "training/serving/export_ollama.py"] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@train_cmd.command("deploy", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def train_deploy(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Plan or provision cloud TGI endpoint via training/serving/deploy_hf_endpoint.py."""
    argv = ["uv", "run", "python", "training/serving/deploy_hf_endpoint.py"] + list(extra_args)
    code = run_repo_argv(argv, dry_run=dry_run)
    if code != 0:
        sys.exit(code)
