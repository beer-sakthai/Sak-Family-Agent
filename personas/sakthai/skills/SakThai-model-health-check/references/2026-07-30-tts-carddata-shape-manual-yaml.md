# TTS Model CardData Shape & Manual YAML Construction (2026-07-30)

**Model:** `Nanthasit/sakthai-tts-model` (Kokoro TTS, 82M Q8_0 GGUF)
**API response date:** 2026-07-30

## TTS/Kokoro CardData Structure

```json
{
  "license": "mit",
  "language": ["en", "ja", "ko", "zh", "fr", "es", "pt", "it", "de", "pl", "ru", "ar", "hi", "bn", "th"],
  "pipeline_tag": "text-to-speech",
  "library_name": "kokoro",
  "tags": ["tts", "text-to-speech", "speech", "kokoro", "gguf", "audio", "voice", "sakthai", "house-of-sak",
           "edge", "cpu-inference", "local-ai", "offline", "privacy", "multilingual", "model-index"],
  "extra": {"sibling": "Nanthasit/sakthai-tts"},
  "datasets": ["Nanthasit/sakthai-combined-v6", "Nanthasit/sakthai-combined-v7",
               "Nanthasit/sakthai-kaggle-notebooks", "Nanthasit/SimpleToolCalling",
               "Nanthasit/food-penguin-v1", "Nanthasit/sakthai-irrelevance-supplement",
               "Nanthasit/sakthai-bench-v1", "Nanthasit/sakthai-bench-v2"]
}
```

**Key observations:**
- No `model-index` key — TTS models don't carry benchmarks
- No `base_model` key — Kokoro TTS is a standalone architecture, not a fine-tune
- No `min_edits`, `min_steps`, `min_audio_len`, `max_audio_len` — these are NOT in the HF API response (they were task assumptions, not real fields)
- No `eval_results` — consistent with no benchmark coverage
- `extra.sibling` links to the companion `Nanthasit/sakthai-tts` repo
- 8 datasets linked — consistent with Beer's training data ecosystem
- MIT license

## Top-Level HF API Keys for TTS Models

The `/api/models/{id}` response uses **camelCase** keys for temporal fields:

```python
data.get("createdAt")       # "2026-07-25T06:54:35.000Z"
data.get("lastModified")    # "2026-07-30T22:38:54.000Z"
```

NOT `created_at` / `last_modified`. The skill's API-sparsity pitfall mentions these may be null, but when present, use the camelCase form.

Other top-level keys confirmed present for TTS repos:
- `_id`, `id`, `private`, `pipeline_tag`, `library_name`, `tags`, `downloads`, `likes`, `modelId`, `author`, `sha`, `lastModified`, `gated`, `disabled`, `cardData`, `gguf`, `siblings`, `spaces`, `createdAt`, `usedStorage`

## Manual YAML Construction (When PyYAML Is Not Available)

When `yaml` module is absent (common in bare cron-mode Python without `uv run python3`), build YAML as plain Python strings:

```python
yaml_lines = []
yaml_lines.append(f"model: Nanthasit/sakthai-tts-model")
yaml_lines.append(f"eval_date: {now_utc}")
yaml_lines.append(f"pipeline_tag: {pipeline_tag}")
yaml_lines.append(f"downloads: {downloads}")
yaml_lines.append(f"likes: {likes}")
yaml_lines.append(f"model_file:")
yaml_lines.append(f"  name: kokoro-82m-q8_0.gguf")
yaml_lines.append(f"  size_bytes: {model_file_size}")    # ← NO comma formatting
yaml_lines.append(f"  size_mb: {round(mfs/(1024*1024),2)}")
yaml_lines.append(f"languages:")
for lang in languages:
    yaml_lines.append(f"  - {lang}")
yaml_lines.append(f"card_summary:")
yaml_lines.append(f"  license: {card_data.get('license', 'mit')}")
yaml_lines.append(f"  tags:")
for t in card_data.get("tags", []):
    yaml_lines.append(f"    - {t}")

yaml_content = "\n".join(yaml_lines) + "\n"
```

**Rules:**
1. NO comma-formatted numbers in YAML values — `f"{num:,}"` produces invalid YAML (e.g., `14,132,233`). Use bare `f"{num}"`.
2. Strings with colons don't need quoting unless they contain special YAML chars.
3. Booleans: write `false`/`true` lowercase — `str(x).lower()`.
4. Nested structure: each level adds 2-space indentation.
5. Lists: `- item` at the appropriate indentation level.
6. Strings may need single quotes if they contain `:` followed by space (to avoid YAML dict parsing).

This approach is simpler than `json.dumps` + key replacements (no regex, no JSON-to-YAML conversions) and more readable for moderately nested (2-3 level) structures.

## GGUF File Size Source (Preferred Path)

For any repo with a `.gguf` file, the top-level `gguf` key provides file size directly:

```python
data.get("gguf", {}).get("totalFileSize")  # 141322336
```

**⚠ The `gguf` key is only present on the RAW endpoint (`/api/models/{id}`).** The `?expand[]=cardData` variant strips the `gguf` dict, returning `null`. If you fetched with `?expand[]=cardData`, the `gguf` key will be absent even though the repo has a `.gguf` file. Always fetch the raw endpoint separately when you need GGUF metadata — see the main skill's Section 1 three-call pattern and the "drops the gguf dict" pitfall.

The sibling entries for the GGUF file may have NO `size` or `lfs` fields at all — just `{"rfilename": "kokoro-82m-q8_0.gguf"}`. The `gguf.totalFileSize` is the authoritative size. Only fall through to HEAD redirects (`x-linked-size`) when the `gguf` key is absent.

## Sibling Counts (TTS Repo)

TTS repos are minimal:
- `kokoro-82m-q8_0.gguf` — the model weights (~135 MB)
- `README.md` — model card
- `.gitattributes` — LFS tracking
- `.eval_results/health-check-*.yaml` — health checks (one per eval)
