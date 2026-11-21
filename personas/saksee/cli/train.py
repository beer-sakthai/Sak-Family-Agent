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


OPENENV_WORKSPACES: dict[str, str] = {
    "sakthai-sft-training": "SFT QLoRA trainers, 10-cycle augmentation, and data governance",
    "openenv-custom-training": "Custom OpenEnv environments (Simple, MCP, Sandbox, BrowserGym) & GRPO",
    "openenv-multi-catalog-training": "8 OpenEnv catalog environments & A2A protocol server",
    "sakthai-agentic-eval-train": "Agentic evaluation harness, PEFT benchmark runner, and FINDINGS.md",
    "browsergym-space": "BrowserGym OpenEnv server Dockerfile & Space configuration",
}

OPENENV_TEST_TARGETS: dict[str, tuple[str, ...]] = {
    "all": (
        "test_browsergym_contract.py",
        "sakthai-agentic-eval-train/tests/",
        "openenv-custom-training/tests/",
        "openenv-multi-catalog-training/tests/",
        "sakthai-sft-training/tests/",
    ),
    "contract": ("test_browsergym_contract.py",),
    "agentic": ("sakthai-agentic-eval-train/tests/",),
    "custom": ("openenv-custom-training/tests/",),
    "catalog": ("openenv-multi-catalog-training/tests/",),
    "sft": ("sakthai-sft-training/tests/",),
}


def _require_openenv_root(dry_run: bool = False) -> Path:
    """Resolve and validate the openenv-rl-training repository root."""
    root = config.resolve_openenv_root()
    if not dry_run and not root.is_dir():
        raise click.ClickException(
            f"openenv-rl-training workspace not found at {root}. "
            "Clone beer-sakthai/openenv-rl-training alongside Sak-Family-Agent "
            "or set SAKTHAI_OPENENV_ROOT."
        )
    return root


def get_openenv_status() -> dict[str, object]:
    """Build a structured readiness report for the openenv-rl-training ecosystem repo."""
    root = config.resolve_openenv_root()
    exists = root.is_dir()
    workspaces: list[dict[str, object]] = []
    for ws_name, desc in OPENENV_WORKSPACES.items():
        ws_dir = root / ws_name
        workspaces.append(
            {
                "name": ws_name,
                "description": desc,
                "present": ws_dir.is_dir(),
            }
        )
    entrypoints = {
        "verify_grpo_contract": (root / "verify_grpo_contract.py").is_file(),
        "test_browsergym_contract": (root / "test_browsergym_contract.py").is_file(),
        "evaluate_baselines": (
            root / "openenv-custom-training" / "evaluate_baselines.py"
        ).is_file(),
        "benchmark_eval_manager": (
            root
            / "sakthai-agentic-eval-train"
            / "scripts"
            / "benchmark_evaluation_manager_agent.py"
        ).is_file(),
        "custom_grpo_train": (root / "openenv-custom-training" / "train.py").is_file(),
        "multi_catalog_train": (
            root / "openenv-multi-catalog-training" / "train_multi_env.py"
        ).is_file(),
        "a2a_server": (
            root / "openenv-multi-catalog-training" / "a2a_agent" / "server.py"
        ).is_file(),
    }
    ready = exists and all(bool(w["present"]) for w in workspaces) and all(entrypoints.values())
    return {
        "root": str(root),
        "exists": exists,
        "ready": ready,
        "workspaces": workspaces,
        "entrypoints": entrypoints,
    }


@train_cmd.group("openenv")
def openenv_cmd() -> None:
    """Run OpenEnv RL (GRPO) training, contract checks, baselines, and tests."""


@openenv_cmd.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit ecosystem status as JSON.")
def openenv_status(as_json: bool) -> None:
    """Inspect openenv-rl-training workspace discovery and readiness."""
    report = get_openenv_status()
    if as_json:
        click.echo(json.dumps(report, indent=2))
        return

    click.echo("# OpenEnv RL Training Ecosystem Status")
    click.echo(f"  Root Path : {report['root']}")
    click.echo(f"  Present   : {'yes' if report['exists'] else 'no'}")
    click.echo(f"  Ready     : {'READY' if report['ready'] else 'INCOMPLETE'}")
    click.echo("\n  Workspaces:")
    workspaces = report["workspaces"]
    if isinstance(workspaces, list):
        for ws in workspaces:
            if isinstance(ws, dict):
                mark = "OK" if ws.get("present") else "MISSING"
                click.echo(
                    f"    [{mark:<7}] {str(ws.get('name', '')):<32} {ws.get('description', '')}"
                )


