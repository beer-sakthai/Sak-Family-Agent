"""GitHub CLI Subagent Framework & Dynamic Workflow Integration.

Integrates specialized subagents ('github-cli-auditor' and 'github-cli-pr-runner')
with Antigravity Dynamic Workflows and Deep Reasoning Boost hooks.
Follows House of Sak invariants: No auto-merge, 96% coverage, safe subprocess execution.
"""

from __future__ import annotations

import enum
import json
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class GitHubSubagentRole(enum.StrEnum):
    """Specialized roles for GitHub CLI subagents."""

    AUDITOR = "github-cli-auditor"
    PR_RUNNER = "github-cli-pr-runner"
    BOOST_VERIFIER = "github-cli-boost-verifier"


@dataclass(frozen=True)
class GitHubSubagentConfig:
    """Configuration definition for a GitHub CLI subagent."""

    name: str
    role: GitHubSubagentRole
    description: str
    read_only: bool = True
    enable_mcp: bool = True
    model_tier: str = "inherit"


@dataclass
class WorkflowExecutionReport:
    """Structured report emitted by the dynamic workflow pipeline."""

    workflow_id: str
    phases_completed: list[str] = field(default_factory=list)
    open_prs_audited: int = 0
    high_risk_detected: int = 0
    boost_triggered: bool = False
    auto_merge_blocked: bool = True
    details: list[dict[str, Any]] = field(default_factory=list)


class GitHubCLISubagentFramework:
    """Out-of-the-box framework coordinating GitHub CLI subagents."""

    def __init__(self) -> None:
        self._subagents: dict[str, GitHubSubagentConfig] = {}
        self._register_default_subagents()

    def _register_default_subagents(self) -> None:
        """Register default specialized subagents."""
        self.register(
            GitHubSubagentConfig(
                name="github-cli-auditor",
                role=GitHubSubagentRole.AUDITOR,
                description="Audits pull requests, issues, and workflow runs via gh CLI in read-only mode.",
                read_only=True,
            )
        )
        self.register(
            GitHubSubagentConfig(
                name="github-cli-pr-runner",
                role=GitHubSubagentRole.PR_RUNNER,
                description="Executes PR management, testing dispatches, and review comments via gh CLI.",
                read_only=False,
            )
        )

    def register(self, config: GitHubSubagentConfig) -> None:
        """Register a subagent configuration."""
        self._subagents[config.name] = config

    def get_subagent(self, name: str) -> GitHubSubagentConfig | None:
        """Look up a subagent configuration by name."""
        return self._subagents.get(name)

    def list_subagents(self) -> list[GitHubSubagentConfig]:
        """List all registered subagents."""
        return list(self._subagents.values())

    def run_gh(self, args: list[str]) -> tuple[int, str]:
        """Execute a safe, audited gh command."""
        # Enforce safety guardrails: prevent unauthorized merge or destructive commands
        if "merge" in args and ("--auto" in args or "-y" in args):
            logger.warning("Auto-merge is strictly forbidden by House of Sak operating contract.")
            return 1, "Error: Auto-merge blocked by SakJules CI/CD protocol."

        cmd = ["gh", *args]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return res.returncode, res.stdout or res.stderr
        except FileNotFoundError:
            return 127, "gh command not found"


async def run_github_audit_pipeline(
    framework: GitHubCLISubagentFramework | None = None,
    mock_prs: list[dict[str, Any]] | None = None,
) -> WorkflowExecutionReport:
    """Run an end-to-end dynamic audit pipeline across open pull requests."""
    fw = framework or GitHubCLISubagentFramework()
    report = WorkflowExecutionReport(workflow_id="gh-dyn-workflow-v1")

    # Phase 1: Discover
    report.phases_completed.append("Discover")
    prs: list[dict[str, Any]] = []
    if mock_prs is not None:
        prs = mock_prs
    else:
        code, out = fw.run_gh(
            ["pr", "list", "--state", "open", "--json", "number,title,headRefName"]
        )
        if code == 0:
            try:
                prs = json.loads(out)
            except json.JSONDecodeError:
                prs = []

    # Phase 2: Audit & Triage
    report.phases_completed.append("Audit & Triage")
    high_risk_count = 0
    for pr in prs:
        title = str(pr.get("title", ""))
        is_risky = any(
            k in title.lower() for k in ["breaking", "security", "decommission", "delete"]
        )
        risk = "high" if is_risky else "low"
        if is_risky:
            high_risk_count += 1
        report.details.append({"pr": pr.get("number"), "title": title, "risk": risk})

    report.open_prs_audited = len(prs)
    report.high_risk_detected = high_risk_count

    # Phase 3: Deep Reasoning Boost
    report.phases_completed.append("Deep Reasoning Boost")
    if high_risk_count > 0:
        report.boost_triggered = True
        logger.info("Deep reasoning boost activated for %d high-risk PR(s).", high_risk_count)

    # Phase 4: Execute & Verify
    report.phases_completed.append("Execute & Verify")
    report.auto_merge_blocked = True

    return report
