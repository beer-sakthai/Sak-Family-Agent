"""Unit tests for agent_workflow.executor module and action handlers."""

import asyncio
import tempfile
import unittest
import unittest.mock
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

    @unittest.mock.patch("socket.getaddrinfo")
    def test_fetch_action_blocks_option_smuggling(self, mock_getaddrinfo):
        """Test option smuggling URLs are blocked."""
        wf = WorkflowDefinition(
            name="test_ssrf_option",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": "-v"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("Option smuggling is blocked", history.step_results["fetch_step"].error)

    @unittest.mock.patch("socket.getaddrinfo")
    def test_fetch_action_blocks_unsupported_scheme(self, mock_getaddrinfo):
        """Test unsupported schemes are blocked."""
        wf = WorkflowDefinition(
            name="test_ssrf_scheme",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": "gopher://example.com"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("only http/https", history.step_results["fetch_step"].error)

    @unittest.mock.patch("socket.getaddrinfo")
    def test_fetch_action_blocks_private_ip(self, mock_getaddrinfo):
        """Test private and loopback IPs are blocked."""
        import socket
        for blocked_ip in ["127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.169.254"]:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", (blocked_ip, 80))
            ]
            wf = WorkflowDefinition(
                name="test_ssrf_private",
                steps=[
                    StepDefinition(id="fetch_step", action="fetch", params={"url": "http://example.com/foo"}),
                ],
            )
            history = asyncio.run(self.executor.execute_workflow(wf))
            self.assertEqual(history.status, RunStatus.FAILED, f"Failed for IP: {blocked_ip}")
            self.assertIn("private/loopback/link-local", history.step_results["fetch_step"].error)

    @unittest.mock.patch("socket.getaddrinfo")
    def test_fetch_action_blocks_multicast_ip(self, mock_getaddrinfo):
        """Test multicast and non-global IPs are blocked."""
        import socket
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("224.0.0.1", 80))
        ]
        wf = WorkflowDefinition(
            name="test_ssrf_multicast",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": "http://example.com/foo"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("private/loopback/link-local", history.step_results["fetch_step"].error)

    @unittest.mock.patch("socket.getaddrinfo")
    @unittest.mock.patch("urllib.request.urlopen")
    def test_fetch_action_success_with_public_ip(self, mock_urlopen, mock_getaddrinfo):
        """Test successful fetch with a safe, public IP."""
        import socket
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))
        ]

        # Mock response object
        mock_response = unittest.mock.MagicMock()
        mock_response.read.return_value = b'{"status": "ok", "message": "hello"}'
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        wf = WorkflowDefinition(
            name="test_ssrf_success",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": "http://example.com/api"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        output = history.step_results["fetch_step"].output
        self.assertEqual(output.get("status"), 200)
        self.assertEqual(output.get("json"), {"status": "ok", "message": "hello"})


if __name__ == "__main__":
    unittest.main()
