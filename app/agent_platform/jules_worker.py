"""Jules Remote Task Delegation & Patch Orchestrator.

Orchestrates remote asynchronous task delegation to Jules (coding agent), parses
repository metadata, formats CLI execution commands, validates patch diffs against
authorized target file lists, and produces git application command sequences.
"""

import re


def parse_git_repo_url(url: str) -> str:
    """Extract owner/repo identifier from HTTPS or SSH GitHub repository URLs.

    Args:
        url: Git clone URL (HTTPS or SSH format).

    Returns:
        Canonical repository slug formatted as 'owner/repo'.

    Raises:
        ValueError: If repository URL is malformed or cannot be parsed.
    """
    cleaned = url.strip()
    if cleaned.endswith("/"):
        cleaned = cleaned.rstrip("/")

    match = re.search(
        r"github\.com[:/]([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+?)(?:\.git)?$",
        cleaned,
    )
    if not match:
        raise ValueError(f"Unable to parse repository from URL: {url}")

    return match.group(1)


def build_jules_task_command(repo: str, task: str) -> list[str]:
    """Construct command-line arguments for launching a remote Jules session.

    Args:
        repo: Repository slug in 'owner/repo' format.
        task: Remote task description or prompt.

    Returns:
        Argument list for subprocess execution.

    Raises:
        ValueError: If repository or task is empty.
    """
    if not repo or not repo.strip() or not task or not task.strip():
        raise ValueError("Repository and task cannot be empty")

    return ["jules", "remote", "new", "--repo", repo.strip(), "--session", task.strip()]


def validate_patch_targets(patch_content: str, valid_files: set[str]) -> bool:
    """Verify that all files modified by a patch diff belong to an authorized set.

    Args:
        patch_content: Unified diff / patch text content.
        valid_files: Set of authorized relative file paths.

    Returns:
        True if all target files in the patch exist in valid_files and at least one
        target file was detected; False otherwise.
    """
    target_files = set()
    for match in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", patch_content, re.MULTILINE):
        target_files.add(match.group(2).strip())

    if not target_files or not valid_files:
        return False

    return all(target in valid_files for target in target_files)


def build_apply_commands(branch: str) -> list[str]:
    """Generate shell command sequence for applying and staging Jules patch diffs.

    Args:
        branch: Target git branch name to create and check out.

    Returns:
        List of shell command strings to execute in sequence.

    Raises:
        ValueError: If branch name is empty or blank, or contains invalid characters.
    """
    cleaned_branch = branch.strip()
    if not cleaned_branch:
        raise ValueError("Branch name cannot be empty")

    if (
        not re.match(r"^[a-zA-Z0-9._/-]+$", cleaned_branch)
        or cleaned_branch.startswith("-")
        or ".." in cleaned_branch
    ):
        raise ValueError(f"Invalid branch name: {branch}")

    return [
        f"git checkout -b {cleaned_branch}",
        "git apply --index .jules/diff.patch",
        "git add .",
        "git rm --cached -r .jules 2>/dev/null || true",
        f'git commit -m "Apply Jules changes on {cleaned_branch}"',
    ]
