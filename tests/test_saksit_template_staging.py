"""Tests for SakSit Asynchronous Content Template Staging & Offline Cache Resilience."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personas.sakthai.agent.stager import (
    ContentTemplateStager,
)


class TestContentTemplateStaging(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.stager = ContentTemplateStager(cache_dir=self.tmp_dir)

    def test_hydrates_all_provided_variables(self) -> None:
        template = (
            "Release {{VERSION}}: Achieved {{BENCHMARK_SCORE}} on HF leaderboard! "
            "Total downloads: {{DOWNLOAD_COUNT}}."
        )
        vars_dict = {
            "VERSION": "v2.53.0",
            "BENCHMARK_SCORE": "91.4%",
            "DOWNLOAD_COUNT": "15,200",
        }
        hydrated = self.stager.stage_template(template, vars_dict)
        self.assertEqual(
            hydrated,
            "Release v2.53.0: Achieved 91.4% on HF leaderboard! Total downloads: 15,200.",
        )
        self.assertEqual(self.stager.detect_unresolved_placeholders(hydrated), [])

    def test_marks_missing_variables_as_pending_verification(self) -> None:
        template = "Release {{VERSION}} commit {{HUB_COMMIT}} with score {{SCORE}}."
        vars_dict = {"VERSION": "v2.53.0"}
        hydrated = self.stager.stage_template(template, vars_dict)
        self.assertIn("v2.53.0", hydrated)
        self.assertIn("[PENDING VERIFICATION: HUB_COMMIT]", hydrated)
        self.assertIn("[PENDING VERIFICATION: SCORE]", hydrated)
        unresolved = self.stager.detect_unresolved_placeholders(hydrated)
        self.assertIn("HUB_COMMIT", unresolved)
        self.assertIn("SCORE", unresolved)

    def test_saves_and_retrieves_cached_hub_metadata(self) -> None:
        repo_id = "beer-sakthai/SakThai-Decision-1"
        data = {
            "downloads": 12500,
            "likes": 42,
            "last_commit": "a1b2c3d4",
            "tags": ["agent", "eval"],
        }
        saved_path = self.stager.save_cached_hub_metadata(repo_id, data)
        self.assertTrue(saved_path.is_file())

        cached = self.stager.get_cached_hub_metadata(repo_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["downloads"], 12500)
        self.assertEqual(cached["likes"], 42)


if __name__ == "__main__":
    unittest.main()
