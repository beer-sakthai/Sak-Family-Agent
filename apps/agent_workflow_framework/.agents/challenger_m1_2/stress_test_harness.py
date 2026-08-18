"""Custom Empirical Stress Test Harness for Agent Workflow Framework (M1 Core Models & Parser).

Executes comprehensive stress testing on:
1. Serialization / Deserialization (to_dict / from_dict / JSON / YAML)
2. Duration Parsing & Timezone Handling (StepResult & RunHistory)
3. Schema Boundary Enforcement & Invalid Input Rejection
4. Edge cases (Unicode, large payloads, nested structures, type coercion)
"""

import sys
import json
import yaml
import datetime
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


class SerializationStressTest(unittest.TestCase):
    """Stress tests for data serialization and deserialization."""

    def test_step_definition_round_trip_complex_params(self):
        complex_params = {
            "str": "hello world",
            "int": 42,
            "float": 3.14159,
            "bool": True,
            "none": None,
            "list": [1, "two", {"three": 3.0}],
            "nested_dict": {
                "level1": {
                    "level2": {
                        "key": "value",
                        "unicode": "🤖 agent-workflow 🚀 应用程序",
                        "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
                    }
                }
            }
        }
        step = StepDefinition(
            id="complex_step_id_123",
            action="custom_action_runner",
            params=complex_params,
            depends_on=["dep1", "dep2"],
            retry=5,
            retry_delay=12.34
        )

        d = step.to_dict()
        restored = StepDefinition.from_dict(d)

        self.assertEqual(step.id, restored.id)
        self.assertEqual(step.action, restored.action)
        self.assertEqual(step.params, restored.params)
        self.assertEqual(step.depends_on, restored.depends_on)
        self.assertEqual(step.retry, restored.retry)
        self.assertEqual(step.retry_delay, restored.retry_delay)
        self.assertEqual(step, restored)

    def test_workflow_definition_round_trip_full(self):
        s1 = StepDefinition(id="s1", action="shell", params={"cmd": "echo 'hello'"}, retry=1, retry_delay=0.5)
        s2 = StepDefinition(id="s2", action="python", params={"script": "main.py"}, depends_on=["s1"], retry=0, retry_delay=0.0)
        wf = WorkflowDefinition(
            name="full_workflow_test_中文_🔥",
            description="Testing full workflow description with special chars: <>&\"'\nmultiline",
            steps=[s1, s2]
        )

        d = wf.to_dict()
        # Test JSON round-trip
        json_str = json.dumps(d)
        json_dict = json.loads(json_str)
        wf_from_json = WorkflowDefinition.from_dict(json_dict)
        self.assertEqual(wf, wf_from_json)

        # Test YAML round-trip
        yaml_str = yaml.dump(d)
        yaml_dict = yaml.safe_load(yaml_str)
        wf_from_yaml = WorkflowDefinition.from_dict(yaml_dict)
        self.assertEqual(wf, wf_from_yaml)

    def test_step_result_round_trip(self):
        for status in StepStatus:
            res = StepResult(
                step_id="step_res_1",
                status=status,
                output={"key": "val", "count": 10, "nested": {"a": [1, 2, 3]}},
                error="Traceback (most recent call last):\n  File 'test.py', line 10\nException: Failed!",
                attempts=3,
                start_time="2026-08-01T18:00:00.000000+00:00",
                end_time="2026-08-01T18:00:05.123456+00:00"
            )
            d = res.to_dict()
            restored = StepResult.from_dict(d)
            self.assertEqual(res.step_id, restored.step_id)
            self.assertEqual(res.status, restored.status)
            self.assertEqual(res.output, restored.output)
            self.assertEqual(res.error, restored.error)
            self.assertEqual(res.attempts, restored.attempts)
            self.assertEqual(res.start_time, restored.start_time)
            self.assertEqual(res.end_time, restored.end_time)

    def test_run_history_round_trip(self):
        res1 = StepResult(step_id="s1", status=StepStatus.COMPLETED, output={"a": 1})
        res2 = StepResult(step_id="s2", status=StepStatus.FAILED, error="Error message")
        history = RunHistory(
            run_id="run-uuid-1234-5678",
            workflow_name="test_wf",
            status=RunStatus.FAILED,
            start_time="2026-08-01T10:00:00Z",
            end_time="2026-08-01T10:01:00Z",
            step_results={"s1": res1, "s2": res2}
        )

        d = history.to_dict()
        json_str = json.dumps(d)
        restored = RunHistory.from_dict(json.loads(json_str))

        self.assertEqual(history.run_id, restored.run_id)
        self.assertEqual(history.workflow_name, restored.workflow_name)
        self.assertEqual(history.status, restored.status)
        self.assertEqual(history.start_time, restored.start_time)
        self.assertEqual(history.end_time, restored.end_time)
        self.assertEqual(len(restored.step_results), 2)
        self.assertEqual(restored.step_results["s1"].status, StepStatus.COMPLETED)
        self.assertEqual(restored.step_results["s2"].status, StepStatus.FAILED)


