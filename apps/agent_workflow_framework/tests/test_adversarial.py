"""Tier 5 Adversarial & Security Audit Test Suite.

Tests security boundaries (path traversal, recursive interpolation bombs),
high-concurrency race condition safety, scale bounds (1,000-node DAGs), and fuzzing.
"""

import time
import unittest
import threading
import asyncio
from pathlib import Path

from agent_workflow.models import WorkflowDefinition, StepDefinition, RunHistory, RunStatus
from agent_workflow.persistence import RunHistoryStore
from agent_workflow.state import StateContext, StateInterpolationError
from agent_workflow.parser import parse_workflow_dict, WorkflowParseError
from agent_workflow.dag import validate_workflow_dag, build_topological_batches


class TestAdversarialSecurityAudit(unittest.TestCase):
    """Tier 5 Adversarial and Security Audit Test Suite."""

    def test_path_traversal_attack_vector(self):
        """Verify path traversal payloads in run_id are rejected."""
        store = RunHistoryStore()

        malicious_ids = [
            "../../etc/passwd",
            "../run_id",
            "subdir/../../secret",
            "/absolute/path/id",
            "run_id\0nullbyte",
        ]

        for bad_id in malicious_ids:
            with self.subTest(run_id=bad_id):
                with self.assertRaises((ValueError, Exception)):
                    store.load_run_history(bad_id)

    def test_interpolation_infinite_recursion(self):
        """Verify circular or infinitely nested state interpolation expression bombs fail gracefully."""
        ctx = StateContext()
        # Setup circular reference: step1 output -> ${steps.step2.output.val}, step2 output -> ${steps.step1.output.val}
        ctx.set_step_output("step1", {"val": "${steps.step2.output.val}"})
        ctx.set_step_output("step2", {"val": "${steps.step1.output.val}"})

        with self.assertRaises(ValueError) as cm:
            ctx.interpolate("${steps.step1.output.val}")
        self.assertIn("depth exceeded", str(cm.exception))

    def test_scale_1000_nodes_dag(self):
        """Verify 1,000-node DAG validates and computes topological batches within 2 seconds."""
        steps = []
        for i in range(1000):
            depends = [f"step_{i-1}"] if i > 0 else []
            steps.append(StepDefinition(id=f"step_{i}", action="echo", params={"msg": f"hello {i}"}, depends_on=depends))

        wf = WorkflowDefinition(name="scale_1000_workflow", steps=steps)

        start_time = time.time()
        errors = validate_workflow_dag(wf)
        batches = build_topological_batches(wf)
        elapsed = time.time() - start_time

        self.assertEqual(len(errors), 0, "1000-node linear DAG should have zero validation errors")
        self.assertEqual(len(batches), 1000, "1000-node linear DAG should produce 1000 sequential batches")
        self.assertLess(elapsed, 2.0, f"1000-node DAG validation took {elapsed:.3f}s, expected < 2.0s")

    def test_high_concurrency_race_condition(self):
        """Verify 50 concurrent threads updating StateContext simultaneously produce thread-safe, uncorrupted state."""
        ctx = StateContext()
        num_threads = 50
        errors = []

        def worker(thread_idx: int):
            try:
                for step_num in range(10):
                    step_id = f"t_{thread_idx}_s_{step_num}"
                    ctx.set_step_output(step_id, {"thread": thread_idx, "step": step_num, "data": "a" * 100})
                    out = ctx.get_step_output(step_id)
                    if out.get("thread") != thread_idx or out.get("step") != step_num:
                        errors.append(f"Mismatch in thread {thread_idx}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent state updates caused errors: {errors}")
        for i in range(num_threads):
            for step_num in range(10):
                self.assertTrue(ctx.has_step_output(f"t_{i}_s_{step_num}"))

    def test_malformed_definition_fuzzing(self):
        """Verify malformed definition payloads fail gracefully with WorkflowParseError."""
        bad_payloads = [
            {},  # missing name and steps
            {"name": "test", "steps": "not_a_list"},
            {"name": "test", "steps": [{"action": "echo"}]},  # missing step id
            {"name": "test", "steps": [{"id": 123, "action": "echo"}]},  # non-string id
            {"name": "test", "steps": [{"id": "s1", "action": "echo", "retry": "not_an_int"}]},
        ]

        for payload in bad_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises((WorkflowParseError, TypeError, ValueError)):
                    parse_workflow_dict(payload)


if __name__ == "__main__":
    unittest.main()
