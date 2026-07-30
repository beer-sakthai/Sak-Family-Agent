---
name: SakThai-ecosystem-improvement-cron
description: One-shot cron task that improves one HF asset per run — model card, cross-links, dataset integrity, or promotion.
category: software-development
---

# HF Ecosystem Improvement (Cron)

Each run picks ONE concrete improvement:

1. **Check current ecosystem state** (downloads, card quality, cross-links)
2. **Pick target** — models with <50 downloads are priority
3. **Improve** — update card, add cross-links, fix metadata
4. **Verify** — check the change took effect
5. **Record** — log to LEARNING_JOURNAL.md

## Priority order
- Model cards missing YAML metadata
- Models with single-digit downloads (vision-7b, tts-model, embedding-multilingual)
- Dataset cards without proper metadata
- Missing cross-links between related model families

## One improvement per run — deep, verified, done.
