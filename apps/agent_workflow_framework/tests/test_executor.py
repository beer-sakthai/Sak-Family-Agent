"""Unit tests for agent_workflow.executor module and action handlers."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from agent_workflow.executor import WorkflowExecutor
from agent_workflow.models import RunStatus, StepDefinition, StepStatus, WorkflowDefinition


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

    def test_file_path_validation_protection(self):
        """Verify that directory traversal, sensitive directories, and sensitive files are blocked by the path validator."""
        dangerous_paths = [
            "../../etc/passwd",
            "index.html/../../etc/shadow",
            "~/.ssh/id_rsa",
            "/etc/passwd",
            "/usr/bin/python3",
            "/var/log/syslog",
            "src/.git/config",
            "config/.ssh/authorized_keys",
            "subfolder/.env",
            "memory.db",
            "subfolder/id_rsa.bak",
            "subfolder/.ENV.production",
        ]
        for path in dangerous_paths:
            with self.subTest(path=path):
                # Test write block
                wf_write = WorkflowDefinition(
                    name="write_protect_test",
                    steps=[
                        StepDefinition(id="write_step", action="file_write", params={"path": path, "content": "test"}),
                    ],
                )
                history_write = asyncio.run(self.executor.execute_workflow(wf_write))
                self.assertEqual(history_write.status, RunStatus.FAILED)
                step_res_write = history_write.step_results["write_step"]
                self.assertEqual(step_res_write.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res_write.error)
                self.assertTrue(
                    any(x in step_res_write.error for x in ["PermissionError", "blocked", "traversal"]),
                    f"Unexpected write error for path '{path}': {step_res_write.error}"
                )

                # Test read block
                wf_read = WorkflowDefinition(
                    name="read_protect_test",
                    steps=[
                        StepDefinition(id="read_step", action="file_read", params={"path": path}),
                    ],
                )
                history_read = asyncio.run(self.executor.execute_workflow(wf_read))
                self.assertEqual(history_read.status, RunStatus.FAILED)
                step_res_read = history_read.step_results["read_step"]
                self.assertEqual(step_res_read.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res_read.error)
                self.assertTrue(
                    any(x in step_res_read.error for x in ["PermissionError", "blocked", "traversal"]),
                    f"Unexpected read error for path '{path}': {step_res_read.error}"
                )

    def test_ssrf_protection(self):
        """Verify that the executor rejects dangerous, private, loopback, and malformed URLs to prevent SSRF and option smuggling."""
        dangerous_urls = [
            "http://localhost",
            "http://127.0.0.1",
            "http://192.168.1.1",
            "http://10.0.0.1",
            "http://169.254.169.254",
            "-v http://example.com",
            "file:///etc/passwd",
            "gopher://example.com",
            "http:///",
        ]
        for url in dangerous_urls:
            with self.subTest(url=url):
                wf = WorkflowDefinition(
                    name="ssrf_test",
                    steps=[
                        StepDefinition(id="fetch_step", action="fetch", params={"url": url}),
                    ],
                )
                history = asyncio.run(self.executor.execute_workflow(wf))
                self.assertEqual(history.status, RunStatus.FAILED)
                step_res = history.step_results["fetch_step"]
                self.assertEqual(step_res.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res.error)
                error_msg = step_res.error.lower()
                self.assertTrue(
                    any(
                        x in error_msg
                        for x in ["ssrf", "smuggling", "scheme", "hostname", "invalid", "forbidden"]
                    ),
                    f"Unexpected error message for URL '{url}': {step_res.error}"
                )


if __name__ == "__main__":
    unittest.main()
