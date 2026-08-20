# 2026-07-30 — sakthai-context-7b-merged Health Check + Sibling Comparison

## What

Health eval of the largest SakThai model (7B, Qwen2.5-7B-Instruct base) with sibling comparison against 1.5B and 0.5B.

## Key findings

- **7B model.safetensors**: 15,231,272,152 bytes (14.19 GB) — confirmed via `curl -sIL` redirect chain
- **7B lacking GGUF** — 1.5B and 0.5B both have Q4_K_M quantized variants, 7B does not
- **Downloads**: 7B=744, 1.5B=1599 (leader), 0.5B=1370
- **Bench v2 selection accuracy**: 7B=57%, 1.5B=48.2%, 0.5B=91.2% (inverted)
- All models have `verified: false` on benchmarks

## Reproduction

```bash
# Fetch model info (don't use ?blobs=true — it collapses scalars)
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/Nanthasit/sakthai-context-7b-merged" \
  -o /tmp/hf-7b-info.json

# File size via Xet redirect chain
curl -sIL -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/sakthai-context-7b-merged/resolve/main/model.safetensors" \
  | grep -i content-length | tail -1
# → Content-Length: 15231272152

# Config
curl -sL -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/sakthai-context-7b-merged/resolve/main/config.json"
# → hidden_size=3584, num_hidden_layers=28, num_attention_heads=28, num_key_value_heads=4, vocab_size=152064

# Tree API verification (upload check)
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/Nanthasit/sakthai-context-7b-merged/tree/main/.eval_results" \
  | python3 -c "import sys,json; files=[f['path'] for f in json.load(sys.stdin) if 'health-check-2026-07-30' in f['path']]; print(files)"
```

## Config comparison

| Field | 7B | 1.5B | 0.5B |
|-------|:--:|:----:|:----:|
| hidden_size | 3584 | 1536 | 896 |
| layers | 28 | 28 | 24 |
| attn_heads | 28 | 12 | 14 |
| KV_heads | 4 | 2 | 2 |
| intermediate | 18944 | 8960 | 4864 |
| vocab | 152064 | 151936 | 151936 |
| context | 32768 | 32768 | 32768 |
| bf16 | ✅ | ✅ | ✅ |

## Files

All siblings use Xet (CAS bridge) storage — `size: null` in HF API.
Real sizes obtained from redirect chain:

| File | 7B | 1.5B | 0.5B |
|------|:--:|:----:|:----:|
| model.safetensors | 14.19 GB | 2.88 GB | 942 MB |
| GGUF Q4_K_M | — | 940 MB | 379 MB |

## Upload pattern

Report uploaded to all three repos (broadcast):
- `Nanthasit/sakthai-context-7b-merged/.eval_results/health-check-2026-07-30.yaml`
- `Nanthasit/sakthai-context-1.5b-merged/.eval_results/health-check-2026-07-30.yaml`
- `Nanthasit/sakthai-context-0.5b-merged/.eval_results/health-check-2026-07-30.yaml`

## Vanity metric note

7B has lowest downloads (744) despite being the strongest model. The absence of a GGUF quant may be the primary blocker — users who want to try locally have no option without hardware for 14 GB weights.
