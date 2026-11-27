"""Multimodal social media dimension presets and prompt formatters for SakSit and family."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MediaPreset:
    name: str
    aspect_ratio: str
    width: int
    height: int
    platform: str
    description: str


PRESETS: dict[str, MediaPreset] = {
    "ig-reel": MediaPreset(
        name="ig-reel",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        platform="Instagram",
        description="Vertical 9:16 portrait video or Reel visual card.",
    ),
    "ig-carousel": MediaPreset(
        name="ig-carousel",
        aspect_ratio="4:5",
        width=1080,
        height=1350,
        platform="Instagram",
        description="Standard 4:5 portrait post or swipe carousel slide.",
    ),
    "x-card": MediaPreset(
        name="x-card",
        aspect_ratio="1.91:1",
        width=1200,
        height=628,
        platform="X / Twitter",
        description="Horizontal OpenGraph summary card or in-feed image.",
    ),
    "x-banner": MediaPreset(
        name="x-banner",
        aspect_ratio="3:1",
        width=1500,
        height=500,
        platform="X / Twitter",
        description="Header banner for profile page.",
    ),
    "linkedin-banner": MediaPreset(
        name="linkedin-banner",
        aspect_ratio="4:1",
        width=1584,
        height=396,
        platform="LinkedIn",
        description="Top background cover banner for LinkedIn profile.",
    ),
    "square": MediaPreset(
        name="square",
        aspect_ratio="1:1",
        width=1080,
        height=1080,
        platform="Universal",
        description="Square 1:1 post for general social feeds.",
    ),
    "youtube-thumb": MediaPreset(
        name="youtube-thumb",
        aspect_ratio="16:9",
        width=1280,
        height=720,
        platform="YouTube",
        description="16:9 landscape thumbnail image.",
    ),
}


def list_media_presets() -> list[str]:
    """Return all available preset identifiers."""
    return sorted(PRESETS.keys())


def get_media_preset(preset_name: str) -> MediaPreset:
    """Retrieve configuration for a specific media preset."""
    if preset_name not in PRESETS:
        raise KeyError(f"Unknown media preset {preset_name!r}. Available: {list_media_presets()}")
    return PRESETS[preset_name]


def format_image_prompt(
    prompt: str, preset_name: str, fallback_to_gemini: bool = False
) -> dict[str, Any]:
    """Format an image generation prompt with preset dimensions and optional Gemini fallback."""
    preset = get_media_preset(preset_name)
    spec: dict[str, Any] = {
        "preset": preset.name,
        "platform": preset.platform,
        "aspect_ratio": preset.aspect_ratio,
        "width": preset.width,
        "height": preset.height,
        "prompt": prompt,
    }
    if fallback_to_gemini:
        spec["gemini_plaintext"] = f"Prompt:\n{prompt}\n\nAspect ratio: {preset.aspect_ratio}"
    return spec
