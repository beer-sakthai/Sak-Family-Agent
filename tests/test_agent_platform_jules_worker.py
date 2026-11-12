# tests/test_agent_platform_jules_worker.py
import pytest

from sakthai.agent_platform.jules_worker import (
    build_apply_commands,
    build_jules_task_command,
    parse_git_repo_url,
    validate_patch_targets,
)


def test_parse_git_repo_url_https():
    repo = parse_git_repo_url("https://github.com/my-org/my-project.git")
    assert repo == "my-org/my-project"


def test_parse_git_repo_url_ssh():
    repo = parse_git_repo_url("git@github.com:my-org/my-project.git")
    assert repo == "my-org/my-project"


def test_parse_git_repo_url_invalid():
    with pytest.raises(ValueError, match="Unable to parse repository"):
        parse_git_repo_url("not-a-valid-url")


def test_validate_patch_empty_targets():
    assert not validate_patch_targets("invalid patch with no diff headers", {"file.py"})


def test_build_jules_task_command():
    cmd = build_jules_task_command(repo="my-org/my-project", task="Implement OAuth2 login")
    assert cmd == [
        "jules",
        "remote",
        "new",
        "--repo",
        "my-org/my-project",
        "--session",
        "Implement OAuth2 login",
    ]


def test_validate_patch_targets_matching():
    patch = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
+import auth
"""
    is_valid = validate_patch_targets(patch, valid_files={"app/main.py", "app/auth.py"})
    assert is_valid


def test_validate_patch_targets_mismatched():
    patch = """diff --git a/unrelated/foreign.go b/unrelated/foreign.go
--- a/unrelated/foreign.go
+++ b/unrelated/foreign.go
"""
    is_valid = validate_patch_targets(patch, valid_files={"app/main.py"})
    assert not is_valid


def test_build_apply_commands():
    cmds = build_apply_commands(branch="jules-oauth2-impl")
    assert cmds[0] == "git checkout -b jules-oauth2-impl"
    assert cmds[1] == "git apply --index .jules/diff.patch"
