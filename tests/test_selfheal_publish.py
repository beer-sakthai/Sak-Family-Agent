"""Tests for the self-healing publish stage.

The branch guard is the load-bearing part: an agent that can commit to ``main``
is not proposing a fix, it is making one. Every entry point re-validates, so
these tests go at each of them rather than only at the helper.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from sakthai.selfheal.publish import (
    DEFAULT_BRANCH_PREFIX,
    PublishError,
    branch_name,
    commit_fix,
    default_runner,
    open_pull_request,
    publish_fix,
    push_branch,
    slugify,
    validate_branch,
)


class _Git:
    """A fake git/gh runner: records commands, fails the ones it is told to."""

    def __init__(self, fail_on: str = "", output: str = "") -> None:
        self.calls: list[tuple[str, ...]] = []
        self.fail_on = fail_on
        self.output = output

    def __call__(self, command: Sequence[str], cwd: Path) -> tuple[int, str]:
        self.calls.append(tuple(command))
        joined = " ".join(command)
        if self.fail_on and self.fail_on in joined:
            return 1, f"fatal: {self.fail_on} refused"
        return 0, self.output

    def ran(self, fragment: str) -> bool:
        return any(fragment in " ".join(call) for call in self.calls)


def test_slugify_produces_a_branch_safe_token() -> None:
    assert slugify("Fix ZeroDivisionError in divide()") == "fix-zerodivisionerror-in-divide"


def test_slugify_is_bounded_and_never_empty() -> None:
    assert len(slugify("x" * 200)) <= 48
    assert slugify("!!!") == "ci-fix"


def test_branch_name_carries_the_prefix_and_the_run_id() -> None:
    name = branch_name("Fix the thing", run_id="12345")

    assert name == "selfheal/fix-the-thing-12345"


def test_branch_name_without_a_run_id() -> None:
    assert branch_name("Fix the thing") == "selfheal/fix-the-thing"


@pytest.mark.parametrize("name", ["main", "master", "develop", "HEAD", "feature/x"])
def test_branches_outside_the_agent_namespace_are_refused(name: str) -> None:
    with pytest.raises(PublishError, match="must start with"):
        validate_branch(name)


@pytest.mark.parametrize("name", ["selfheal/main", "selfheal/master", "selfheal/"])
def test_protected_names_are_refused_even_inside_the_namespace(name: str) -> None:
    with pytest.raises(PublishError, match="protected branch"):
        validate_branch(name)


def test_a_namespaced_branch_is_accepted() -> None:
    validate_branch("selfheal/fix-thing-123")


def test_commit_stages_only_the_changed_files(tmp_path: Path) -> None:
    git = _Git()

    commit_fix(tmp_path, "selfheal/fix", ["a.py", "b.py"], "message", runner=git)

    assert git.calls[0] == ("git", "checkout", "-b", "selfheal/fix")
    assert git.calls[1] == ("git", "add", "--", "a.py", "b.py")
    assert git.calls[2] == ("git", "commit", "-m", "message")
    assert not git.ran("git add -A"), "a blanket add would sweep up unrelated runner state"


def test_commit_to_a_protected_branch_is_refused_before_git_runs(tmp_path: Path) -> None:
    git = _Git()

    with pytest.raises(PublishError, match="must start with"):
        commit_fix(tmp_path, "main", ["a.py"], "message", runner=git)

    assert git.calls == []


def test_commit_with_no_files_is_refused(tmp_path: Path) -> None:
    git = _Git()

    with pytest.raises(PublishError, match="no files were changed"):
        commit_fix(tmp_path, "selfheal/fix", [], "message", runner=git)


def test_a_failing_git_command_raises_with_its_output(tmp_path: Path) -> None:
    git = _Git(fail_on="commit")

    with pytest.raises(PublishError, match="git commit failed"):
        commit_fix(tmp_path, "selfheal/fix", ["a.py"], "message", runner=git)


def test_push_sets_upstream(tmp_path: Path) -> None:
    git = _Git()

    push_branch(tmp_path, "selfheal/fix", runner=git)

    assert git.calls == [("git", "push", "-u", "origin", "selfheal/fix")]


def test_push_to_a_protected_branch_is_refused(tmp_path: Path) -> None:
    git = _Git()

    with pytest.raises(PublishError, match="must start with"):
        push_branch(tmp_path, "main", runner=git)

    assert git.calls == []


def test_pull_request_body_is_passed_as_a_file_not_an_argument(tmp_path: Path) -> None:
    git = _Git(output="https://github.com/o/r/pull/7\n")
    body = tmp_path / "body.md"
    body.write_text("# report", encoding="utf-8")

    url = open_pull_request(tmp_path, "selfheal/fix", "title", body, runner=git)

    assert url == "https://github.com/o/r/pull/7"
    assert "--body-file" in git.calls[0]
    assert "--body" not in git.calls[0]


def test_pull_request_url_is_empty_when_gh_prints_none(tmp_path: Path) -> None:
    git = _Git(output="created\n")

    assert open_pull_request(tmp_path, "selfheal/fix", "t", tmp_path / "b.md", runner=git) == ""


def test_publish_fix_commits_pushes_and_opens_a_pr(tmp_path: Path) -> None:
    git = _Git(output="https://github.com/o/r/pull/9")

    result = publish_fix(
        tmp_path,
        branch="selfheal/fix",
        paths=["a.py"],
        commit_message="msg",
        pr_title="title",
        pr_body="# body",
        runner=git,
    )

    assert result.pushed is True
    assert result.pull_request_url == "https://github.com/o/r/pull/9"
    assert git.ran("gh pr create")


def test_publish_fix_cleans_up_the_temporary_body_file(tmp_path: Path) -> None:
    git = _Git(output="https://github.com/o/r/pull/9")

    publish_fix(
        tmp_path,
        branch="selfheal/fix",
        paths=["a.py"],
        commit_message="msg",
        pr_title="title",
        pr_body="# body",
        runner=git,
    )

    assert not (tmp_path / ".selfheal-pr-body.md").exists()


def test_body_file_is_removed_even_when_the_pr_call_fails(tmp_path: Path) -> None:
    git = _Git(fail_on="gh pr create")

    with pytest.raises(PublishError, match="gh pr create failed"):
        publish_fix(
            tmp_path,
            branch="selfheal/fix",
            paths=["a.py"],
            commit_message="msg",
            pr_title="title",
            pr_body="# body",
            runner=git,
        )

    assert not (tmp_path / ".selfheal-pr-body.md").exists()


def test_publish_without_opening_a_pr_stops_after_the_push(tmp_path: Path) -> None:
    git = _Git()

    result = publish_fix(
        tmp_path,
        branch="selfheal/fix",
        paths=["a.py"],
        commit_message="msg",
        pr_title="title",
        pr_body="# body",
        open_pr=False,
        runner=git,
    )

    assert result.pushed is True
    assert result.pull_request_url == ""
    assert not git.ran("gh")


def test_publish_uses_the_configured_base_branch(tmp_path: Path) -> None:
    git = _Git(output="https://github.com/o/r/pull/1")

    publish_fix(
        tmp_path,
        branch="selfheal/fix",
        paths=["a.py"],
        commit_message="msg",
        pr_title="title",
        pr_body="body",
        base="develop",
        runner=git,
    )

    pr_call = next(call for call in git.calls if call[0] == "gh")
    assert pr_call[pr_call.index("--base") + 1] == "develop"


def test_default_prefix_is_a_dedicated_namespace() -> None:
    assert DEFAULT_BRANCH_PREFIX.endswith("/")


def test_default_runner_executes_a_real_command(tmp_path: Path) -> None:
    returncode, output = default_runner(["python", "-c", "print('ok')"], tmp_path)

    assert returncode == 0
    assert "ok" in output


def test_default_runner_reports_a_missing_executable(tmp_path: Path) -> None:
    returncode, output = default_runner(["definitely-not-a-real-binary"], tmp_path)

    assert returncode == 127


def test_default_runner_reports_a_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timing_out(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="git", timeout=1.0)

    monkeypatch.setattr(subprocess, "run", timing_out)

    returncode, output = default_runner(["git", "status"], tmp_path)

    assert returncode == 124
    assert "timed out" in output