@openenv_cmd.command("verify", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_verify(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Run CPU-only OpenEnv RL environment_factory contract verification."""
    root = _require_openenv_root(dry_run=dry_run)
    argv = [
        "uv",
        "run",
        "--with",
        "datasets",
        "python3",
        "verify_grpo_contract.py",
        *extra_args,
    ]
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@openenv_cmd.command("test", context_settings={"ignore_unknown_options": True})
@click.option(
    "--workspace",
    type=click.Choice(list(OPENENV_TEST_TARGETS.keys()), case_sensitive=False),
    default="all",
    help="Target workspace test suite to execute (default: all 149 tests in one invocation).",
)
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_test(workspace: str, dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Execute openenv-rl-training pytest suites with isolated CPU stubs."""
    root = _require_openenv_root(dry_run=dry_run)
    targets = OPENENV_TEST_TARGETS[workspace.lower()]
    argv = [
        "uv",
        "run",
        "--with",
        "datasets",
        "--with",
        "pytest",
        "--with",
        "pydantic",
        "--with",
        "httpx",
        "--with",
        "anyio",
        "pytest",
        *targets,
        *extra_args,
    ]
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@openenv_cmd.command("baselines", context_settings={"ignore_unknown_options": True})
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_baselines(dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Run CPU heuristic baseline policy competition and GRPO reward-variance checks."""
    root = _require_openenv_root(dry_run=dry_run)
    argv = [
        "uv",
        "run",
        "--with",
        "datasets",
        "--with",
        "pydantic",
        "python3",
        "openenv-custom-training/evaluate_baselines.py",
        *extra_args,
    ]
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@openenv_cmd.command("benchmark", context_settings={"ignore_unknown_options": True})
@click.option("--json", "as_json", is_flag=True, help="Emit evaluation manager benchmark as JSON.")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_benchmark(as_json: bool, dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Run the deterministic Evaluation Manager Agent rubric benchmark."""
    root = _require_openenv_root(dry_run=dry_run)
    argv = [
        "python3",
        "sakthai-agentic-eval-train/scripts/benchmark_evaluation_manager_agent.py",
    ]
    if as_json:
        argv.append("--json")
    argv.extend(extra_args)
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


_GRPO_ENVS = ("simple", "mcp", "agent_tools", "browsergym", "multi", "catalog")


@openenv_cmd.command("grpo", context_settings={"ignore_unknown_options": True})
@click.option(
    "--env",
    "env_name",
    type=click.Choice(list(_GRPO_ENVS), case_sensitive=False),
    default="mcp",
    help="Target OpenEnv RL environment or multi-env runner (default: mcp).",
)
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_grpo(env_name: str, dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Launch GRPO training across OpenEnv custom or catalog environments."""
    root = _require_openenv_root(dry_run=dry_run)
    choice = env_name.lower()
    if choice == "multi":
        argv = ["uv", "run", "python3", "openenv-custom-training/multi_env.py", *extra_args]
    elif choice == "catalog":
        argv = [
            "uv",
            "run",
            "python3",
            "openenv-multi-catalog-training/train_multi_env.py",
            *extra_args,
        ]
    else:
        argv = [
            "uv",
            "run",
            "python3",
            "openenv-custom-training/train.py",
            "--env",
            choice,
            *extra_args,
        ]
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)


@openenv_cmd.command("a2a", context_settings={"ignore_unknown_options": True})
@click.option("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1).")
@click.option("--port", type=int, default=9000, help="Port to listen on (default: 9000).")
@click.option("--dry-run", is_flag=True, help="Print command without executing.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def openenv_a2a(host: str, port: int, dry_run: bool, extra_args: tuple[str, ...]) -> None:
    """Launch the OpenEnv 8-catalog A2A protocol server."""
    root = _require_openenv_root(dry_run=dry_run)
    argv = [
        "uv",
        "run",
        "python3",
        "openenv-multi-catalog-training/a2a_agent/server.py",
        "--host",
        host,
        "--port",
        str(port),
        *extra_args,
    ]
    code = run_repo_argv(argv, cwd=root, dry_run=dry_run)
    if code != 0:
        sys.exit(code)
