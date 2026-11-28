"""Tests for SakSit Automated Social Asset Bundler."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from sakthai.agent.bundler import (
    SocialAssetBundle,
    create_social_asset_bundle,
)


class TestSocialAssetBundler(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_create_social_asset_bundle_success(self) -> None:
        slug = "sakthai-decision-1-launch"
        content = "# Launching SakThai Decision 1\n\nZero-cost local MLOps model."
        prompts = {
            "flux_hero_banner": "A cinematic high-tech minimalist workstation with neon accents",
            "aspect_ratio": "16:9",
        }
        metadata = {
            "channels": ["telegram", "discord", "huggingface"],
            "version": "v1.0.0",
            "editorial_score": 92.5,
        }

        bundle: SocialAssetBundle = create_social_asset_bundle(
            slug=slug,
            content=content,
            prompts=prompts,
            metadata=metadata,
            output_dir=self.tmp_dir,
        )

        self.assertEqual(bundle.slug, slug)
        self.assertTrue(bundle.bundle_dir.is_dir())
        self.assertTrue(bundle.post_path.is_file())
        self.assertTrue(bundle.prompts_path.is_file())
        self.assertTrue(bundle.metadata_path.is_file())
        self.assertTrue(bundle.zip_path.is_file())

        # Verify content of files
        self.assertEqual(bundle.post_path.read_text(encoding="utf-8"), content)
        saved_prompts = json.loads(bundle.prompts_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_prompts["aspect_ratio"], "16:9")
        saved_meta = json.loads(bundle.metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_meta["editorial_score"], 92.5)

        # Verify zip archive integrity
        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("post.md", namelist)
            self.assertIn("prompts.json", namelist)
            self.assertIn("metadata.json", namelist)
            self.assertEqual(zf.read("post.md").decode("utf-8"), content)

    def test_create_bundle_with_extra_files_and_slug_sanitization(self) -> None:
        messy_slug = "  Release/v2.5.0: Special Edition!  "
        content = "Release details."
        prompts = ["prompt 1", "prompt 2"]
        metadata = {"env": "prod"}
        extra = {"banner.txt": "Mock banner asset content"}

        bundle = create_social_asset_bundle(
            slug=messy_slug,
            content=content,
            prompts=prompts,
            metadata=metadata,
            output_dir=self.tmp_dir,
            extra_files=extra,
        )

        self.assertNotIn("/", bundle.slug)
        self.assertNotIn(":", bundle.slug)
        self.assertTrue((bundle.bundle_dir / "banner.txt").is_file())

        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            self.assertIn("banner.txt", zf.namelist())

    def test_create_bundle_binary_file_and_empty_slug(self) -> None:
        binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        extra = {"image.png": binary_data}
        bundle = create_social_asset_bundle(
            slug="???///---",
            content="Binary test",
            prompts={},
            metadata={},
            output_dir=self.tmp_dir,
            extra_files=extra,
        )
        self.assertEqual(bundle.slug, "social_bundle")
        self.assertTrue((bundle.bundle_dir / "image.png").is_file())
        self.assertEqual((bundle.bundle_dir / "image.png").read_bytes(), binary_data)

        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            self.assertIn("image.png", zf.namelist())
            self.assertEqual(zf.read("image.png"), binary_data)

    def test_default_output_dir(self) -> None:
        bundle = create_social_asset_bundle(
            slug="default-dir-test",
            content="Content",
            prompts={},
            metadata={},
        )
        self.assertTrue(bundle.bundle_dir.is_dir())
        self.assertTrue(bundle.zip_path.is_file())


if __name__ == "__main__":
    unittest.main()
