"""GitHub CLI Subagent Framework & Dynamic Workflow Integration.

Integrates specialized subagents ('github-cli-auditor' and 'github-cli-pr-runner')
with Antigravity Dynamic Workflows and Deep Reasoning Boost hooks.
Follows House of Sak invariants: No auto-merge, 96% coverage, safe subprocess execution.
"""

from __future__ import annotations

import contextlib
import enum
import json
import logging
import os
import re
import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitHubSubagentRole(enum.StrEnum):
    """Specialized roles for GitHub CLI subagents."""

    AUDITOR = "github-cli-auditor"
    PR_RUNNER = "github-cli-pr-runner"
    BOOST_VERIFIER = "github-cli-boost-verifier"
    MAINTENANCE_SYNC = "github-cli-maintenance-sync"
    SECURITY_AUDITOR = "github-cli-security-auditor"


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
        self.register(
            GitHubSubagentConfig(
                name="github-cli-maintenance-sync",
                role=GitHubSubagentRole.MAINTENANCE_SYNC,
                description="Performs weekly backlog synchronization, database vacuum, and fleet health verification.",
                read_only=False,
            )
        )
        self.register(
            GitHubSubagentConfig(
                name="github-cli-security-auditor",
                role=GitHubSubagentRole.SECURITY_AUDITOR,
                description="Audits branch protection, workflow action pins, and credential hygiene invariants.",
                read_only=True,
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
        if "merge" in args:
            logger.warning("Auto-merge is strictly forbidden by House of Sak operating contract.")
            return 1, "Error: Auto-merge blocked by SakJules CI/CD protocol."

        cmd = ["gh", *args]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return res.returncode, res.stdout or res.stderr
        except FileNotFoundError:
            return 127, "gh command not found"

    def check_duplicate_prs(
        self, target_files: list[str] | None = None, branch_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Check for existing open pull requests that overlap with the target branch or files."""
        code, out = self.run_gh(
            ["pr", "list", "--state", "open", "--json", "number,title,headRefName,url"]
        )
        if code != 0 or not out:
            return []
        try:
            prs = json.loads(out)
            if not isinstance(prs, list):
                return []
        except json.JSONDecodeError:
            return []

        overlaps: list[dict[str, Any]] = []
        for pr in prs:
            ref = pr.get("headRefName", "")
            if branch_name and ref == branch_name:
                overlaps.append(pr)
                continue
            if target_files:
                num = str(pr.get("number", ""))
                code_f, out_f = self.run_gh(["pr", "view", num, "--json", "files"])
                if code_f == 0:
                    with contextlib.suppress(Exception):
                        data = json.loads(out_f)
                        pr_files = {
                            f["path"]
                            for f in data.get("files", [])
                            if isinstance(f, dict) and "path" in f
                        }
                        if any(tf in pr_files for tf in target_files):
                            overlaps.append(pr)
        return overlaps


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


async def run_github_maintenance_pipeline(
    framework: GitHubCLISubagentFramework | None = None,
    vacuum: bool = False,
    run_audit: bool = False,
) -> WorkflowExecutionReport:
    """Run an automated maintenance & backlog sync pipeline."""
    fw = framework or GitHubCLISubagentFramework()
    report = WorkflowExecutionReport(workflow_id="gh-dyn-maintenance-v1")

    # Phase 1: Environment & Memory Shards
    report.phases_completed.append("Shard Maintenance")
    vacuum_count = 0
    if vacuum:
        home_base = os.path.expanduser(os.environ.get("SAKTHAI_HOME", "~/.sakthai"))
        if os.path.isdir(home_base):
            for root, _, files in os.walk(home_base):
                for f in files:
                    if f.endswith(".db"):
                        db_p = os.path.join(root, f)
                        try:
                            conn = sqlite3.connect(db_p)
                            cursor = conn.cursor()
                            cursor.execute("PRAGMA integrity_check;")
                            res = cursor.fetchone()
                            if res and res[0] == "ok":
                                conn.execute("VACUUM;")
                                vacuum_count += 1
                            else:
                                logger.warning("Integrity check failed on %s: %s", db_p, res)
                            conn.close()
                        except Exception as e:
                            logger.warning("Vacuum failed on %s: %s", db_p, e)
    report.details.append({"phase": "shards", "vacuumed": vacuum_count})

    # Phase 2: Backlog Discovery
    report.phases_completed.append("Backlog Discovery")
    code, out = fw.run_gh(["issue", "list", "--state", "open", "--json", "number,title,labels"])
    open_issues: list[dict[str, Any]] = []
    if code == 0:
        try:
            open_issues = json.loads(out)
        except json.JSONDecodeError:
            open_issues = []
    report.details.append({"phase": "issues", "open_issues_count": len(open_issues)})

    # Phase 3: PR Discovery
    report.phases_completed.append("PR Discovery")
    code_pr, out_pr = fw.run_gh(["pr", "list", "--state", "open", "--json", "number,title"])
    open_prs: list[dict[str, Any]] = []
    if code_pr == 0:
        try:
            open_prs = json.loads(out_pr)
        except json.JSONDecodeError:
            open_prs = []
    report.open_prs_audited = len(open_prs)

    # Phase 4: Fleet Health
    if run_audit:
        try:
            from ..agent.eval import summarize_fleet_audit

            fleet_res = summarize_fleet_audit()
            report.phases_completed.append("Fleet Audit")
            fleet_status = (
                f"passed (Grade {fleet_res.get('fleet_grade', 'A+')})"
                if fleet_res.get("all_passed")
                else f"failed (Grade {fleet_res.get('fleet_grade', 'F')})"
            )
            report.details.append(
                {"phase": "fleet", "status": fleet_status, "audit_summary": fleet_res}
            )
        except Exception as e:
            logger.warning("Fleet audit failed: %s", e)
            report.details.append({"phase": "fleet", "status": "error", "error": str(e)})
    else:
        report.details.append({"phase": "fleet", "status": "skipped"})

    # Phase 5: Execute & Verify
    report.phases_completed.append("Execute & Verify")
    report.auto_merge_blocked = True
    return report


async def run_github_security_pipeline(
    framework: GitHubCLISubagentFramework | None = None,
) -> WorkflowExecutionReport:
    """Run an automated security & governance audit pipeline."""
    fw = framework or GitHubCLISubagentFramework()
    report = WorkflowExecutionReport(workflow_id="gh-dyn-security-v1")

    # Phase 1: Branch Protection Verification
    report.phases_completed.append("Branch Protection")
    code, out = fw.run_gh(["api", "repos/:owner/:repo/branches/main"])
    has_protection = False
    if code == 0:
        try:
            data = json.loads(out)
            has_protection = bool(data.get("protected", False))
        except json.JSONDecodeError:
            has_protection = False
    report.details.append({"phase": "branch_protection", "protected": has_protection})

    # Phase 2: Action Pinning Scan
    report.phases_completed.append("Action Pinning")
    workflow_dir = Path(".github/workflows")
    unpinned_actions: list[str] = []
    if workflow_dir.is_dir():
        for yml in workflow_dir.glob("*.yml"):
            try:
                content = yml.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("uses:") and "@" in line:
                        action_ref = line.split("uses:")[1].strip()
                        if "#" in action_ref:
                            action_ref = action_ref.split("#")[0].strip()
                        if "@" in action_ref:
                            _, tag_or_sha = action_ref.split("@", 1)
                            is_sha = len(tag_or_sha) == 40 and all(
                                c in "0123456789abcdefABCDEF" for c in tag_or_sha
                            )
                            if not is_sha and not tag_or_sha.startswith("./"):
                                unpinned_actions.append(f"{yml.name}: {action_ref}")
            except OSError as err:
                logger.debug("Failed reading workflow %s: %s", yml, err)
    report.details.append({"phase": "action_pinning", "unpinned_count": len(unpinned_actions)})

    # Phase 3: Credential Hygiene Check
    report.phases_completed.append("Credential Hygiene")
    sensitive_patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"hf_[a-zA-Z0-9]{30,}", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{30,}", re.IGNORECASE),
    ]
    excluded_dirs = {
        ".git",
        ".pytest_cache",
        ".venv",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        "tests",
    }
    leak_count = 0
    repo_root = Path.cwd()
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d for d in dirs if d not in excluded_dirs and (not d.startswith(".") or d == ".github")
        ]
        for f in files:
            if f.endswith((".py", ".yml", ".yaml", ".json", ".md", ".ts", ".tsx")):
                file_p = Path(root) / f
                try:
                    text = file_p.read_text(encoding="utf-8", errors="ignore")
                    for pat in sensitive_patterns:
                        for m in pat.findall(text):
                            m_lower = m.lower()
                            if any(
                                k in m_lower
                                for k in (
                                    "placeholder",
                                    "example",
                                    "dummy",
                                    "xxx",
                                    "your_",
                                    "test",
                                )
                            ):
                                continue
                            leak_count += 1
                except OSError:
                    pass
    cred_status = "clean" if leak_count == 0 else f"flagged ({leak_count} leaks)"
    report.details.append(
        {"phase": "credential_hygiene", "status": cred_status, "leak_count": leak_count}
    )

    # Phase 4: Policy Enforcement
    report.phases_completed.append("Policy Enforcement")
    report.auto_merge_blocked = True
    return report
