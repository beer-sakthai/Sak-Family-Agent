"""Tests for SakSit Hybrid Joy Approval Pipeline & Staged Markdown Reports."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sakthai.telegram.digest import (
    ApprovalDigest,
    format_telegram_approval_digest,
    stage_markdown_report,
)


class TestApprovalPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_format_telegram_approval_digest_creates_callback_buttons(self) -> None:
        digest: ApprovalDigest = format_telegram_approval_digest(
            draft_id="draft-2026-11-26-release",
            title="House of Sak v2.53.0 Release Post",
            summary="Announcing persistent SQLite memory shards and $0 execution.",
            channel="social",
        )
        self.assertEqual(digest.draft_id, "draft-2026-11-26-release")
        self.assertIn("v2.53.0", digest.title)
        self.assertEqual(len(digest.inline_keyboard), 1)
        buttons = digest.inline_keyboard[0]
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0]["callback_data"], "approve:draft-2026-11-26-release")
        self.assertEqual(buttons[1]["callback_data"], "revise:draft-2026-11-26-release")

    def test_stage_markdown_report_creates_structured_file(self) -> None:
        title = "Model Card Enrichment: SakThai-Decision-1"
        content = "## Model Card\n\nFull evaluation scores across 6 agent personas."
        staged_path = stage_markdown_report(
            title=title,
            content=content,
            persona="saksit",
            output_dir=self.tmp_dir,
        )
        self.assertTrue(staged_path.is_file())
        text = staged_path.read_text(encoding="utf-8")
        self.assertIn("status: staged", text)
        self.assertIn("awaiting: Beer", text)
        self.assertIn(title, text)
        self.assertIn(content, text)


if __name__ == "__main__":
    unittest.main()
