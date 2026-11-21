"""Tests for sakthai.agent.eval — local model eval/MLOps logging."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sakthai.agent.eval import (
    AGENTS_MD_RUBRIC_CRITERIA,
    SKILL_RUBRIC_CRITERIA,
    EvalRecord,
    _score_to_grade,
    evaluate_agents_md_trials,
    evaluate_all_personas,
    evaluate_persona_agents_md_alignment,
    evaluate_persona_audit,
    evaluate_persona_readiness,
    evaluate_persona_safety_compliance,
    evaluate_persona_skills_health,
    evaluate_persona_soul_alignment,
    evaluate_skills_trials,
    extract_soul_intro_line,
    persona_eval_log_path,
    record_eval,
    summarize_evals,
    summarize_fleet_audit,
    summarize_persona_readiness,
    task_preview,
)
from sakthai.config import PERSONA_NAMES


def _record(**overrides: object) -> EvalRecord:
    base: dict[str, object] = {
        "timestamp": 1_700_000_000,
        "task_preview": "do a thing",
        "model": "claude-opus-4-8",
        "provider": "anthropic",
        "iterations": 2,
        "stop_reason": "end_turn",
        "latency_s": 1.5,
        "input_tokens": 100,
        "output_tokens": 50,
        "tool_call_count": 1,
        "had_error": False,
    }
    base.update(overrides)
    return EvalRecord(**base)  # type: ignore[arg-type]


class TestTaskPreview:
    def test_short_task_unchanged(self) -> None:
        assert task_preview("hello") == "hello"

    def test_collapses_whitespace(self) -> None:
        assert task_preview("hello   \n\n  world") == "hello world"

    def test_truncates_long_task(self) -> None:
        long_task = "x" * 200
        preview = task_preview(long_task, limit=80)
        assert len(preview) == 80
        assert preview.endswith("…")


class TestRecordEval:
    def test_appends_jsonl_line(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(), path=log_path)
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["model"] == "claude-opus-4-8"

    def test_appends_multiple_records(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="model-a"), path=log_path)
        record_eval(_record(model="model-b"), path=log_path)
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nested" / "eval.jsonl"
        record_eval(_record(), path=log_path)
        assert log_path.exists()

    def test_never_raises_on_failure(self, tmp_path: Path) -> None:
        # Pointing at a directory (not a file) makes the open() fail; this must
        # be swallowed, matching _save_session_log's best-effort contract.
        bad_path = tmp_path  # a directory, not a file
        record_eval(_record(), path=bad_path)


class TestSummarizeEvals:
    def test_empty_log_returns_zero_count(self, tmp_path: Path) -> None:
        summary = summarize_evals(path=tmp_path / "missing.jsonl")
        assert summary == {"count": 0}

    def test_aggregates_counts_and_tokens(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(input_tokens=100, output_tokens=50), path=log_path)
        record_eval(_record(input_tokens=200, output_tokens=75), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2
        assert summary["total_input_tokens"] == 300
        assert summary["total_output_tokens"] == 125

    def test_error_rate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(had_error=False), path=log_path)
        record_eval(_record(had_error=True), path=log_path)
        record_eval(_record(had_error=True), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["error_rate"] == 2 / 3

    def test_avg_latency(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(latency_s=1.0), path=log_path)
        record_eval(_record(latency_s=3.0), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["avg_latency_s"] == 2.0

    def test_per_model_breakdown(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="model-a", latency_s=1.0), path=log_path)
        record_eval(_record(model="model-a", latency_s=3.0), path=log_path)
        record_eval(_record(model="model-b", latency_s=5.0), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["per_model"]["model-a"]["count"] == 2
        assert summary["per_model"]["model-a"]["avg_latency_s"] == 2.0
        assert summary["per_model"]["model-b"]["count"] == 1

    def test_respects_limit_by_taking_most_recent(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        for i in range(5):
            record_eval(_record(model=f"model-{i}"), path=log_path)

        summary = summarize_evals(path=log_path, limit=2)
        assert summary["count"] == 2
        assert set(summary["per_model"]) == {"model-3", "model-4"}

    def test_tolerates_malformed_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(), path=log_path)
        with log_path.open("a", encoding="utf-8") as f:
            f.write("not json\n")

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 1


class TestPersonaAttribution:
    """The persona field exists so the dashboard need not guess who ran what.

    It is a trailing defaulted field because the log is append-only: records
    written before it existed simply lack the key, and must stay readable.
    """

    def test_persona_defaults_to_none(self) -> None:
        assert _record().persona is None

    def test_persona_round_trips_through_the_log(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(persona="saksee"), path=log_path)

        line = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert line["persona"] == "saksee"

    def test_legacy_record_without_the_key_still_parses(self, tmp_path: Path) -> None:
        """A line written before this field existed must not break the reader."""
        log_path = tmp_path / "eval.jsonl"
        legacy = {
            "timestamp": 1_700_000_000,
            "task_preview": "old run",
            "model": "claude-opus-4-8",
            "provider": "anthropic",
            "iterations": 1,
            "stop_reason": "end_turn",
            "latency_s": 1.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "tool_call_count": 0,
            "had_error": False,
        }
        log_path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 1

    def test_mixed_legacy_and_attributed_lines_coexist(self, tmp_path: Path) -> None:
        """The expected steady state: some lines attributed, some not."""
        log_path = tmp_path / "eval.jsonl"
        log_path.write_text(
            json.dumps(
                {
                    "timestamp": 1_700_000_000,
                    "task_preview": "old run",
                    "model": "m",
                    "provider": "anthropic",
                    "iterations": 1,
                    "stop_reason": "end_turn",
                    "latency_s": 1.0,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "tool_call_count": 0,
                    "had_error": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        record_eval(_record(model="m", persona="sakthai"), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2
        assert summary["per_model"]["m"]["count"] == 2
        assert summary["per_persona"]["unattributed"]["count"] == 1
        assert summary["per_persona"]["sakthai"]["count"] == 1


class TestPerPersonaEvaluation:
    def test_filter_summarize_evals_by_persona(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="m1", persona="sakthai", latency_s=1.0), path=log_path)
        record_eval(_record(model="m2", persona="sakking", latency_s=3.0), path=log_path)
        record_eval(_record(model="m1", persona="sakthai", latency_s=5.0), path=log_path)

        summary = summarize_evals(path=log_path, persona="sakthai")
        assert summary["count"] == 2
        assert summary["avg_latency_s"] == 3.0
        assert set(summary["per_persona"]) == {"sakthai"}

    def test_persona_eval_log_path_and_invalid_persona(self, tmp_path: Path) -> None:
        old_home = os.environ.get("SAKTHAI_HOME")
        os.environ["SAKTHAI_HOME"] = str(tmp_path)
        try:
            path = persona_eval_log_path("sakthai")
            assert path.name == "eval.jsonl"
            assert path.parent.name == "sakthai"
        finally:
            if old_home is None:
                os.environ.pop("SAKTHAI_HOME", None)
            else:
                os.environ["SAKTHAI_HOME"] = old_home

        with pytest.raises(ValueError, match="Unknown persona"):
            persona_eval_log_path("not-a-persona")

        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_readiness("not-a-persona")

    def test_include_persona_shards_merges_and_attributes_records(self, tmp_path: Path) -> None:
        old_home = os.environ.get("SAKTHAI_HOME")
        os.environ["SAKTHAI_HOME"] = str(tmp_path)
        try:
            shard = persona_eval_log_path("saktan")
            record_eval(_record(model="sakthai", persona=None, latency_s=1.0), path=shard)
            record_eval(_record(model="sakthai", persona="saktan", latency_s=3.0), path=shard)

            summary = summarize_evals(include_persona_shards=True)
            assert summary["count"] == 2
            assert summary["per_persona"]["saktan"]["count"] == 2
        finally:
            if old_home is None:
                os.environ.pop("SAKTHAI_HOME", None)
            else:
                os.environ["SAKTHAI_HOME"] = old_home

    def test_extract_soul_intro_line_missing_returns_none(self) -> None:
        assert extract_soul_intro_line("No intro line here.") is None

    def test_evaluate_persona_readiness_incomplete_dir(self, tmp_path: Path) -> None:
        info = evaluate_persona_readiness("sakthai", personas_dir=tmp_path)
        assert info["all_working_files_present"] is False
        assert info["skill_count"] == 0
        assert info["ready"] is False
        assert info["readiness_score"] < 1.0
        assert len(info["diagnostics"]) > 0
        assert info["checks"]["working_files_present"] is False

    def test_evaluate_all_six_personas_ready(self) -> None:
        report = evaluate_all_personas()
        assert set(report) == set(PERSONA_NAMES)
        for persona, info in report.items():
            assert info["all_working_files_present"] is True, f"{persona} missing working files"
            assert info["has_v9_rubric_soul"] is True, f"{persona} missing v9 rubric in SOUL.md"
            assert info["has_v9_rubric_cycle"] is True, f"{persona} missing v9 rubric in CYCLE.md"
            assert info["intro_line"], f"{persona} missing intro_line"
            assert info["primary_skills_present"] is True, f"{persona} missing primary skills"
            assert info["evolution_ready"] is True, f"{persona} missing evolution engine"
            assert info["mcp_ready"] is True, f"{persona} invalid mcp config"
            assert info["readiness_score"] == 1.0, (
                f"{persona} score below 100%: {info['readiness_score']}"
            )
            assert info["checks_passed"] == info["checks_total"]
            assert info["diagnostics"] == []
            assert info["ready"] is True, f"{persona} not ready: {info}"

    def test_summarize_persona_readiness(self) -> None:
        summary = summarize_persona_readiness()
        assert summary["total_personas"] == 6
        assert summary["ready_personas"] == 6
        assert summary["all_ready"] is True
        assert summary["average_score"] == 1.0

        mock_data = {
            "p1": {"ready": True, "readiness_score": 1.0},
            "p2": {"ready": False, "readiness_score": 0.5},
        }
        mock_summary = summarize_persona_readiness(report=mock_data)
        assert mock_summary["total_personas"] == 2
        assert mock_summary["ready_personas"] == 1
        assert mock_summary["all_ready"] is False
        assert mock_summary["average_score"] == 0.75
        assert summarize_persona_readiness(report={})["average_score"] == 0.0

    def test_summarize_evals_percentiles_and_success_rate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(
            _record(latency_s=1.0, had_error=False, input_tokens=10, output_tokens=5), path=log_path
        )
        record_eval(
            _record(latency_s=2.0, had_error=False, input_tokens=20, output_tokens=10),
            path=log_path,
        )
        record_eval(
            _record(latency_s=4.0, had_error=True, input_tokens=30, output_tokens=15), path=log_path
        )

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 3
        assert summary["error_rate"] == pytest.approx(1 / 3)
        assert summary["success_rate"] == pytest.approx(2 / 3)
        assert summary["avg_latency_s"] == pytest.approx(7.0 / 3)
        assert summary["p50_latency_s"] == 2.0
        assert summary["p95_latency_s"] == 4.0
        assert summary["total_tokens"] == 90
        assert summary["per_model"]["claude-opus-4-8"]["success_rate"] == pytest.approx(2 / 3)
        assert summary["per_model"]["claude-opus-4-8"]["total_tokens"] == 90

    def test_read_records_edge_cases(self, tmp_path: Path) -> None:
        from sakthai.agent.eval import read_records

        log_path = tmp_path / "eval.jsonl"
        with log_path.open("w", encoding="utf-8") as f:
            f.write("\n\n")  # empty lines
        assert read_records(path=log_path) == []

        record_eval(_record(model="m1"), path=log_path)
        record_eval(_record(model="m2"), path=log_path)
        record_eval(_record(model="m3"), path=log_path)
        recs = read_records(path=log_path, limit=2)
        assert len(recs) == 2
        assert recs[-1]["model"] == "m3"

    def test_evaluate_persona_readiness_mcp_and_skills_variations(self, tmp_path: Path) -> None:
        pdir = tmp_path / "sakking"
        pdir.mkdir(parents=True)
        cdir = pdir / "config"
        cdir.mkdir()
        (cdir / "mcp.json").write_text("not json", encoding="utf-8")
        (cdir / "workspace.yaml").write_text(
            "role: Assistant\nprimary_skills:\n  - non-existent\n", encoding="utf-8"
        )
        info = evaluate_persona_readiness("sakking", personas_dir=tmp_path)
        assert info["mcp_ready"] is False
        assert "Missing or invalid config/mcp.json configuration" in info["diagnostics"]
        assert any("Missing primary skill" in d for d in info["diagnostics"])
        assert info["ready"] is False

        # mcp json with valid json but non-dict or non-dict servers
        (cdir / "mcp.json").write_text('{"mcpServers": "invalid"}', encoding="utf-8")
        info2 = evaluate_persona_readiness("sakking", personas_dir=tmp_path)
        assert info2["mcp_ready"] is True
        assert info2["mcp_servers"] == []


class TestSoulAlignment:
    def test_all_real_personas_aligned(self) -> None:
        for p in PERSONA_NAMES:
            res = evaluate_persona_soul_alignment(p)
            assert res["aligned"] is True
            assert res["soul_score"] == 1.0
            assert res["intro_line"] is not None
            assert res["checks_passed"] == res["checks_total"]
            assert len(res["diagnostics"]) == 0

    def test_unknown_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_soul_alignment("unknown_bot")

    def test_synthetic_soul_variations(self, tmp_path: Path) -> None:
        pdir = tmp_path / "sakking"
        pdir.mkdir(parents=True)
        # Missing SOUL.md
        res1 = evaluate_persona_soul_alignment("sakking", personas_dir=tmp_path)
        assert res1["aligned"] is False
        assert "Missing SOUL.md" in res1["diagnostics"]

        # Anti-pattern and missing principles
        (pdir / "SOUL.md").write_text(
            "Every reply I give begins with: **NotSak**\n"
            "As an AI language model, I do not have feelings.\n",
            encoding="utf-8",
        )
        res2 = evaluate_persona_soul_alignment("sakking", personas_dir=tmp_path)
        assert res2["aligned"] is False
        assert any("anti-patterns" in d for d in res2["diagnostics"])
        assert any("canonical" in d for d in res2["diagnostics"])


class TestSkillsHealth:
    def test_all_real_personas_healthy(self) -> None:
        for p in PERSONA_NAMES:
            res = evaluate_persona_skills_health(p)
            assert res["healthy"] is True
            assert res["skills_score"] >= 0.90
            assert res["valid_skills"] == res["total_skills"]
            assert len(res["missing_primary_skills"]) == 0

    def test_unknown_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_skills_health("unknown_bot")

    def test_synthetic_skill_variations(self, tmp_path: Path) -> None:
        from sakthai.agent.eval import evaluate_persona_skills_health

        pdir = tmp_path / "sakthai"
        sdir = pdir / "skills"
        sdir.mkdir(parents=True)
        cdir = pdir / "config"
        cdir.mkdir()
        (cdir / "workspace.yaml").write_text("primary_skills: []\n", encoding="utf-8")

        # Skill 1: Missing header
        sk1 = sdir / "skill1"
        sk1.mkdir()
        (sk1 / "SKILL.md").write_text("no header here", encoding="utf-8")

        # Skill 2: Unclosed header
        sk2 = sdir / "skill2"
        sk2.mkdir()
        (sk2 / "SKILL.md").write_text("---\nonly one marker", encoding="utf-8")

        # Skill 3: Parse error
        sk3 = sdir / "skill3"
        sk3.mkdir()
        (sk3 / "SKILL.md").write_text("---\n[unclosed yaml\n---\nbody", encoding="utf-8")

        # Skill 4: Non-dict
        sk4 = sdir / "skill4"
        sk4.mkdir()
        (sk4 / "SKILL.md").write_text("---\n- a list\n---\nbody", encoding="utf-8")

        # Skill 5: Short body
        sk5 = sdir / "skill5"
        sk5.mkdir()
        (sk5 / "SKILL.md").write_text(
            "---\nname: sk5\ndescription: d\n---\nshort", encoding="utf-8"
        )

        res = evaluate_persona_skills_health("sakthai", personas_dir=tmp_path)
        assert res["total_skills"] == 5
        assert res["valid_skills"] == 0
        assert len(res["diagnostics"]) >= 5

    def test_all_real_personas_pass_10_criteria(self) -> None:
        assert len(SKILL_RUBRIC_CRITERIA) == 10
        for p in PERSONA_NAMES:
            res = evaluate_persona_skills_health(p)
            assert res["criteria_count"] == 10
            assert res["skills_passed_all_criteria"] == res["total_skills"]
            assert res["valid_skills"] == res["total_skills"]
            assert res["skills_score"] == 1.0
            breakdown = res["dimensions_breakdown"]
            assert set(breakdown.keys()) == set(SKILL_RUBRIC_CRITERIA)
            for crit, count in breakdown.items():
                assert count == res["total_skills"], (
                    f"{p} {crit} only passed {count}/{res['total_skills']}"
                )

    def test_evaluate_skills_trials_10x(self) -> None:
        report = evaluate_skills_trials(trials=10)
        assert report["trials"] == 10
        assert report["consistent"] is True
        assert report["all_trials_healthy"] is True
        assert len(report["latencies_ms"]) == 10
        assert len(report["trial_history"]) == 10
        assert report["avg_latency_ms"] > 0
        assert report["min_latency_ms"] > 0
        assert report["max_latency_ms"] >= report["min_latency_ms"]
        assert report["jitter_ms"] >= 0
        assert len(report["latest_report"]) == 6

    def test_evaluate_skills_trials_single_persona(self) -> None:
        report = evaluate_skills_trials(persona="sakjules", trials=3)
        assert report["trials"] == 3
        assert report["persona"] == "sakjules"
        assert report["consistent"] is True
        assert report["all_trials_healthy"] is True
        assert len(report["latest_report"]) == 1
        assert "sakjules" in report["latest_report"]

    def test_evaluate_skills_trials_invalid_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_skills_trials(persona="invalid_agent")

    def test_evaluate_skills_trials_drift_detection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sakthai.agent.eval as eval_mod

        calls = 0

        def _mock_eval(persona: str, personas_dir: Path | None = None) -> dict[str, object]:
            nonlocal calls
            calls += 1
            score = 1.0 if calls <= 6 else 0.8
            return {
                "persona": persona,
                "skills_score": score,
                "healthy": score >= 0.9,
                "total_skills": 10,
                "valid_skills": 10,
                "skills_passed_all_criteria": 10,
            }

        monkeypatch.setattr(eval_mod, "evaluate_persona_skills_health", _mock_eval)
        drift_report = evaluate_skills_trials(trials=2)
        assert drift_report["trials"] == 2
        assert drift_report["consistent"] is False
        assert drift_report["all_trials_healthy"] is False


class TestMemoryHealth:
    def test_all_real_personas_memory_healthy(self) -> None:
        from sakthai.agent.eval import evaluate_persona_memory_health

        for p in PERSONA_NAMES:
            res = evaluate_persona_memory_health(p)
            assert res["healthy"] is True
            assert res["memory_score"] == 1.0

    def test_unknown_persona_raises(self) -> None:
        from sakthai.agent.eval import evaluate_persona_memory_health

        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_memory_health("unknown_bot")

    def test_existing_db_and_corrupt(self, tmp_path: Path) -> None:
        import sqlite3

        from sakthai.agent.eval import evaluate_persona_memory_health

        p_home = tmp_path / "sakking"
        p_home.mkdir(parents=True)
        db_file = p_home / "memory.db"

        # Valid DB
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE facts (id INT, key TEXT, value TEXT)")
        conn.execute("CREATE TABLE observations (id INT, value TEXT)")
        conn.execute("INSERT INTO facts VALUES (1, 'k', 'v')")
        conn.commit()
        conn.close()

        res = evaluate_persona_memory_health("sakking", home_dir=tmp_path)
        assert res["healthy"] is True
        assert res["facts_count"] == 1
        assert res["observations_count"] == 0

        # Corrupt DB
        db_file.write_text("corrupted content", encoding="utf-8")
        res_corrupt = evaluate_persona_memory_health("sakking", home_dir=tmp_path)
        assert res_corrupt["healthy"] is False
        assert any("Memory DB access error" in d for d in res_corrupt["diagnostics"])

    def test_memory_parent_dir_creation_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from sakthai.agent.eval import evaluate_persona_memory_health

        def _bad_mkdir(*args: object, **kwargs: object) -> None:
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", _bad_mkdir)
        res = evaluate_persona_memory_health("sakking", home_dir=tmp_path)
        assert res["healthy"] is False
        assert any("not writable" in d for d in res["diagnostics"])


class TestSafetyCompliance:
    def test_all_real_personas_safety_compliant(self) -> None:
        for p in PERSONA_NAMES:
            res = evaluate_persona_safety_compliance(p)
            assert res["compliant"] is True
            assert res["safety_score"] == 1.0
            assert res["checks_passed"] == res["checks_total"]

    def test_unknown_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_safety_compliance("unknown_bot")

    def test_safety_compliance_failure_branches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sakthai.agent.eval as eval_mod
        from sakthai.agent.eval import evaluate_persona_safety_compliance

        monkeypatch.setattr(eval_mod, "redact_secrets", lambda text: text)
        res = evaluate_persona_safety_compliance("sakthai")
        assert res["compliant"] is False
        assert any("Secret redaction pattern failed" in d for d in res["diagnostics"])


class TestGradeScale:
    def test_score_to_grade_all_brackets(self) -> None:
        assert _score_to_grade(1.0) == "A+"
        assert _score_to_grade(0.95) == "A+"
        assert _score_to_grade(0.92) == "A"
        assert _score_to_grade(0.87) == "A-"
        assert _score_to_grade(0.82) == "B+"
        assert _score_to_grade(0.77) == "B"
        assert _score_to_grade(0.72) == "C"
        assert _score_to_grade(0.50) == "F"


class TestAuditAndFleetSummary:
    def test_evaluate_persona_audit(self) -> None:
        for p in PERSONA_NAMES:
            card = evaluate_persona_audit(p)
            assert card["passed"] is True
            assert card["composite_score"] >= 0.90
            assert card["grade"] in ("A+", "A")
            assert set(card["pillars"].keys()) == {
                "readiness",
                "soul",
                "skills",
                "memory",
                "safety",
                "tools",
            }

    def test_summarize_fleet_audit(self) -> None:
        summary = summarize_fleet_audit()
        assert summary["personas_audited"] == 6
        assert summary["fleet_average_score"] >= 0.95
        assert summary["fleet_grade"] == "A+"
        assert summary["all_passed"] is True
        assert len(summary["scorecards"]) == 6


class TestAgentsMdAlignment:
    def test_all_real_personas_agents_md_aligned(self) -> None:
        assert len(AGENTS_MD_RUBRIC_CRITERIA) == 8
        for p in PERSONA_NAMES:
            res = evaluate_persona_agents_md_alignment(p)
            assert res["aligned"] is True, f"{p} AGENTS.md diagnostics: {res['diagnostics']}"
            assert res["agents_md_score"] == 1.0
            assert res["checks_passed"] == res["checks_total"] == 8
            assert res["diagnostics"] == []

    def test_unknown_persona_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_agents_md_alignment("unknown_bot")
        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_agents_md_trials(persona="unknown_bot")

    def test_incomplete_agents_md_reports_diagnostics(self, tmp_path: Path) -> None:
        pdir = tmp_path / "sakking"
        pdir.mkdir(parents=True)
        res = evaluate_persona_agents_md_alignment("sakking", personas_dir=tmp_path)
        assert res["aligned"] is False
        assert res["agents_md_score"] == 0.0
        assert "Missing AGENTS.md" in res["diagnostics"]

    def test_evaluate_agents_md_trials_10x(self) -> None:
        bench = evaluate_agents_md_trials(trials=10)
        assert bench["trials"] == 10
        assert bench["consistent"] is True
        assert bench["all_trials_aligned"] is True
        assert len(bench["trial_history"]) == 10
        assert len(bench["latest_report"]) == 6

        single = evaluate_agents_md_trials(persona="sakjules", trials=3)
        assert single["persona"] == "sakjules"
        assert single["trials"] == 3
        assert single["all_trials_aligned"] is True
