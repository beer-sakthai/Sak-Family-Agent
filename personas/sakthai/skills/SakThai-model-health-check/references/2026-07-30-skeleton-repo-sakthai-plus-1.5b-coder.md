# Skeleton Repo: sakthai-plus-1.5b-coder (2026-07-30)

## Context

First health check of `Nanthasit/sakthai-plus-1.5b-coder`, a model created on HF Hub
but with no weight files uploaded. Found during the 2026-07-30 cron sweep.

## Key observations

| Field | Value | Note |
|-------|-------|------|
| `createdAt` | 2026-07-30T13:03:02.000Z | Today, 8h old |
| `downloads` | 0 | Nothing to download |
| `likes` | 0 | Expected |
| `usedStorage` | 0 | **Zero bytes** |
| `config` | `{}` | Empty dict — no model architecture |
| `siblings` | 4 | Only README.md, .gitattributes, 2× .eval_results/ |
| `tree/main` entries | 3 | 2 files + .eval_results/ directory |
| `safetensors` key | absent | No weight files |
| `gguf` key | absent | No quantized files |

## Detection

The API response had:
- `pipeline_tag: text-generation` (telemetry-only, no actual inference possible)
- `library_name: transformers` and `transformersInfo.auto_model: AutoModel`
- But NO `safetensors` key, NO `gguf` key, NO `config` content
- NO model weight files in `siblings`
- `usedStorage: 0`

This was NOT a LoRA adapter (no `adapter_model.safetensors`) and NOT a real model
(no `model.safetensors`). Pure skeleton.

## Sibling comparison

The `sakthai-plus-1.5b` (non-coder) variant was created **1 minute earlier** and
**did** have full weights (2.9 GB `model.safetensors`, 8 files, `usedStorage: 6.1 GB`).
The coder variant lagged — either weights hadn't been pushed yet or the HF repo
creation completed without an upload step.

The previous-generation coder (`sakthai-coder-1.5b`) had 93 downloads in 6 days
and 1,561 siblings (mostly `.venv/` dev artifacts) with a 1.06 GB GGUF Q4_K_M file.

## Health score: 10/100

```
popularity:         0   — 0 downloads, 0 likes
download_momentum:  0   — 0/day velocity
benchmark_coverage: 0   — no model-index
card_quality:      80   — good README, tags, widget examples
repo_hygiene:      25   — "too clean" penalty: 4 files, nothing useful
```

The `repo_hygiene` score was deliberately lowered from a naive 100 (0 dev artifacts)
to 25 to reflect that a skeleton with nothing to download is not a clean repo —
it's an unfinished one.

## Delta from previous check (2h later)

- downloads: unchanged (0)
- likes: unchanged (0)
- lastModified: 20:59:44Z → 21:16:23Z (only the previous health-check YAML was uploaded)
- Health score: 12 → 10 (slight regression captured in `changes_since_previous`)

## Recommendations logged in YAML

1. **CRITICAL**: Upload safetensors (merge rsLoRA adapters) + config.json + tokenizer
2. **HIGH**: Push GGUF Q4_K_M quant (~1 GB) — v1 coder's main distribution channel
3. **HIGH**: Add benchmark results to model-index
4. **MEDIUM**: Add to sakthai-model-family collection

## Links

- Model: https://huggingface.co/Nanthasit/sakthai-plus-1.5b-coder
- Previous coder: https://huggingface.co/Nanthasit/sakthai-coder-1.5b
- Non-coder plus sibling: https://huggingface.co/Nanthasit/sakthai-plus-1.5b
- Base: https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct
