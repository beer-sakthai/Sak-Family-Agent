"""Test suite for Hugging Face Hub ecosystem scanner, models, and card validator."""

import unittest
from unittest.mock import MagicMock, patch

from sakthai.hub.models import (
    AssetType,
    EcosystemHealthReport,
    HubAssetSpec,
    SpaceState,
)
from sakthai.hub.scanner import HubEcosystemScanner
from sakthai.hub.sync import HubCardSynchronizer
from sakthai.hub.validator import ModelCardValidator


class TestHubModels(unittest.TestCase):
    def test_hub_asset_spec_initialization(self):
        spec = HubAssetSpec(
            id="m_context_1_5b",
            name="sakthai/context-1.5b-merged",
            type=AssetType.MODEL,
            repo_id="sakthai/context-1.5b-merged",
            author="Nanthasit",
            url="https://huggingface.co/sakthai/context-1.5b-merged",
            downloads=15000,
            likes=400,
            tags=["agent", "th-en", "gguf"],
            has_gguf=True,
        )
        self.assertEqual(spec.type, AssetType.MODEL)
        self.assertTrue(spec.has_gguf)
        self.assertEqual(spec.downloads, 15000)

    def test_space_state_enum(self):
        self.assertEqual(SpaceState("RUNNING"), SpaceState.RUNNING)
        self.assertEqual(SpaceState("SLEEPING"), SpaceState.SLEEPING)
        self.assertEqual(SpaceState("PAUSED"), SpaceState.PAUSED)


class TestModelCardValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ModelCardValidator()

    def test_valid_canonical_card(self):
        clean_content = """---
license: apache-2.0
pipeline_tag: text-generation
tags:
  - sak-family
  - agent-framework
---
# SakThai Context 1.5B Flagship

> SakThai · Core Persona Intelligence

## What it is
A specialized 1.5B reasoning and tool-calling model.

## Evaluation
- Internal benchmark: 78.4% (internal, not third-party verified; verified: false)

| Model | Size | Role |
|---|---|---|
| context-1.5b-merged | 1.5B | Flagship |
"""
        report = self.validator.validate_card("sakthai/context-1.5b-merged", clean_content)
        self.assertTrue(report.valid)
        self.assertGreaterEqual(report.score, 80)
        self.assertEqual(len([i for i in report.issues if i.severity == "error"]), 0)

    def test_flags_hardcoded_downloads(self):
        content = "---\nlicense: apache-2.0\n---\n# Test\nTotal 25,000 downloads achieved!"
        report = self.validator.validate_card("sakthai/test-model", content)
        self.assertTrue(any(i.rule == "no_hardcoded_downloads" for i in report.issues))

    def test_flags_fake_verified_evals(self):
        content = "---\nlicense: apache-2.0\n---\n# Test\n- benchmark: verified: true"
        report = self.validator.validate_card("sakthai/test-model", content)
        self.assertFalse(report.valid)
        self.assertTrue(any(i.rule == "honest_evals" for i in report.issues))

    def test_flags_misclassified_food_penguin(self):
        content = "---\nlicense: apache-2.0\n---\n# Test\nDataset food-penguin used for food image classification."
        report = self.validator.validate_card("sakthai/test-model", content)
        self.assertFalse(report.valid)
        self.assertTrue(any(i.rule == "canonical_dataset_facts" for i in report.issues))


class TestHubCardSynchronizer(unittest.TestCase):
    def setUp(self):
        self.sync = HubCardSynchronizer()

    def test_render_model_card(self):
        spec = HubAssetSpec(
            id="m_context_1_5b",
            name="sakthai/context-1.5b-merged",
            type=AssetType.MODEL,
            repo_id="sakthai/context-1.5b-merged",
            author="Nanthasit",
            url="https://huggingface.co/sakthai/context-1.5b-merged",
            license="apache-2.0",
            tags=["sak-family", "qwen"],
        )
        rendered = self.sync.render_model_card(spec)
        self.assertTrue(rendered.startswith("---"))
        self.assertIn("license: apache-2.0", rendered)
        self.assertIn("verified: false", rendered)


class TestHubScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = HubEcosystemScanner(author="Nanthasit", cache_ttl=10.0)

    @patch("sakthai.hub.scanner.urllib.request.urlopen")
    def test_scan_ecosystem_mocked(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = (
            b'[{"id": "Nanthasit/context-1.5b", "downloads": 1200, "likes": 50, "tags": ["gguf"]}]'
        )
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        report = self.scanner.scan_ecosystem(force=True)
        self.assertIsInstance(report, EcosystemHealthReport)
        self.assertGreaterEqual(report.total_models, 1)
        self.assertEqual(report.assets[0].repo_id, "Nanthasit/context-1.5b")


if __name__ == "__main__":
    unittest.main()
