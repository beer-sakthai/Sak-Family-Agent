#!/usr/bin/env python3
"""Auto-update pull request branches when out of date with base branches.

This script identifies open pull requests whose head branch is out of date
with their target base branch (mergeable_state == 'behind'), and automatically
requests GitHub to merge the latest base branch changes into the pull request
branch via the GitHub REST API (PUT /repos/{owner}/{repo}/pulls/{number}/update-branch).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

ALLOWED_API_HOSTS = {"api.github.com"}


@dataclass
class PRUpdateResult:
    """Outcome of attempting to evaluate and update a pull request branch."""

    number: int
    title: str
    base_branch: str
    head_branch: str
    status: str  # "updated", "already_up_to_date", "conflict", "skipped", "error"
    message: str


def make_github_request(
    url: str,
    token: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    """Execute an authenticated HTTP request against GitHub's REST API."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Insecure or invalid URL scheme: {parsed.scheme}")
    if parsed.netloc not in ALLOWED_API_HOSTS:
        raise ValueError(f"Untrusted API host: {parsed.netloc}")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SakFamily-AutoUpdateBranch/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data_bytes: bytes | None = None
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            if body:
                try:
                    return status_code, json.loads(body)
                except json.JSONDecodeError:
                    return status_code, body
            return status_code, {}
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8")
        try:
            parsed_error = json.loads(error_body)
        except json.JSONDecodeError:
            parsed_error = {"message": error_body}
        return err.code, parsed_error


def fetch_open_pull_requests(
    repository: str,
    token: str,
    base_branch: str = "main",
) -> list[dict[str, Any]]:
    """Fetch all open pull requests targeting a specific base branch."""
    url = (
        f"https://api.github.com/repos/{repository}/pulls"
        f"?state=open&base={base_branch}&per_page=100"
    )
    status, data = make_github_request(url, token)
    if status != 200 or not isinstance(data, list):
        print(f"Warning: Failed to fetch pull requests targeting '{base_branch}' (HTTP {status})")
        return []
    return data


def fetch_pull_request(
    repository: str,
    token: str,
    pr_number: int,
) -> dict[str, Any] | None:
    """Fetch single pull request details including mergeable state."""
    url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    status, data = make_github_request(url, token)
    if status != 200 or not isinstance(data, dict):
        print(f"Warning: Failed to fetch pull request #{pr_number} (HTTP {status})")
        return None
    return data


def update_pr_branch(
    repository: str,
    token: str,
    pr_number: int,
    expected_head_sha: str | None = None,
) -> tuple[bool, str]:
    """Request GitHub to merge latest changes from the base branch into the PR branch."""
    url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/update-branch"
    payload: dict[str, Any] = {}
    if expected_head_sha:
        payload["expected_head_sha"] = expected_head_sha

    status, response = make_github_request(url, token, method="PUT", payload=payload)
    if status in (200, 202):
        msg = (
            response.get("message", "Updating pull request branch.")
            if isinstance(response, dict)
            else "Update initiated."
        )
        return True, msg

    error_msg = (
        response.get("message", "Unknown error")
        if isinstance(response, dict)
        else str(response)
    )
    return False, f"HTTP {status}: {error_msg}"


