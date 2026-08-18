import unittest
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class TestVerifyFailureHandling(unittest.TestCase):
    """Stress test verify.py failure detection"""

    def test_verify_exits_1_when_scenario_fails(self):
        with open(BASE_DIR / "verify.py") as f:
            code_text = f.read()

        tampered_code = code_text.replace(
            'if step3_out.get("final_result") != 20:',
            'if step3_out.get("final_result") == 20: # Forced failure for stress test'
        )

        tampered_script = BASE_DIR / ".agents/challenger_e2e_r1_1/scratch/tampered_verify.py"
        tampered_script.write_text(tampered_code)

        try:
            res = subprocess.run([sys.executable, str(tampered_script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=BASE_DIR)
            print("SUBPROCESS STDOUT:\n", res.stdout)
            print("SUBPROCESS STDERR:\n", res.stderr)
            print("SUBPROCESS RETURN CODE:", res.returncode)
            self.assertEqual(res.returncode, 1, f"verify.py should exit 1 when scenario fails, got {res.returncode}")
            self.assertIn("VERIFICATION FAILED", res.stdout)
        finally:
            if tampered_script.exists():
                tampered_script.unlink()

if __name__ == "__main__":
    unittest.main()
