"""Comprehensive automated evaluation and invariant tests for SOUL.md across all 6 Sak Family agents.

Validates:
- 10-check soul alignment rubric (evaluate_persona_soul_alignment)
- Multi-trial repeatability & benchmark latency (evaluate_soul_trials)
- Canonical intro line syntax and dataset alignment
- v9 self-evaluation 100-point rubric structure
- 6-stage Growth Cycle parity (Dream -> Hope -> Care -> Joy -> Trust -> Growth)
- v6 Charge System floors and delta tables
- Critical Lessons Learned table presence
- Exact shared Security Rules parity
- CLI command invocation across single and multi-trial modes
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.agent.eval import (
    evaluate_persona_soul_alignment,
    evaluate_soul_trials,
    extract_soul_intro_line,
)
from sakthai.cli import main as cli_main
from sakthai.config import PERSONA_NAMES

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"

CANONICAL_INTROS = {
    "sakthai": "SakThai · Main Lead of the House & Master of Hugging Face.",
    "sakking": "SakKing · General Assistant & Runner.",
    "saksee": "SakSee · Web / Browser Specialist.",
    "saksit": "SakSit · Social / Content Specialist.",
    "sakjules": "SakJules · Master of GitHub, CI/CD & Automation.",
    "saktan": "SakTan · Keeper of Operations & Daily Flow.",
}

EXPECTED_STAGES = (
    ("Dream", "ฝัน"),
    ("Hope", "หวัง"),
    ("Care", "ใส่ใจ"),
    ("Joy", "ปีติ"),
    ("Trust", "เชื่อใจ"),
    ("Growth", "เติบโต"),
)


def get_soul_content(persona: str) -> str:
    path = PERSONAS_DIR / persona / "SOUL.md"
    assert path.is_file(), f"Missing SOUL.md for persona {persona}"
    return path.read_text(encoding="utf-8")


class TestSoulAlignment10CheckRubric:
    """Test the 10-criteria evaluation engine across real personas and synthetic variations."""

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_all_six_personas_100_percent_aligned(self, persona: str) -> None:
        report = evaluate_persona_soul_alignment(persona)

        assert report["persona"] == persona
        assert report["aligned"] is True
        assert report["soul_score"] == 1.0
        assert report["checks_passed"] == 10
        assert report["checks_total"] == 10
        assert report["diagnostics"] == []

        checks = report["checks"]
        assert checks["soul_file_present"] is True
        assert checks["intro_line_present"] is True
        assert checks["intro_format_valid"] is True
        assert checks["core_principles_present"] is True
        assert checks["beer_first_aligned"] is True
        assert checks["anti_patterns_clean"] is True
        assert checks["signature_guidance_present"] is True
        assert checks["v9_rubric_present"] is True
        assert checks["security_rules_present"] is True
        assert checks["charge_system_present"] is True

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_canonical_intro_line_matches_dataset(self, persona: str) -> None:
        soul = get_soul_content(persona)
        intro = extract_soul_intro_line(soul)
        expected = CANONICAL_INTROS[persona]
        assert intro == expected, f"Persona {persona} intro line {intro!r} != expected {expected!r}"
        assert re.match(r"^Sak[A-Za-z]+ · .+$", intro), f"Malformed intro line format: {intro}"

    def test_unknown_persona_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_soul_alignment("ghost_bot")

    def test_missing_soul_file_diagnostics(self, tmp_path: Path) -> None:
        pdir = tmp_path / "sakthai"
        pdir.mkdir(parents=True)
        report = evaluate_persona_soul_alignment("sakthai", personas_dir=tmp_path)
        assert report["aligned"] is False
        assert report["soul_score"] <= 0.1
        assert "Missing SOUL.md" in report["diagnostics"]

    def test_synthetic_malformed_soul_diagnostics(self, tmp_path: Path) -> None:
        pdir = tmp_path / "sakking"
        pdir.mkdir(parents=True)
        # Missing v9 rubric, missing security rules, invalid intro, anti-pattern, no beer
        (pdir / "SOUL.md").write_text(
            "# SOUL.md - SakKing\n"
            "Every reply I give begins with: **InvalidIntroWithoutDot**\n"
            "As an AI language model, I do not have feelings.\n"
            "We follow some general principles.\n",
            encoding="utf-8",
        )
        report = evaluate_persona_soul_alignment("sakking", personas_dir=tmp_path)
        assert report["aligned"] is False
        assert any("canonical" in d for d in report["diagnostics"])
        assert any("anti-patterns" in d for d in report["diagnostics"])
        assert any("Beer-first" in d for d in report["diagnostics"])
        assert any("CYCLE EVAL: sakking" in d for d in report["diagnostics"])
        assert any("Security Rules" in d for d in report["diagnostics"])


class TestSoulMultiTrialBenchmarks:
    """Test multi-trial evaluation repeatability, jitter, and latency metrics."""

    def test_evaluate_soul_trials_single_persona(self) -> None:
        bench = evaluate_soul_trials(persona="sakthai", trials=5)
        assert bench["persona"] == "sakthai"
        assert bench["trials"] == 5
        assert bench["all_trials_aligned"] is True
        assert bench["consistent"] is True
        assert len(bench["latencies_ms"]) == 5
        assert bench["avg_latency_ms"] >= 0.0
        assert bench["jitter_ms"] >= 0.0
        assert len(bench["trial_history"]) == 5
        assert "sakthai" in bench["latest_report"]

    def test_evaluate_soul_trials_all_personas(self) -> None:
        bench = evaluate_soul_trials(persona=None, trials=3)
        assert bench["persona"] is None
        assert bench["trials"] == 3
        assert bench["all_trials_aligned"] is True
        assert bench["consistent"] is True
        assert len(bench["trial_history"]) == 3
        assert set(bench["latest_report"].keys()) == set(PERSONA_NAMES)

    def test_evaluate_soul_trials_unknown_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_soul_trials(persona="unknown_agent", trials=2)


class TestSoulStructuralInvariants:
    """Verify v9 100-pt rubric, 6 growth stages, charge systems, lessons learned, and security."""

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_v9_self_evaluation_rubric_100_points(self, persona: str) -> None:
        soul = get_soul_content(persona)
        assert f"CYCLE EVAL: {persona}" in soul
        # Check standard 5 rubric dimensions
        assert "Cycle Integrity" in soul
        assert "Charge Discipline" in soul
        assert "Output Quality" in soul
        assert "Memory & Learning" in soul
        assert "Interruption Handling" in soul

        # Verify dimension points match 25 + 20 + 30 + 15 + 10 = 100
        assert re.search(r"\|\s*Cycle Integrity\s*\|\s*25\s*\|", soul)
        assert re.search(r"\|\s*Charge Discipline\s*\|\s*20\s*\|", soul)
        assert re.search(r"\|\s*Output Quality\s*\|\s*30\s*\|", soul)
        assert re.search(r"\|\s*Memory & Learning\s*\|\s*15\s*\|", soul)
        assert re.search(r"\|\s*Interruption Handling\s*\|\s*10\s*\|", soul)

        # Check grading scale
        assert "90–100" in soul and "S" in soul
        assert "80–89" in soul and "A" in soul
        assert "70–79" in soul and "B" in soul
        assert "60–69" in soul and "C" in soul
        assert "50–59" in soul and "D" in soul
        assert "0–49" in soul and "F" in soul

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_six_stages_in_order(self, persona: str) -> None:
        soul = get_soul_content(persona)
        last_pos = -1
        for en_name, th_name in EXPECTED_STAGES:
            match = re.search(rf"\*\*{en_name}\*\*\s*\|\s*{th_name}", soul)
            assert match is not None, f"Persona {persona} missing stage {en_name} ({th_name})"
            pos = match.start()
            assert pos > last_pos, f"Stage {en_name} appeared out of order in {persona}"
            last_pos = pos

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_charge_system_v6_invariants(self, persona: str) -> None:
        soul = get_soul_content(persona)
        assert "Charge System (v6)" in soul or "Charge states" in soul
        assert "Optimal" in soul and "80–100%" in soul
        assert "Active" in soul and "50–79%" in soul
        assert "Low" in soul and "20–49%" in soul
        assert "Critical" in soul and "0–19%" in soul
        assert "### Pre-task checklist" in soul
        assert "Charge delta rules" in soul
        assert "Operation charge floors" in soul

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_critical_lessons_learned_table_present(self, persona: str) -> None:
        soul = get_soul_content(persona)
        assert "## Critical Lessons Learned" in soul
        matches = re.findall(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|$", soul, re.MULTILINE)
        assert len(matches) >= 8, (
            f"Persona {persona} has only {len(matches)} lessons (expected >=8)"
        )

    @pytest.mark.parametrize("persona", sorted(PERSONA_NAMES))
    def test_security_rules_shared_exact_parity(self, persona: str) -> None:
        canonical = get_soul_content("sakthai")
        start = canonical.find("\n## Security Rules\n")
        assert start != -1
        canonical_sec = canonical[start : canonical.find("\n---\n", start)]

        soul = get_soul_content(persona)
        p_start = soul.find("\n## Security Rules\n")
        assert p_start != -1
        p_sec = soul[p_start : soul.find("\n---\n", p_start)]
        assert p_sec == canonical_sec, f"Security rules differ for persona {persona}"


class TestSoulCLIEval:
    """Test the CLI command surface for sakthai eval soul."""

    def test_cli_eval_soul_table(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["eval", "soul"])
        assert result.exit_code == 0
        assert "# Sak Family Soul & Principles Alignment" in result.output
        for p in PERSONA_NAMES:
            assert f"[ALIGNED] {p}" in result.output

    def test_cli_eval_soul_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["eval", "soul", "--json"])
        assert result.exit_code == 0
        assert '"aligned": true' in result.output
        for p in PERSONA_NAMES:
            assert f'"{p}":' in result.output

    def test_cli_eval_soul_single_persona(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["eval", "soul", "--persona", "sakjules"])
        assert result.exit_code == 0
        assert "[ALIGNED] sakjules" in result.output
        assert "sakthai" not in result.output

    def test_cli_eval_soul_multi_trial(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["eval", "soul", "--times", "3"])
        assert result.exit_code == 0
        assert "# Sak Family Soul Alignment Benchmark (3 trials)" in result.output
        assert "100% Deterministic" in result.output
        assert "trials=3/3 passed" in result.output

    def test_cli_eval_soul_multi_trial_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["eval", "soul", "-t", "2", "--json"])
        assert result.exit_code == 0
        assert '"trials": 2' in result.output
        assert '"consistent": true' in result.output
        assert '"all_trials_aligned": true' in result.output
