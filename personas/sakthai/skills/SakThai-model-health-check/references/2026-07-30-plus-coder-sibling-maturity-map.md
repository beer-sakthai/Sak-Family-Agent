# Plus-Family Sibling Maturity Map: Coder Variant (2026-07-30)

## Context

Fourth health check of `Nanthasit/sakthai-plus-1.5b-coder`, the last
unpopulated repo in the "plus" family tree. Previous checks (2026-07-30 ×3,
2026-07-31 ×1) all confirmed skeleton status but did NOT systematically map
the sibling repos.

## New Discovery: Complete Family Mapping

| Variant | Has Weights? | Size | Created | Notes |
|---------|-------------|------|---------|-------|
| `sakthai-plus-1.5b` (full) | ✅ `model.safetensors` | 2.96 GB | 2026-07-30 13:02:40 | has config, tokenizer, chat_template |
| `sakthai-plus-1.5b-lora` | ✅ `adapter_model.safetensors` | 81 MB | 2026-07-30 13:02:41 | PEFT adapter, 11 files |
| **`sakthai-plus-1.5b-coder`** | **❌** | **0.02 MB** | 2026-07-30 13:03:02 | **only skeleton** |

## Diagnostic Pattern

**If a skeleton repo has sibling repos with weights → likely "weights not yet
pushed" rather than "never trained / project stalled."**

This distinction matters for:
- **Scoring**: The skeleton cap (max 30) still applies, but the assessment
  section should note sibling maturity as a positive signal
- **Recommendation tone**: "Push pending weights" vs. "Train and upload" are
  very different recommendations
- **Prioritization**: A late sibling in an otherwise-mature family is a
  higher-value fix than a standalone skeleton (the pipeline exists, the
  checkpoint probably exists locally)

## Implementation Approach

```python
# In skeleton detection, add sibling weight check:
from huggingface_hub import HfApi
api = HfApi(token=HF_TOKEN)

# Author's models, same family prefix
author_models = list(api.list_models(author=author))
family_prefix = model_id.split('/')[-1].rsplit('-', 1)[0]  # e.g. "sakthai-plus"

family_siblings = []
for m in author_models:
    mid = getattr(m, 'modelId', getattr(m, 'id', ''))
    if family_prefix in mid and mid != model_id:
        full_info = api.model_info(mid, files_metadata=True)
        siblings = full_info.siblings if hasattr(full_info, 'siblings') else []
        has_weights = any(
            s.rfilename.endswith(('.safetensors', '.gguf', '.bin', '.pth', '.pt'))
            for s in siblings
        )
        family_siblings.append({
            'id': mid,
            'has_weights': has_weights,
            'downloads': getattr(full_info, 'downloads', 0) or 0,
        })

mature_count = sum(1 for s in family_siblings if s['has_weights'])
```

## Links

- Model repo: https://huggingface.co/Nanthasit/sakthai-plus-1.5b-coder
- Full model: https://huggingface.co/Nanthasit/sakthai-plus-1.5b
- LoRA adapter: https://huggingface.co/Nanthasit/sakthai-plus-1.5b-lora
- Base model: https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct
