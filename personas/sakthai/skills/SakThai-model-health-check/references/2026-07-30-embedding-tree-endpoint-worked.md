# Tree Endpoint Returned Real Sizes for Xet-Backed Embedding Model

## Date
2026-07-30, nightly cron run.

## Model
`Nanthasit/sakthai-embedding-multilingual` — BERT-12L-384H embedding model, Xet-backed storage.

## Finding
The `/api/models/{id}/tree/main` endpoint **can** return real file sizes for Xet-stored models. The skill previously claimed it "also returns null for large LFS/Xet blobs" — this is not universally true.

## Command

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/Nanthasit/sakthai-embedding-multilingual/tree/main" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
for item in d:
    print(item.get('path',''), item.get('size','N/A'), item.get('type',''))
"
```

## Result

```
.eval_results         0          directory
1_Pooling             0          directory
.gitattributes        1570       file
README.md             9961       file
config.json           747        file
config_sentence_transformers.json 284 file
model.safetensors     470637416  file
modules.json          277        file
sentence_bert_config.json 241    file
tokenizer.json        17082987   file
tokenizer_config.json 588        file
```

Key: `model.safetensors` → **470,637,416 bytes** (448.8 MB), `tokenizer.json` → **17,082,987 bytes** (16.3 MB). Both are Xet-backed files with real sizes returned.

## When the Tree Endpoint May Still Fail
- Skeleton repos with no weights (returns 0-sized entries or missing files)
- Very new repos where blob indexing hasn't caught up (observed on day-zero uploads)
- GGUF repos sometimes return `null` for `.gguf` files — fall back to Method 0 (API `gguf.totalFileSize`) in that case

## Recommendation
Try the tree endpoint first in every health check. If it returns real sizes for weight-bearing files, use them directly — it's the cheapest call (no redirects, no HEAD chains). Fall through to HEAD + `x-linked-size` or redirect chain only when the tree returns 0/null for known-weight files.
