"""PR walkthrough — the report a human reads before approving an automated fix.

The body has two halves, and the split is the point. The **structured** half is
generated from the pipeline's own records: what failed, what changed, which
verification commands ran, and what the safety gate checked. It is deterministic
and cannot overstate what happened. The **narrative** half is a model's plain-
English explanation of the change, clearly labelled as such, and is best-effort:
if the provider is down or the reply is empty, the PR still gets a complete,
accurate body.

A reviewer should never have to trust the narrative to know what the agent did.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ..config import redact_secrets
from .completion import Completion
from .models import Diagnosis, FailureSignal, VerificationResult
from .safety import MAX_EDITS, describe_violations

logger = logging.getLogger(__name__)

# The walkthrough is a summarisation job, not a reasoning one — the persona
# default for cheap, fast narration (see `personas/*/config/config.yaml`).
DEFAULT_WALKTHROUGH_MODEL = "gemini-3.1-flash-lite"

NARRATIVE_SYSTEM_PROMPT = """You are writing the explanation section of a pull
request opened by an automated CI repair agent.

You are given the failure, the diagnosis, and the exact edits that were applied
and verified. Write 3-6 sentences for a reviewer who has not seen the CI log:
what broke, why the change fixes it, and what a reviewer should look at most
closely. Be specific and plain. Do not invent changes that are not in the diff,
do not claim anything was tested beyond what you are shown, and do not add
headings, bullet lists, or a sign-off. Prose only."""

_MAX_EDIT_PREVIEW_LINES = 20


def _preview(text: str) -> str:
    lines = text.splitlines()
    if len(lines) <= _MAX_EDIT_PREVIEW_LINES:
        return text
    return "\n".join(lines[:_MAX_EDIT_PREVIEW_LINES]) + "\n… (truncated)"


def _edits_section(diagnosis: Diagnosis) -> str:
    if not diagnosis.edits:
        return "_no edits were applied_"
    chunks: list[str] = []
    for index, edit in enumerate(diagnosis.edits[:MAX_EDITS], start=1):
        chunks.append(
            f"**{index}. `{edit.path}`**\n\n"
            f"```diff\n- {_preview(edit.old)}\n+ {_preview(edit.new)}\n```"
        )
    return "\n\n".join(chunks)


def _verification_section(outcome: VerificationResult | None) -> str:
    if outcome is None:
        return "_verification did not run_"
    status = "passed" if outcome.passed else f"FAILED (exit {outcome.returncode})"
    command = " ".join(outcome.command) if outcome.command else "(none)"
    body = f"- last command: `{command}`\n- result: **{status}**"
    if not outcome.passed and outcome.output:
        body += (
            f"\n\n<details><summary>Output</summary>\n\n```\n{outcome.output}\n```\n\n</details>"
        )
    return body


def build_narrative_prompt(
    signal: FailureSignal,
    diagnosis: Diagnosis,
    changed_files: Sequence[str],
) -> str:
    """Render the user half of the narrative prompt."""
    edits = "\n\n".join(
        f"{edit.path}:\n--- before ---\n{_preview(edit.old)}\n--- after ---\n{_preview(edit.new)}"
        for edit in diagnosis.edits[:MAX_EDITS]
    )
    return "\n".join(
        [
            f"Failure: {signal.describe()}",
            f"Root cause (from the diagnosis stage): {diagnosis.root_cause}",
            f"Files changed: {', '.join(changed_files) or '(none)'}",
            "",
            "Applied edits:",
            edits or "(none)",
        ]
    )


def narrate(
    signal: FailureSignal,
    diagnosis: Diagnosis,
    changed_files: Sequence[str],
    *,
    completion: Completion | None,
) -> str:
    """Ask a model to explain the change. Best-effort — returns ``""`` on any failure."""
    if completion is None:
        return ""
    try:
        text = completion(
            NARRATIVE_SYSTEM_PROMPT, build_narrative_prompt(signal, diagnosis, changed_files)
        )
    except Exception as exc:  # noqa: BLE001 — the PR body must survive a provider outage
        logger.warning("selfheal: walkthrough narration failed: %s", exc)
        return ""
    return redact_secrets(text.strip())


def render_report(
    signal: FailureSignal,
    diagnosis: Diagnosis,
    *,
    test_outcome: VerificationResult | None = None,
    changed_files: Sequence[str] = (),
    narrative: str = "",
    run_url: str = "",
) -> str:
    """Render the full structured walkthrough as markdown."""
    sections = [
        "## Automated CI fix",
        "",
        f"**Failure**: `{signal.describe()}`",
    ]
    if run_url:
        sections.append(f"**Failed run**: {run_url}")
    sections += [
        "",
        "### Root cause",
        diagnosis.root_cause or "_not reported_",
        "",
        "### Change",
        _edits_section(diagnosis),
        "",
        "### Verification",
        _verification_section(test_outcome),
        "",
        "### Safety review",
        (
            f"- files changed: {', '.join(changed_files) or '(none)'}\n"
            f"- diagnosis confidence: {diagnosis.confidence:.2f}\n"
            f"- gate violations: {describe_violations(diagnosis.violations)}"
        ),
    ]
    if narrative:
        sections += ["", "### Walkthrough _(model-generated)_", narrative]
    sections += [
        "",
        "---",
        (
            "_Opened by the self-healing CI agent (`sakthai heal`). The edits above were applied "
            "and verified locally before this branch was pushed; the structured sections are "
            "generated from the pipeline's own records, not from a model._"
        ),
    ]
    return redact_secrets("\n".join(sections))


def render_abort_report(
    signal: FailureSignal | None,
    diagnosis: Diagnosis | None,
    reason: str,
) -> str:
    """Render the report for a run that deliberately did not fix anything."""
    lines = ["## Automated CI triage — no fix applied", "", f"**Reason**: {reason}"]
    if signal is not None:
        lines += ["", f"**Failure**: `{signal.describe()}`"]
    if diagnosis is not None:
        lines += [
            "",
            "### Root cause",
            diagnosis.root_cause or "_not reported_",
            "",
            f"- diagnosis confidence: {diagnosis.confidence:.2f}",
            f"- gate violations:\n{describe_violations(diagnosis.violations)}",
        ]
    lines += [
        "",
        "---",
        "_Reported by the self-healing CI agent (`sakthai heal`). No files were changed._",
    ]
    return redact_secrets("\n".join(lines))
