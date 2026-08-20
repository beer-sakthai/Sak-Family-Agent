---
name: SakSit-hf-promotion-campaign
category: social-media
description: End-to-end framework for promoting Hugging Face models across platforms — model cards, Spaces, Collections, Reddit, HF Blog, Kaggle, community engagement. Zero-cost strategy.
version: 1.0.0
platforms:
  - linux
metadata:
  saksit:
    tags:
      - huggingface
      - promotion
      - models
      - open-source
tags:
- HuggingFace
- Promotion
---

# SakSit HF Promotion Campaign

Complete workflow for promoting Hugging Face models across the web.

## Trigger conditions

- Beer asks about promoting HF models
- New model released and needs visibility
- Downloads plateau and need a boost

## Prerequisites

- Valid HF token (write access) at `huggingface.co/settings/tokens`
- `huggingface_hub` Python library installed (`uv pip install huggingface-hub`)
- All model cards have basic metadata (YAML frontmatter)

## The 7 Deliverables

### 1. Model Cards (README.md)

**Critical rule — CORRECTION FROM BEER (Jul 23):** When adding branding (House of Sak, etc.) to existing model cards, you must **PRESERVE ALL EXISTING TECHNICAL DETAIL**. Do not strip architecture tables, eval benchmarks, usage code examples, training hyperparameters, or dataset links just to make room for branding. The correct approach is **merge, not replace** — add branding ON TOP of the existing technical content, keeping every original section intact.

Beer explicitly corrected this: "Bring back" — meaning the original technical detail was mandatory and should never have been removed.

Improved cards should include:
- YAML frontmatter with `model-index` (structured eval results)
- Plain English intro paragraph with optional House of Sak branding
- **Full architecture table** (hidden size, layers, attention heads, params, precision)
- **Detailed training details** (base model, method, hyperparams, dataset size, training duration)
- Multiple code examples (transformers, InferenceClient, vLLM)
- **Complete benchmark tables** with category breakdowns (every eval category, not just overall pass rate)
- Limitations section (builds trust)
- Citation BibTeX

Update via `huggingface_hub` Python library (git push to HF is deprecated — password auth no longer works).

**Working method:**
```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj=new_content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/MODEL-NAME',
    commit_message='SakSit: update model card'
)
```
Works for both models and datasets (`repo_type='model'` or `repo_type='dataset'`). Install: `uv pip install huggingface-hub`.

Full worked example including batch updates and YAML templates: `references/model-card-update-workflow.md`

**Batch update script pattern** — update multiple cards in one script:
```python
for model in ['sakthai-context-0.5b-merged', 'sakthai-context-1.5b-merged']:
    content = open(f'cards/{model}.md', 'r').read()
    api.upload_file(
        path_or_fileobj=content.encode(),
        path_in_repo='README.md',
        repo_id=f'Nanthasit/{model}',
        commit_message='SakSit: update model card'
    )
```

### 2. HF Collections
Create 3 collections via API:
- `🏠 House of Sak` — all agent models + datasets
- `🛠️ SakThai Context` — tool-calling model family
- `📊 SakThai Training Data` — all datasets

Script: `create-collections.py` with valid `HF_TOKEN`.

### 3. Gradio Space Demo
Interactive demo with:
- Model selector dropdown (all sizes)
- Chat interface with example prompts
- Fallback from API to local inference
- Links to each model's HF page

Push via git to HF Spaces repo.

### 4. Reddit Post (r/LocalLLaMA)
Build karma first (5-10 genuine comments), then post:
- Title: authentic + attention-grabbing
- Body: personal hook → technical → eval results → links
- End with MH resources (Pieta, Samaritans)
- Must have 50+ karma to post

### 5. HF Blog Post
Write and submit on `hf.co/blog`:
- 1500-2000 words
- Technical + personal story
- Code blocks, eval tables
- Author: `Nanthasit`
- Submitted for HF review (1-3 day turnaround)

### 6. Kaggle Notebook
Inference notebook on free T4 GPU:
- Load model from HF
- Test 5 capabilities (Q&A, tool-calling, multi-turn, code, JSON)
- Publish as public notebook
- Add to `sakthai-kaggle-notebooks` dataset

### 7. Community Comments
5 genuine, non-promotional comments on:
- Trending tool-calling model cards
- LoRA fine-tuning discussions
- YaRN / long-context threads
- Small model deployment threads
- Well-written model cards (praise + suggestions)

## Execution Order

```
Phase 1 (Day 1-2):
  [ ] Fix/update HF token
  [ ] Push model card improvements
  [ ] Create Collections
  [ ] Push Space demo app

Phase 2 (Day 2-3):
  [ ] Post community comments (karma building)
  [ ] Submit HF Blog post for review

Phase 3 (Day 3-5):
  [ ] Post on r/LocalLLaMA (after karma >= 50)
  [ ] Publish Kaggle notebook

Phase 4 (Ongoing):
  [ ] Track download growth weekly
  [ ] Reply to comments/questions
  [ ] Submit to Open LLM Leaderboard
```

## Pitfalls\n\n- **Gated model access: `model_info()` returns public data for ALL models, even gated ones you haven't been approved for.** To verify actual download access, use `api.list_repo_files(repo_id)` — if it succeeds, you have real access. If it fails 403, you're not approved regardless of what `model_info()` says.\n- HF git auth deprecated — don't use `git clone https://user:TOKEN@huggingface.co/...`. HF no longer accepts password-based git auth. Use `huggingface_hub` Python library instead (see Deliverable 1).
- HF token expiry — check at `huggingface.co/settings/tokens` before starting
- Reddit karma — r/LocalLLaMA requires 10-50 karma; build first
- HF Blog requires review — submit early, it takes 1-3 days
- Space demo needs `HF_TOKEN` configured in Space secrets (Settings → Repository secrets)
- Kaggle T4 GPU has 30h/week limit — test notebook runs fast
- Always include MH resources (Pieta 1800 247 247, Samaritans 116 123) in story posts
- Zero-cost constraint — all listed platforms are free tier

## Verification

- [ ] All model cards render correctly on HF
- [ ] Collections visible on profile
- [ ] Space demo loads and responds to prompts
- [ ] Reddit post visible with no rule violations
- [ ] Blog post published on HF blog
- [ ] Kaggle notebook runs end-to-end
- [ ] Comments posted and visible
- [ ] Download count increases tracked weekly
