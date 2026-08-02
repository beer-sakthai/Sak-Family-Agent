"""Stress test harness for agent_workflow M1 (dag.py, parser.py, models.py)."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from typing import List, Dict, Set

from agent_workflow.models import WorkflowDefinition, StepDefinition, StepStatus, RunStatus
from agent_workflow.parser import (
    parse_workflow_dict,
    parse_workflow_yaml,
    parse_workflow_json,
    parse_workflow_file,
    WorkflowParseError,
)
from agent_workflow.dag import validate_workflow_dag, build_topological_batches


class TestM1StressAndEdgeCases(unittest.TestCase):
    """Stress tests and edge case verification for M1 DAG and Parser modules."""

    # -------------------------------------------------------------------------
    # 1. Large Scale DAG Tests
    # -------------------------------------------------------------------------

    def test_large_linear_dag(self):
        """Test large linear chain DAG with 500 steps (step_0 -> step_1 -> ... -> step_499)."""
        n = 500
        steps = []
        for i in range(n):
            deps = [f"step_{i-1}"] if i > 0 else []
            steps.append(StepDefinition(id=f"step_{i}", action="echo", depends_on=deps))

        wf = WorkflowDefinition(name="large_linear", steps=steps)

        t0 = time.perf_counter()
        errors = validate_workflow_dag(wf)
        t1 = time.perf_counter()
        self.assertEqual(errors, [], f"Expected 0 errors for linear DAG, got: {errors}")

        t2 = time.perf_counter()
        batches = build_topological_batches(wf)
        t3 = time.perf_counter()

        self.assertEqual(len(batches), n)
        for i, batch in enumerate(batches):
            self.assertEqual(len(batch), 1)
            self.assertEqual(batch[0].id, f"step_{i}")

        print(f"[PASS] Large linear DAG ({n} steps): validate={t1-t0:.4f}s, batch={t3-t2:.4f}s")

    def test_1000_node_linear_dag(self):
        """Test 1000-node linear DAG resolution performance."""
        n = 1000
        steps = []
        for i in range(n):
            deps = [f"s_{i-1}"] if i > 0 else []
            steps.append(StepDefinition(id=f"s_{i}", action="echo", depends_on=deps))

        wf = WorkflowDefinition(name="linear_1000", steps=steps)
        t0 = time.perf_counter()
        errors = validate_workflow_dag(wf)
        t1 = time.perf_counter()
        batches = build_topological_batches(wf)
        t2 = time.perf_counter()

        self.assertEqual(errors, [])
        self.assertEqual(len(batches), n)
        print(f"[PASS] 1000-node linear DAG: validate={t1-t0:.4f}s, batch={t2-t1:.4f}s")

    def test_large_wide_parallel_dag(self):
        """Test wide parallel DAG: 1 root -> 500 parallel nodes -> 1 leaf."""
        num_parallel = 500
        steps = [StepDefinition(id="root", action="start")]
        for i in range(num_parallel):
            steps.append(StepDefinition(id=f"mid_{i}", action="work", depends_on=["root"]))
        mid_ids = [f"mid_{i}" for i in range(num_parallel)]
        steps.append(StepDefinition(id="leaf", action="finish", depends_on=mid_ids))

        wf = WorkflowDefinition(name="wide_parallel", steps=steps)

        t0 = time.perf_counter()
        errors = validate_workflow_dag(wf)
        t1 = time.perf_counter()
        self.assertEqual(errors, [])

        t2 = time.perf_counter()
        batches = build_topological_batches(wf)
        t3 = time.perf_counter()

        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 1)
        self.assertEqual(batches[0][0].id, "root")
        self.assertEqual(len(batches[1]), num_parallel)
        self.assertEqual(len(batches[2]), 1)
        self.assertEqual(batches[2][0].id, "leaf")

        print(f"[PASS] Wide parallel DAG (1+{num_parallel}+1 steps): validate={t1-t0:.4f}s, batch={t3-t2:.4f}s")

    def test_large_dense_dag(self):
        """Test dense DAG where node i depends on all previous nodes j < i (150 nodes, ~11,000 edges)."""
        n = 150
        steps = []
        for i in range(n):
            deps = [f"node_{j}" for j in range(i)]
            steps.append(StepDefinition(id=f"node_{i}", action="compute", depends_on=deps))

        wf = WorkflowDefinition(name="dense_dag", steps=steps)

        t0 = time.perf_counter()
        errors = validate_workflow_dag(wf)
        t1 = time.perf_counter()
        self.assertEqual(errors, [])

        t2 = time.perf_counter()
        batches = build_topological_batches(wf)
        t3 = time.perf_counter()

        self.assertEqual(len(batches), n)
        print(f"[PASS] Dense DAG ({n} nodes, ~{n*(n-1)//2} edges): validate={t1-t0:.4f}s, batch={t3-t2:.4f}s")

    def test_disconnected_subgraphs(self):
        """Test DAG with 50 independent subgraphs of 5 steps each (250 total steps)."""
        steps = []
        for g in range(50):
            steps.append(StepDefinition(id=f"g{g}_s0", action="echo"))
            steps.append(StepDefinition(id=f"g{g}_s1", action="echo", depends_on=[f"g{g}_s0"]))
            steps.append(StepDefinition(id=f"g{g}_s2", action="echo", depends_on=[f"g{g}_s0"]))
            steps.append(StepDefinition(id=f"g{g}_s3", action="echo", depends_on=[f"g{g}_s1", f"g{g}_s2"]))
            steps.append(StepDefinition(id=f"g{g}_s4", action="echo", depends_on=[f"g{g}_s3"]))

        wf = WorkflowDefinition(name="disconnected_subgraphs", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 4)  # Layer 0: all s0; Layer 1: all s1, s2; Layer 2: all s3; Layer 3: all s4
        self.assertEqual(len(batches[0]), 50)
        self.assertEqual(len(batches[1]), 100)
        self.assertEqual(len(batches[2]), 50)
        self.assertEqual(len(batches[3]), 50)
        print(f"[PASS] Disconnected subgraphs (50 components x 5 steps = 250 steps): 4 batches")

    # -------------------------------------------------------------------------
    # 2. Cycle Detection Accuracy (False Positives & Negatives)
    # -------------------------------------------------------------------------

    def test_cycle_2_nodes(self):
        """Verify cycle detection on a simple A -> B -> A cycle."""
        steps = [
            StepDefinition(id="A", action="echo", depends_on=["B"]),
            StepDefinition(id="B", action="echo", depends_on=["A"]),
        ]
        wf = WorkflowDefinition(name="cycle_2", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency" in e for e in errors), f"Expected cycle error, got: {errors}")
        with self.assertRaises(ValueError):
            build_topological_batches(wf)

    def test_cycle_deep_300_nodes(self):
        """Verify cycle detection on a deep cycle of 300 nodes: 0->1->2...->299->0."""
        n = 300
        steps = []
        for i in range(n):
            prev_dep = f"step_{(i - 1) % n}"
            steps.append(StepDefinition(id=f"step_{i}", action="echo", depends_on=[prev_dep]))

        wf = WorkflowDefinition(name="deep_cycle", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency" in e for e in errors), f"Expected cycle error, got: {errors}")

    def test_disconnected_subgraph_with_cycle(self):
        """Verify cycle detection when a cyclic component exists alongside a valid component."""
        steps = [
            # Valid component
            StepDefinition(id="v1", action="echo"),
            StepDefinition(id="v2", action="echo", depends_on=["v1"]),
            # Cyclic component
            StepDefinition(id="c1", action="echo", depends_on=["c2"]),
            StepDefinition(id="c2", action="echo", depends_on=["c1"]),
        ]
        wf = WorkflowDefinition(name="disconnected_cycle", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency" in e for e in errors), f"Expected cycle error, got: {errors}")

    def test_valid_complex_diamond_and_bypass_no_false_positives(self):
        """Verify complex DAG with bypass connections (A->B, A->C, B->C, B->D, C->D) has NO cycle false positives."""
        steps = [
            StepDefinition(id="A", action="echo"),
            StepDefinition(id="B", action="echo", depends_on=["A"]),
            StepDefinition(id="C", action="echo", depends_on=["A", "B"]),
            StepDefinition(id="D", action="echo", depends_on=["B", "C"]),
        ]
        wf = WorkflowDefinition(name="bypass_dag", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [], f"False positive cycle detected: {errors}")
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 4)

    def test_self_dependency_detection(self):
        """Verify self-dependency error."""
        steps = [StepDefinition(id="A", action="echo", depends_on=["A"])]
        wf = WorkflowDefinition(name="self_dep", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("cannot depend on itself" in e for e in errors))

    def test_missing_dependency_detection(self):
        """Verify missing dependency error."""
        steps = [StepDefinition(id="A", action="echo", depends_on=["NON_EXISTENT"])]
        wf = WorkflowDefinition(name="missing_dep", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("depends on non-existent step" in e for e in errors))

    def test_duplicate_dependencies_in_depends_on(self):
        """Verify duplicate step IDs in a single step's depends_on list do not break batching."""
        steps = [
            StepDefinition(id="s1", action="echo"),
            StepDefinition(id="s2", action="echo", depends_on=["s1", "s1", "s1"]),
        ]
        wf = WorkflowDefinition(name="dup_deps", steps=steps)
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0][0].id, "s1")
        self.assertEqual(batches[1][0].id, "s2")

    # -------------------------------------------------------------------------
    # 3. Deterministic Topological Batching Order
    # -------------------------------------------------------------------------

    def test_intra_batch_declaration_ordering(self):
        """Verify steps in the same batch maintain original declaration order across permutations."""
        steps = [
            StepDefinition(id="Z", action="echo"),
            StepDefinition(id="A", action="echo"),
            StepDefinition(id="M", action="echo"),
        ]
        wf1 = WorkflowDefinition(name="w1", steps=steps)
        batches1 = build_topological_batches(wf1)
        self.assertEqual([s.id for s in batches1[0]], ["Z", "A", "M"])

        steps_perm = [
            StepDefinition(id="A", action="echo"),
            StepDefinition(id="M", action="echo"),
            StepDefinition(id="Z", action="echo"),
        ]
        wf2 = WorkflowDefinition(name="w2", steps=steps_perm)
        batches2 = build_topological_batches(wf2)
        self.assertEqual([s.id for s in batches2[0]], ["A", "M", "Z"])

    def test_multi_layer_batching_determinism(self):
        """Verify multi-layer dependency satisfaction across batches."""
        steps = [
            StepDefinition(id="in1", action="echo"),
            StepDefinition(id="in2", action="echo"),
            StepDefinition(id="p1", action="echo", depends_on=["in1", "in2"]),
            StepDefinition(id="p2", action="echo", depends_on=["in1"]),
            StepDefinition(id="out", action="echo", depends_on=["p1", "p2"]),
        ]
        wf = WorkflowDefinition(name="multi_layer", steps=steps)
        batches = build_topological_batches(wf)

        self.assertEqual(len(batches), 3)
        self.assertEqual([s.id for s in batches[0]], ["in1", "in2"])
        self.assertEqual([s.id for s in batches[1]], ["p1", "p2"])
        self.assertEqual([s.id for s in batches[2]], ["out"])

    # -------------------------------------------------------------------------
    # 4. Parser & Schema Validation (Malformed payloads & edge cases)
    # -------------------------------------------------------------------------

    def test_parse_valid_yaml_and_json(self):
        """Test parsing valid YAML and JSON strings."""
        yaml_str = """
name: test_yaml
description: A test YAML workflow
steps:
  - id: step_a
    action: echo
    params:
      msg: hello
  - id: step_b
    action: python
    depends_on:
      - step_a
    retry: 3
    retry_delay: 1.5
"""
        wf = parse_workflow_yaml(yaml_str)
        self.assertEqual(wf.name, "test_yaml")
        self.assertEqual(len(wf.steps), 2)
        self.assertEqual(wf.steps[1].retry, 3)
        self.assertEqual(wf.steps[1].retry_delay, 1.5)

        json_str = json.dumps(wf.to_dict())
        wf_json = parse_workflow_json(json_str)
        self.assertEqual(wf_json.name, "test_yaml")
        self.assertEqual(wf_json.steps[1].depends_on, ["step_a"])

    def test_parse_invalid_types_and_keys(self):
        """Test parser error handling on invalid schema attributes."""
        # Non-dict top-level
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict("not a dict")
        self.assertIn("must be a dictionary", str(ctx.exception))

        # Unknown top-level key
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "act"}], "invalid_field": 123})
        self.assertIn("Unknown top-level attribute", str(ctx.exception))

        # Missing name
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"steps": [{"id": "s1", "action": "act"}]})
        self.assertIn("missing required field 'name'", str(ctx.exception))

        # Empty steps
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": []})
        self.assertIn("must contain at least one step", str(ctx.exception))

        # Unknown step key
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "act", "extra": "bad"}]})
        self.assertIn("unknown attribute", str(ctx.exception))

        # Non-string step ID (e.g. integer 123)
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({"name": "test", "steps": [{"id": 123, "action": "act"}]})
        self.assertIn("'id' must be a non-empty string", str(ctx.exception))

        # Invalid retry (bool or string or negative)
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "act", "retry": True}]})
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "act", "retry": -1}]})
        with self.assertRaises(WorkflowParseError):
            parse_workflow_dict({"name": "test", "steps": [{"id": "s1", "action": "act", "retry_delay": -0.5}]})

        # Duplicate step ID in parser
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_dict({
                "name": "test",
                "steps": [
                    {"id": "s1", "action": "act"},
                    {"id": "s1", "action": "act2"}
                ]
            })
        self.assertIn("Duplicate step ID", str(ctx.exception))

    def test_parse_malformed_syntax(self):
        """Test handling of broken YAML or JSON syntax."""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml("name: [unclosed list")
        self.assertIn("YAML syntax error", str(ctx.exception))

        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_json("{bad_json: 123}")
        self.assertIn("JSON syntax error", str(ctx.exception))

    def test_file_parser_edge_cases(self):
        """Test parse_workflow_file error handling for nonexistent files and directories."""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_file("/nonexistent/file/path.yaml")
        self.assertIn("file not found", str(ctx.exception).lower())

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(WorkflowParseError) as ctx:
                parse_workflow_file(tmpdir)
            self.assertIn("not a file", str(ctx.exception).lower())

            # Valid temp yaml file
            yaml_path = Path(tmpdir) / "test.yaml"
            yaml_path.write_text("name: temp_wf\nsteps:\n  - id: s1\n    action: echo")
            wf = parse_workflow_file(yaml_path)
            self.assertEqual(wf.name, "temp_wf")

            # Valid temp json file
            json_path = Path(tmpdir) / "test.json"
            json_path.write_text(json.dumps({"name": "json_wf", "steps": [{"id": "s1", "action": "echo"}]}))
            wf_json = parse_workflow_file(json_path)
            self.assertEqual(wf_json.name, "json_wf")

    # -------------------------------------------------------------------------
    # 5. Unicode and Special Characters
    # -------------------------------------------------------------------------

    def test_unicode_and_special_character_ids(self):
        """Verify handling of unicode step IDs and special characters."""
        unicode_steps = [
            StepDefinition(id="🚀_start", action="launch"),
            StepDefinition(id="步骤_2", action="process", depends_on=["🚀_start"]),
            StepDefinition(id="café-node.123", action="finish", depends_on=["步骤_2"]),
        ]
        wf = WorkflowDefinition(name="unicode_wf", steps=unicode_steps)

        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0][0].id, "🚀_start")
        self.assertEqual(batches[1][0].id, "步骤_2")
        self.assertEqual(batches[2][0].id, "café-node.123")

        # Test parser with unicode YAML
        yaml_unicode = """
name: 🚀_workflow
description: 带有中文和 Emoji 的 Flow
steps:
  - id: 🚀_start
    action: launch
  - id: 步骤_2
    action: process
    depends_on:
      - 🚀_start
"""
        parsed = parse_workflow_yaml(yaml_unicode)
        self.assertEqual(parsed.name, "🚀_workflow")
        self.assertEqual(parsed.steps[1].depends_on, ["🚀_start"])


if __name__ == "__main__":
    unittest.main()
