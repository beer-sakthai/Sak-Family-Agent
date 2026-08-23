"""Canonical card synchronizer synthesizing standardized model and dataset cards."""

from __future__ import annotations

import logging

from .models import HubAssetSpec

logger = logging.getLogger(__name__)

CANONICAL_FAMILY_TABLE = """| Model | Base / Architecture | Parameters | Primary Persona / Role |
|---|---|---|---|
| [`context-1.5b-merged`](https://huggingface.co/Nanthasit/context-1.5b-merged) | Qwen2.5-1.5B-Instruct | 1.5B | 🇹🇭 SakThai (Flagship Multi-Turn) |
| [`context-0.5b-merged`](https://huggingface.co/Nanthasit/context-0.5b-merged) | Qwen2.5-0.5B-Instruct | 0.5B | ⚡ Ultra-Light Edge Inference |
| [`context-7b-merged`](https://huggingface.co/Nanthasit/context-7b-merged) | Qwen2.5-7B-Instruct | 7.0B | 👑 SakKing (Deep Reasoning & Security) |
| [`context-7b-128k`](https://huggingface.co/Nanthasit/context-7b-128k) | Qwen2.5-7B-Instruct | 7.0B | 📚 Long-Context RAG (128k window) |
| [`coder-1.5b`](https://huggingface.co/Nanthasit/coder-1.5b) | Qwen2.5-Coder-1.5B | 1.5B | 🛠️ SakJules (Automation & CI/CD) |
| [`vision-7b`](https://huggingface.co/Nanthasit/vision-7b) | LLaVA-1.5-7B | 7.0B | 👁️ SakSee (Multimodal & UI Eval) |
| [`tts-model`](https://huggingface.co/Nanthasit/tts-model) | Kokoro-82M | 82M | 🎙️ SakSit (Thai/English Voice Synthesis) |
| [`embedding-multilingual`](https://huggingface.co/Nanthasit/embedding-multilingual) | BGE-M3 | 560M | 🧠 SakTan (Knowledge Graph Embeddings) |"""


class HubCardSynchronizer:
    """Generates standardized canonical markdown cards complying with House of Sak standards."""

    def render_model_card(
        self,
        asset: HubAssetSpec,
        tagline: str = "House of Sak Autonomous Intelligence",
        what_it_is: str = "Specialized fine-tuned model for multi-persona autonomous workflows.",
    ) -> str:
        tags_yaml = "\n".join(f"  - {t}" for t in asset.tags)
        return f"""---
license: {asset.license}
pipeline_tag: {asset.pipeline_tag or "text-generation"}
tags:
{tags_yaml}
---

# {asset.name}

> **{tagline}** · [[Read the full story →](https://huggingface.co/Nanthasit/Nanthasit)]

[![HF Downloads](https://img.shields.io/badge/dynamic/json?label=downloads&query=%24.downloads&url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2F{asset.repo_id})](https://huggingface.co/{asset.repo_id})

## 🌟 What it is
{what_it_is}

## 📊 Evaluation & Verification
- All internal benchmarks labeled: `internal, not third-party verified` (`verified: false`).
- Zero hardcoded download counters in markdown body.

## 🏛️ The House of Sak Model Family
{CANONICAL_FAMILY_TABLE}

## 📜 License
Licensed under {asset.license}.
"""
