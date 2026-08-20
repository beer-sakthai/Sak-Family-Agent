"""Tests for the self-healing code editor and its rollback.

The rollback guarantee is what makes the rest of the pipeline safe to run in a
CI checkout, so these tests assert the working tree is *byte-identical* after an
undo, not merely that no exception was raised.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.selfheal.models import ProposedEdit
from sakthai.selfheal.patch import PatchError, apply_edits

ORIGINAL = "def divide(a, b):\n    return a / b\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "sakthai").mkdir(parents=True)
    (root / "sakthai" / "calc.py").write_text(ORIGINAL, encoding="utf-8")
    (root / "sakthai" / "other.py").write_text("VALUE = 1\n", encoding="utf-8")
    return root


def test_applies_a_single_edit(repo: Path) -> None:
    transaction = apply_edits(
        [ProposedEdit("sakthai/calc.py", "return a / b", "return a / b if b else 0")], repo
    )

    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == (
        "def divide(a, b):\n    return a / b if b else 0\n"
    )
    assert transaction.changed_files == ("sakthai/calc.py",)
    assert transaction.applied is True


def test_rollback_restores_the_file_exactly(repo: Path) -> None:
    transaction = apply_edits([ProposedEdit("sakthai/calc.py", "return a / b", "return 0")], repo)

    restored = transaction.rollback()

    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == ORIGINAL
    assert restored == ("sakthai/calc.py",)
    assert transaction.applied is False


def test_rollback_is_idempotent(repo: Path) -> None:
    transaction = apply_edits([ProposedEdit("sakthai/calc.py", "return a / b", "return 0")], repo)
    transaction.rollback()

    assert transaction.rollback() == ()
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == ORIGINAL


def test_applies_edits_across_several_files(repo: Path) -> None:
    transaction = apply_edits(
        [
            ProposedEdit("sakthai/calc.py", "return a / b", "return 0"),
            ProposedEdit("sakthai/other.py", "VALUE = 1", "VALUE = 2"),
        ],
        repo,
    )

    assert transaction.changed_files == ("sakthai/calc.py", "sakthai/other.py")
    assert (repo / "sakthai" / "other.py").read_text(encoding="utf-8") == "VALUE = 2\n"


def test_two_edits_to_one_file_both_land_and_both_roll_back(repo: Path) -> None:
    transaction = apply_edits(
        [
            ProposedEdit("sakthai/calc.py", "def divide", "def safe_divide"),
            ProposedEdit("sakthai/calc.py", "return a / b", "return 0"),
        ],
        repo,
    )
    patched = (repo / "sakthai" / "calc.py").read_text(encoding="utf-8")

    assert patched == "def safe_divide(a, b):\n    return 0\n"

    transaction.rollback()
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == ORIGINAL


def test_a_failing_edit_rolls_back_the_ones_already_applied(repo: Path) -> None:
    """All-or-nothing: a bad second edit must not leave the first one on disk."""
    with pytest.raises(PatchError, match="expected exactly one"):
        apply_edits(
            [
                ProposedEdit("sakthai/calc.py", "return a / b", "return 0"),
                ProposedEdit("sakthai/other.py", "NOT PRESENT", "x"),
            ],
            repo,
        )

    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == ORIGINAL
    assert (repo / "sakthai" / "other.py").read_text(encoding="utf-8") == "VALUE = 1\n"


def test_ambiguous_search_text_is_refused(repo: Path) -> None:
    (repo / "sakthai" / "dup.py").write_text("x = 1\nx = 1\n", encoding="utf-8")

    with pytest.raises(PatchError, match="appears 2 times"):
        apply_edits([ProposedEdit("sakthai/dup.py", "x = 1", "x = 2")], repo)


def test_path_escaping_the_repository_is_refused(repo: Path) -> None:
    outside = repo.parent / "outside.py"
    outside.write_text("secret\n", encoding="utf-8")

    with pytest.raises(PatchError, match="resolves outside the repository"):
        apply_edits([ProposedEdit("../outside.py", "secret", "changed")], repo)

    assert outside.read_text(encoding="utf-8") == "secret\n"


def test_missing_file_is_refused(repo: Path) -> None:
    with pytest.raises(PatchError, match="not an existing file"):
        apply_edits([ProposedEdit("sakthai/nope.py", "a", "b")], repo)


def test_a_directory_target_is_refused(repo: Path) -> None:
    with pytest.raises(PatchError, match="not an existing file"):
        apply_edits([ProposedEdit("sakthai", "a", "b")], repo)


def test_unreadable_file_is_refused(repo: Path) -> None:
    (repo / "sakthai" / "blob.py").write_bytes(b"\xff\xfe\x00\x80")

    with pytest.raises(PatchError, match="cannot read"):
        apply_edits([ProposedEdit("sakthai/blob.py", "a", "b")], repo)


def test_an_empty_edit_list_is_refused(repo: Path) -> None:
    with pytest.raises(PatchError, match="no edits to apply"):
        apply_edits([], repo)


def test_a_write_failure_rolls_back(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_write = Path.write_text

    def failing_write(self: Path, *args: object, **kwargs: object) -> int:
        if self.name == "other.py":
            raise OSError("disk full")
        return real_write(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "write_text", failing_write)

    with pytest.raises(PatchError, match="cannot write"):
        apply_edits(
            [
                ProposedEdit("sakthai/calc.py", "return a / b", "return 0"),
                ProposedEdit("sakthai/other.py", "VALUE = 1", "VALUE = 2"),
            ],
            repo,
        )

    monkeypatch.undo()
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == ORIGINAL
