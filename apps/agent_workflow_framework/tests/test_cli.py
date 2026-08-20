"""Unit tests for agent_workflow.cli module and command subcommands."""

import tempfile
import unittest
from pathlib import Path

from agent_workflow.cli import cli_main


class TestCLI(unittest.TestCase):
    """Test suite for CLI commands and exit code contracts."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.valid_yaml = Path(self.temp_dir.name) / "valid.yaml"
        self.valid_yaml.write_text(
            "name: cli_test_wf\nsteps:\n  - id: step_1\n    action: echo\n    params:\n      msg: hi\n"
        )
        self.cyclic_yaml = Path(self.temp_dir.name) / "cyclic.yaml"
        self.cyclic_yaml.write_text(
            "name: cyclic_wf\nsteps:\n  - id: a\n    depends_on: [b]\n  - id: b\n    depends_on: [a]\n"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_validate_success(self):
        """Test 'validate' subcommand with valid workflow returns exit code 0."""
        code = cli_main(["validate", str(self.valid_yaml)])
        self.assertEqual(code, 0)

    def test_cli_validate_cyclic_exit_code_2(self):
        """Test 'validate' subcommand with cyclic workflow returns exit code 2."""
        code = cli_main(["validate", str(self.cyclic_yaml)])
        self.assertEqual(code, 2)

    def test_cli_run_success(self):
        """Test 'run' subcommand with valid workflow returns exit code 0."""
        code = cli_main(["run", str(self.valid_yaml)])
        self.assertEqual(code, 0)

    def test_cli_inspect_and_list(self):
        """Test 'inspect' and 'list' subcommands."""
        run_code = cli_main(["run", str(self.valid_yaml), "--run-id", "test_cli_inspect_run"])
        self.assertEqual(run_code, 0)

        inspect_code = cli_main(["inspect", "test_cli_inspect_run"])
        self.assertEqual(inspect_code, 0)

        list_code = cli_main(["list"])
        self.assertEqual(list_code, 0)


if __name__ == "__main__":
    unittest.main()
