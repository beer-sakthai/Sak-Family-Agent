"""Tests for SakSit Multimodal Social Media Dimension Presets and Tooling."""

from __future__ import annotations

import unittest

from sakthai.agent_platform.media_presets import (
    format_image_prompt,
    get_media_preset,
    list_media_presets,
)


class TestMediaPresets(unittest.TestCase):
    def test_list_presets_contains_core_platforms(self) -> None:
        presets = list_media_presets()
        self.assertIn("ig-reel", presets)
        self.assertIn("ig-carousel", presets)
        self.assertIn("x-card", presets)
        self.assertIn("linkedin-banner", presets)

    def test_get_ig_reel_preset(self) -> None:
        preset = get_media_preset("ig-reel")
        self.assertEqual(preset.aspect_ratio, "9:16")
        self.assertEqual(preset.width, 1080)
        self.assertEqual(preset.height, 1920)

    def test_get_x_card_preset(self) -> None:
        preset = get_media_preset("x-card")
        self.assertEqual(preset.aspect_ratio, "1.91:1")
        self.assertEqual(preset.width, 1200)
        self.assertEqual(preset.height, 628)

    def test_unknown_preset_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            get_media_preset("unknown-preset-xyz")

    def test_format_image_prompt_standard(self) -> None:
        prompt = "Midnight navy gradient background with glowing node network"
        spec = format_image_prompt(prompt, "ig-carousel")
        self.assertEqual(spec["aspect_ratio"], "4:5")
        self.assertEqual(spec["width"], 1080)
        self.assertEqual(spec["height"], 1350)
        self.assertEqual(spec["prompt"], prompt)

    def test_format_image_prompt_gemini_fallback(self) -> None:
        prompt = "Midnight navy gradient background with glowing node network"
        spec = format_image_prompt(prompt, "ig-carousel", fallback_to_gemini=True)
        plaintext = spec["gemini_plaintext"]
        self.assertTrue(plaintext.startswith("Prompt:\nMidnight navy"))
        self.assertIn("Aspect ratio: 4:5", plaintext)


if __name__ == "__main__":
    unittest.main()
