"""The self-healing pipeline — one function that walks the whole flow.

::

    CI failure
      → ingest job log            (ingest.parse_job_log)
      → gather repo context       (inspector.gather_context)
      → diagnose + safety gate    (diagnose.diagnose)
          ├─ violations / low confidence → abort and report
      → apply patch               (patch.apply_edits)
      → run pytest locally        (verify.run_tests)
          ├─ tests fail → roll back, clean the branch, report
      → push fix branch + open PR (publish.publish_fix)
      → structured walkthrough    (walkthrough.render_report)

Every stage is injectable, so the whole pipeline runs in a test with a stub
completion and a stub command runner — no model, no git, no pytest subprocess.

One deliberate departure from a naive reading of that flow: the fix branch is
created **after** verification passes, not before. Verification runs against the
working tree either way, and creating the branch last means a failed run has
nothing to clean up beyond restoring the files it wrote. The branch *is* cleaned
up on the one path where it can exist and still be unwanted — a commit that
succeeded followed by a push or PR that did not.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from . import ingest, inspector, patch, publish, verify, walkthrough
from .completion import Completion
from .diagnose import DEFAULT_MIN_CONFIDENCE, diagnose
from .models import Diagnosis, FailureSignal, FileContext, HealingOutcome, HealStatus
from .publish import DEFAULT_BRANCH_PREFIX, PublishError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HealConfig:
    """Everything the pipeline needs to know that is not the log itself."""

    repo_root: Path
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    branch_prefix: str = DEFAULT_BRANCH_PREFIX
    base_branch: str = "main"
    run_id: str = ""
    run_url: str = ""
    # Stop after diagnosis; propose nothing, write nothing.
    dry_run: bool = False
    # Apply and verify, but leave the fix in the working tree unpublished.
    publish_fix: bool = True
    open_pr: bool = True


def _current_branch(repo_root: Path, runner: publish.CommandRunner) -> str:
    returncode, output = runner(("git", "rev-parse", "--abbrev-ref", "HEAD"), repo_root)
    return output.strip() if returncode == 0 else ""


def _clean_branch(
    repo_root: Path, branch: str, original: str, runner: publish.CommandRunner
) -> None:
    """Return to ``original`` and delete a fix branch that should not survive.

    Publishing can fail at any step, including the very first one, so the branch
    may never have been created. Re-read HEAD and only clean up what is actually
    there — deleting a branch that does not exist would turn one clear failure
    into two confusing ones.
    """
    if not branch or not original or branch == original:
        return
    if _current_branch(repo_root, runner) != branch:
        return
    runner(("git", "checkout", original), repo_root)
    runner(("git", "branch", "-D", branch), repo_root)


def _abort(
    status: HealStatus,
    reason: str,
    signal: FailureSignal | None,
    diagnosis: Diagnosis | None,
    contexts: Sequence[FileContext] = (),
) -> HealingOutcome:
    return HealingOutcome(
        status=status,
        detail=reason,
        signal=signal,
        diagnosis=diagnosis,
        contexts=tuple(contexts),
        report=walkthrough.render_abort_report(signal, diagnosis, reason),
    )


def heal(
    log_text: str,
    config: HealConfig,
    *,
    completion: Completion,
    narrator: Completion | None = None,
    test_runner: verify.CommandRunner | None = None,
    command_runner: publish.CommandRunner | None = None,
) -> HealingOutcome:
    """Run the full self-healing flow over one CI job log.

    Returns a :class:`HealingOutcome` for every path, including the ones that
    deliberately change nothing. The function does not raise on an ordinary
    failure — an unfixable log, a rejected patch, or a red verification run are
    all normal outcomes with their own status.
    """
    repo_root = config.repo_root.resolve()

    signals = ingest.parse_job_log(log_text)
    if not signals:
        return _abort(HealStatus.NO_FAILURE, "no recognised failure in the job log", None, None)

    # Signals arrive most-specific-first (pytest before the line checkers), so
    # the first is the failure worth explaining. Fixing one failure per run keeps
    # the PR reviewable and the blast radius small.
    signal = signals[0]
    logger.info("selfheal: diagnosing %s", signal.describe())

    contexts = inspector.gather_context(signal, repo_root)
    diagnosis = diagnose(signal, contexts, repo_root, completion=completion)

    if not diagnosis.edits:
        return _abort(
            HealStatus.NO_DIAGNOSIS,
            diagnosis.root_cause or "the diagnosis stage proposed no fix",
            signal,
            diagnosis,
            contexts,
        )
    if diagnosis.violations:
        return _abort(
            HealStatus.ABORTED_UNSAFE,
            "the proposed patch was rejected by the safety gate",
            signal,
            diagnosis,
            contexts,
        )
    if diagnosis.confidence < config.min_confidence:
        return _abort(
            HealStatus.ABORTED_LOW_CONFIDENCE,
            f"confidence {diagnosis.confidence:.2f} is below the {config.min_confidence:.2f} bar",
            signal,
            diagnosis,
            contexts,
        )
    if config.dry_run:
        return _abort(
            HealStatus.DRY_RUN,
            "dry run — a safe fix was found but nothing was applied",
            signal,
            diagnosis,
            contexts,
        )

    try:
        transaction = patch.apply_edits(diagnosis.edits, repo_root)
    except patch.PatchError as exc:
        return _abort(
            HealStatus.ABORTED_UNSAFE,
            f"patch could not be applied: {exc}",
            signal,
            diagnosis,
            contexts,
        )

    changed_files = transaction.changed_files
    test_outcome = verify.run_tests(signal, repo_root, runner=test_runner)

    if not test_outcome.passed:
        restored = transaction.rollback()
        logger.info(
            "selfheal: verification failed; rolled back %s", ", ".join(restored) or "nothing"
        )
        return HealingOutcome(
            status=HealStatus.ROLLED_BACK,
            detail="local verification failed; the patch was rolled back",
            signal=signal,
            diagnosis=diagnosis,
            test_outcome=test_outcome,
            contexts=contexts,
            changed_files=restored,
            report=walkthrough.render_report(
                signal,
                diagnosis,
                test_outcome=test_outcome,
                changed_files=restored,
                run_url=config.run_url,
            ),
        )

    narrative = walkthrough.narrate(signal, diagnosis, changed_files, completion=narrator)
    report = walkthrough.render_report(
        signal,
        diagnosis,
        test_outcome=test_outcome,
        changed_files=changed_files,
        narrative=narrative,
        run_url=config.run_url,
    )
    title = diagnosis.summary or f"fix {signal.error_type} in CI"

    if not config.publish_fix:
        return HealingOutcome(
            status=HealStatus.FIXED,
            detail="fix applied and verified locally; publishing was disabled",
            signal=signal,
            diagnosis=diagnosis,
            test_outcome=test_outcome,
            contexts=contexts,
            changed_files=changed_files,
            report=report,
        )

    runner = command_runner or publish.default_runner
    branch = publish.branch_name(title, config.run_id, config.branch_prefix)
    original_branch = _current_branch(repo_root, runner)
    try:
        result = publish.publish_fix(
            repo_root,
            branch=branch,
            paths=changed_files,
            commit_message=f"{title}\n\nAutomated fix for {signal.describe()}.",
            pr_title=title,
            pr_body=report,
            base=config.base_branch,
            open_pr=config.open_pr,
            runner=runner,
            prefix=config.branch_prefix,
        )
    except PublishError as exc:
        _clean_branch(repo_root, branch, original_branch, runner)
        transaction.rollback()
        return _abort(
            HealStatus.ROLLED_BACK, f"publishing failed: {exc}", signal, diagnosis, contexts
        )

    return HealingOutcome(
        status=HealStatus.PUBLISHED,
        detail=f"fix pushed to {result.branch}",
        signal=signal,
        diagnosis=diagnosis,
        test_outcome=test_outcome,
        contexts=contexts,
        changed_files=changed_files,
        branch=result.branch,
        pull_request_url=result.pull_request_url,
        report=report,
    )
