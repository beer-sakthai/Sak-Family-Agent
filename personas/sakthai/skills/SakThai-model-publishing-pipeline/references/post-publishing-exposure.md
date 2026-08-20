# Post-Publishing Exposure Plan

Promote published models to increase downloads and discoverability on Hugging Face.

## Signal

Use after a model is published with a complete card, benchmarks, and GGUF variants. The model exists but nobody knows about it.

## Tiers

| Tier | Action | Effort | Expected downloads | Probability |
|:----:|--------|:------:|:------------------:|:-----------:|
| **P0** | Cross-link on base model's discussion page | 5 min | +100-300/mo | 🟢 90% |
| **P0** | Create HF Collection with descriptive notes | 5 min | +50-100/mo | 🟢 85% |
| **P1** | Post on r/LocalLLaMA with benchmark table | 10 min | +200-500 | 🟡 50% |
| **P1** | Share on Twitter/X @huggingface | 5 min | +50-200 | 🟡 50% |
| **P2** | Submit to Open LLM Leaderboard | 30 min | +100-500/mo | 🟡 40% |

## Execution order

### Step 1: Cross-link on base model (HF Discussion)

Create a discussion on the BASE model's page recommending your fine-tuned variant:

```python
from huggingface_hub import HfApi
api = HfApi()
api.create_discussion(
    repo_id='Qwen/Qwen2.5-1.5B-Instruct',  # the base model
    repo_type='model',
    title='Fine-tuned variant: SakThai Context 1.5B (4/5 tool-calling)',
    description='''## SakThai Context 1.5B
A fine-tuned variant optimized for tool-calling.

**Metrics:** 4/5 BFCL | 942 downloads | Runs on CPU

**Links:** [Model](...) | [GGUF](...) | [Family Collection](...)
'''
)
```

### Step 2: HF Collection with notes

Create or update a collection that bundles all models + datasets:

```python
col = create_collection(
    title='SakThai Model Family',
    description='All SakThai models and datasets...'
)
add_collection_item(col.slug, 'owner/model-name', item_type='model',
    note='🏆 Most popular — 942 downloads, 4/5 BFCL', exists_ok=True)
```

Add notes to top items describing what makes each special.

### Step 3: Healing cron

Set up a cron that checks all exposure links every 2 min and reports if any go down:

```bash
#!/bin/bash
# Check each exposure link
curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/discussions/25"
curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/collections/..."
curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/owner/model"
```

Create via cronjob(action='create', no_agent=True, schedule='2m', script='exposure-healer.sh').

## Metrics to track

| Metric | How to measure | Target |
|--------|---------------|--------|
| Model downloads | HF API `model.downloads` | +350/mo conservative |
| Collection views | HF Collection page views | Growing |
| Discussion engagement | Replies / upvotes on HF discussion | Any activity |
| GGUF downloads | Separate from model downloads | Growing |

## Results (2026-07-25)

On SakThai 1.5B: Discussion created on Qwen2.5 model page, Collection with notes updated, healing cron active. +30 downloads observed same day.

## Pitfalls

- **Don't spam**: One discussion per base model, not multiple. Create quality content with actual benchmark data.
- **HF discussion permissions**: Some model repos (especially official org repos like `Qwen/`, `google/`) may have discussions disabled or require approval. Handle 403/404 gracefully.
- **Collection requires items**: An empty collection with no models doesn't show in search. Add at least 5 items before considering it published.
- **No upvote API**: You cannot programmatically upvote your own collection or discussion. Growth comes from genuine interest.
