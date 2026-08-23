"""Tests for the self-healing repo inspector.

A CI log is attacker-influenceable input: anyone who can make a job print a line
can suggest a path to read. The containment tests below are the ones that matter
most — they pin that a frame pointing outside the repository resolves to nothing.
"""

from __future__ import annotations

from pathlib import Path

from sakthai.selfheal.inspector import (
    gather_context,
    read_window,
    render_contexts,
    resolve_repo_path,
)
from sakthai.selfheal.models import FailureSignal, FileContext, LogFrame


def _repo(tmp_path: Path) -> Path:
    """A repository *below* ``tmp_path``, so "outside the repo" is a real place."""
    repo = tmp_path / "repo"
    (repo / "sakthai").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "sakthai" / "calc.py").write_text(
        "\n".join(f"line {i}" for i in range(1, 201)), encoding="utf-8"
    )
    (repo / "tests" / "test_calc.py").write_text("def test_x():\n    assert 1\n", encoding="utf-8")
    return repo


def test_resolves_a_repo_relative_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert resolve_repo_path("sakthai/calc.py", repo) == (repo / "sakthai" / "calc.py").resolve()


def test_resolves_a_runner_absolute_path_by_dropping_leading_components(tmp_path: Path) -> None:
    """``/home/runner/work/repo/repo/sakthai/calc.py`` must find the local file."""
    repo = _repo(tmp_path)

    resolved = resolve_repo_path("/home/runner/work/repo/repo/sakthai/calc.py", repo)

    assert resolved == (repo / "sakthai" / "calc.py").resolve()


def test_resolves_a_dot_slash_prefixed_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert resolve_repo_path("./sakthai/calc.py", repo) == (repo / "sakthai" / "calc.py").resolve()


def test_traversal_out_of_the_repository_resolves_to_nothing(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (tmp_path / "outside.py").write_text("secret", encoding="utf-8")

    assert resolve_repo_path("../outside.py", repo) is None


def test_absolute_path_outside_the_repository_resolves_to_nothing(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert resolve_repo_path("/etc/passwd", repo) is None


def test_symlink_escaping_the_repository_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    secret = tmp_path / "secrets.txt"
    secret.write_text("token", encoding="utf-8")
    (repo / "sakthai" / "link.py").symlink_to(secret)

    assert resolve_repo_path("sakthai/link.py", repo) is None


def test_directory_is_not_a_resolvable_frame(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert resolve_repo_path("sakthai", repo) is None


def test_empty_path_resolves_to_nothing(tmp_path: Path) -> None:
    assert resolve_repo_path("   ", _repo(tmp_path)) is None


def test_read_window_is_centred_and_bounded(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    window = read_window(repo / "sakthai" / "calc.py", 100, radius=5)

    assert window is not None
    start, end, text = window
    assert (start, end) == (95, 105)
    assert text.splitlines()[0] == "line 95"
    assert text.splitlines()[-1] == "line 105"


def test_read_window_clamps_at_the_start_of_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    window = read_window(repo / "sakthai" / "calc.py", 2, radius=10)

    assert window is not None
    assert window[0] == 1


def test_read_window_refuses_an_oversized_file(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr("sakthai.selfheal.inspector.MAX_FILE_BYTES", 10)

    assert read_window(repo / "sakthai" / "calc.py", 5) is None


def test_read_window_on_a_missing_file_returns_none(tmp_path: Path) -> None:
    assert read_window(tmp_path / "nope.py", 1) is None


def test_read_window_on_an_empty_file_returns_none(tmp_path: Path) -> None:
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")

    assert read_window(empty, 1) is None


def test_read_window_on_binary_content_returns_none(tmp_path: Path) -> None:
    binary = tmp_path / "blob.py"
    binary.write_bytes(b"\xff\xfe\x00\x80 not utf-8")

    assert read_window(binary, 1) is None


def test_gather_context_leads_with_the_innermost_frame(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    signal = FailureSignal(
        tool="pytest",
        error_type="ZeroDivisionError",
        message="division by zero",
        frames=(LogFrame("tests/test_calc.py", 1), LogFrame("sakthai/calc.py", 100)),
    )

    contexts = gather_context(signal, repo, radius=2)

    assert [c.path for c in contexts] == ["sakthai/calc.py", "tests/test_calc.py"]


def test_gather_context_skips_unresolvable_frames(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    signal = FailureSignal(
        tool="pytest",
        error_type="E",
        message="m",
        frames=(LogFrame("/etc/passwd", 1), LogFrame("sakthai/calc.py", 10)),
    )

    contexts = gather_context(signal, repo)

    assert [c.path for c in contexts] == ["sakthai/calc.py"]


def test_gather_context_deduplicates_repeated_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    signal = FailureSignal(
        tool="pytest",
        error_type="E",
        message="m",
        frames=(LogFrame("sakthai/calc.py", 10), LogFrame("sakthai/calc.py", 20)),
    )

    assert len(gather_context(signal, repo)) == 1


def test_gather_context_respects_the_file_cap(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for index in range(6):
        (repo / f"mod{index}.py").write_text("x = 1\n", encoding="utf-8")
    signal = FailureSignal(
        tool="pytest",
        error_type="E",
        message="m",
        frames=tuple(LogFrame(f"mod{i}.py", 1) for i in range(6)),
    )

    assert len(gather_context(signal, repo, max_files=2)) == 2


def test_gather_context_skips_a_file_it_cannot_read(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "blob.py").write_bytes(b"\xff\xfe\x00\x80")
    signal = FailureSignal(
        tool="pytest", error_type="E", message="m", frames=(LogFrame("blob.py", 1),)
    )

    assert gather_context(signal, repo) == ()


def test_gathered_context_is_redacted(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "leaky.py").write_text(
        'TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"\n', encoding="utf-8"
    )
    signal = FailureSignal(
        tool="pytest", error_type="E", message="m", frames=(LogFrame("leaky.py", 1),)
    )

    contexts = gather_context(signal, repo)

    assert "ghp_abcdefghijklmnopqrstuvwxyz0123456789" not in contexts[0].text


def test_signal_with_no_frames_gathers_nothing(tmp_path: Path) -> None:
    signal = FailureSignal(tool="ruff", error_type="F401", message="unused")

    assert gather_context(signal, _repo(tmp_path)) == ()


def test_render_contexts_labels_each_file_and_range() -> None:
    rendered = render_contexts((FileContext(path="a.py", start_line=3, end_line=5, text="x = 1"),))

    assert "--- a.py (lines 3-5) ---" in rendered
    assert "x = 1" in rendered


def test_render_contexts_says_so_when_there_is_nothing() -> None:
    assert "no repository context" in render_contexts(())
