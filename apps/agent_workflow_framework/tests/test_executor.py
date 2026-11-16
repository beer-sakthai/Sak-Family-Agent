"""Unit tests for agent_workflow.executor module and action handlers."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from agent_workflow.executor import WorkflowExecutor
from agent_workflow.models import RunStatus, StepDefinition, StepStatus, WorkflowDefinition
from agent_workflow.persistence import DuplicateRunError


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

    def test_validate_shell_command_process_substitution(self):
        """Verify that shell commands with process substitution to interpreters are blocked."""
        malicious_commands = [
            "eval <(echo 'cat /etc/passwd')",
            "exec <(echo 'cat /etc/passwd')",
            "source <(echo 'cat /etc/passwd')",
            ". <(echo 'cat /etc/passwd')",
            "bash <(echo 'cat /etc/passwd')",
            "sh < (echo 'cat /etc/passwd')",
            "python <(echo 'import os; os.system(\"cat /etc/passwd\")')",
            "ENV_VAR=1 python <(echo 'cat /etc/passwd')",
            "/bin/bash <(echo 'cat /etc/passwd')",
        ]

        for cmd in malicious_commands:
            with self.subTest(cmd=cmd):
                wf = WorkflowDefinition(
                    name="test_shell_security",
                    steps=[
                        StepDefinition(
                            id="shell_step",
                            action="shell",
                            params={"cmd": cmd},
                        ),
                    ],
                )
                history = asyncio.run(self.executor.execute_workflow(wf))
                self.assertEqual(history.status, RunStatus.FAILED)
                step_res = history.step_results["shell_step"]
                self.assertEqual(step_res.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res.error)
                self.assertIn(
                    "Process substitution for interpreter execution is prohibited", step_res.error
                )

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
        """Test python literal evaluation action handler."""
        wf = WorkflowDefinition(
            name="test_python",
            steps=[
                StepDefinition(
                    id="s1",
                    action="python",
                    params={"expr": "{'key': 'value', 'numbers': [1, 2, 3]}"},
                ),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(
            history.step_results["s1"].output.get("result"), {"key": "value", "numbers": [1, 2, 3]}
        )

    def test_python_action_security_blocking(self):
        """Verify that unsafe Python expressions and code injection attempts are safely blocked."""
        malicious_expressions = [
            "__import__('os').system('echo pwned')",
            "10 * 5",  # non-literal binary expression is blocked
            "open('/etc/passwd').read()",
            "eval('1+1')",
            "exec('import os')",
            "lambda: None",
        ]
        for expr in malicious_expressions:
            with self.subTest(expr=expr):
                wf = WorkflowDefinition(
                    name="test_python_security",
                    steps=[
                        StepDefinition(id="s1", action="python", params={"expr": expr}),
                    ],
                )
                history = asyncio.run(self.executor.execute_workflow(wf))
                self.assertEqual(history.status, RunStatus.FAILED)
                step_res = history.step_results["s1"]
                self.assertEqual(step_res.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res.error)
                self.assertIn("Invalid or unsafe expression", step_res.error)

    def test_file_write_and_read(self):
        """Test file_write and file_read pipeline."""
        target_file = Path(self.temp_dir.name) / "test_output.txt"
        wf = WorkflowDefinition(
            name="test_file_io",
            steps=[
                StepDefinition(
                    id="write_step",
                    action="file_write",
                    params={"path": str(target_file), "content": "sample content"},
                ),
                StepDefinition(
                    id="read_step",
                    action="file_read",
                    params={"path": "${steps.write_step.output.path}"},
                    depends_on=["write_step"],
                ),
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
                StepDefinition(
                    id="fail_step",
                    action="shell",
                    params={"cmd": "bash -c 'exit 1'", "check": True},
                    retry=1,
                ),
                StepDefinition(
                    id="blocked_step",
                    action="echo",
                    params={"msg": "should not run"},
                    depends_on=["fail_step"],
                ),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["fail_step"].status, StepStatus.FAILED)
        self.assertEqual(history.step_results["fail_step"].attempts, 2)
        self.assertEqual(history.step_results["blocked_step"].status, StepStatus.SKIPPED)

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
                    f"Unexpected error message for URL '{url}': {step_res.error}",
                )

    def test_ssrf_url_fragment_stripping(self):
        """Verify that URL fragments are stripped before DNS resolution."""
        # The URL has a fragment that might confuse a naive parser or SSRF filter,
        # but because we strip it, it correctly resolves the base hostname
        # (which is localhost/127.0.0.1) and thus is blocked by the IP validator.
        url = "http://127.0.0.1#@example.com"
        wf = WorkflowDefinition(
            name="ssrf_fragment_test",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": url}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        step_res = history.step_results["fetch_step"]
        self.assertEqual(step_res.status, StepStatus.FAILED)
        self.assertIsNotNone(step_res.error)
        self.assertIn("ssrf", step_res.error.lower())

    def test_ssrf_backslash_authority_confusion(self):
        """Verify that backslashes in the netloc are blocked to prevent authority confusion bypasses."""
        url = "http://example.com\\@127.0.0.1"
        wf = WorkflowDefinition(
            name="ssrf_backslash_test",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": url}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        step_res = history.step_results["fetch_step"]
        self.assertEqual(step_res.status, StepStatus.FAILED)
        self.assertIsNotNone(step_res.error)
        self.assertIn("backslash", step_res.error.lower())

    def test_ssrf_ipv4_mapped_ipv6(self):
        """Verify that IPv4-mapped IPv6 addresses are unwrapped and blocked by SSRF protection."""
        url = "http://[::ffff:127.0.0.1]"
        wf = WorkflowDefinition(
            name="ssrf_ipv6_mapped_test",
            steps=[
                StepDefinition(id="fetch_step", action="fetch", params={"url": url}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        step_res = history.step_results["fetch_step"]
        self.assertEqual(step_res.status, StepStatus.FAILED)
        self.assertIsNotNone(step_res.error)
        self.assertIn("ssrf", step_res.error.lower())

    def test_file_path_validation_protection(self):
        """Verify that the file actions reject path traversal, system roots, and sensitive files/directories."""
        malicious_paths = [
            "../../etc/passwd",
            "../.env",
            "~/.ssh/id_rsa",
            "@/etc/passwd",
            "@@.env",
            "@/var/log/syslog",
            "@@.git/config",
            "@@etc/passwd",
            "/etc/passwd",
            "/bin/sh",
            "etc/passwd",
            "etc/shadow",
            ".env",
            ".ENV",
            ".env.production",
            ".Env.production",
            "memory.db",
            "id_rsa",
            "ID_RSA",
            "credentials.json",
            "Credentials.json",
            "subdir/.git/config",
            "subdir/.ssh/authorized_keys",
            # Windows-style separators must not smuggle a traversal segment past
            # the POSIX-only split.
            "..\\..\\etc\\passwd",
            "subdir\\..\\..\\.env",
            # Additional critical system root.
            "/opt/app/config.yaml",
            # Additional credential directories.
            "subdir/.docker/config.json",
            "subdir/.kube/config",
            "subdir/.gnupg/secring.gpg",
            "subdir/.gcloud/credentials.db",
            "subdir/.azure/accessTokens.json",
            # Dotenv prefix variants beyond ".env.".
            ".env-production",
            ".env_local",
            # SQLite sidecars of the agent memory database.
            "memory.db-wal",
            "memory.db-shm",
            "memory.db-journal",
            # Renamed / backed-up private keys.
            "id_rsa.bak",
            "id_ed25519.pub",
            "ID_ECDSA.old",
            # Encoded path traversal vectors.
            "%252e%252e/etc/passwd",
            "%252e%252e/%252e%252e/secret.txt",
            "%25252e%25252e/etc/passwd",
        ]
        for path in malicious_paths:
            for action in ("file_read", "file_write"):
                with self.subTest(path=path, action=action):
                    wf = WorkflowDefinition(
                        name="path_validation_test",
                        steps=[
                            StepDefinition(
                                id="file_step",
                                action=action,
                                params={"path": path, "content": "dummy"},
                            ),
                        ],
                    )
                    history = asyncio.run(self.executor.execute_workflow(wf))
                    self.assertEqual(history.status, RunStatus.FAILED)
                    step_res = history.step_results["file_step"]
                    self.assertEqual(step_res.status, StepStatus.FAILED)
                    self.assertIsNotNone(step_res.error)
                    self.assertTrue(
                        any(
                            x in step_res.error.lower()
                            for x in ["traversal", "prohibited", "system", "sensitive", "invalid"]
                        ),
                        f"Unexpected error for path '{path}' and action '{action}': {step_res.error}",
                    )

    def test_file_path_validation_allows_ordinary_paths(self):
        """Verify the hardened validator still permits ordinary workspace paths."""
        target = Path(self.temp_dir.name) / "reports" / "summary.json"
        wf = WorkflowDefinition(
            name="path_allow_test",
            steps=[
                StepDefinition(
                    id="write_step",
                    action="file_write",
                    params={"path": str(target), "content": {"ok": True}},
                ),
                StepDefinition(
                    id="read_step",
                    action="file_read",
                    params={"path": str(target)},
                    depends_on=["write_step"],
                ),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["read_step"].status, StepStatus.COMPLETED)

    def test_duplicate_run_id_rejection(self):
        """Verify that starting a workflow with an existing run_id raises DuplicateRunError unless allowed."""
        wf = WorkflowDefinition(
            name="test_dup_run",
            steps=[StepDefinition(id="s1", action="echo", params={"msg": "first"})],
        )
        h1 = asyncio.run(self.executor.execute_workflow(wf, run_id="my_fixed_run_id"))
        self.assertEqual(h1.status, RunStatus.COMPLETED)

        # Attempting to run again with the same run_id must raise DuplicateRunError
        with self.assertRaises(DuplicateRunError):
            asyncio.run(self.executor.execute_workflow(wf, run_id="my_fixed_run_id"))

        # Explicitly allowing duplicate run_id succeeds
        h2 = asyncio.run(
            self.executor.execute_workflow(wf, run_id="my_fixed_run_id", allow_duplicate_run_id=True)
        )
        self.assertEqual(h2.status, RunStatus.COMPLETED)

    def test_callback_exception_isolation_sync(self):
        """Verify that a failing synchronous status_callback does not crash workflow execution."""
        wf = WorkflowDefinition(
            name="test_failing_callback",
            steps=[
                StepDefinition(id="step_a", action="echo", params={"msg": "alpha"}),
                StepDefinition(id="step_b", action="echo", params={"msg": "beta"}, depends_on=["step_a"]),
            ],
        )

        callback_calls = []

        def broken_callback(run_id, step_res):
            callback_calls.append(step_res.step_id)
            raise RuntimeError(f"Callback crashed on step {step_res.step_id}!")

        # Workflow execution must succeed despite callback raising RuntimeError
        history = asyncio.run(self.executor.execute_workflow(wf, status_callback=broken_callback))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(len(callback_calls), 2)
        self.assertEqual(history.step_results["step_a"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_b"].status, StepStatus.COMPLETED)

    def test_callback_exception_isolation_async(self):
        """Verify that a failing asynchronous status_callback does not crash workflow execution."""
        wf = WorkflowDefinition(
            name="test_async_failing_callback",
            steps=[StepDefinition(id="step_1", action="echo", params={"x": 1})],
        )

        async def broken_async_callback(run_id, step_res):
            await asyncio.sleep(0.001)
            raise ValueError("Async callback exploded!")

        history = asyncio.run(self.executor.execute_workflow(wf, status_callback=broken_async_callback))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["step_1"].status, StepStatus.COMPLETED)

    def test_raise_callback_exceptions_flag(self):
        """Verify that raise_callback_exceptions=True re-raises callback errors."""
        wf = WorkflowDefinition(
            name="test_raise_cb_flag",
            steps=[StepDefinition(id="s1", action="echo")],
        )

        def explosive_callback(run_id, step_res):
            raise ArithmeticError("Explosive callback error")

        with self.assertRaises(ArithmeticError):
            asyncio.run(
                self.executor.execute_workflow(
                    wf,
                    status_callback=explosive_callback,
                    raise_callback_exceptions=True,
                )
            )

    def test_callback_on_skipped_steps_isolation(self):
        """Verify that callback exceptions on skipped steps are also safely isolated."""
        wf = WorkflowDefinition(
            name="test_skip_callback",
            steps=[
                StepDefinition(id="fail_step", action="fail_always"),
                StepDefinition(id="downstream_skip", action="echo", depends_on=["fail_step"]),
            ],
        )

        skipped_callback_invoked = []

        def failing_skip_callback(run_id, step_res):
            if step_res.status == StepStatus.SKIPPED:
                skipped_callback_invoked.append(step_res.step_id)
                raise RuntimeError("Skipped callback error")

        history = asyncio.run(self.executor.execute_workflow(wf, status_callback=failing_skip_callback))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["downstream_skip"].status, StepStatus.SKIPPED)
        self.assertEqual(skipped_callback_invoked, ["downstream_skip"])


if __name__ == "__main__":
    unittest.main()
