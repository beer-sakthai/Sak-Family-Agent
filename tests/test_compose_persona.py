"""Tests for scripts/compose_persona.py.

This script rebuilds a persona's full skill tree as ``shared + overlay``
(overlay wins on any path collision) and is documented in CLAUDE.md as
producing output that is byte-for-byte identical to the persona's
pre-consolidation ``skills/`` directory. It lives under ``scripts/`` (not
``sakthai/``, and not an installed package), so it is loaded here via
``importlib`` rather than a normal import.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "compose_persona.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("compose_persona", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compose_persona = _load_module()


@pytest.fixture
def personas_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A synthetic ``personas/`` tree with a shared library and a sakthai overlay."""
    root = tmp_path / "personas"
    shared = root / "shared" / "skills"
    overlay = root / "sakthai" / "skills"
    shared.mkdir(parents=True)
    overlay.mkdir(parents=True)

    (shared / "shared-only.md").write_text("shared content", encoding="utf-8")
    (shared / "collides.md").write_text("shared version", encoding="utf-8")
    nested = shared / "category"
    nested.mkdir()
    (nested / "nested.md").write_text("nested shared", encoding="utf-8")

    (overlay / "overlay-only.md").write_text("overlay content", encoding="utf-8")
    (overlay / "collides.md").write_text("overlay version", encoding="utf-8")

    monkeypatch.setattr(compose_persona, "PERSONAS_DIR", root)
    return root


def test_compose_overlay_wins_on_collision(personas_dir: Path, tmp_path: Path) -> None:
    out = compose_persona.compose("sakthai", tmp_path / "out")
    assert (out / "collides.md").read_text(encoding="utf-8") == "overlay version"


def test_compose_includes_shared_only_files(personas_dir: Path, tmp_path: Path) -> None:
    out = compose_persona.compose("sakthai", tmp_path / "out")
    assert (out / "shared-only.md").read_text(encoding="utf-8") == "shared content"


def test_compose_includes_overlay_only_files(
    personas_dir: Path, tmp_path: Path
) -> None:
    out = compose_persona.compose("sakthai", tmp_path / "out")
    assert (out / "overlay-only.md").read_text(encoding="utf-8") == "overlay content"


def test_compose_preserves_nested_shared_layout(
    personas_dir: Path, tmp_path: Path
) -> None:
    out = compose_persona.compose("sakthai", tmp_path / "out")
    assert (out / "category" / "nested.md").read_text(
        encoding="utf-8"
    ) == "nested shared"


def test_compose_unknown_persona_raises(personas_dir: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        compose_persona.compose("not-a-real-persona", tmp_path / "out")


def test_compose_wipes_stale_output_directory(
    personas_dir: Path, tmp_path: Path
) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "stale.md").write_text("leftover from a previous run", encoding="utf-8")

    out = compose_persona.compose("sakthai", out_dir)

    assert not (out / "stale.md").exists()
    assert (out / "collides.md").read_text(encoding="utf-8") == "overlay version"


def test_compose_tolerates_missing_overlay_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "personas"
    shared = root / "shared" / "skills"
    shared.mkdir(parents=True)
    (shared / "only.md").write_text("shared content", encoding="utf-8")
    # sakking has no overlay skills directory at all.
    monkeypatch.setattr(compose_persona, "PERSONAS_DIR", root)

    out = compose_persona.compose("sakking", tmp_path / "out")
    assert (out / "only.md").read_text(encoding="utf-8") == "shared content"


def test_compose_tolerates_missing_shared_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "personas"
    overlay = root / "sakthai" / "skills"
    overlay.mkdir(parents=True)
    (overlay / "only.md").write_text("overlay content", encoding="utf-8")
    monkeypatch.setattr(compose_persona, "PERSONAS_DIR", root)

    out = compose_persona.compose("sakthai", tmp_path / "out")
    assert (out / "only.md").read_text(encoding="utf-8") == "overlay content"


def test_diff_reports_no_mismatches_for_identical_trees(
    personas_dir: Path, tmp_path: Path
) -> None:
    expected = compose_persona.compose("sakthai", tmp_path / "expected")
    composed = compose_persona.compose("sakthai", tmp_path / "composed")

    assert compose_persona._diff(expected, composed) == []


def test_diff_reports_content_and_presence_mismatches(
    personas_dir: Path, tmp_path: Path
) -> None:
    expected = compose_persona.compose("sakthai", tmp_path / "expected")
    composed_dir = tmp_path / "composed"
    composed_dir.mkdir()
    (composed_dir / "collides.md").write_text("wrong content", encoding="utf-8")
    (composed_dir / "unexpected.md").write_text("extra file", encoding="utf-8")

    diffs = compose_persona._diff(expected, composed_dir)

    assert any("content differs" in d and "collides.md" in d for d in diffs)
    assert any("only in composed" in d and "unexpected.md" in d for d in diffs)
    assert any("only in expected" in d for d in diffs)


def test_main_check_succeeds_on_matching_tree(
    personas_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    expected = compose_persona.compose("sakthai", tmp_path / "expected")
    out_dir = tmp_path / "out"

    exit_code = compose_persona.main(
        ["sakthai", "--out", str(out_dir), "--check", str(expected)]
    )

    assert exit_code == 0
    assert "OK: composed sakthai matches" in capsys.readouterr().out


def test_main_check_fails_on_mismatched_tree(
    personas_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    expected_dir = tmp_path / "expected"
    expected_dir.mkdir()
    (expected_dir / "does-not-exist-in-composed.md").write_text("x", encoding="utf-8")
    out_dir = tmp_path / "out"

    exit_code = compose_persona.main(
        ["sakthai", "--out", str(out_dir), "--check", str(expected_dir)]
    )

    assert exit_code == 1
    assert "MISMATCH" in capsys.readouterr().err


def test_main_without_check_reports_composed_file_count(
    personas_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out_dir = tmp_path / "out"

    exit_code = compose_persona.main(["sakthai", "--out", str(out_dir)])

    assert exit_code == 0
    assert "composed sakthai ->" in capsys.readouterr().out


def test_main_rejects_unknown_persona_via_argparse(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        compose_persona.main(["not-a-real-persona", "--out", str(tmp_path / "out")])
