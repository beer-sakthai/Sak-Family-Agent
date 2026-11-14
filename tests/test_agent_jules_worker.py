import pytest

from app.agent_platform.jules_worker import (
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


def test_parse_git_repo_url_without_dot_git():
    repo = parse_git_repo_url("https://github.com/my-org/my-project")
    assert repo == "my-org/my-project"


def test_parse_git_repo_url_trailing_slash_and_whitespace():
    repo = parse_git_repo_url("  https://github.com/my-org/my-project.git/  ")
    assert repo == "my-org/my-project"
    repo_slash = parse_git_repo_url("git@github.com:my-org/my-project/")
    assert repo_slash == "my-org/my-project"


def test_parse_git_repo_url_invalid_raises_value_error():
    with pytest.raises(ValueError, match="Unable to parse repository from URL"):
        parse_git_repo_url("https://example.com/not-github/repo.git")

    with pytest.raises(ValueError, match="Unable to parse repository from URL"):
        parse_git_repo_url("invalid-url-string")

    with pytest.raises(ValueError, match="Unable to parse repository from URL"):
        parse_git_repo_url("")


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


def test_build_jules_task_command_empty_args_raises_value_error():
    with pytest.raises(ValueError, match="Repository and task cannot be empty"):
        build_jules_task_command(repo="", task="Implement OAuth2 login")

    with pytest.raises(ValueError, match="Repository and task cannot be empty"):
        build_jules_task_command(repo="my-org/my-project", task="   ")


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


def test_validate_patch_targets_empty_patch_or_no_diff():
    assert not validate_patch_targets("", valid_files={"app/main.py"})
    assert not validate_patch_targets(
        "random text without diff headers", valid_files={"app/main.py"}
    )


def test_validate_patch_targets_multiple_files():
    patch = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
+import auth
diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,2 +1,3 @@
+TOKEN = "secret"
"""
    # All files valid
    assert validate_patch_targets(patch, valid_files={"app/main.py", "app/auth.py"})
    # One file missing from valid set
    assert not validate_patch_targets(patch, valid_files={"app/main.py"})


def test_validate_patch_targets_empty_valid_files():
    patch = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
+import auth
"""
    assert not validate_patch_targets(patch, valid_files=set())


def test_build_apply_commands():
    cmds = build_apply_commands(branch="jules-oauth2-impl")
    assert len(cmds) == 5
    assert cmds[0] == "git checkout -b jules-oauth2-impl"
    assert cmds[1] == "git apply --index .jules/diff.patch"
    assert cmds[2] == "git add ."
    assert cmds[3] == "git rm --cached -r .jules 2>/dev/null || true"
    assert cmds[4] == 'git commit -m "Apply Jules changes on jules-oauth2-impl"'


def test_build_apply_commands_empty_branch_raises_value_error():
    with pytest.raises(ValueError, match="Branch name cannot be empty"):
        build_apply_commands(branch="")

    with pytest.raises(ValueError, match="Branch name cannot be empty"):
        build_apply_commands(branch="   ")


def test_build_apply_commands_invalid_branch_names():
    invalid_branches = [
        "feature; rm -rf /",
        'feature"evil',
        "feature'evil",
        "-flag",
        "--dangerous-flag",
        "feature/../escape",
        "feature$variable",
        "feature`whoami`",
        "feature\ninjection",
        "feature|pipe",
        "feature&background",
        "feature>redirect",
        "feature<redirect",
        "feature space",
    ]
    for branch in invalid_branches:
        with pytest.raises(ValueError, match="Invalid branch name"):
            build_apply_commands(branch=branch)
