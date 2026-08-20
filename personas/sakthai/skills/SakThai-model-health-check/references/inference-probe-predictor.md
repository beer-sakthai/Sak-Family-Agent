# Inference Probe Predictor

Pre-check model metadata to predict whether serverless inference will work. Saves time and avoids blind endpoint retries.

## Quick Decision Table

Check these from `/api/models/{owner}/{repo}` before probing:

| Tags present | library_name | pipeline_tag | Size | Likely result | Action |
|---|---|---|---|---|---|
| `merged`, `peft`, `qlorafinetuned` | transformers | text-generation | 7B+ | ❌ Not on any provider | Skip probe. Report as "custom community merge — not on serverless" |
| `base_model:*` (points to non-base arch) | transformers | text-generation | any | ❌ Likely not supported | Quick-check router once, fall back immediately |
| `sentence-transformers` | sentence-transformers | feature-extraction / sentence-similarity | any | ❌ Not on serverless | Skip probe. Suggest local `SentenceTransformer` |
| `kokoro`, `gguf` | kokoro | text-to-speech | any | ❌ Not on serverless | Skip probe. Suggest local inference |
| `gguf` | transformers | image-to-text | any | ❌ Not on serverless | Vision GGUF needs llama.cpp --mmproj. Router returns 400 "model not supported". Skip probe, report as local-only format |
| `text-generation-inference` present | transformers | text-generation | any | ✅ May work | Full probe |
| `endpoints_compatible` present | transformers | text-generation | any | ✅ May work | Full probe |

## Quick Tag Check Script

```bash
# Check if model is likely unsupported before probing
curl -s "https://huggingface.co/api/models/$MODEL" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
tags = d.get('tags', [])
lib = d.get('library_name', '')
pipe = d.get('pipeline_tag', '')
# Heuristic: merged/peft + transformers + text-generation + no TGI tag = community merge
if 'merged' in tags and lib == 'transformers' and pipe == 'text-generation' and 'text-generation-inference' not in tags:
    print('PREDICT: model_not_on_serverless')
elif lib == 'sentence-transformers':
    print('PREDICT: model_not_on_serverless')
elif 'kokoro' in tags:
    print('PREDICT: model_not_on_serverless')
else:
    print('PREDICT: unknown — probe needed')
"
```