def evaluate_and_update_pr(
    repository: str,
    token: str,
    pr_data: dict[str, Any],
    dry_run: bool = False,
) -> PRUpdateResult:
    """Check whether a pull request is out of date and update it if appropriate."""
    pr_number = pr_data.get("number", 0)
    title = pr_data.get("title", "")
    base_ref = pr_data.get("base", {}).get("ref", "")
    head_ref = pr_data.get("head", {}).get("ref", "")
    head_repo = pr_data.get("head", {}).get("repo", {}).get("full_name")
    is_draft = pr_data.get("draft", False)

    # 1. Skip draft PRs
    if is_draft:
        return PRUpdateResult(
            number=pr_number,
            title=title,
            base_branch=base_ref,
            head_branch=head_ref,
            status="skipped",
            message="Draft pull request — skipping automatic update",
        )

    # 2. Check repository ownership (same repo vs fork)
    if head_repo != repository:
        # Cross-repository PRs require maintainer edit permission
        maintainer_can_modify = pr_data.get("maintainer_can_modify", False)
        if not maintainer_can_modify:
            return PRUpdateResult(
                number=pr_number,
                title=title,
                base_branch=base_ref,
                head_branch=head_ref,
                status="skipped",
                message="Fork PR without maintainer edit permission",
            )

    # 3. Inspect mergeable status
    # Detailed PR fetch ensures mergeable_state is populated
    detailed_pr = fetch_pull_request(repository, token, pr_number)
    if not detailed_pr:
        return PRUpdateResult(
            number=pr_number,
            title=title,
            base_branch=base_ref,
            head_branch=head_ref,
            status="error",
            message="Failed to retrieve detailed pull request metadata",
        )

    mergeable_state = detailed_pr.get("mergeable_state")
    mergeable = detailed_pr.get("mergeable")

    # If mergeable is explicitly False or state is dirty, conflicts exist
    if mergeable is False or mergeable_state == "dirty":
        return PRUpdateResult(
            number=pr_number,
            title=title,
            base_branch=base_ref,
            head_branch=head_ref,
            status="conflict",
            message="Branch has merge conflicts with base; manual resolution required",
        )

    # If mergeable_state is 'behind', base branch has new commits not in head branch
    if mergeable_state == "behind":
        if dry_run:
            return PRUpdateResult(
                number=pr_number,
                title=title,
                base_branch=base_ref,
                head_branch=head_ref,
                status="updated",
                message="[DRY-RUN] Branch is out of date; update would be requested",
            )

        success, msg = update_pr_branch(repository, token, pr_number)
        if success:
            return PRUpdateResult(
                number=pr_number,
                title=title,
                base_branch=base_ref,
                head_branch=head_ref,
                status="updated",
                message=f"Branch updated successfully: {msg}",
            )
        # Check if error message indicates conflict
        if "conflict" in msg.lower() or "not allowed" in msg.lower():
            return PRUpdateResult(
                number=pr_number,
                title=title,
                base_branch=base_ref,
                head_branch=head_ref,
                status="conflict",
                message=f"Conflict detected during update: {msg}",
            )
        return PRUpdateResult(
            number=pr_number,
            title=title,
            base_branch=base_ref,
            head_branch=head_ref,
            status="error",
            message=f"Failed to update branch: {msg}",
        )

    # Branch is clean, blocked (waiting checks/reviews), or already up to date
    if mergeable_state in ("clean", "blocked", "unstable", "has_hooks"):
        return PRUpdateResult(
            number=pr_number,
            title=title,
            base_branch=base_ref,
            head_branch=head_ref,
            status="already_up_to_date",
            message=f"Branch is up to date with base '{base_ref}' (state: {mergeable_state})",
        )

    # If mergeable_state is 'unknown', GitHub is calculating mergeability
    return PRUpdateResult(
        number=pr_number,
        title=title,
        base_branch=base_ref,
        head_branch=head_ref,
        status="already_up_to_date",
        message=f"Branch mergeability state '{mergeable_state}' does not require update",
    )


def parse_comment_trigger(comment_body: str) -> bool:
    """Detect if an issue or PR comment requests a branch update."""
    cleaned = comment_body.strip().lower()
    trigger_tokens = {"/update", "/update-branch", "/autoupdate", "@sakjules update"}
    return any(token in cleaned for token in trigger_tokens)


