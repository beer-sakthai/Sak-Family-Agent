---
name: SakSit-audiocraft-audio-generation
version: 1.0.0
description: Generate music and sound effects from text descriptions and melodic conditioning using AudioCraft.
category: content-marketing
tags:
- audio
- audiocraft
- content
- generation
- media
---

# SakSit AudioCraft Audio Generation Protocol

## Overview

Generates custom background music, podcast intros, Foley sound effects, and melody-conditioned tracks using Meta's AudioCraft framework (MusicGen, AudioGen, EnCodec).

Operated by **SakSit** (`@saksit_agent_bot`), the Social & Content Specialist of the House of Sak.

---

## 1. Operating Rules & Core Constraints

| Rule | Requirement |
|:---|:---|
| **Zero Cost Policy** | Use local PyTorch / CUDA inference or free-tier Hugging Face Spaces; zero paid API spend. |
| **Model Selection** | Default to `musicgen-small` (300M) for fast iteration; use `musicgen-melody` for branded tunes. |
| **Duration Limit** | Generate clips $\le 30$ seconds per pass to conserve memory and GPU VRAM. |
| **Export Formats** | Export 32 kHz WAV or compressed AAC for social media embeds. |
| **Audio-Visual Sync** | Coordinate with SakSee and SakKing when attaching audio to video reels. |

---

## 2. Audio Generation Workflow

```
Text Prompt / Melody Stem ──► Load AudioCraft Model (Small / Medium / Melody)
                                    │
                                    ▼
          Configure Generation Parameters (Duration, Temperature, Guidance)
                                    │
                                    ▼
          Synthesize Waveform ──► Normalize & Export Audio (WAV / MP3)
```

1. **Select Model**: Pick MusicGen (music) or AudioGen (Foley/SFX).
2. **Define Prompt**: Combine genre, tempo, instruments, and mood descriptors.
3. **Generate**: Execute tensor inference and export audio file.
4. **Stage Asset**: Save output under `assets/audio/` for video integration.

---

## 3. Reference Documents

For Python installation recipes, parameter tuning guides, and advanced usage:
- [AudioCraft Quickstart & Models Reference](./references/quickstart-and-models.md)
- [Advanced Usage & Multi-Stem Generation](./references/advanced-usage.md)
- [Troubleshooting & CUDA Memory Allocation](./references/troubleshooting.md)
