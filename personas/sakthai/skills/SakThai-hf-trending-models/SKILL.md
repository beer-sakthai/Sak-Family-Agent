---
name: SakThai-hf-trending-models
version: 1.0.0
description: Tracked snapshot of trending models from Hugging Face Hub
category: mlops
tags:
- hf
- huggingface
- models
- trending
---

# Trending Models Tracker

Monitors high-velocity and breakout models across the Hugging Face ecosystem via the `trendingScore` and `recentlyTrending` APIs.

---

## 📊 Trending Data Ingestion Endpoints

### Option A: Ranked Model List (`trendingScore`)
Returns flat model catalog sorted by global trend velocity score:
```bash
# Get top 15 models by trendingScore
curl -s "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=15" -o /tmp/hf_trending.json
python3 -c "
import json
with open('/tmp/hf_trending.json') as f:
    data = json.load(f)
for i, m in enumerate(data, 1):
    print(f'{i:2d}. {m["modelId"]:50s} ⭐{m.get("likes",0):>5d}  ⬇{m.get("downloads",0):>9d}  TS={m.get("trendingScore","?")}')
"
```

### Option B: High-Velocity Feed (`recentlyTrending`)
Returns fastest accelerating models (limit $\le 20$):
```bash
# Get top 20 recently trending
curl -s "https://huggingface.co/api/trending?limit=20" -o /tmp/hf_trending_recent.json
python3 -c "
import json
with open('/tmp/hf_trending_recent.json') as f:
    d = json.load(f)
items = [i for i in d.get('recentlyTrending', []) if i.get('repoType') == 'model']
for i, item in enumerate(items[:15], 1):
    m = item['repoData']
    print(f'{i:2d}. {m["id"]:50s} ⭐{m.get("likes",0):>5d}  ⬇{m.get("downloads",0):>9d}')
"
```

---

## ⚠️ Key Operational Pitfalls

1. **`hf models list --sort trending` CLI Flag**: The CLI `models list` command does NOT support `--sort trending`. Always use direct API queries shown above.
2. **Safe Pipe Execution**: Avoid piping `curl ... | python3` directly in automated scripts to prevent hanging processes. Write to `/tmp/hf_data.json` first.
3. **Canonical ID Resolution**: Query `/api/models/{id}` to verify canonical IDs before logging to avoid tracking transient redirects.
4. **Quantized Weights Detection**: A large `I32` count in `safetensors.parameters` indicates native INT4 quantization rather than 32-bit parameters.

---

## 🏛️ Deep-Dive Architecture References
Detailed architectural analysis for recent breakout trending models:
- [Bonsai 27B Binary Quantization](./references/bonsai27b-binary-quantization.md)
- [GLM-5.2 DSA IndexShare Architecture](./references/glm52-architecture-dsa-indexshare.md)
- [Kimi K2.7 Code Architecture & MLA](./references/kimi-k27-code-architecture-mla.md)
- [Motif 3 Architecture & GDLA](./references/motif3-architecture-gdla-poly.md)
- [Qwen 3.5 Hybrid Architecture](./references/qwen35-hybrid-architecture.md)
- [UltraX Progress Refinement](./references/ultrax-architecture-progrefine.md)
- [Unlimited OCR Vision-Language Transformer](./references/unlimited-ocr-architecture-rsa.md)
