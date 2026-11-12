import re

def parse_git_repo_url(url: str) -> str:
    cleaned = url.strip()
    match = re.search(r"github\.com[:/]([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+?)(?:\.git)?$", cleaned)
    if not match:
        raise ValueError(f"Unable to parse repository from URL: {url}")
    return match.group(1)

def build_jules_task_command(repo: str, task: str) -> list[str]:
    return ["jules", "remote", "new", "--repo", repo, "--session", task]

def validate_patch_targets(patch_content: str, valid_files: set[str]) -> bool:
    target_files = set()
    for match in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", patch_content, re.MULTILINE):
        target_files.add(match.group(2).strip())

    if not target_files:
        return False

    return all(target in valid_files for target in target_files)

def build_apply_commands(branch: str) -> list[str]:
    return [
        f"git checkout -b {branch}",
        "git apply --index .jules/diff.patch",
        "git add .",
        "git rm --cached -r .jules 2>/dev/null || true",
        f'git commit -m "Apply Jules changes on {branch}"',
    ]
