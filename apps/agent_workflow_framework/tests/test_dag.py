"""Unit tests for agent_workflow models, parser, and dag modules."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflow.models import (
    StepStatus,
    RunStatus,
    StepDefinition,
    WorkflowDefinition,
    StepResult,
    RunHistory,
)
from agent_workflow.parser import (
    WorkflowParseError,
    parse_workflow_dict,
    parse_workflow_yaml,
    parse_workflow_json,
    parse_workflow_file,
)
from agent_workflow.dag import validate_workflow_dag, build_topological_batches


class TestModels(unittest.TestCase):
    """Test suite for agent_workflow.models data structures."""

    def test_enums(self):
        self.assertTrue(StepStatus.COMPLETED.is_terminal())
        self.assertTrue(StepStatus.FAILED.is_terminal())
        self.assertTrue(StepStatus.SKIPPED.is_terminal())
        self.assertFalse(StepStatus.PENDING.is_terminal())
        self.assertFalse(StepStatus.RUNNING.is_terminal())
        self.assertTrue(StepStatus.COMPLETED.is_successful())

        self.assertTrue(RunStatus.COMPLETED.is_terminal())
        self.assertTrue(RunStatus.FAILED.is_terminal())
        self.assertFalse(RunStatus.PENDING.is_terminal())

    def test_step_definition_serialization(self):
        s = StepDefinition(
            id="s1",
            action="echo",
            params={"key": "val"},
            depends_on=["s0"],
            retry=2,
            retry_delay=1.5,
        )
        self.assertEqual(s.validate_schema(), [])
        s_dict = s.to_dict()
        s_restored = StepDefinition.from_dict(s_dict)
        self.assertEqual(s, s_restored)

    def test_workflow_definition(self):
        s1 = StepDefinition(id="s1", action="echo")
        s2 = StepDefinition(id="s2", action="python", depends_on=["s1"])
        wf = WorkflowDefinition(name="wf1", description="desc", steps=[s1, s2])

        self.assertEqual(wf.step_ids, ["s1", "s2"])
        self.assertEqual(wf.get_step("s1"), s1)
        self.assertEqual(wf.get_step("s2"), s2)
        self.assertIsNone(wf.get_step("nonexistent"))
        self.assertEqual(wf.validate_schema(), [])

        wf_dict = wf.to_dict()
        wf_restored = WorkflowDefinition.from_dict(wf_dict)
        self.assertEqual(wf, wf_restored)

    def test_step_result_and_duration(self):
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            output={"out": 123},
            start_time="2026-08-01T12:00:00+00:00",
            end_time="2026-08-01T12:00:05.5+00:00",
        )
        self.assertEqual(res.duration_seconds, 5.5)
        res_dict = res.to_dict()
        res_restored = StepResult.from_dict(res_dict)
        self.assertEqual(res, res_restored)

    def test_run_history_serialization(self):
        res1 = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00+00:00",
            end_time="2026-08-01T12:00:02+00:00",
        )
        history = RunHistory(
            run_id="run-1",
            workflow_name="wf1",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00+00:00",
            end_time="2026-08-01T12:00:10+00:00",
        )
        history.add_step_result(res1)
        self.assertEqual(history.get_step_result("s1"), res1)
        self.assertEqual(history.duration_seconds, 10.0)

        h_dict = history.to_dict()
        h_restored = RunHistory.from_dict(h_dict)
        self.assertEqual(history.run_id, h_restored.run_id)
        self.assertEqual(history.workflow_name, h_restored.workflow_name)
        self.assertEqual(history.status, h_restored.status)
        self.assertEqual(history.step_results["s1"].step_id, h_restored.step_results["s1"].step_id)


class TestParser(unittest.TestCase):
    """Test suite for agent_workflow.parser module."""

    def test_parse_valid_yaml(self):
        yaml_str = """
name: sample_workflow
description: A sample test workflow
steps:
  - id: step1
    action: echo
    params:
      message: hello
  - id: step2
    action: python
    depends_on:
      - step1
    retry: 3
    retry_delay: 2.0
