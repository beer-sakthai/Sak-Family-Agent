import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestTieredScrapingAndSkills(unittest.TestCase):
    def test_saksee_web_scraping_defines_3_tiers(self) -> None:
        skill = (
            REPO_ROOT / "personas" / "saksee" / "skills" / "SakSee-web-scraping" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Tier 1 (Fast & Free)", skill)
        self.assertIn("Tier 2 (Render-Only)", skill)
        self.assertIn("Tier 3 (Interactive Playwright)", skill)

    def test_sakthai_skills_exposes_domain_manifests(self) -> None:
        from personas.sakthai.skills import get_skill_domain_manifests

        manifests = get_skill_domain_manifests()
        self.assertIn("mlops", manifests)
        self.assertIn("inference", manifests)
