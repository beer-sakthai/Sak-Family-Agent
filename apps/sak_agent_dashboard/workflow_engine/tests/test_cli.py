"""Unit tests for agent_workflow.cli module and command subcommands."""

import os
import tempfile
import unittest
from pathlib import Path

from agent_workflow.cli import cli_main


class TestCLI(unittest.TestCase):
    """Test suite for CLI commands and exit code contracts."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self._old_storage_dir = os.environ.get("AGENT_WORKFLOW_STORAGE_DIR")
        os.environ["AGENT_WORKFLOW_STORAGE_DIR"] = self.temp_dir.name
        self.valid_yaml = Path(self.temp_dir.name) / "valid.yaml"
        self.valid_yaml.write_text(
            "name: cli_test_wf\nsteps:\n  - id: step_1\n    action: echo\n    params:\n      msg: hi\n"
        )
        self.cyclic_yaml = Path(self.temp_dir.name) / "cyclic.yaml"
        self.cyclic_yaml.write_text(
            "name: cyclic_wf\nsteps:\n  - id: a\n    depends_on: [b]\n  - id: b\n    depends_on: [a]\n"
        )

    def tearDown(self):
        if self._old_storage_dir is None:
            os.environ.pop("AGENT_WORKFLOW_STORAGE_DIR", None)
        else:
            os.environ["AGENT_WORKFLOW_STORAGE_DIR"] = self._old_storage_dir
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
        run_code = cli_main(
            [
                "--storage-dir",
                self.temp_dir.name,
                "run",
                str(self.valid_yaml),
                "--run-id",
                "test_cli_inspect_run",
            ]
        )
        self.assertEqual(run_code, 0)

        inspect_code = cli_main(
            ["--storage-dir", self.temp_dir.name, "inspect", "test_cli_inspect_run"]
        )
        self.assertEqual(inspect_code, 0)

        list_code = cli_main(["--storage-dir", self.temp_dir.name, "list"])
        self.assertEqual(list_code, 0)

    def test_cli_storage_dir_flag_isolates_runs(self):
        """Verify --storage-dir writes and lists runs exclusively in the custom directory."""
        with tempfile.TemporaryDirectory() as custom_dir:
            code = cli_main(
                [
                    "--storage-dir",
                    custom_dir,
                    "run",
                    str(self.valid_yaml),
                    "--run-id",
                    "isolated-run-1",
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((Path(custom_dir) / "isolated-run-1.json").is_file())

            list_code = cli_main(["--storage-dir", custom_dir, "list"])
            self.assertEqual(list_code, 0)

            inspect_code = cli_main(["--storage-dir", custom_dir, "inspect", "isolated-run-1"])
            self.assertEqual(inspect_code, 0)

    def test_pyproject_toml_defines_console_entry_point(self):
        """Verify pyproject.toml exists and registers agent-workflow CLI script."""
        import tomllib

        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        self.assertTrue(
            pyproject_path.is_file(), "apps/agent_workflow_framework/pyproject.toml must exist"
        )
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["name"], "agent-workflow-framework")
        self.assertEqual(
            data["project"]["scripts"]["agent-workflow"],
            "agent_workflow.cli:main",
        )

    def test_cli_duplicate_run_id_contract(self):
        """Verify CLI 'run' fails with code 1 on duplicate run ID unless --allow-duplicate is set."""
        code1 = cli_main(
            [
                "--storage-dir",
                self.temp_dir.name,
                "run",
                str(self.valid_yaml),
                "--run-id",
                "cli_dup_run",
            ]
        )
        self.assertEqual(code1, 0)

        # Duplicate run ID without flag returns exit code 1
        code2 = cli_main(
            [
                "--storage-dir",
                self.temp_dir.name,
                "run",
                str(self.valid_yaml),
                "--run-id",
                "cli_dup_run",
            ]
        )
        self.assertEqual(code2, 1)

        # With --allow-duplicate returns exit code 0
        code3 = cli_main(
            [
                "--storage-dir",
                self.temp_dir.name,
                "run",
                str(self.valid_yaml),
                "--run-id",
                "cli_dup_run",
                "--allow-duplicate",
            ]
        )
        self.assertEqual(code3, 0)

    def test_cli_inspect_malformed_run_history_exit_code_1(self):
        """Verify inspect on corrupted history returns exit code 1."""
        corrupted_path = Path(self.temp_dir.name) / "corrupt_run.json"
        corrupted_path.write_text("{ malformed json ", encoding="utf-8")

        code = cli_main(["--storage-dir", self.temp_dir.name, "inspect", "corrupt_run"])
        self.assertEqual(code, 1)

    def test_cli_json_output_flags(self):
        """Verify --json flag on inspect and list subcommands."""
        run_code = cli_main(
            [
                "--storage-dir",
                self.temp_dir.name,
                "run",
                str(self.valid_yaml),
                "--run-id",
                "json_test_run",
            ]
        )
        self.assertEqual(run_code, 0)

        insp_code = cli_main(
            ["--storage-dir", self.temp_dir.name, "inspect", "json_test_run", "--json"]
        )
        self.assertEqual(insp_code, 0)

        list_code = cli_main(["--storage-dir", self.temp_dir.name, "list", "--json"])
        self.assertEqual(list_code, 0)

    def test_cli_validate_invalid_retry_exit_code_2(self):
        """Verify CLI validate returns exit code 2 when step retry is invalid."""
        bad_retry_yaml = Path(self.temp_dir.name) / "bad_retry.yaml"
        bad_retry_yaml.write_text(
            "name: bad_wf\nsteps:\n  - id: s1\n    action: echo\n    retry: -1\n"
        )

        code = cli_main(["validate", str(bad_retry_yaml)])
        self.assertEqual(code, 2)

    def test_verify_benchmark_baselines_and_summary_file(self):
        """Verify verify_benchmark_baselines execution and --summary-file output generation."""
        import json
        from unittest.mock import patch

        import verify

        passed, metrics = verify.verify_benchmark_baselines()
        self.assertTrue(passed)
        self.assertIn("parallel_fanout", metrics)
        self.assertIn("retry_recovery", metrics)
        self.assertEqual(metrics["parallel_fanout"]["status"], "PASS")
        self.assertEqual(metrics["retry_recovery"]["status"], "PASS")

        summary_file = Path(self.temp_dir.name) / "test_summary.json"
        with (
            patch.object(verify, "verify_unittest_suite", return_value=True),
            patch.object(verify, "verify_adversarial_suite", return_value=True),
        ):
            exit_code = verify.main(["--summary-file", str(summary_file)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(summary_file.exists())
        data = json.loads(summary_file.read_text(encoding="utf-8"))
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["total_phases"], 8)
        self.assertIn("benchmarks", data)


if __name__ == "__main__":
    unittest.main()
