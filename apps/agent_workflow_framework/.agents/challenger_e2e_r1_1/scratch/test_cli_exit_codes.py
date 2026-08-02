import unittest
import os
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from agent_workflow.cli import main as cli_main
except ModuleNotFoundError:
    from tests.engine_fallback import cli_main

class TestCLIExitCodesStress(unittest.TestCase):
    """Empirical challenge of CLI exit codes (0, 1, 2)"""

    def setUp(self):
        self.fixtures_dir = BASE_DIR / "tests" / "test_workflows"

    def test_exit_code_0_validate_success(self):
        code = cli_main(["validate", str(self.fixtures_dir / "linear_workflow.yaml")])
        self.assertEqual(code, 0)

    def test_exit_code_0_run_success(self):
        code = cli_main(["run", str(self.fixtures_dir / "linear_workflow.yaml")])
        self.assertEqual(code, 0)

    def test_exit_code_0_inspect_success(self):
        # Run linear workflow first to ensure run_id exists
        from tests.engine_fallback import parse_workflow_file, WorkflowExecutor
        import asyncio
        wf = parse_workflow_file(str(self.fixtures_dir / "linear_workflow.yaml"))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf, run_id="stress_inspect_0"))
        code = cli_main(["inspect", "stress_inspect_0"])
        self.assertEqual(code, 0)

    def test_exit_code_1_run_runtime_failure(self):
        code = cli_main(["run", str(self.fixtures_dir / "retry_workflow.yaml")])
        self.assertEqual(code, 1)

    def test_exit_code_1_inspect_nonexistent_run_id(self):
        code = cli_main(["inspect", "nonexistent_run_id_xyz999"])
        self.assertEqual(code, 1)

    def test_exit_code_1_inspect_missing_arg(self):
        code = cli_main(["inspect"])
        self.assertEqual(code, 1)

    def test_exit_code_1_run_missing_arg(self):
        code = cli_main(["run"])
        self.assertEqual(code, 1)

    def test_exit_code_1_unknown_command(self):
        code = cli_main(["unknown_subcmd"])
        self.assertEqual(code, 1)

    def test_exit_code_1_no_command(self):
        code = cli_main([])
        self.assertEqual(code, 1)

    def test_exit_code_2_validate_cyclic(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: cyc\nsteps:\n  - id: a\n    depends_on: [b]\n  - id: b\n    depends_on: [a]\n")
            path = f.name
        try:
            code = cli_main(["validate", path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(path)

    def test_exit_code_2_validate_self_loop(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: self_cyc\nsteps:\n  - id: a\n    depends_on: [a]\n")
            path = f.name
        try:
            code = cli_main(["validate", path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(path)

    def test_exit_code_2_validate_undefined_dep(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: undef\nsteps:\n  - id: a\n    depends_on: [ghost]\n")
            path = f.name
        try:
            code = cli_main(["validate", path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(path)

    def test_exit_code_2_validate_missing_file(self):
        code = cli_main(["validate", "non_existent_file_abc123.yaml"])
        self.assertEqual(code, 2)

    def test_exit_code_2_validate_missing_arg(self):
        code = cli_main(["validate"])
        self.assertEqual(code, 2)

    def test_exit_code_2_run_validation_failure(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: cyc_run\nsteps:\n  - id: a\n    depends_on: [b]\n  - id: b\n    depends_on: [a]\n")
            path = f.name
        try:
            code = cli_main(["run", path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
