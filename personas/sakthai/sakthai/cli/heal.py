"""sakthai heal — the self-healing CI agent, driven from a failed job's log.

heal inspect is the hermetic half: it parses a log and prints what it found,
with no model call and no writes. heal run walks the full pipeline.

The exit code reports whether the *pipeline* ran, not whether a fix was found:
an honest "this failure is not safely fixable" is a successful run. Callers that
need to branch on the result should read --json (or the report file), where
the terminal status is explicit. Only an internal error — an unreadable log, a
bad repository root, an unbuildable provider client — exits non-zero.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from ..agent.loop import DEFAULT_MODEL
from ..selfheal import ingest
from ..selfheal.completion import build_completion
from ..selfheal.diagnose import DEFAULT_MIN_CONFIDENCE
from ..selfheal.models import HealingOutcome
from ..selfheal.pipeline import HealConfig
from ..selfheal.pipeline import heal as run_heal
from ..selfheal.publish import DEFAULT_BRANCH_PREFIX
from ..selfheal.walkthrough import DEFAULT_WALKTHROUGH_MODEL


@dataclass(frozen=True)
class HealRunArgs:
    """Arguments passed to the sakthai heal run command."""

    log_source: str
    repo_root: str
    model: str
    provider: str | None
    walkthrough_model: str
    min_confidence: float
    base: str
    branch_prefix: str
    run_id: str
    run_url: str
    dry_run: bool
    no_publish: bool
    no_pr: bool
    report_path: str | None
    as_json: bool

    @classmethod
    def from_dict(cls, kwargs: dict[str, Any]) -> HealRunArgs:
        return cls(**kwargs)


def _read_log(source: str) -> str:
    """Read the job log from a file, or from stdin when source is -."""
    if source == "-":
        return sys.stdin.read()
    path = Path(source)
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise click.ClickException(f"cannot read log {source}: {exc}") from exc


def _outcome_json(outcome: HealingOutcome) -> dict[str, Any]:
    signal = outcome.signal
    diagnosis = outcome.diagnosis
    return {
        "status": str(outcome.status),
        "detail": outcome.detail,
        "failure": signal.describe() if signal else "",
        "confidence": diagnosis.confidence if diagnosis else 0.0,
        "violations": list(diagnosis.violations) if diagnosis else [],
        "changed_files": list(outcome.changed_files),
        "branch": outcome.branch,
        "pull_request_url": outcome.pull_request_url,
        "tests_passed": outcome.test_outcome.passed if outcome.test_outcome else None,
    }


@click.group()
def heal() -> None:
    """Diagnose a failed CI run and, when it is safe to, fix it."""


@heal.command("inspect")
@click.option("--log", "log_source", required=True, help="Job log file, or '-' for stdin.")
@click.option("--json", "as_json", is_flag=True, help="Emit the parsed failures as JSON.")
def heal_inspect(log_source: str, as_json: bool) -> None:
    """Parse a CI job log and show the failures found. Makes no model call."""
    signals = ingest.parse_job_log(_read_log(log_source))

    if as_json:
        click.echo(json.dumps([dataclasses.asdict(s) for s in signals], indent=2))
        return

    if not signals:
        click.echo("(no recognised failure in this log)")
        return

    click.echo(f"# {len(signals)} failure(s)")
    for index, signal in enumerate(signals, start=1):
        click.echo(f"{index}. {signal.describe()}")
        for frame in signal.frames:
            suffix = f" in {frame.function}" if frame.function else ""
            click.echo(f"     {frame.path}:{frame.line}{suffix}")


@heal.command("run")
@click.option("--log", "log_source", required=True, help="Job log file, or '-' for stdin.")
@click.option(
    "--repo-root",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, exists=True),
    help="Repository the fix is applied to.",
)
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Diagnosis model.")
@click.option("--provider", default=None, help="Force a provider for the diagnosis model.")
@click.option(
    "--walkthrough-model",
    default=DEFAULT_WALKTHROUGH_MODEL,
    show_default=True,
    help="Model that narrates the PR walkthrough.",
)
@click.option(
    "--min-confidence",
    default=DEFAULT_MIN_CONFIDENCE,
    show_default=True,
    type=float,
    help="Abort below this diagnosis confidence.",
)
@click.option("--base", default="main", show_default=True, help="Base branch for the pull request.")
@click.option(
    "--branch-prefix",
    default=DEFAULT_BRANCH_PREFIX,
    show_default=True,
    help="Namespace every fix branch must sit under.",
)
@click.option("--run-id", default="", help="Failed workflow run id, used in the branch name.")
@click.option("--run-url", default="", help="Failed workflow run URL, linked in the report.")
@click.option("--dry-run", is_flag=True, help="Diagnose only — apply nothing, write nothing.")
@click.option("--no-publish", is_flag=True, help="Apply and verify, but do not commit or push.")
@click.option("--no-pr", is_flag=True, help="Push the fix branch but do not open a pull request.")
@click.option(
    "--report",
    "report_path",
    default=None,
    type=click.Path(dir_okay=False),
    help="Write the markdown report here.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the outcome as JSON.")
def heal_run(**kwargs: Any) -> None:
    """Diagnose a failed CI run, apply a verified fix, and open a pull request."""
    args = HealRunArgs.from_dict(kwargs)
    log_text = _read_log(args.log_source)

    try:
        completion = build_completion(provider=args.provider, model=args.model)
        # The walkthrough is best-effort; a provider that cannot be built for it
        # must not stop a fix that is otherwise ready to publish.
        try:
            narrator = build_completion(model=args.walkthrough_model)
        except Exception:  # noqa: BLE001 — narration is optional by design
            narrator = None
    except Exception as exc:  # noqa: BLE001 — surface a provider failure as a CLI error
        raise click.ClickException(f"cannot build the diagnosis model client: {exc}") from exc

    config = HealConfig(
        repo_root=Path(args.repo_root),
        min_confidence=args.min_confidence,
        branch_prefix=args.branch_prefix,
        base_branch=args.base,
        run_id=args.run_id,
        run_url=args.run_url,
        dry_run=args.dry_run,
        publish_fix=not (args.no_publish or args.dry_run),
        open_pr=not args.no_pr,
    )
    outcome = run_heal(log_text, config, completion=completion, narrator=narrator)

    if args.report_path:
        Path(args.report_path).write_text(outcome.report, encoding="utf-8")

    if args.as_json:
        click.echo(json.dumps(_outcome_json(outcome), indent=2))
        return

    click.echo(f"status: {outcome.status}")
    click.echo(f"detail: {outcome.detail}")
    if outcome.changed_files:
        click.echo(f"files:  {', '.join(outcome.changed_files)}")
    if outcome.branch:
        click.echo(f"branch: {outcome.branch}")
    if outcome.pull_request_url:
        click.echo(f"pr:     {outcome.pull_request_url}")
