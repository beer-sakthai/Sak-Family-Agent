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
                    id="fail_step", action="shell", params={"cmd": "exit 1", "check": True}, retry=1
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
        """Verify that _validate_url strips fragment identifiers to prevent fragment-based SSRF or host confusion bypasses."""
        from agent_workflow.executor import _validate_url

        # A URL with a fragment targeting loopback after # should be validated against the real host example.com,
        # but the fragment must not interfere with host/scheme parsing.
        # Conversely, if someone attempts host confusion like http://example.com#@127.0.0.1
        _validate_url("https://example.com/path#fragment")
        _validate_url("https://example.com#@127.0.0.1")

    def test_ssrf_redirect_protection(self):
        """Verify that the redirect handler intercepts and blocks redirects to loopback or private IPs."""
        from agent_workflow.executor import SafeRedirectHandler
        import urllib.request
        from unittest.mock import MagicMock

        handler = SafeRedirectHandler()
        req = urllib.request.Request("https://example.com/start")

        # Test redirects that should be blocked
        unsafe_redirects = [
            "http://localhost",
            "http://127.0.0.1",
            "http://192.168.1.1",
            "http://10.0.0.1",
            "http://169.254.169.254",
            "file:///etc/passwd",
            "gopher://example.com",
        ]

        for url in unsafe_redirects:
            with self.subTest(url=url):
                with self.assertRaises((ValueError, RuntimeError)):
                    handler.redirect_request(
                        req, fp=None, code=302, msg="Found", headers=MagicMock(), newurl=url
                    )

        # Test safe redirect that should be allowed
        try:
            res = handler.redirect_request(
                req,
                fp=None,
                code=302,
                msg="Found",
                headers=MagicMock(),
                newurl="https://example.org/home",
            )
            self.assertIsNotNone(res)
        except Exception as e:
            # Safe requests should not fail due to validation/SSRF blocks.
            # (If DNS or network is offline, it might raise, but not a ValueError)
            self.assertNotIsInstance(e, ValueError)

    def test_file_path_validation_protection(self):
        """Verify that the file actions reject path traversal, system roots, and sensitive files/directories."""
        malicious_paths = [
            "../../etc/passwd",
            "../.env",
            "~/.ssh/id_rsa",
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

    def test_python_action_sandbox_restrictions(self):
        """Verify that the python evaluation action restricts access to dangerous modules and builtins."""
        # Attempting to use open() should raise NameError ("name 'open' is not defined")
        wf_open = WorkflowDefinition(
            name="test_python_open",
            steps=[
                StepDefinition(id="s1", action="python", params={"expr": "open('test.txt', 'r')"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf_open))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("not defined", history.step_results["s1"].error.lower())

        # Attempting to use __import__ should raise NameError ("name '__import__' is not defined")
        wf_import = WorkflowDefinition(
            name="test_python_import",
            steps=[
                StepDefinition(id="s1", action="python", params={"expr": "__import__('os')"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf_import))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("not defined", history.step_results["s1"].error.lower())

        # Attempting to use os should raise NameError ("name 'os' is not defined")
        wf_os = WorkflowDefinition(
            name="test_python_os",
            steps=[
                StepDefinition(id="s1", action="python", params={"expr": "os.system('echo')"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf_os))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("not defined", history.step_results["s1"].error.lower())

        # Attempting to use sys should raise NameError ("name 'sys' is not defined")
        wf_sys = WorkflowDefinition(
            name="test_python_sys",
            steps=[
                StepDefinition(id="s1", action="python", params={"expr": "sys.exit(0)"}),
            ],
        )
        history = asyncio.run(self.executor.execute_workflow(wf_sys))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertIn("not defined", history.step_results["s1"].error.lower())

    def test_python_action_blocks_every_proposed_escape(self):
        """Union of the escape payloads from PRs #573/#574/#575/#577/#578.

        Five Sentinel PRs proposed competing blocklists for the python action and
        each shipped its own subset of these payloads. No blocklist was a superset
        of the others, so the implementations were folded into one union rather
        than merged in sequence. This test is the matching union: it fails if any
        single proposal's protection is ever dropped from that consolidated set.

        The escape chains matter as much as the obvious primitives. Removing
        `open`/`__import__`/`eval` alone is not enough — `getattr`, `type`,
        `object` and `super` each still reach
        `().__class__.__bases__[0].__subclasses__()`, from which `subprocess` is
        reachable, so the blocklist has to close those too.
        """
        escape_payloads = [
            # file / exec / import primitives
            "open('/etc/passwd', 'r')",
            "__import__('os').system('id')",
            "eval('1+1')",
            "exec('x = 5')",
            "compile('1+1', '<string>', 'eval')",
            # os / sys must not be in scope at all
            "os.system('id')",
            "sys.exit(1)",
            # interpreter control
            "exit()",
            "quit()",
            "input('prompt')",
            "help()",
            "breakpoint()",
            # namespace introspection
            "globals()",
            "locals()",
            "vars()",
            "dir()",
            # attribute traversal -> __subclasses__ escape chain
            "getattr(json, 'loads')",
            "hasattr(json, 'loads')",
            "setattr(json, 'x', 1)",
            "delattr(json, 'loads')",
            # type-graph entry points -> the same chain
            "object.__subclasses__()",
            "type(1)",
            "super",
            "property",
            "classmethod",
            "staticmethod",
        ]
        for payload in escape_payloads:
            with self.subTest(payload=payload):
                wf = WorkflowDefinition(
                    name="python_escape_union",
                    steps=[
                        StepDefinition(id="s1", action="python", params={"expr": payload}),
                    ],
                )
                history = asyncio.run(self.executor.execute_workflow(wf))
                self.assertEqual(
                    history.status,
                    RunStatus.FAILED,
                    f"payload {payload!r} was not blocked by the python sandbox",
                )
                step_res = history.step_results["s1"]
                self.assertEqual(step_res.status, StepStatus.FAILED)
                self.assertIsNotNone(step_res.error)

    def test_python_action_still_evaluates_ordinary_expressions(self):
        """The hardened blocklist must not break legitimate workflow expressions.

        Guards the other direction of the union above: a blocklist wide enough to
        stop `type` and `object` is also wide enough to break real workflows, so
        the arithmetic/string/collection builtins workflows actually use are
        pinned here.
        """
        cases = [
            ("1 + 1", 2),
            ("sum([1, 2, 3])", 6),
            ("len('abcd')", 4),
            ("sorted([3, 1, 2])", [1, 2, 3]),
            ("max(4, 7)", 7),
            ("str(12) + 'x'", "12x"),
            ("int('42')", 42),
            ("list(range(3))", [0, 1, 2]),
            ("json.dumps({'a': 1})", '{"a": 1}'),
        ]
        for expr, expected in cases:
            with self.subTest(expr=expr):
                wf = WorkflowDefinition(
                    name="python_ok",
                    steps=[
                        StepDefinition(id="s1", action="python", params={"expr": expr}),
                    ],
                )
                history = asyncio.run(self.executor.execute_workflow(wf))
                self.assertEqual(
                    history.status,
                    RunStatus.COMPLETED,
                    f"{expr!r} should still evaluate; "
                    f"error was {history.step_results['s1'].error!r}",
                )
                self.assertEqual(history.step_results["s1"].output["result"], expected)


if __name__ == "__main__":
    unittest.main()
