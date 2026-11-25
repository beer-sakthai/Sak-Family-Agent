"""PatchFlow automated patching engine package."""

from __future__ import annotations

from .engine import PatchExecutionResult, PatchFlowEngine
from .gate import AntiGamingGate, GateVerdict
from .generator import PatchCandidate, PatchGenerator
from .pr_emitter import PREmitter, PullRequestPayload
from .scanners import DependabotScanner, Finding, LinterScanner, TestFailureScanner

__all__ = [
    "AntiGamingGate",
    "DependabotScanner",
    "Finding",
    "GateVerdict",
    "LinterScanner",
    "PREmitter",
    "PatchCandidate",
    "PatchExecutionResult",
    "PatchFlowEngine",
    "PatchGenerator",
    "PullRequestPayload",
    "TestFailureScanner",
]
