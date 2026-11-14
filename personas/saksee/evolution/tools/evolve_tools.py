"""Evolve built-in tool descriptions using DSPy + GEPA.

Usage:
    python -m evolution.tools.evolve_tools --iterations 10
    python -m evolution.tools.evolve_tools --eval-source golden --dataset-path datasets/tools/
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import click
import dspy
from rich.console import Console
from rich.table import Table

# Cap max_tokens on every dspy.LM
_orig_lm_init = dspy.LM.__init__


def _capped_lm_init(self, model, *a, **kw):
    kw.setdefault("max_tokens", int(os.getenv("EVO_MAX_TOKENS", "2048")))
    if isinstance(model, str) and model.startswith(("ollama/", "ollama_chat/")):
        kw.setdefault("api_base", os.getenv("OLLAMA_API_BASE", "http://localhost:11434"))
        kw.setdefault("keep_alive", os.getenv("OLLAMA_KEEP_ALIVE", "30m"))
        kw.setdefault("num_ctx", int(os.getenv("EVO_NUM_CTX", "4096")))
    return _orig_lm_init(self, model, *a, **kw)


dspy.LM.__init__ = _capped_lm_init

from evolution.core.config import (
    _DEFAULT_LOCAL_MODEL,
    EvolutionConfig,
    resolve_hermes_agent_path,
)
from evolution.core.constraints import ConstraintValidator
from evolution.core.dataset_builder import (
    EvalDataset,
    GoldenDatasetLoader,
    ToolSelectionDatasetBuilder,
)
from evolution.core.fitness import tool_selection_metric
from evolution.tools.tool_module import (
    ToolSelectionModule,
    format_baseline_descriptions,
    parse_evolved_descriptions,
)

console = Console()


def evolve_tools(
    iterations: int = 10,
    eval_source: str = "synthetic",
    dataset_path: str | None = None,
    optimizer_model: str = _DEFAULT_LOCAL_MODEL,
    eval_model: str = _DEFAULT_LOCAL_MODEL,
    hermes_repo: str | None = None,
    dry_run: bool = False,
):
    """Main tool description evolution orchestration function."""
    config = EvolutionConfig(
        hermes_agent_path=resolve_hermes_agent_path(hermes_repo),
        iterations=iterations,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        judge_model=eval_model,
    )

    console.print(
        "\n[bold cyan]🧬 Hermes Agent Self-Evolution[/bold cyan] — Evolving Tool Descriptions\n"
    )

    # Make sure we can find/import BUILTIN_TOOLS from the canonical path
    hermes_path = config.hermes_agent_path
    if not hermes_path:
        console.print("[red]✗ hermes-agent repository path not resolved.[/red]")
        sys.exit(1)

    # Insert package directory into sys.path to load BUILTIN_TOOLS
    package_dir = str(hermes_path / "personas" / "sakthai")
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)

    try:
        from sakthai.agent.tools import BUILTIN_TOOLS
    except ImportError as e:
        console.print(f"[red]✗ Failed to load BUILTIN_TOOLS from {package_dir}: {e}[/red]")
        sys.exit(1)

    console.print(f"  Loaded {len(BUILTIN_TOOLS)} built-in tools from sakthai package.")

    # 1. Format baseline descriptions
    baseline_text = format_baseline_descriptions(list(BUILTIN_TOOLS))
    console.print(f"  Baseline formatting: {len(baseline_text):,} chars")

    if dry_run:
        console.print("\n[bold green]DRY RUN — setup validated successfully.[/bold green]")
        console.print(f"  Would generate tool selection dataset (source: {eval_source})")
        console.print(f"  Would run GEPA optimization ({iterations} iterations)")
        return

    # 2. Build or load evaluation dataset
    console.print(f"\n[bold]Building evaluation dataset[/bold] (source: {eval_source})")

    if eval_source == "golden" and dataset_path:
        dataset = GoldenDatasetLoader.load(Path(dataset_path))
        console.print(f"  Loaded golden dataset: {len(dataset.all_examples)} examples")
    elif eval_source == "synthetic":
        # Package tools into schemas
        tool_schemas = [tool.schema() for tool in BUILTIN_TOOLS]
        builder = ToolSelectionDatasetBuilder(config)
        dataset = builder.generate(tool_schemas)

        save_path = Path("datasets") / "tools" / "tool_selection"
        dataset.save(save_path)
        console.print(f"  Generated {len(dataset.all_examples)} synthetic tool selection examples")
        console.print(f"  Saved to {save_path}/")
    elif dataset_path:
        dataset = EvalDataset.load(Path(dataset_path))
        console.print(f"  Loaded dataset: {len(dataset.all_examples)} examples")
    else:
        console.print("[red]✗ Specify --dataset-path or use --eval-source synthetic[/red]")
        sys.exit(1)

    console.print(
        f"  Split: {len(dataset.train)} train / {len(dataset.val)} val / {len(dataset.holdout)} holdout"
    )

    # 3. Validate baseline constraints
    console.print("\n[bold]Validating baseline constraints[/bold]")
    validator = ConstraintValidator(config)
    baseline_constraints = validator.validate_all(baseline_text, "tool_descriptions")
    all_pass = True
    for c in baseline_constraints:
        icon = "✓" if c.passed else "✗"
        color = "green" if c.passed else "red"
        console.print(f"  [{color}]{icon} {c.constraint_name}[/{color}]: {c.message}")
        if not c.passed:
            all_pass = False

    if not all_pass:
        console.print(
            "[yellow]⚠ Baseline descriptions have constraint violations — proceeding anyway[/yellow]"
        )

    # 4. Set up DSPy + GEPA optimizer
    console.print("\n[bold]Configuring optimizer[/bold]")
    console.print(f"  Optimizer: GEPA ({iterations} iterations)")
    console.print(f"  Optimizer model: {optimizer_model}")
    console.print(f"  Eval model: {eval_model}")

    lm = dspy.LM(eval_model)
    dspy.configure(lm=lm)

    # Create baseline tool selection module
    baseline_module = ToolSelectionModule(baseline_text)

    # Prepare DSPy examples
    trainset = dataset.to_dspy_examples("train")
    valset = dataset.to_dspy_examples("val")

    # 5. Run GEPA optimization
    console.print(
        f"\n[bold cyan]Running GEPA optimization ({iterations} iterations)...[/bold cyan]\n"
    )

    start_time = time.time()

    def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        score = tool_selection_metric(gold, pred, trace)
        if score >= 0.8:
            fb = f"Score {score:.2f}: predicted correct tool and parameters."
        else:
            fb = (
                f"Score {score:.2f}: predicted wrong tool/arguments. Review the "
                "tool descriptions to make their distinctions, capabilities, and "
                "parameter requirements extremely clear and unambiguous."
            )
        return dspy.Prediction(score=score, feedback=fb)

    try:
        reflection_lm = dspy.LM(optimizer_model)
        optimizer = dspy.GEPA(
            metric=gepa_metric,
            reflection_lm=reflection_lm,
            max_metric_calls=max(4, iterations * 2),
            reflection_minibatch_size=2,
        )
        optimized_module = optimizer.compile(
            baseline_module,
            trainset=trainset,
            valset=valset,
        )
    except Exception as e:
        console.print(f"[yellow]GEPA unavailable ({e}); falling back to MIPROv2[/yellow]")
        optimizer = dspy.MIPROv2(
            metric=tool_selection_metric,
            auto="light",
        )
        optimized_module = optimizer.compile(
            baseline_module,
            trainset=trainset,
        )

    elapsed = time.time() - start_time
    console.print(f"\n  Optimization completed in {elapsed:.1f}s")

    # 6. Extract evolved descriptions
    evolved_text = optimized_module.formatted_descriptions

    # 7. Validate evolved descriptions
    console.print("\n[bold]Validating evolved tool descriptions[/bold]")
    evolved_constraints = validator.validate_all(evolved_text, "tool_descriptions")
    all_pass = True
    for c in evolved_constraints:
        icon = "✓" if c.passed else "✗"
        color = "green" if c.passed else "red"
        console.print(f"  [{color}]{icon} {c.constraint_name}[/{color}]: {c.message}")
        if not c.passed:
            all_pass = False

    if not all_pass:
        console.print("[red]✗ Evolved tool descriptions FAILED constraints — not deploying[/red]")
        output_path = Path("output") / "tools" / "evolved_FAILED.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(evolved_text)
        console.print(f"  Saved failed variant to {output_path}")
        return

    # Parse overrides
    overrides = parse_evolved_descriptions(evolved_text)
    console.print(f"  Parsed {len(overrides)} evolved tool overrides.")

    # 8. Evaluate on holdout set
    console.print(f"\n[bold]Evaluating on holdout set ({len(dataset.holdout)} examples)[/bold]")
    holdout_examples = dataset.to_dspy_examples("holdout")

    baseline_scores = []
    evolved_scores = []
    for ex in holdout_examples:
        with dspy.context(lm=lm):
            baseline_pred = baseline_module(task_input=ex.task_input)
            baseline_score = tool_selection_metric(ex, baseline_pred)
            baseline_scores.append(baseline_score)

            evolved_pred = optimized_module(task_input=ex.task_input)
            evolved_score = tool_selection_metric(ex, evolved_pred)
            evolved_scores.append(evolved_score)

    avg_baseline = sum(baseline_scores) / max(1, len(baseline_scores))
    avg_evolved = sum(evolved_scores) / max(1, len(evolved_scores))
    improvement = avg_evolved - avg_baseline

    # 9. Report results
    table = Table(title="Tool Evolution Results")
    table.add_column("Metric", style="bold")
    table.add_column("Baseline", justify="right")
    table.add_column("Evolved", justify="right")
    table.add_column("Change", justify="right")

    change_color = "green" if improvement > 0 else "red"
    table.add_row(
        "Holdout Accuracy",
        f"{avg_baseline:.3f}",
        f"{avg_evolved:.3f}",
        f"[{change_color}]{improvement:+.3f}[/{change_color}]",
    )
    table.add_row("Time", "", f"{elapsed:.1f}s", "")
    table.add_row("Iterations", "", str(iterations), "")

    console.print()
    console.print(table)

    # 10. Save output overrides JSON and text
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / "tools" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save descriptions txt files
    (output_dir / "baseline_descriptions.txt").write_text(baseline_text)
    (output_dir / "evolved_descriptions.txt").write_text(evolved_text)

    # Save JSON overrides config
    overrides_path = output_dir / "tool_descriptions.json"
    with open(overrides_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, indent=2)

    # Save metrics
    metrics = {
        "timestamp": timestamp,
        "iterations": iterations,
        "optimizer_model": optimizer_model,
        "eval_model": eval_model,
        "baseline_score": avg_baseline,
        "evolved_score": avg_evolved,
        "improvement": improvement,
        "train_examples": len(dataset.train),
        "val_examples": len(dataset.val),
        "holdout_examples": len(dataset.holdout),
        "elapsed_seconds": elapsed,
        "constraints_passed": all_pass,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    console.print(f"\n  Output files saved to {output_dir}/")

    if improvement > 0:
        console.print(
            f"\n[bold green]✓ Evolution improved selection accuracy by {improvement:+.3f} ({improvement / max(0.001, avg_baseline) * 100:+.1f}%)[/bold green]"
        )
        console.print(f"  Overrides JSON: {overrides_path}")
    else:
        console.print(
            f"\n[yellow]⚠ Evolution did not improve tool selection (change: {improvement:+.3f})[/yellow]"
        )


@click.command()
@click.option("--iterations", default=10, help="Number of GEPA iterations")
@click.option(
    "--eval-source",
    default="synthetic",
    type=click.Choice(["synthetic", "golden"]),
    help="Source for evaluation dataset",
)
@click.option("--dataset-path", default=None, help="Path to existing eval dataset (JSONL)")
@click.option(
    "--optimizer-model",
    default=lambda: os.getenv("EVO_OPTIMIZER_MODEL", _DEFAULT_LOCAL_MODEL),
    help="LiteLLM model for GEPA reflections",
)
@click.option(
    "--eval-model",
    default=lambda: os.getenv("EVO_EVAL_MODEL", _DEFAULT_LOCAL_MODEL),
    help="LiteLLM model for evaluations",
)
@click.option("--hermes-repo", default=None, help="Path to hermes-agent repo")
@click.option("--dry-run", is_flag=True, help="Validate setup without running optimization")
def main(
    iterations,
    eval_source,
    dataset_path,
    optimizer_model,
    eval_model,
    hermes_repo,
    dry_run,
):
    """Evolve tool descriptions using DSPy + GEPA optimization."""
    evolve_tools(
        iterations=iterations,
        eval_source=eval_source,
        dataset_path=dataset_path,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        hermes_repo=hermes_repo,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    main()