"""
        wf = parse_workflow_yaml(yaml_str)
        self.assertEqual(wf.name, "sample_workflow")
        self.assertEqual(wf.description, "A sample test workflow")
        self.assertEqual(len(wf.steps), 2)
        self.assertEqual(wf.steps[0].id, "step1")
        self.assertEqual(wf.steps[1].depends_on, ["step1"])
        self.assertEqual(wf.steps[1].retry, 3)

    def test_parse_valid_json(self):
        json_str = json.dumps({
            "name": "json_wf",
            "steps": [
                {"id": "s1", "action": "echo", "params": {"x": 1}}
            ]
        })
        wf = parse_workflow_json(json_str)
        self.assertEqual(wf.name, "json_wf")
        self.assertEqual(len(wf.steps), 1)

    def test_parse_file(self):
        yaml_str = "name: file_wf\nsteps:\n  - id: s1\n    action: shell\n"
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(yaml_str)
            f_path = f.name

        try:
            wf = parse_workflow_file(f_path)
            self.assertEqual(wf.name, "file_wf")
        finally:
            Path(f_path).unlink()

    def test_parser_errors(self):
        # Empty input
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({})

        # Missing steps
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({"name": "test"})

        # Unknown attribute
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "echo"}], "extra": 123})

        # Duplicate step ID
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({
                "name": "test",
                "steps": [
                    {"id": "s1", "action": "echo"},
                    {"id": "s1", "action": "echo"}
                ]
            })

        # Non-existent file
        with self.assertRaises(WorkflowParseError):
            parse_workflow_file("/nonexistent/file/path.yaml")


class TestValidateWorkflowDAG(unittest.TestCase):
    """Test suite for validate_workflow_dag."""

    def test_valid_linear_dag(self):
        wf = WorkflowDefinition(
            name="linear",
            steps=[
                StepDefinition(id="step1", action="echo"),
                StepDefinition(id="step2", action="echo", depends_on=["step1"]),
                StepDefinition(id="step3", action="echo", depends_on=["step2"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_valid_parallel_dag(self):
        wf = WorkflowDefinition(
            name="parallel",
            steps=[
                StepDefinition(id="start", action="echo"),
                StepDefinition(id="worker1", action="echo", depends_on=["start"]),
                StepDefinition(id="worker2", action="echo", depends_on=["start"]),
                StepDefinition(id="join", action="echo", depends_on=["worker1", "worker2"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_valid_disconnected_dag(self):
        wf = WorkflowDefinition(
            name="disconnected",
            steps=[
                StepDefinition(id="a1", action="echo"),
                StepDefinition(id="a2", action="echo", depends_on=["a1"]),
                StepDefinition(id="b1", action="echo"),
                StepDefinition(id="b2", action="echo", depends_on=["b1"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_single_step_dag(self):
        wf = WorkflowDefinition(
            name="single",
            steps=[StepDefinition(id="lone_step", action="echo")],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_empty_workflow(self):
        wf = WorkflowDefinition(name="empty", steps=[])
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Workflow must contain at least one step" in err for err in errors))

    def test_duplicate_step_ids(self):
        wf = WorkflowDefinition(
            name="dup",
            steps=[
                StepDefinition(id="step1", action="echo"),
                StepDefinition(id="step1", action="echo"),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Duplicate step ID found: 'step1'" in err for err in errors))

    def test_missing_dependency(self):
        wf = WorkflowDefinition(
            name="missing_dep",
            steps=[
                StepDefinition(id="step1", action="echo", depends_on=["non_existent"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(
            any("Step 'step1' depends on non-existent step 'non_existent'" in err for err in errors)
        )

    def test_self_dependency(self):
        wf = WorkflowDefinition(
            name="self_dep",
            steps=[
                StepDefinition(id="step1", action="echo", depends_on=["step1"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Step 'step1' cannot depend on itself" in err for err in errors))

    def test_direct_cyclic_dependency(self):
        wf = WorkflowDefinition(
            name="direct_cycle",
            steps=[
                StepDefinition(id="A", action="echo", depends_on=["B"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_indirect_cyclic_dependency(self):
        wf = WorkflowDefinition(
            name="indirect_cycle",
            steps=[
                StepDefinition(id="A", action="echo", depends_on=["C"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
                StepDefinition(id="C", action="echo", depends_on=["B"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_cycle_in_subgraph(self):
        wf = WorkflowDefinition(
            name="subgraph_cycle",
            steps=[
                StepDefinition(id="ok1", action="echo"),
                StepDefinition(id="ok2", action="echo", depends_on=["ok1"]),
                StepDefinition(id="A", action="echo", depends_on=["B"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_multiple_validation_errors(self):
        wf = WorkflowDefinition(
            name="multi_error",
            steps=[
                StepDefinition(id="dup", action="echo"),
                StepDefinition(id="dup", action="echo"),
                StepDefinition(id="missing", action="echo", depends_on=["ghost"]),
                StepDefinition(id="self", action="echo", depends_on=["self"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertGreaterEqual(len(errors), 3)


class TestBuildTopologicalBatches(unittest.TestCase):
    """Test suite for build_topological_batches."""

    def test_linear_batches(self):
        s1 = StepDefinition(id="step1", action="echo")
        s2 = StepDefinition(id="step2", action="echo", depends_on=["step1"])
        s3 = StepDefinition(id="step3", action="echo", depends_on=["step2"])
        wf = WorkflowDefinition(name="linear", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2], [s3]])

    def test_parallel_fan_out_batches(self):
        s1 = StepDefinition(id="start", action="echo")
        s2 = StepDefinition(id="w1", action="echo", depends_on=["start"])
        s3 = StepDefinition(id="w2", action="echo", depends_on=["start"])
        wf = WorkflowDefinition(name="fan_out", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2, s3]])

    def test_parallel_fan_in_batches(self):
        s1 = StepDefinition(id="w1", action="echo")
        s2 = StepDefinition(id="w2", action="echo")
        s3 = StepDefinition(id="join", action="echo", depends_on=["w1", "w2"])
        wf = WorkflowDefinition(name="fan_in", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s2], [s3]])

    def test_diamond_dag_batches(self):
        s1 = StepDefinition(id="A", action="echo")
        s2 = StepDefinition(id="B", action="echo", depends_on=["A"])
        s3 = StepDefinition(id="C", action="echo", depends_on=["A"])
        s4 = StepDefinition(id="D", action="echo", depends_on=["B", "C"])
        wf = WorkflowDefinition(name="diamond", steps=[s1, s2, s3, s4])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2, s3], [s4]])

    def test_disconnected_subgraphs_batches(self):
        s1 = StepDefinition(id="a1", action="echo")
        s2 = StepDefinition(id="a2", action="echo", depends_on=["a1"])
        s3 = StepDefinition(id="b1", action="echo")
        s4 = StepDefinition(id="b2", action="echo", depends_on=["b1"])
        wf = WorkflowDefinition(name="disconnected", steps=[s1, s2, s3, s4])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s3], [s2, s4]])

    def test_single_step_batch(self):
        s1 = StepDefinition(id="single", action="echo")
        wf = WorkflowDefinition(name="single", steps=[s1])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1]])

    def test_invalid_dag_raises_value_error(self):
        s1 = StepDefinition(id="A", action="echo", depends_on=["B"])
        s2 = StepDefinition(id="B", action="echo", depends_on=["A"])
        wf = WorkflowDefinition(name="cyclic", steps=[s1, s2])
        with self.assertRaises(ValueError) as ctx:
            build_topological_batches(wf)
        self.assertIn("Invalid workflow DAG", str(ctx.exception))

    def test_batch_determinism(self):
        s1 = StepDefinition(id="alpha", action="echo")
        s2 = StepDefinition(id="beta", action="echo")
        s3 = StepDefinition(id="gamma", action="echo")
        wf = WorkflowDefinition(name="order", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s2, s3]])


if __name__ == "__main__":
    unittest.main()