def generate_step_summary(results: list[PRUpdateResult]) -> str:
    """Format markdown summary for GitHub Actions Step Summary."""
    lines: list[str] = [
        "## 🔄 Pull Request Branch Synchronization Summary",
        "",
    ]
    if not results:
        lines.append("No pull requests were evaluated.")
        return "\n".join(lines)

    updated = [r for r in results if r.status == "updated"]
    up_to_date = [r for r in results if r.status == "already_up_to_date"]
    conflicts = [r for r in results if r.status == "conflict"]
    skipped = [r for r in results if r.status == "skipped"]
    errors = [r for r in results if r.status == "error"]

    lines.append(
        f"**Total Evaluated:** {len(results)} | "
        f"**Updated:** {len(updated)} | "
        f"**Up-to-Date:** {len(up_to_date)} | "
        f"**Conflicts:** {len(conflicts)} | "
        f"**Skipped:** {len(skipped)}"
    )
    lines.append("")

    if updated:
        lines.append("### 🚀 Updated Pull Request Branches")
        lines.append("| PR | Title | Base | Head | Outcome |")
        lines.append("|---|---|---|---|---|")
        for r in updated:
            lines.append(f"| #{r.number} | {r.title} | `{r.base_branch}` | `{r.head_branch}` | {r.message} |")
        lines.append("")

    if conflicts:
        lines.append("### ⚠️ Merge Conflicts (Manual Action Required)")
        lines.append("| PR | Title | Base | Head | Status |")
        lines.append("|---|---|---|---|---|")
        for r in conflicts:
            lines.append(f"| #{r.number} | {r.title} | `{r.base_branch}` | `{r.head_branch}` | {r.message} |")
        lines.append("")

    if up_to_date:
        lines.append("<details><summary><b>Already Up-to-Date Branches (" + str(len(up_to_date)) + ")</b></summary>")
        lines.append("")
        for r in up_to_date:
            lines.append(f"- PR #{r.number} (`{r.head_branch}` ➔ `{r.base_branch}`): {r.title}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    if skipped or errors:
        lines.append("<details><summary><b>Skipped / Other (" + str(len(skipped) + len(errors)) + ")</b></summary>")
        lines.append("")
        for r in skipped + errors:
            lines.append(f"- PR #{r.number} [{r.status}]: {r.message}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Auto-update PR branches when out of date with base branch."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="GitHub repository in owner/repo format",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", ""),
        help="GitHub API token",
    )
    parser.add_argument(
        "--base-branch",
        default="all",
        help="Base branch to filter by ('all', 'main', 'staging', 'develop')",
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        default=0,
        help="Specific PR number to update (0 for all open PRs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate evaluation without triggering branch updates",
    )

    args = parser.parse_args(argv)

    repository = args.repository.strip()
    token = args.token.strip()

    if not repository:
        print("Error: GITHUB_REPOSITORY or --repository is required", file=sys.stderr)
        return 1
    if not token:
        print("Error: GITHUB_TOKEN or --token is required", file=sys.stderr)
        return 1

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")

    # Read event JSON if available
    event_data: dict[str, Any] = {}
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, encoding="utf-8") as f:
                event_data = json.load(f)
        except Exception as exc:
            print(f"Warning: Could not parse GITHUB_EVENT_PATH: {exc}", file=sys.stderr)

    prs_to_evaluate: list[dict[str, Any]] = []

    # Case 1: Specific PR requested via CLI flag
    if args.pr_number > 0:
        pr = fetch_pull_request(repository, token, args.pr_number)
        if pr:
            prs_to_evaluate.append(pr)
        else:
            print(f"Error: PR #{args.pr_number} could not be fetched", file=sys.stderr)
            return 1

    # Case 2: Issue comment event
    elif event_name == "issue_comment":
        comment = event_data.get("comment", {})
        issue = event_data.get("issue", {})
        if "pull_request" in issue and parse_comment_trigger(comment.get("body", "")):
            pr_num = issue.get("number")
            print(f"Triggered by PR comment on #{pr_num}")
            pr = fetch_pull_request(repository, token, pr_num)
            if pr:
                prs_to_evaluate.append(pr)
        else:
            print("Comment does not contain branch update command. Exiting.")
            return 0

    # Case 3: Pull request event
    elif event_name == "pull_request" and "pull_request" in event_data:
        prs_to_evaluate.append(event_data["pull_request"])

    # Case 4: Push / Schedule / Workflow Run / Dispatch / Default
    else:
        bases = (
            ["main", "staging", "develop"]
            if args.base_branch == "all"
            else [args.base_branch]
        )
        seen_prs: set[int] = set()
        for base in bases:
            open_prs = fetch_open_pull_requests(repository, token, base)
            for pr in open_prs:
                num = pr.get("number")
                if num and num not in seen_prs:
                    seen_prs.add(num)
                    prs_to_evaluate.append(pr)

    print(f"Evaluating {len(prs_to_evaluate)} pull request(s) for branch updates...\n")

    results: list[PRUpdateResult] = []
    for pr in prs_to_evaluate:
        res = evaluate_and_update_pr(repository, token, pr, dry_run=args.dry_run)
        results.append(res)
        print(f"PR #{res.number} ({res.head_branch} ➔ {res.base_branch}): [{res.status.upper()}] {res.message}")

    summary_md = generate_step_summary(results)

    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write(summary_md + "\n")
        except Exception as exc:
            print(f"Warning: Failed to write to GITHUB_STEP_SUMMARY: {exc}", file=sys.stderr)

    print("\n" + "=" * 50)
    print("Branch Synchronization Completed")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
