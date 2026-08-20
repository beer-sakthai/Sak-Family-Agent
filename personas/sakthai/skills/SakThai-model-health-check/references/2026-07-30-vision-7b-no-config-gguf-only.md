# Vision 7B: GGUF-only, no config.json

**Model:** `Nanthasit/sakthai-vision-7b` (LLaVA-1.5-7b Q4_K_M quant)
**Date:** 2026-07-30

## Key characteristics

- **GGUF-only model:** no `config.json`, `preprocessor_config.json`, `tokenizer_config.json`, or any other JSON config. All architecture metadata is embedded in the GGUF header.
- **Two GGUF files:** `llava-1.5-7b-hf-q4_k_m.gguf` (6.4 GB) + `mmproj-model-f16.gguf` (~1 GB). The `gguf.total` field from the API reports 6,738,939,904 bytes (6,426 MB uncompressed tensor data). The sibling `size` field returns 0 for all files (Xet storage) — use the `gguf` top-level dict for real sizes.
- **`config.json` returns "Entry not found"** (15-byte error response from HF).
- **Architecture details obtained from the `gguf` field** in the `/api/models/{id}` response: `gguf.architecture` = "llama", `gguf.context_length` = 4096. Card metadata and tags supply the vision encoder + projector details.
- **Multimodal chat template** is embedded in the `gguf.chat_template` field — includes image token (`<image>`) handling.

## Health check implications

- Without `config.json`, the `has_real_weights: true, config: MISSING` pattern applies. The `missing_config` flag is set but doesn't penalize the health score as harshly as missing weights — GGUF-only repos are valid deployment artifacts.
- Pipeline tag (`image-to-text`) visits the "old" schema path in verify-health-check.py.
- The `gguf` API field is the **only** source of architecture info (context length, arch family, quantization). It's populated from the GGUF file header at upload time.
- Stable metrics: this model has had 0 downloads growth in two consecutive health checks (186 → 186 across 13 minutes). Low-velocity by design — niche vision model, not a text-generation workhorse.

## Related

- GGUF architecture metadata extraction via the raw API endpoint (no blobs expand needed): `gguf` is a top-level field on the standard `/api/models/{id}` response.
- For inference, llama.cpp requires both GGUF files: `--model llava.gguf --mmproj mmproj-model-f16.gguf`.