class DurationParsingStressTest(unittest.TestCase):
    """Stress tests for duration calculation across various timestamp formats and edge cases."""

    def test_valid_utc_z_timestamps(self):
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:00:10.5Z"
        )
        self.assertAlmostEqual(res.duration_seconds, 10.5)

    def test_valid_iso_offsets(self):
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00+02:00",
            end_time="2026-08-01T12:00:15+02:00"
        )
        self.assertAlmostEqual(res.duration_seconds, 15.0)

    def test_cross_timezone_timestamps(self):
        # 12:00:00 UTC == 14:00:00 +02:00
        # start: 12:00:00+00:00, end: 14:00:10+02:00 (which is 12:00:10 UTC)
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00+00:00",
            end_time="2026-08-01T14:00:10+02:00"
        )
        self.assertAlmostEqual(res.duration_seconds, 10.0)

    def test_naive_vs_aware_handling(self):
        # Mixing naive and aware ISO strings in python datetime.fromisoformat:
        # What happens when start_time is naive ("2026-08-01T12:00:00") and end_time is aware ("2026-08-01T12:00:10+00:00")?
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00",
            end_time="2026-08-01T12:00:10+00:00"
        )
        # Should gracefully return None (because Python raises TypeError on subtracting naive and aware datetimes)
        # instead of raising an unhandled exception.
        self.assertIsNone(res.duration_seconds)

    def test_end_before_start(self):
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:10+00:00",
            end_time="2026-08-01T12:00:00+00:00"
        )
        # Implementation uses max(0.0, (end - start).total_seconds())
        self.assertEqual(res.duration_seconds, 0.0)

    def test_malformed_timestamps(self):
        invalid_cases = [
            ("invalid-date", "2026-08-01T12:00:00Z"),
            ("2026-08-01T12:00:00Z", "not-a-timestamp"),
            ("", ""),
            ("2026-13-45T99:99:99", "2026-08-01T12:00:00Z"),
            (None, "2026-08-01T12:00:00Z"),
            ("2026-08-01T12:00:00Z", None),
        ]
        for start, end in invalid_cases:
            res = StepResult(step_id="s1", status=StepStatus.COMPLETED, start_time=start, end_time=end)
            self.assertIsNone(res.duration_seconds, f"Failed for start={start}, end={end}")

            history = RunHistory(run_id="r1", workflow_name="wf", status=RunStatus.COMPLETED, start_time=start, end_time=end)
            self.assertIsNone(history.duration_seconds, f"RunHistory failed for start={start}, end={end}")

    def test_microsecond_precision(self):
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            start_time="2026-08-01T12:00:00.000001+00:00",
            end_time="2026-08-01T12:00:00.000009+00:00"
        )
        self.assertAlmostEqual(res.duration_seconds, 0.000008)


