import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestBreakGlassProtocol(unittest.TestCase):
    def test_sakthai_soul_defines_break_glass_protocol(self) -> None:
        soul = (REPO_ROOT / "personas" / "sakthai" / "SOUL.md").read_text(encoding="utf-8")
        self.assertIn("emergency-hf-delegate", soul)
        self.assertIn("emergency-hub-write", soul)
        self.assertIn("Deputy 1 (SakKing)", soul)

    def test_sakking_soul_defines_emergency_hub_proxy(self) -> None:
        soul = (REPO_ROOT / "personas" / "sakking" / "SOUL.md").read_text(encoding="utf-8")
        self.assertIn("emergency-hf-delegate", soul)
        self.assertIn("quorum-approved", soul)
        self.assertIn("emergency-hub-write", soul)
