"""Tests for Anti-Gaming & Holdout Isolation Safeguards.

Covers:
1. Three-Way Dataset Split (BaseEvalDataPoint & load_benchmark_tasks split filtering)
2. Paired Blind Judging (PairedBlindJudge, randomized A/B, de-biasing)
3. Description Token Ceiling & Few-Shot stuffing checks (ConstraintValidator)
4. Human Approval Gate (SchemaChangeValidator)
5. Snapshot Rollback (FileSessionStore & FirestoreSessionStore)
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from evolution.core.config import EvolutionConfig
from evolution.core.constraints import ConstraintValidator, SchemaChangeValidator

from evaluation_tasks.graders import (
    BenchmarkTask,
    PairedBlindJudge,
    load_benchmark_tasks,
)
from evaluation_tasks.utils import BaseEvalDataPoint
from sakthai.memory.session_store import (
    FileSessionStore,
    FirestoreSessionStore,
)
from sakthai.memory.store import MemoryStore


class TestThreeWayDatasetSplit:
    def test_base_eval_data_point_parsing(self):
        sample = {
            "testCaseId": "val-042",
            "split": "validation",
            "input": {
                "prompt": "Evaluate system performance",
                "expectedTool": "system_diagnostics",
                "maxAllowedTurns": 4,
                "simulatedToolOutput": '{"cpu": 12.5}',
                "requireA2ui": True,
            },
            "reference": {
                "expectedFacts": ["cpu", "12.5"],
                "goldenAnswer": "System CPU load is 12.5%",
            },
            "rubric": "Score 1.0 if CPU load is mentioned accurately",
        }
        dp = BaseEvalDataPoint.from_dict(sample)
        assert dp.test_case_id == "val-042"
        assert dp.split == "validation"
        assert dp.prompt == "Evaluate system performance"
        assert dp.expected_tool == "system_diagnostics"
        assert dp.max_allowed_turns == 4
        assert dp.require_a2ui is True
        assert "cpu" in dp.expected_facts
        assert dp.golden_answer == "System CPU load is 12.5%"

        task = BenchmarkTask.from_data_point(dp)
        assert task.id == "val-042"
        assert task.split == "validation"
        assert task.metadata.get("expected_tool") == "system_diagnostics"
        assert task.metadata.get("require_a2ui") is True

    def test_dataset_template_split_filtering(self):
        tasks_dev = load_benchmark_tasks("dataset-template", split="dev")
        tasks_val = load_benchmark_tasks("dataset-template", split="validation")
        tasks_holdout = load_benchmark_tasks("dataset-template", split="holdout")

        assert len(tasks_dev) == 1
        assert tasks_dev[0].id == "dev-001"
        assert tasks_dev[0].split == "dev"

        assert len(tasks_val) == 1
        assert tasks_val[0].id == "val-001"
        assert tasks_val[0].split == "validation"

        assert len(tasks_holdout) == 1
        assert tasks_holdout[0].id == "holdout-001"
        assert tasks_holdout[0].split == "holdout"


class TestPairedBlindJudging:
    def test_paired_judge_prompt_construction(self):
        prompt = PairedBlindJudge.build_judge_prompt(
            task_prompt="Calculate 2 + 2",
            rubric="Must output 4",
            response_a="The answer is 4.",
            response_b="The answer is 5.",
        )
        assert "<task_prompt>" in prompt
        assert "<response_a>" in prompt
        assert "<response_b>" in prompt
        assert "verbosity bias" in prompt

    def test_paired_judge_unswapped_candidate_win(self):
        # When swapped=True, response_a is candidate, response_b is baseline
        def mock_call_a_wins(p: str) -> str:
            return json.dumps({"winner": "A", "confidence": 0.95, "reasoning": "A is correct"})

        res = PairedBlindJudge.judge(
            task_prompt="test",
            rubric="rubric",
            baseline_trace="bad trace",
            candidate_trace="good trace",
            call_fn=mock_call_a_wins,
            force_swap=True,
        )
        assert res.winner == "candidate"
        assert res.candidate_score == 1.0
        assert res.swapped is True

        # When swapped=False, response_a is baseline, response_b is candidate
        # If judge says A wins, then baseline wins -> candidate loses
        res_baseline = PairedBlindJudge.judge(
            task_prompt="test",
            rubric="rubric",
            baseline_trace="good trace",
            candidate_trace="bad trace",
            call_fn=mock_call_a_wins,
            force_swap=False,
        )
        assert res_baseline.winner == "baseline"
        assert res_baseline.candidate_score == 0.0

    def test_paired_judge_tie(self):
        def mock_call_tie(p: str) -> str:
            return json.dumps({"winner": "TIE", "confidence": 0.5, "reasoning": "Both equal"})

        res = PairedBlindJudge.judge(
            task_prompt="test",
            rubric="rubric",
            baseline_trace="trace 1",
            candidate_trace="trace 2",
            call_fn=mock_call_tie,
        )
        assert res.winner == "tie"
        assert res.candidate_score == 0.5
        assert res.to_dict()["winner"] == "tie"


class TestDescriptionTokenCeiling:
    def test_description_token_ceiling_pass(self):
        cfg = EvolutionConfig(max_tool_desc_tokens=50, max_param_desc_tokens=20)
        val = ConstraintValidator(cfg)

        valid_evolved = (
            "[TOOL read_file]\n"
            "description: Read a file safely from disk\n"
            "parameters:\n"
            "  path: Path to file\n"
        )
        res = val._check_tool_descriptions_structure(valid_evolved)
        assert res.passed is True

    def test_description_token_ceiling_rejects_exceeded_tokens(self):
        cfg = EvolutionConfig(max_tool_desc_tokens=10, max_param_desc_tokens=10)
        val = ConstraintValidator(cfg)

        long_desc = (
            "[TOOL read_file]\n"
            "description: Read a file safely from disk with exhaustive detail and many words that exceed ten tokens\n"
            "parameters:\n"
            "  path: Path to file\n"
        )
        res = val._check_tool_descriptions_structure(long_desc)
        assert res.passed is False
        assert "exceeds token ceiling" in res.message

    def test_rejects_few_shot_example_stuffing(self):
        cfg = EvolutionConfig(forbid_few_shot_stuffing=True)
        val = ConstraintValidator(cfg)

        stuffed_desc = (
            "[TOOL search]\n"
            "description: Search query. User: find docs. Assistant: here are docs.\n"
            "parameters:\n"
            "  q: search term\n"
        )
        res = val._check_tool_descriptions_structure(stuffed_desc)
        assert res.passed is False
        assert "few-shot example stuffing detected" in res.message


class TestHumanApprovalGate:
    def test_detect_tool_deletion(self):
        baseline = {"read_file": {"parameters": {}}, "write_file": {"parameters": {}}}
        candidate = {"read_file": {"parameters": {}}}

        breaking = SchemaChangeValidator.detect_breaking_changes(baseline, candidate)
        assert any("Deleted tool: 'write_file'" in b for b in breaking)

        res = SchemaChangeValidator.validate_approval(breaking, approved=False)
        assert res.passed is False
        assert "Human approval required" in res.message

        res_approved = SchemaChangeValidator.validate_approval(breaking, approved=True)
        assert res_approved.passed is True

    def test_detect_breaking_schema_param(self):
        baseline = {"tool_a": {"parameters": {"p1": "str", "p2": "int"}, "required": ["p1"]}}
        candidate = {"tool_a": {"parameters": {"p1": "str"}, "required": ["p1"]}}

        breaking = SchemaChangeValidator.detect_breaking_changes(baseline, candidate)
        assert any("Deleted parameter 'p2'" in b for b in breaking)

    def test_detect_newly_required_param(self):
        baseline = {"tool_a": {"parameters": {"p1": "str", "p2": "int"}, "required": ["p1"]}}
        candidate = {"tool_a": {"parameters": {"p1": "str", "p2": "int"}, "required": ["p1", "p2"]}}

        breaking = SchemaChangeValidator.detect_breaking_changes(baseline, candidate)
        assert any("Newly required parameter(s)" in b for b in breaking)

    def test_detect_broadening_allowed_tools(self):
        base_allowed = ["read_file", "search"]
        cand_allowed = ["*"]
        breaking = SchemaChangeValidator.detect_breaking_changes(
            {}, {}, baseline_allowed_tools=base_allowed, candidate_allowed_tools=cand_allowed
        )
        assert any("wildcard" in b for b in breaking)


class TestSnapshotRollback:
    def test_file_session_store_checkpoint_and_revert(self):
        with TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir)
            db_path = store_dir / "test_memory.db"
            mem = MemoryStore(db_path)
            mem.add_fact(kind="fact", key="initial_key", value="initial_value")

            session_store = FileSessionStore(checkpoints_dir=store_dir / "checkpoints")

            # Checkpoint 1
            snap_id = session_store.create_checkpoint(
                snapshot_id="checkpoint-001",
                memory_store=mem,
                metadata={"test": "pass"},
            )
            assert snap_id == "checkpoint-001"
            assert "checkpoint-001" in session_store.list_checkpoints()

            # Mutate state (e.g. regression during evaluation)
            mem.delete_facts_by_key("fact", "initial_key")
            mem.add_fact(kind="fact", key="initial_key", value="corrupted_value")
            mem.add_fact(kind="fact", key="rogue_key", value="rogue_value")
            fact = mem.get_fact_by_key("fact", "initial_key")
            assert fact is not None and fact.value == "corrupted_value"

            # Rollback to Checkpoint 1
            ok = session_store.revert_checkpoint("checkpoint-001", memory_store=mem)
            assert ok is True
            initial_fact = mem.get_fact_by_key("fact", "initial_key")
            assert initial_fact is not None and initial_fact.value == "initial_value"
            assert mem.get_fact_by_key("fact", "rogue_key") is None

    def test_firestore_session_store_fallback(self):
        store = FirestoreSessionStore()
        snap_id = store.create_checkpoint(
            snapshot_id="fs-snap-1",
            session_data={"session": "data"},
            metadata={"source": "test"},
        )
        assert snap_id == "fs-snap-1"
        snap = store.get_checkpoint("fs-snap-1")
        assert snap is not None
        assert snap.session_data == {"session": "data"}
        assert "fs-snap-1" in store.list_checkpoints()
