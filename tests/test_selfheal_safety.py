"""Tests for the self-healing safety gate.

This is the module that decides whether a model's patch touches the repository at
all, so every test here pins the *specific* reason a patch was refused, not just
that something was refused. Several rules overlap — a path can be both protected
and sensitive — and asserting only "it was rejected" would let a rule silently
stop working behind a broader one (the trap documented in CLAUDE.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.selfheal.models import ProposedEdit
from sakthai.selfheal.safety import (
    MAX_EDITS,
    MAX_NEW_LINES,
    MAX_REMOVED_LINES,
    describe_violations,
    evaluate_edits,
    is_protected,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repository with one ordinary, editable module."""
    root = tmp_path / "repo"
    (root / "sakthai").mkdir(parents=True)
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "sakthai" / "calc.py").write_text(
        "def divide(a, b):\n    return a / b\n", encoding="utf-8"
    )
    (root / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    return root


def _edit(
    path: str = "sakthai/calc.py", old: str = "return a / b", new: str = "return 0"
) -> ProposedEdit:
    return ProposedEdit(path=path, old=old, new=new)


def _reasons(violations: tuple[str, ...]) -> str:
    return "\n".join(violations)


def test_an_ordinary_minimal_edit_is_allowed(repo: Path) -> None:
    assert evaluate_edits([_edit()], repo) == ()


def test_no_edits_is_itself_a_violation(repo: Path) -> None:
    assert evaluate_edits([], repo) == ("no edits were proposed",)


# -- scope ---------------------------------------------------------------


def test_edit_escaping_the_repository_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(path="../outside.py")], repo)

    assert "resolves outside the repository" in _reasons(violations)


def test_absolute_path_outside_the_repository_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(path="/etc/passwd")], repo)

    assert "resolves outside the repository" in _reasons(violations)


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "uv.lock",
        "Makefile",
        "scripts/release.sh",
        "infra/vm-agents/run.sh",
        "security/policy.md",
        "personas/sakthai/sakthai/agent/guardrails.py",
        "personas/sakthai/sakthai/auth.py",
        "personas/sakthai/sakthai/selfheal/safety.py",
        "tests/test_guardrails_shell.py",
        "tests/test_sentinel_paths.py",
        "tests/test_selfheal_safety.py",
        ".gitleaks.toml",
    ],
)
def test_protected_paths_are_refused(path: str) -> None:
    assert is_protected(path), f"{path} should be protected"


def test_an_ordinary_module_is_not_protected() -> None:
    assert not is_protected("personas/sakthai/sakthai/memory/store.py")
    assert not is_protected("tests/test_memory_store.py")


def test_editing_ci_config_is_refused_by_the_protected_rule(repo: Path) -> None:
    """The agent must not be able to rewrite the workflow that gates it."""
    violations = evaluate_edits(
        [ProposedEdit(path=".github/workflows/ci.yml", old="on: push", new="on: never")], repo
    )

    assert "is a protected path" in _reasons(violations)


def test_editing_a_sensitive_path_is_refused(repo: Path) -> None:
    (repo / "config").mkdir()
    (repo / "config" / "id_rsa").write_text("KEY\n", encoding="utf-8")

    violations = evaluate_edits([ProposedEdit(path="config/id_rsa", old="KEY", new="OTHER")], repo)

    assert "is a sensitive path" in _reasons(violations)


def test_creating_a_new_file_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(path="sakthai/brand_new.py")], repo)

    assert "does not exist" in _reasons(violations)


# -- shape ---------------------------------------------------------------


def test_empty_search_text_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(old="", new="anything")], repo)

    assert "empty search text" in _reasons(violations)


def test_a_no_op_replacement_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(old="return a / b", new="return a / b")], repo)

    assert "identical to the original" in _reasons(violations)


def test_search_text_that_is_not_in_the_file_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(old="return a % b")], repo)

    assert "was not found" in _reasons(violations)


def test_ambiguous_search_text_is_refused(repo: Path) -> None:
    (repo / "sakthai" / "dup.py").write_text("x = 1\nx = 1\n", encoding="utf-8")

    violations = evaluate_edits([_edit(path="sakthai/dup.py", old="x = 1", new="x = 2")], repo)

    assert "appears 2 times" in _reasons(violations)


