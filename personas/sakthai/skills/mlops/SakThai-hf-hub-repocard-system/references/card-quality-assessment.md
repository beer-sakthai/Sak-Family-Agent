# Card Quality Assessment Matrix

**Trigger:** After listing models but before picking a target. Run this to decide which card needs improvement most.

## The Problem

The "pick a target" step in the cron maintenance loop is the hardest to automate. Without a systematic quality check, you either always pick the lowest-download model (ignoring already-enriched cards) or waste API calls re-checking everything.

## The Solution: Feature Matrix Check

Download each model's README.md and check for 5 key feature markers. Score as present/absent. Rank by (gaps desc, downloads asc).

### The 5-Feature Check

| Feature | Marker | Why it matters |
|---------|--------|----------------|
| **Dynamic Badge** | `img.shields.io` in content | Downloads auto-update from HF API |
| **Pipeline Integration** | `## Pipeline Integration` heading | Shows how model connects to siblings |
| **Family Links** | `SakThai`, `Family`, or `siblings` | Cross-references sibling models |
| **Call-to-Action** | `leave a like`, `support the project`, etc. | Community engagement hook |
| **model-index YAML** | `model-index:` in content | Enables HF search indexing |

### How to Run

```python
from huggingface_hub import hf_hub_download

targets = [
    ('Nanthasit/sakthai-vision-7b', 'vision-7b', 0),
    ('Nanthasit/sakthai-tts-model', 'tts-model', 0),
    ('Nanthasit/sakthai-embedding-multilingual', 'embedding-multilingual', 0),
    ('Nanthasit/sakthai-context-0.5b-tools', '0.5b-tools', 7),
    ('Nanthasit/sakthai-coder-1.5b', 'coder-1.5b', 15),
    ('Nanthasit/sakthai-embedding', 'embedding', 28),
]

for repo_id, name, dl in targets:
    card_path = hf_hub_download(repo_id, 'README.md', force_download=True)
    with open(card_path) as f:
        content = f.read()
    
    badge = 'img.shields.io' in content
    pipeline = '## Pipeline Integration' in content
    family = any(x in content.lower() for x in ['sakthai', 'family', 'siblings'])
    cta = any(x in content.lower() for x in ['leave a like', 'support the project', 'report issues'])
    model_index = 'model-index:' in content
    missing = sum(not x for x in [badge, pipeline, family, cta, model_index])
    
    gap_list = []
    if not badge: gap_list.append('badge')
    if not pipeline: gap_list.append('pipeline')
    if not family: gap_list.append('family')
    if not cta: gap_list.append('cta')
    if not model_index: gap_list.append('m-index')
    
    print(f'{name:30s} ({dl:>3} dl) | {len(content):>5} chars | {missing} gap(s): {", ".join(gap_list)}')
```

### Priority Heuristics

Sort order:
1. **Feature gaps** (descending) — most holes first
2. **Downloads** (ascending) — lowest downloads need most visibility help
3. **Card length** (ascending) — thinner cards have bigger marginal gain per char

### Tiebreakers

| Situation | Pick |
|-----------|------|
| Same gaps, different downloads | Lower downloads first |
| model-index missing vs CTA missing | **model-index** first (controls search visibility) |
| Zero dl + no model-index | Highest priority overall (invisible in search AND no traffic) |
| Multiple cards with same scores | Thinnest card (biggest marginal improvement per char) |

### Real-World Example (2026-07-27)

This session's assessment of models <50 downloads:

| Model | dl | Chars | Badge | Pipeline | Family | CTA | M-Idx | Gaps |
|-------|:--:|:-----:|:-----:|:--------:|:------:|:---:|:-----:|:----:|
| 0.5b-tools | 7 | 6,510 | ✅ | ✅ | ✅ | ❌ | ❌ | 2 |
| coder-1.5b | 15 | 10,186 | ✅ | ✅ | ✅ | ✅ | ✅ | 0 |
| vision-7b | 0 | 11,958 | ✅ | ✅ | ✅ | ❌ | ✅ | 1 |
| tts-model | 0 | 9,497 | ✅ | ✅ | ✅ | ❌ | ❌ | 2 |
| embedding-multilingual | 0 | 14,921 | ✅ | ✅ | ✅ | ❌ | ✅ | 1 |

**Winner:** tts-model (0 dl, 2 gaps incl. model-index). Added both → card 9,497→10,346 chars, 11/11 verify pass.

### Pitfalls

- **`hf_hub_download` caches aggressively.** Use `force_download=True` to bypass cache; otherwise you get the version from the first download in the session, not the live Hub state.
- **Only check models < 50 downloads.** Checking every model every run wastes API calls on already-enriched cards (>500 dl). Focus on the marginal tail.
- **pipeline_tag ≠ model-index.** A model can have `pipeline_tag: text-to-speech` in frontmatter (for the badge) but no `model-index:` block (for search indexing). Both are needed — don't confuse them.
- **Char count is a proxy, not a quality metric.** A 15K-char card could be padded; a 5K-char card could be perfectly concise. Always verify actual features present.
