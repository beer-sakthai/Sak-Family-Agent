import subprocess
import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestCIAutoHealAndSakTan(unittest.TestCase):
    def test_ci_auto_heal_script_exists_and_help_runs(self) -> None:
        script = REPO_ROOT / "scripts" / "ci_auto_heal.py"
        self.assertTrue(script.is_file())
        res = subprocess.run(
            [sys.executable, str(script), "--help"], capture_output=True, text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("auto-heal", res.stdout.lower())

    def test_saktan_config_has_guarded_cloud_fallback(self) -> None:
        cfg = yaml.safe_load(
            (REPO_ROOT / "personas" / "saktan" / "config" / "config.yaml").read_text()
        )
        self.assertIn("algorithmic_fallback", cfg)
