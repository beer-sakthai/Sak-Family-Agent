# Jul 23, 2026 HF Session — Key Learnings

## What Went Wrong (And How To Avoid)
1. **Stripped content on 6 model cards** — I added House of Sak branding but REMOVED architecture tables, eval results, and usage code. User had to ask "bring back" and "more detail and professional" three times. Lesson: ALWAYS merge, never replace.
2. **Only updated 6/16 repos** — Missed 10 repos including embedding model, tools adapters, old datasets, v6, and kaggle-notebooks. Lesson: Full audit first.
3. **False gated access report** — `model_info()` returns data for any public model. Listed 13 models as "ACCESS GRANTED" but actual approved list was only the ones on the settings page. Lesson: `list_repo_files()` confirms real access, but even that can lie — settings page is source of truth.

## What Worked Well
1. **huggingface_hub Python library** for uploads — reliable, git-free
2. **FLUX.1-schnell gradio_client** — free image gen, no API key needed
3. **Full audit** found combined-v6 (agent configs!), GGUF file, embedding model
4. **Professional card template** (11 sections, 8K+ chars) — user approved

## Professional Card Evolution
- v1 (my first): 2-3K chars, stripped detail, brand only ❌
- v2 (restored): 3-4K chars, added back basic tech ✅
- v3 (final): 8K+ chars, badges, full benchmark tables, training hyperparams, limitations, citation, sample responses ✅✅

## Approved Gated Models (from settings page)
- Google's Gemma models family
- FLUX.1 and FLUX.1 ONNX
- Ideogram 4
- google/path-foundation
- google/medsiglip-448
- google/medgemma-1.5-4b-it, medgemma-27b-text-it
- google/medasr
- AlphaGenome

## Total HF Repos (Nanthasit)
- 16 models (some dual-listed as datasets)
- 8 datasets (with dedup: 6 unique)
- 1 Space
- ~19 unique repos