def test_too_many_edits_are_refused(repo: Path) -> None:
    edits = [_edit() for _ in range(MAX_EDITS + 1)]

    violations = evaluate_edits(edits, repo)

    assert f"{MAX_EDITS + 1} edits proposed" in _reasons(violations)


def test_an_oversized_replacement_is_refused(repo: Path) -> None:
    violations = evaluate_edits([_edit(new="\n".join(["x = 1"] * (MAX_NEW_LINES + 1)))], repo)

    assert f"limit {MAX_NEW_LINES}" in _reasons(violations)


def test_deleting_too_much_is_refused(repo: Path) -> None:
    body = "\n".join(f"line{i} = {i}" for i in range(MAX_REMOVED_LINES + 1))
    (repo / "sakthai" / "big.py").write_text(body + "\n", encoding="utf-8")

    violations = evaluate_edits([_edit(path="sakthai/big.py", old=body, new="pass")], repo)

    assert f"limit {MAX_REMOVED_LINES}" in _reasons(violations)


def test_an_unreadable_file_does_not_crash_the_shape_check(repo: Path) -> None:
    (repo / "sakthai" / "blob.py").write_bytes(b"\xff\xfe\x00\x80")

    violations = evaluate_edits([_edit(path="sakthai/blob.py", old="a", new="b")], repo)

    # No occurrence check is possible, but the edit is not falsely reported as safe
    # by some other rule either — it simply produces no shape violation.
    assert "appears" not in _reasons(violations)


# -- content -------------------------------------------------------------


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        ("eval(user_input)", "adds eval()"),
        ("exec(payload)", "adds exec()"),
        ("__import__('os')", "adds __import__()"),
        ("os.system('rm -rf /')", "adds os.system()"),
        ("os.popen('id')", "adds os.popen()"),
        ("subprocess.run(cmd, shell=True)", "adds a shell=True subprocess call"),
        ("pickle.loads(blob)", "adds pickle deserialisation"),
        ("yaml.load(text)", "adds unsafe yaml.load()"),
        ("httpx.get(url, verify=False)", "disables TLS verification"),
        ("return a / b  # nosec", "suppresses bandit with # nosec"),
        ("return a / b  # type: ignore[no-any-return]", "suppresses mypy with # type: ignore"),
        ("return a / b  # noqa: E501", "suppresses ruff with # noqa"),
        ("return a / b  # pragma: no cover", "excludes code from coverage"),
        ("@pytest.mark.skip", "skips or xfails a test"),
        ("@pytest.mark.xfail", "skips or xfails a test"),
        ("pytest.skip('flaky')", "skips a test at runtime"),
    ],
)
def test_dangerous_replacements_are_refused_with_their_own_reason(
    repo: Path, replacement: str, expected: str
) -> None:
    violations = evaluate_edits([_edit(new=replacement)], repo)

    assert expected in _reasons(violations)


def test_a_construct_already_present_is_not_blamed_on_the_edit(repo: Path) -> None:
    """Carrying existing code through a replacement is not *introducing* it."""
    (repo / "sakthai" / "legacy.py").write_text(
        "def go():\n    return eval('1 + 1')\n", encoding="utf-8"
    )

    violations = evaluate_edits(
        [
            ProposedEdit(
                path="sakthai/legacy.py",
                old="def go():\n    return eval('1 + 1')",
                new="def go(x=0):\n    return eval('1 + 1')",
            )
        ],
        repo,
    )

    assert violations == ()


def test_a_replacement_containing_a_credential_is_refused(repo: Path) -> None:
    violations = evaluate_edits(
        [_edit(new='TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"')], repo
    )

    assert "looks like a credential" in _reasons(violations)


# -- reporting -----------------------------------------------------------


def test_every_violation_is_reported_not_just_the_first(repo: Path) -> None:
    violations = evaluate_edits(
        [ProposedEdit(path="pyproject.toml", old="[project]", new="[project]  # noqa")], repo
    )

    reasons = _reasons(violations)
    assert "is a protected path" in reasons
    assert "suppresses ruff with # noqa" in reasons


def test_describe_violations_renders_a_bullet_list() -> None:
    assert describe_violations(["a", "b"]) == "- a\n- b"


def test_describe_violations_says_none_when_empty() -> None:
    assert describe_violations([]) == "_none_"
