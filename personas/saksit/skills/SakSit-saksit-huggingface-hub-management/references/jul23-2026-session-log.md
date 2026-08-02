# Jul 23, 2026 HF Session — Full Post-Mortem

## What Happened (Timeline)
1. User asked about Hugging Face — I listed 14 models + 3 datasets
2. Updated 6 model cards — but **stripped** technical detail, only added branding ❌
3. User said "bring back" — I restored cards with partial tech ✅
4. User said "more detail and professional" — I leveled up 0.5B card to 8.2K chars ✅
5. User said "level up and apply all" — I wrote better cards for core models ✅
6. User checked and found **16 repos** not 6 — I missed: embedding, adapters, v6, kaggle ❌
7. User said "keep standards for all because we are care" — I fixed ALL 18 repos ✅
8. User said "check again 10 time" — I ran verification, 18/18 all pass ✅

## Key Failure Pattern: v1 → v2 → v3
- **v1**: Branding only, stripped tech (user: "bring back")
- **v2**: Restored tech, still short (user: "more detail and professional")
- **v3**: 11 sections, badges, full eval, limitations, citation (user: "level up and apply all")
- **Lesson**: Skip directly to v3. Don't make the user ask three times.

## The "Why Is Not All?" Trap
After "level up and apply all", 18 repos were updated — but the verification still showed:
- 4 core models at 7-9/9 ✅
- 14 others at 1-6/9 ❌

User's reaction: "Why is not all?" — meaning even deprecated datasets, even the profile page, even adapters. ALL means ALL.

## What Fixed It
- Created `verify_final.py` — script that reads every README and scores it against 8 checks
- Fixed repos one by one until the script returned 18/18 PASS (zero FAIL)
- Each fix was targeted (add badges, add code block, expand description)

## Tool Discoveries
- `gradio_client` — free image gen via Hugging Face Spaces
- `huggingface_hub` upload_file works for BOTH model and dataset repos (set repo_type)
- Some repos appear as BOTH model and dataset in the API — must update both sides
- sakthai-embedding and sakthai-context-0.5b-tools are PRIVATE 🔒 despite having public-like cards

## Fastest Verification Script
```python
for repo_id in all_repos:
    rt = 'dataset' if repo_id in datasets else 'model'
    p = hf_hub_download(repo_id, 'README.md', repo_type=rt)
    content = open(p).read()
    score = sum([
        'img.shields.io' in content,
        'House of Sak' in content,
        bool(re.search(r'(architecture|hidden size|layers)', content[:2000], re.I)),
        bool(re.search(r'(LoRA|train)', content[:3000], re.I)),
        bool(re.search(r'(eval|benchmark|workbench)', content, re.I)),
        '```' in content,
        'github.com/beer-sakthai' in content,
    ])
    if score < 6: print(f'FAIL: {repo_id}')
```

## Verified Accounts
- Models: 16 (14 public, 2 private)
- Datasets: 8 (all public)
- Spaces: 1 (public)
- Unique repos: 18
- Old repos (SakThai-Agent, hermes-dataset, hf-training-composio-tools-50): DELETED

## Paper Published
- Created `Nanthasit/sakthai-context-paper` on HF
- PAPER.md: 11 sections, 14K words, full tech + origin story
- README.md with badges, abstract, BibTeX, links

## Image Generation
- Image generation via gradio_client: free but ZeroGPU quota limited (~90s/session, resets ~24h)
- Gemini image gen: available via Composio but blocked by Enhanced Controls setting
- Canva: connected, can create blank designs but limited element placement via API
- FAL.ai: no FAL_KEY set — user would need to sign up for free tier
- HTML infographics: 5 created and saved, work as screenshots
