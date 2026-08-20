"""Tests for skill injection: render_skills_prompt_block + default_skill_roots."""

from __future__ import annotations

from pathlib import Path

from sakthai import skills as skills_mod
from sakthai.skills import default_skill_roots, render_skills_prompt_block


def _write_skill(root: Path, name: str, body: str, *, description: str = "d") -> None:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\nversion: 1.0.0\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_render_selected_skill_bodies(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", "ALPHA INSTRUCTIONS")
    _write_skill(tmp_path, "beta", "BETA INSTRUCTIONS")
    block = render_skills_prompt_block(["alpha"], roots=[tmp_path])
    assert "## Active skills" in block
    assert "### alpha" in block
    assert "ALPHA INSTRUCTIONS" in block
    assert "BETA INSTRUCTIONS" not in block  # only the selected skill


def test_render_skips_unknown_names(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", "A")
    block = render_skills_prompt_block(["alpha", "ghost"], roots=[tmp_path])
    assert "### alpha" in block
    assert "ghost" not in block


def test_render_empty_when_no_names_or_no_match(tmp_path: Path) -> None:
    assert render_skills_prompt_block([], roots=[tmp_path]) == ""
    assert render_skills_prompt_block(["nope"], roots=[tmp_path]) == ""


def test_default_skill_roots_includes_extensions(sakthai_home: Path) -> None:
    roots = default_skill_roots()
    assert skills_mod.SKILLS_DIR in roots
    assert sakthai_home / "extensions" in roots


def test_default_skill_roots_includes_shared_persona_skills(sakthai_home: Path) -> None:
    from sakthai.config import PERSONAS_DIR

    assert PERSONAS_DIR / "shared" / "skills" in default_skill_roots()


def test_shared_auto_cycle_loop_skill_resolves(sakthai_home: Path) -> None:
    # Regression guard: the shared cycle skill must be reachable at runtime
    # (it lives only in personas/shared/skills/, not skills/ or library/).
    from sakthai.skills import find_skill

    assert find_skill("Sak-auto-cycle-loop", *default_skill_roots()) is not None


def test_default_skill_roots_includes_curated_library(sakthai_home: Path) -> None:
    from sakthai.config import CURATED_LIBRARY_DIR

    assert CURATED_LIBRARY_DIR in default_skill_roots()


def test_curated_library_skill_resolves(sakthai_home: Path) -> None:
    # Regression guard: the repo-root library/ catalog (31 skills, 11
    # categories, legacy `sakthai-` names) must be reachable at runtime —
    # it used to be defined but never wired into any discovery root.
    from sakthai.skills import find_skill

    assert find_skill("sakthai-security-red-teaming", *default_skill_roots()) is not None


def test_resolve_skill_names_partitions_hits_and_misses(tmp_path: Path) -> None:
    from sakthai.skills import resolve_skill_names

    _write_skill(tmp_path, "alpha", "A")
    resolved, missing = resolve_skill_names(["alpha", "ghost"], roots=[tmp_path])
    assert resolved == ["alpha"]
    assert missing == ["ghost"]


def test_default_skill_roots_no_persona_uses_sakthai_skills_dir(sakthai_home: Path) -> None:
    """Omitting persona keeps today's behavior unchanged."""
    from sakthai.config import PERSONAS_DIR

    roots = default_skill_roots()
    assert PERSONAS_DIR / "sakthai" / "skills" in roots
    assert PERSONAS_DIR / "saksee" / "skills" not in roots


def test_default_skill_roots_persona_substitutes_own_skills_dir(sakthai_home: Path) -> None:
    """A persona's own overlay replaces SakThai's in the roots, not adds to it."""
    from sakthai.config import PERSONAS_DIR

    roots = default_skill_roots("saksee")
    assert PERSONAS_DIR / "saksee" / "skills" in roots
    assert PERSONAS_DIR / "sakthai" / "skills" not in roots


def test_resolve_skill_names_persona_scoped_finds_persona_only_skill(
    sakthai_home: Path, tmp_path: Path, monkeypatch
) -> None:
    """A skill living only under personas/<persona>/skills/ resolves with persona=<persona>."""
    from sakthai import config as config_mod
    from sakthai.skills import resolve_skill_names

    monkeypatch.setattr(config_mod, "PERSONAS_DIR", tmp_path)
    _write_skill(tmp_path / "saksee" / "skills", "SakSee-only-skill", "SEE ONLY")

    resolved_without_persona, missing_without_persona = resolve_skill_names(["SakSee-only-skill"])
    assert resolved_without_persona == []
    assert missing_without_persona == ["SakSee-only-skill"]

    resolved_with_persona, missing_with_persona = resolve_skill_names(
        ["SakSee-only-skill"], persona="saksee"
    )
    assert resolved_with_persona == ["SakSee-only-skill"]
    assert missing_with_persona == []
