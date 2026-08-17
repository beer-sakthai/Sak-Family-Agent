"""Self-healing CI — diagnose a failed CI run and propose a verified fix.

The pipeline reads a failed job's log, resolves the source it implicates,
diagnoses the failure with a model, gates the proposed patch through a
deterministic safety check, applies it, verifies it against the local test
suite, and either pushes a fix branch with a structured walkthrough or rolls
everything back. :func:`~sakthai.selfheal.pipeline.heal` is the entry point;
``sakthai heal`` is the CLI over it.

Nothing here runs automatically. It is invoked by ``.github/workflows/
self-healing-ci.yml`` after a CI failure, or by hand against a saved log.
"""

from __future__ import annotations

from .models import (
    Diagnosis,
    FailureSignal,
    FileContext,
    HealingOutcome,
    HealStatus,
    LogFrame,
    ProposedEdit,
    VerificationResult,
)
from .pipeline import HealConfig, heal

__all__ = [
    "Diagnosis",
    "FailureSignal",
    "FileContext",
    "HealConfig",
    "HealStatus",
    "HealingOutcome",
    "LogFrame",
    "ProposedEdit",
    "VerificationResult",
    "heal",
]
