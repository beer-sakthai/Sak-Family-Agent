"""Deep Stress Testing Script for Agent Workflow Framework (M1).

Stress tests:
1. Complex DAG graph topologies & cycle detection performance.
2. Mutation safety & object encapsulation.
3. YAML/JSON parser robustness against edge cases, corrupt data, and unicode.
4. Scale & performance limits.
"""

import sys
import time
import json
import yaml
import tempfile
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


class ComplexDAGStressTest(unittest.TestCase):
    """Stress tests for complex graph structures and cycle detection algorithms."""

    def test_deep_linear_chain(self):
        # 1000 sequential steps: s_0 -> s_1 -> ... -> s_999
        n = 1000
        steps = [
            StepDefinition(id=f"s_{i}", action="echo", depends_on=[f"s_{i-1}"] if i > 0 else [])
            for i in range(n)
        ]
        wf = WorkflowDefinition(name="linear_1000", steps=steps)

        start_t = time.perf_counter()
        errs = validate_workflow_dag(wf)
        duration = time.perf_counter() - start_t

        self.assertEqual(errs, [])
        self.assertLess(duration, 1.0, "DAG validation took too long for 1000 steps")

        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 1000)
        for i, batch in enumerate(batches):
            self.assertEqual(len(batch), 1)
            self.assertEqual(batch[0].id, f"s_{i}")

    def test_wide_fan_out_fan_in(self):
        # 1 start step, 500 parallel worker steps, 1 join step
        n_workers = 500
        start_step = StepDefinition(id="start", action="echo")
        workers = [
            StepDefinition(id=f"worker_{i}", action="echo", depends_on=["start"])
            for i in range(n_workers)
        ]
        join_step = StepDefinition(
            id="join",
            action="echo",
            depends_on=[f"worker_{i}" for i in range(n_workers)]
        )
        wf = WorkflowDefinition(name="fan_out_fan_in", steps=[start_step] + workers + [join_step])

        errs = validate_workflow_dag(wf)
        self.assertEqual(errs, [])

        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 1)
        self.assertEqual(batches[0][0].id, "start")
        self.assertEqual(len(batches[1]), n_workers)
        self.assertEqual(len(batches[2]), 1)
        self.assertEqual(batches[2][0].id, "join")

    def test_multi_node_cycle_detection(self):
        # A -> B -> C -> D -> E -> A
        steps = [
            StepDefinition(id="A", action="echo", depends_on=["E"]),
            StepDefinition(id="B", action="echo", depends_on=["A"]),
            StepDefinition(id="C", action="echo", depends_on=["B"]),
            StepDefinition(id="D", action="echo", depends_on=["C"]),
            StepDefinition(id="E", action="echo", depends_on=["D"]),
        ]
        wf = WorkflowDefinition(name="5_node_cycle", steps=steps)
        errs = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency" in err for err in errs))

    def test_multiple_disjoint_cycles(self):
        # Graph with 2 separate cycles: (A <-> B) and (X <-> Y)
        steps = [
            StepDefinition(id="A", action="echo", depends_on=["B"]),
            StepDefinition(id="B", action="echo", depends_on=["A"]),
            StepDefinition(id="X", action="echo", depends_on=["Y"]),
            StepDefinition(id="Y", action="echo", depends_on=["X"]),
            StepDefinition(id="OK", action="echo"),
        ]
        wf = WorkflowDefinition(name="disjoint_cycles", steps=steps)
        errs = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency" in err for err in errs))


class ParserEdgeCasesTest(unittest.TestCase):
    """Stress test parser against edge cases and malformed inputs."""

    def test_yaml_corrupt_syntax(self):
        corrupt_yaml = """
name: test
steps:
  - id: step1
    action: echo
  invalid_yaml_indentation: [unclosed
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(corrupt_yaml)
        self.assertIn("YAML syntax error", str(ctx.exception))

    def test_json_corrupt_syntax(self):
        corrupt_json = '{"name": "test", "steps": [{"id": "s1", "action": "echo"}'
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_json(corrupt_json)
        self.assertIn("JSON syntax error", str(ctx.exception))

    def test_parse_file_extensions(self):
        yaml_content = "name: test_ext\nsteps:\n  - id: s1\n    action: shell\n"
        for ext in [".yaml", ".yml", ".json", ".txt", ".workflow"]:
            if ext == ".json":
                content = json.dumps({"name": "test_ext", "steps": [{"id": "s1", "action": "shell"}]})
            else:
                content = yaml_content

            with tempfile.NamedTemporaryFile("w", suffix=ext, delete=False) as f:
                f.write(content)
                f_path = f.name

            try:
                wf = parse_workflow_file(f_path)
                self.assertEqual(wf.name, "test_ext")
            finally:
                Path(f_path).unlink()

    def test_floating_point_retry_delay_formats(self):
        delays = [0, 0.0, 1, 1.5, 1e-3, 10e2]
        for delay in delays:
            wf_dict = {
                "name": "delay_test",
                "steps": [{"id": "s1", "action": "echo", "retry_delay": delay}]
            }
            wf = parse_workflow_dict(wf_dict)
            self.assertEqual(wf.steps[0].retry_delay, float(delay))

    def test_unicode_and_emoji_fields(self):
        wf_dict = {
            "name": "工作流_Workflow_🚀",
            "description": "描述 description עם עברית और हिंदी 🌟",
            "steps": [
                {
                    "id": "步骤_1_⭐",
                    "action": "动作_action_🔥",
                    "params": {"输入": "值_val_🎉", "list": ["元素1", "元素2"]},
                    "retry": 2,
                    "retry_delay": 1.0
                }
            ]
        }
        wf = parse_workflow_dict(wf_dict)
        self.assertEqual(wf.name, "工作流_Workflow_🚀")
        self.assertEqual(wf.steps[0].id, "步骤_1_⭐")
        self.assertEqual(wf.steps[0].action, "动作_action_🔥")

        # Test DAG validation with unicode IDs
        errs = validate_workflow_dag(wf)
        self.assertEqual(errs, [])
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 1)


class MutationSafetyTest(unittest.TestCase):
    """Test object mutation behavior and state isolation."""

    def test_step_definition_depends_on_copy(self):
        original_deps = ["dep1", "dep2"]
        step = StepDefinition(id="s1", action="echo", depends_on=original_deps)
        d = step.to_dict()

        # Mutate dictionary's depends_on list
        d["depends_on"].append("dep3")

        # Original step dataclass depends_on should remain unchanged
        self.assertEqual(step.depends_on, ["dep1", "dep2"])

    def test_step_definition_from_dict_isolation(self):
        input_dict = {
            "id": "s1",
            "action": "echo",
            "depends_on": ["dep1"],
            "params": {"k": "v"}
        }
        step = StepDefinition.from_dict(input_dict)
        input_dict["depends_on"].append("dep2")
        input_dict["params"]["k2"] = "v2"

        self.assertEqual(step.depends_on, ["dep1"])


if __name__ == "__main__":
    unittest.main()
