"""Unit tests for agent_workflow.executor module and action handlers."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from agent_workflow.executor import WorkflowExecutor
from agent_workflow.models import WorkflowDefinition, StepDefinition, RunStatus, StepStatus


class TestWorkflowExecutor(unittest.TestCase):
    """Test suite for WorkflowExecutor and built-in actions."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.executor = WorkflowExecutor(storage_dir=Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_echo_action(self):
        """Test echo action handler."""
        wf = WorkflowDefinition(
            name="test_echo",
            steps=[
                StepDefinition(id="s1", action="echo", params={"msg": "hello world"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["s1"].output.get("msg"), "hello world")

    def test_shell_action(self):
        """Test shell action handler."""
        wf = WorkflowDefinition(
            name="test_shell",
            steps=[
                StepDefinition(id="s1", action="shell", params={"cmd": "echo 'foo_bar'"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["s1"].output.get("stdout"), "foo_bar")

    def test_python_action(self):
        """Test python evaluation action handler."""
        wf = WorkflowDefinition(
            name="test_python",
            steps=[
                StepDefinition(id="s1", action="python", params={"expr": "10 * 5"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["s1"].output.get("result"), 50)

    def test_file_write_and_read(self):
        """Test file_write and file_read pipeline."""
        target_file = Path(self.temp_dir.name) / "test_output.txt"
        wf = WorkflowDefinition(
            name="test_file_io",
            steps=[
                StepDefinition(id="write_step", action="file_write", params={"path": str(target_file), "content": "sample content"}),
                StepDefinition(id="read_step", action="file_read", params={"path": "${steps.write_step.output.path}"}, depends_on=["write_step"]),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["read_step"].output.get("content"), "sample content")

    def test_retry_and_short_circuit(self):
        """Test step retry exhaustion and downstream short-circuiting."""
        wf = WorkflowDefinition(
            name="test_retry_fail",
            steps=[
                StepDefinition(id="fail_step", action="shell", params={"cmd": "exit 1", "check": True}, retry=1),
                StepDefinition(id="blocked_step", action="echo", params={"msg": "should not run"}, depends_on=["fail_step"]),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["fail_step"].status, StepStatus.FAILED)
        self.assertEqual(history.step_results["fail_step"].attempts, 2)
        self.assertEqual(history.step_results["blocked_step"].status, StepStatus.SKIPPED)


if __name__ == "__main__":
    unittest.main()
