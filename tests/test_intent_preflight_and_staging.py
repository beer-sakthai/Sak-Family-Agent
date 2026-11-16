import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestIntentPreflightAndStaging(unittest.TestCase):
    def test_sakking_plan_has_intent_preflight(self) -> None:
        plan = (REPO_ROOT / "personas" / "sakking" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("3-Second Intent Preflight", plan)
        self.assertIn("Specialist beats generalist", plan)

    def test_saksit_plan_has_async_template_staging(self) -> None:
        plan = (REPO_ROOT / "personas" / "saksit" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("Asynchronous Template Staging", plan)
        self.assertIn("{{VARIABLE}}", plan)
