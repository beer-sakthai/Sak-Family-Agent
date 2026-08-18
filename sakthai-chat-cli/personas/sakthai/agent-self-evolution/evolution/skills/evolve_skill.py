"""Evolve a Hermes Agent skill using DSPy + GEPA.

Usage:
    python -m evolution.skills.evolve_skill --skill github-code-review --iterations 10
    python -m evolution.skills.evolve_skill --skill arxiv --eval-source golden --dataset datasets/skills/arxiv/
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

# Cap max_tokens on every dspy.LM (DSPy defaults to a huge value that overruns
# credit-limited / free OpenRouter models and small local context windows).
# Override via EVO_MAX_TOKENS. For local Ollama models also pin the api_base and
# keep the weights resident between the many calls a run makes (keep_alive) so a
# RAM-starved, CPU-only box doesn't reload ~1GB of weights on every request.
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
    LayoutDatasetBuilder,
    SyntheticDatasetBuilder,
)
from evolution.core.external_importers import build_dataset_from_external
from evolution.core.fitness import skill_fitness_metric
from evolution.skills.skill_module import (
    SkillModule,
    find_skill,
    load_skill,
    reassemble_skill,
)

console = Console()


def _load_target_skill(config: EvolutionConfig, skill_name: str) -> tuple[Path, dict]:
    """Find and load the target skill artifact."""
    skill_path = find_skill(skill_name, config.hermes_agent_path)
    if not skill_path:
        console.print(
            f"[red]✗ Skill '{skill_name}' not found in {config.hermes_agent_path / 'skills'}[/red]"
        )
        sys.exit(1)

    skill = load_skill(skill_path)
    console.print(f"  Loaded: {skill_path.relative_to(config.hermes_agent_path)}")
    console.print(f"  Name: {skill['name']}")
    console.print(f"  Size: {len(skill['raw']):,} chars")
    console.print(f"  Description: {skill['description'][:80]}...")
    return skill_path, skill


def _build_eval_dataset(
    config: EvolutionConfig,
    skill_name: str,
    skill: dict,
    skill_path: Path,
    eval_source: str,
    dataset_path: str | None,
    eval_model: str,
    test_layout: bool,
) -> tuple[EvalDataset, str]:
    """Build or load evaluation dataset based on eval_source."""
    console.print(f"\n[bold]Building evaluation dataset[/bold] (source: {eval_source})")

    if test_layout:
        console.print("  [cyan]Layout testing enabled.[/cyan]")
        reference_dir = skill_path.parent / "references"
        reference_guides = []
        if reference_dir.exists():
            for ref_file in reference_dir.glob("*.md"):
                reference_guides.append(ref_file.read_text())
        if not reference_guides:
            console.print("[yellow]⚠ No reference guides found for layout testing.[/yellow]")

        builder = LayoutDatasetBuilder(config)
        dataset = builder.generate(
            artifact_text=skill["raw"],
            reference_guides=reference_guides,
        )
        save_path = Path("datasets") / "skills" / f"{skill_name}_layout"
        dataset.save(save_path)
        console.print(f"  Generated {len(dataset.all_examples)} layout-specific examples")
        console.print(f"  Saved to {save_path}/")
        eval_source = "layout_synthetic"

    if eval_source == "golden" and dataset_path:
        dataset = GoldenDatasetLoader.load(Path(dataset_path))
        console.print(f"  Loaded golden dataset: {len(dataset.all_examples)} examples")
    elif eval_source == "sessiondb":
        save_path = Path(dataset_path) if dataset_path else Path("datasets") / "skills" / skill_name
        dataset = build_dataset_from_external(
            skill_name=skill_name,
            skill_text=skill["raw"],
            sources=["claude-code", "copilot", "hermes"],
            output_path=save_path,
            model=eval_model,
        )
        if not dataset.all_examples:
            console.print("[red]✗ No relevant examples found from session history[/red]")
    elif eval_source == "synthetic":
        builder = SyntheticDatasetBuilder(config)
        dataset = builder.generate(
            artifact_text=skill["raw"],
            artifact_type="skill",
        )
        save_path = Path("datasets") / "skills" / skill_name
        dataset.save(save_path)
        console.print(f"  Generated {len(dataset.all_examples)} synthetic examples")
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
    return dataset, eval_source


def _validate_baseline_constraints(validator: ConstraintValidator, skill_body: str) -> bool:
    """Validate baseline skill constraints."""
    console.print("\n[bold]Validating baseline constraints[/bold]")
    baseline_constraints = validator.validate_all(skill_body, "skill")
    all_pass = True
    for c in baseline_constraints:
        icon = "✓" if c.passed else "✗"
        color = "green" if c.passed else "red"
        console.print(f"  [{color}]{icon} {c.constraint_name}[/{color}]: {c.message}")
        if not c.passed:
            all_pass = False

    if not all_pass:
        console.print(
            "[yellow]⚠ Baseline skill has constraint violations — proceeding anyway[/yellow]"
        )
    return all_pass


def _gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """Metric wrapper for GEPA optimization with feedback."""
    score = skill_fitness_metric(gold, pred, trace)
    if score >= 0.6:
        fb = f"Score {score:.2f}: output covered the expected behavior."
    else:
        fb = (
            f"Score {score:.2f}: output missed key expected points. Make the "
            "skill's procedure clearer, more actionable, and better aligned "
            "with what the task asks for."
        )
    return dspy.Prediction(score=score, feedback=fb)


def _run_gepa_optimization(
    skill_body: str,
    dataset: EvalDataset,
    iterations: int,
    optimizer_model: str,
    eval_model: str,
) -> tuple[dspy.Module, float]:
    """Configure DSPy and run GEPA or MIPROv2 optimization loop."""
    console.print("\n[bold]Configuring optimizer[/bold]")
    console.print(f"  Optimizer: GEPA ({iterations} iterations)")
    console.print(f"  Optimizer model: {optimizer_model}")
    console.print(f"  Eval model: {eval_model}")

    lm = dspy.LM(eval_model)
    dspy.configure(lm=lm)

    baseline_module = SkillModule(skill_body)
    trainset = dataset.to_dspy_examples("train")
    valset = dataset.to_dspy_examples("val")

    console.print(
        f"\n[bold cyan]Running GEPA optimization ({iterations} iterations)...[/bold cyan]\n"
    )
    start_time = time.time()

    try:
        reflection_lm = dspy.LM(optimizer_model)
        optimizer = dspy.GEPA(
            metric=_gepa_metric,
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
            metric=skill_fitness_metric,
            auto="light",
        )
        optimized_module = optimizer.compile(
            baseline_module,
            trainset=trainset,
        )

    elapsed = time.time() - start_time
    console.print(f"\n  Optimization completed in {elapsed:.1f}s")
    return optimized_module, elapsed


def _validate_evolved_skill(
    validator: ConstraintValidator,
    evolved_full: str,
    skill_raw: str,
    skill_name: str,
) -> bool:
    """Validate evolved skill against constraints."""
    console.print("\n[bold]Validating evolved skill[/bold]")
    evolved_constraints = validator.validate_all(evolved_full, "skill", baseline_text=skill_raw)
    all_pass = True
    for c in evolved_constraints:
        icon = "✓" if c.passed else "✗"
        color = "green" if c.passed else "red"
        console.print(f"  [{color}]{icon} {c.constraint_name}[/{color}]: {c.message}")
        if not c.passed:
            all_pass = False

    if not all_pass:
        console.print("[red]✗ Evolved skill FAILED constraints — not deploying[/red]")
        output_path = Path("output") / skill_name / "evolved_FAILED.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(evolved_full)
        console.print(f"  Saved failed variant to {output_path}")
    return all_pass


def _evaluate_holdout(
    dataset: EvalDataset,
    baseline_module: SkillModule,
    optimized_module: dspy.Module,
    eval_model: str,
) -> tuple[float, float, float]:
    """Evaluate baseline and evolved modules on holdout dataset."""
    console.print(f"\n[bold]Evaluating on holdout set ({len(dataset.holdout)} examples)[/bold]")
    holdout_examples = dataset.to_dspy_examples("holdout")
    lm = dspy.LM(eval_model)

    baseline_scores = []
    evolved_scores = []
    for ex in holdout_examples:
        with dspy.context(lm=lm):
            baseline_pred = baseline_module(task_input=ex.task_input)
            baseline_score = skill_fitness_metric(ex, baseline_pred)
            baseline_scores.append(baseline_score)

            evolved_pred = optimized_module(task_input=ex.task_input)
            evolved_score = skill_fitness_metric(ex, evolved_pred)
            evolved_scores.append(evolved_score)

    avg_baseline = sum(baseline_scores) / max(1, len(baseline_scores))
    avg_evolved = sum(evolved_scores) / max(1, len(evolved_scores))
    improvement = avg_evolved - avg_baseline
    return avg_baseline, avg_evolved, improvement


def _report_and_save_results(
    skill_name: str,
    skill: dict,
    evolved_body: str,
    evolved_full: str,
    dataset: EvalDataset,
    iterations: int,
    optimizer_model: str,
    eval_model: str,
    avg_baseline: float,
    avg_evolved: float,
    improvement: float,
    elapsed: float,
    all_pass: bool,
) -> None:
    """Print results table and save evolved skill and metrics to disk."""
    table = Table(title="Evolution Results")
    table.add_column("Metric", style="bold")
    table.add_column("Baseline", justify="right")
    table.add_column("Evolved", justify="right")
    table.add_column("Change", justify="right")

    change_color = "green" if improvement > 0 else "red"
    table.add_row(
        "Holdout Score",
        f"{avg_baseline:.3f}",
        f"{avg_evolved:.3f}",
        f"[{change_color}]{improvement:+.3f}[/{change_color}]",
    )
    table.add_row(
        "Skill Size",
        f"{len(skill['body']):,} chars",
        f"{len(evolved_body):,} chars",
        f"{len(evolved_body) - len(skill['body']):+,} chars",
    )
    table.add_row("Time", "", f"{elapsed:.1f}s", "")
    table.add_row("Iterations", "", str(iterations), "")

    console.print()
    console.print(table)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / skill_name / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "evolved_skill.md").write_text(evolved_full)
    (output_dir / "baseline_skill.md").write_text(skill["raw"])

    metrics = {
        "skill_name": skill_name,
        "timestamp": timestamp,
        "iterations": iterations,
        "optimizer_model": optimizer_model,
        "eval_model": eval_model,
        "baseline_score": avg_baseline,
        "evolved_score": avg_evolved,
        "improvement": improvement,
        "baseline_size": len(skill["body"]),
        "evolved_size": len(evolved_body),
        "train_examples": len(dataset.train),
        "val_examples": len(dataset.val),
        "holdout_examples": len(dataset.holdout),
        "elapsed_seconds": elapsed,
        "constraints_passed": all_pass,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    console.print(f"\n  Output saved to {output_dir}/")

    if improvement > 0:
        console.print(
            f"\n[bold green]✓ Evolution improved skill by {improvement:+.3f} ({improvement / max(0.001, avg_baseline) * 100:+.1f}%)[/bold green]"
        )
        console.print(
            f"  Review the diff: diff {output_dir}/baseline_skill.md {output_dir}/evolved_skill.md"
        )
    else:
        console.print(
            f"\n[yellow]⚠ Evolution did not improve skill (change: {improvement:+.3f})[/yellow]"
        )
        console.print("  Try: more iterations, better eval dataset, or different optimizer model")


def evolve(
    skill_name: str,
    iterations: int = 10,
    eval_source: str = "synthetic",
    dataset_path: str | None = None,
    optimizer_model: str = _DEFAULT_LOCAL_MODEL,
    eval_model: str = _DEFAULT_LOCAL_MODEL,
    hermes_repo: str | None = None,
    run_tests: bool = False,
    test_layout: bool = False,
    dry_run: bool = False,
):
    """Main evolution function — orchestrates the full optimization loop."""

    config = EvolutionConfig(
        hermes_agent_path=resolve_hermes_agent_path(hermes_repo),
        iterations=iterations,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        judge_model=eval_model,  # Use same model for dataset generation
        run_pytest=run_tests,
    )

    # ── 1. Find and load the skill ──────────────────────────────────────
    console.print(
        f"\n[bold cyan]🧬 Hermes Agent Self-Evolution[/bold cyan] — Evolving skill: [bold]{skill_name}[/bold]\n"
    )

    skill_path, skill = _load_target_skill(config, skill_name)

    if dry_run:
        console.print("\n[bold green]DRY RUN — setup validated successfully.[/bold green]")
        console.print(f"  Would generate eval dataset (source: {eval_source})")
        if test_layout:
            console.print("  Would use LayoutDatasetBuilder for layout-specific tests.")
        console.print(f"  Would run GEPA optimization ({iterations} iterations)")
        console.print("  Would validate constraints and create PR")
        return

    # ── 2. Build or load evaluation dataset ─────────────────────────────
    dataset, eval_source = _build_eval_dataset(
        config=config,
        skill_name=skill_name,
        skill=skill,
        skill_path=skill_path,
        eval_source=eval_source,
        dataset_path=dataset_path,
        eval_model=eval_model,
        test_layout=test_layout,
    )

    # ── 3. Validate constraints on baseline ─────────────────────────────
    validator = ConstraintValidator(config)
    _validate_baseline_constraints(validator, skill["body"])

    # ── 4 & 5. Set up and run GEPA optimization ─────────────────────────
    optimized_module, elapsed = _run_gepa_optimization(
        skill_body=skill["body"],
        dataset=dataset,
        iterations=iterations,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
    )

    # ── 6. Extract evolved skill text ───────────────────────────────────
    evolved_body = optimized_module.skill_text
    evolved_full = reassemble_skill(skill["frontmatter"], evolved_body)

    # ── 7. Validate evolved skill ───────────────────────────────────────
    all_pass = _validate_evolved_skill(validator, evolved_full, skill["raw"], skill_name)
    if not all_pass:
        return

    # ── 8. Evaluate on holdout set ──────────────────────────────────────
    baseline_module = SkillModule(skill["body"])
    avg_baseline, avg_evolved, improvement = _evaluate_holdout(
        dataset=dataset,
        baseline_module=baseline_module,
        optimized_module=optimized_module,
        eval_model=eval_model,
    )

    # ── 9 & 10. Report results and save output ──────────────────────────
    _report_and_save_results(
        skill_name=skill_name,
        skill=skill,
        evolved_body=evolved_body,
        evolved_full=evolved_full,
        dataset=dataset,
        iterations=iterations,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        avg_baseline=avg_baseline,
        avg_evolved=avg_evolved,
        improvement=improvement,
        elapsed=elapsed,
        all_pass=all_pass,
    )


@click.command()
@click.option("--skill", required=True, help="Name of the skill to evolve")
@click.option("--iterations", default=10, help="Number of GEPA iterations")
@click.option(
    "--eval-source",
    default="synthetic",
    type=click.Choice(["synthetic", "golden", "sessiondb"]),
    help="Source for evaluation dataset",
)
@click.option("--dataset-path", default=None, help="Path to existing eval dataset (JSONL)")
@click.option(
    "--optimizer-model",
    default=lambda: os.getenv("EVO_OPTIMIZER_MODEL", _DEFAULT_LOCAL_MODEL),
    help="LiteLLM model for GEPA reflections (default: local Ollama)",
)
@click.option(
    "--eval-model",
    default=lambda: os.getenv("EVO_EVAL_MODEL", _DEFAULT_LOCAL_MODEL),
    help="LiteLLM model for evaluations (default: local Ollama)",
)
@click.option("--hermes-repo", default=None, help="Path to hermes-agent repo")
@click.option("--run-tests", is_flag=True, help="Run full pytest suite as constraint gate")
@click.option("--test-layout", is_flag=True, help="Generate layout-specific test cases")
@click.option("--dry-run", is_flag=True, help="Validate setup without running optimization")
def main(
    skill,
    iterations,
    eval_source,
    dataset_path,
    optimizer_model,
    eval_model,
    hermes_repo,
    run_tests,
    test_layout,
    dry_run,
):
    """Evolve a Hermes Agent skill using DSPy + GEPA optimization."""
    evolve(
        skill_name=skill,
        iterations=iterations,
        eval_source=eval_source,
        dataset_path=dataset_path,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        hermes_repo=hermes_repo,
        run_tests=run_tests,
        test_layout=test_layout,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    main()
