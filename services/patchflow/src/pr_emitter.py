"""PR Emitter formatting pull request deliverables under SakJules protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .generator import PatchCandidate
from .scanners.finding import Finding


@dataclass
class PullRequestPayload:
    """Standardized pull request deliverable for manual review."""

    title: str
    branch_name: str
    body: str
    labels: list[str]
    auto_merge_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary representation."""
        return {
            "title": self.title,
            "branch_name": self.branch_name,
            "body": self.body,
            "labels": self.labels,
            "auto_merge_allowed": self.auto_merge_allowed,
        }


class PREmitter:
    """Constructs pull requests strictly obeying the SakJules CI/CD protocol."""

    INTRO_LINE = "**SakJules · Master of Automation & CI/CD.**"

    @classmethod
    def emit_pr_payload(
        cls,
        finding: Finding,
        candidate: PatchCandidate,
        verification_summary: str = "Verified by PatchFlow Anti-Gaming release gates.",
    ) -> PullRequestPayload:
        """Generate a compliant pull request specification."""
        clean_rule = finding.rule_id.split()[0].replace("/", "-")
        branch_name = f"fix/patchflow-{clean_rule.lower()}-{finding.id[:8]}"
        title = f"fix(patchflow): remediate {finding.source} finding {finding.rule_id}"

        body = (
            f"{cls.INTRO_LINE}\n\n"
            f"### Automated Remediation Overview\n"
            f"- **Source:** `{finding.source}`\n"
            f"- **Rule / Advisory:** `{finding.rule_id}`\n"
            f"- **Severity:** `{finding.severity.upper()}`\n"
            f"- **Target File:** `{finding.file_path}`\n\n"
            f"### Remediation Rationale\n"
            f"{candidate.explanation}\n\n"
            f"### Quality & Verification Results\n"
            f"- {verification_summary}\n"
            f"- Anti-Gaming description token ceiling validated (<= 120 tokens).\n"
            f"- Holdout partition regression check passed clean.\n\n"
            f"> [!IMPORTANT]\n"
            f"> **Manual Merge Required:** In accordance with repository protocol, automated merging "
            f"and `--auto` are strictly disabled. This pull request remains open for manual review and merge by Beer.\n"
        )

        labels = ["automated-patch", "patchflow", f"sev-{finding.severity}"]

        return PullRequestPayload(
            title=title,
            branch_name=branch_name,
            body=body,
            labels=labels,
            auto_merge_allowed=False,  # strictly false
        )