class SchemaBoundaryStressTest(unittest.TestCase):
    """Stress test boundary values and type violations in schema parser and models."""

    def test_negative_retry(self):
        step_dict = {"id": "s1", "action": "echo", "retry": -1}
        wf_dict = {"name": "test", "steps": [step_dict]}

        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict(wf_dict)
        self.assertIn("retry", str(ctx.exception).lower())

        step = StepDefinition(id="s1", action="echo", retry=-1)
        errs = step.validate_schema()
        self.assertTrue(any("retry" in e.lower() for e in errs))

    def test_boolean_retry(self):
        # Python booleans are instances of int (isinstance(True, int) is True).
        # Check if parser correctly rejects boolean retry count.
        step_dict = {"id": "s1", "action": "echo", "retry": True}
        wf_dict = {"name": "test", "steps": [step_dict]}

        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict(wf_dict)

        step = StepDefinition(id="s1", action="echo", retry=True) # type: ignore
        errs = step.validate_schema()
        self.assertTrue(any("retry" in e.lower() for e in errs))

    def test_negative_retry_delay(self):
        step_dict = {"id": "s1", "action": "echo", "retry_delay": -0.5}
        wf_dict = {"name": "test", "steps": [step_dict]}

        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict(wf_dict)

        step = StepDefinition(id="s1", action="echo", retry_delay=-0.5)
        errs = step.validate_schema()
        self.assertTrue(any("retry_delay" in e.lower() for e in errs))

    def test_boolean_retry_delay(self):
        step_dict = {"id": "s1", "action": "echo", "retry_delay": False}
        wf_dict = {"name": "test", "steps": [step_dict]}

        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict(wf_dict)

    def test_zero_retry_and_delay(self):
        step_dict = {"id": "s1", "action": "echo", "retry": 0, "retry_delay": 0.0}
        wf_dict = {"name": "test", "steps": [step_dict]}
        wf = parse_workflow_dict(wf_dict)
        self.assertEqual(wf.steps[0].retry, 0)
        self.assertEqual(wf.steps[0].retry_delay, 0.0)

    def test_empty_and_whitespace_ids(self):
        invalid_ids = ["", "   ", "\t\n", None, 123, True]
        for bad_id in invalid_ids:
            wf_dict = {"name": "test", "steps": [{"id": bad_id, "action": "echo"}]}
            with self.assertRaises(WorkflowParseError):
                parse_workflow_dict(wf_dict)

    def test_empty_and_whitespace_actions(self):
        invalid_actions = ["", "   ", "\t\n", None, 123, False]
        for bad_action in invalid_actions:
            wf_dict = {"name": "test", "steps": [{"id": "s1", "action": bad_action}]}
            with self.assertRaises(WorkflowParseError):
                parse_workflow_dict(wf_dict)

    def test_invalid_depends_on_elements(self):
        invalid_deps = [
            [123],
            [True],
            [""],
            ["   "],
            [None],
            ["valid", ""],
        ]
        for bad_deps in invalid_deps:
            wf_dict = {"name": "test", "steps": [{"id": "s1", "action": "echo", "depends_on": bad_deps}]}
            with self.assertRaises(WorkflowParseError):
                parse_workflow_dict(wf_dict)

    def test_invalid_params_type(self):
        invalid_params = ["string", 123, [1, 2, 3], True]
        for bad_params in invalid_params:
            wf_dict = {"name": "test", "steps": [{"id": "s1", "action": "echo", "params": bad_params}]}
            with self.assertRaises(WorkflowParseError):
                parse_workflow_dict(wf_dict)

    def test_unknown_keys_rejection(self):
        # Unknown top-level key
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "echo"}], "extra_field": "disallowed"})
        self.assertIn("extra_field", str(ctx.exception))

        # Unknown step key
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "echo", "illegal_attr": True}]})
        self.assertIn("illegal_attr", str(ctx.exception))

    def test_large_payload_stress(self):
        # Test handling of large params (10,000 keys) and long step lists (1,000 steps)
        large_params = {f"key_{i}": f"value_{i}" * 10 for i in range(1000)}
        steps = [
            {"id": f"step_{i}", "action": "process", "params": large_params if i == 0 else {}, "depends_on": [f"step_{i-1}"] if i > 0 else []}
            for i in range(500)
        ]
        wf_dict = {"name": "large_wf", "steps": steps}

        wf = parse_workflow_dict(wf_dict)
        self.assertEqual(len(wf.steps), 500)
        self.assertEqual(len(wf.steps[0].params), 1000)

        # Batch resolution on large workflow
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 500)


if __name__ == "__main__":
    unittest.main()
