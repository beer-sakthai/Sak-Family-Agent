
## 2026-07-29 — Cron #009: Vision-7B Model Card Enrichment

**One concrete improvement:** Revamped the model card for `sakthai-vision-7b` (104 dl — the weakest card among the "needs promotion" trio).

### Changes
- **Tags:** 8 → 20 tags (added `visual-question-answering`, `image-captioning`, `edge`, `cpu-inference`, `local-ai`, `privacy`, `quantized`, `clip`, `vicuna`, `finetune`, `sentence-transformers`, `transformers` + existing)
- **Model-index:** Added 3 upstream benchmark entries (VQAv2 78.5%, COCO CIDEr 110.1, GQA 62.0%) — honestly attributed as upstream LLaVA-1.5-7B scores
- **Pipeline integration:** Added ASCII pipeline diagram showing Vision→Embedding→Reason→Speak chain
- **Python example:** Added `llama-cpp-python` code snippet showing how to load and run the model
- **Use cases table:** 7 use cases with descriptions
- **Cross-links:** Added badges to vision-demo Space, proper cross-links to all sibling models
- **Low-download gems section:** Promoting context-0.5b-tools (7 dl), sakthai-embedding (34 dl), tts-model (69 dl), and sakthai-irrelevance-supplement dataset (0 dl)
- **Family table:** Updated to **11 models · 8 datasets · 3 Spaces**, sorted by downloads
- **README:** 78 lines / 3,700 chars → 293 lines / 11,469 chars (+275%)

### Verification
- Tags confirmed: 20
- Model-index confirmed: 3 entries (VQAv2, COCO, GQA)
- Upload via HfApi, verified via `model_info()` + raw README fetch

### Current ecosystem state

| Asset | Downloads | Status |
|-------|:---------:|--------|
| context-1.5b-merged | 1,269 | Top performer |
| context-0.5b-merged | 1,030 | Strong second |
| context-7b-merged | 585 | Workhorse |
| context-7b-128k | 382 | Long context |
| context-7b-tools | 219 | Tool adapter |
| embedding-multilingual | 188 | Cross-lingual |
| context-1.5b-tools | 163 | Tool adapter |
| **vision-7b** | **104** | **⬆ Enriched this run** |
| coder-1.5b | 70 | Code |
| tts-model | 69 | TTS |
| sakthai-embedding | 34 | English-only embedding |
| context-0.5b-tools | 7 | Edge tool-calling |
| Nanthasit (profile) | 0 | Profile |
| irrelevance-supplement (ds) | 0 | Dataset |

### Lesson
Vision-7b had the thinnest card in the family despite being a key pipeline component (image→text). The card lacked discoverability tags, benchmark data, Python examples, and pipeline context — all things that help users understand *how* to use it and *where* it fits. Bringing every card up to the family standard compounds the network effect: each enriched card promotes all sibling models through the low-download gems sections and family tables. The final tagline — "Built from a shelter in Cork, Ireland" — adds an emotional hook that distinguishes our models from generic repackagings.

---
