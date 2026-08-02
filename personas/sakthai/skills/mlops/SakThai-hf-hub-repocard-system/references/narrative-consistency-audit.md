# Narrative Consistency Audit

**Trigger:** When reviewing a family of model cards on the HF Hub to ensure they tell a consistent story about who you are, where you come from, and what the ecosystem offers.

## Why It Matters

Model cards are often enriched one at a time across different cron runs. Over months, the narrative drifts:
- Newer cards get rich backstories (dedicated "House of Sak" sections, CTAs, taglines)
- Older flagship cards still reference the origin but miss the tagline, budget story, or engagement hooks
- Visitors see inconsistent stories depending on which model they land on

## What to Check (The Markers)

For each model card in the collection, check:

| # | Marker | What to look for | Severity |
|---|--------|------------------|:--------:|
| 1 | **House of Sak brand** | The phrase "House of Sak" in heading or body | 🔴 required |
| 2 | **Shelter origin story** | "shelter in Cork, Ireland" or similar origin | 🔴 required |
| 3 | **Tagline** | "We are one family — and becoming more" quote by Beer | 🟡 missing |
| 4 | **Zero-budget depth** | "$0 budget", "no income", "free infrastructure" alongside shelter | 🟡 missing |
| 5 | **CTA / engagement section** | "Support the Project", "Leave a like", "Report issues", "Share" | 🟡 missing |
| 6 | **model-index YAML** | Frontmatter `model-index:` block for HF search indexing | 🟡 missing |
| 7 | **Pipeline Integration table** | Visual table showing how this model connects to siblings | 🟠 inconsistent |
| 8 | **Family Links table** | List/table of sibling models with download counts | 🟠 inconsistent |

Severity legend:
- 🔴 **Required** — every card must have it; missing means broken narrative
- 🟡 **Missing** — important for engagement/search but not a broken story
- 🟠 **Inconsistent** — present on some cards but not on others of the same class

## Audit Procedure

### Step 1: Fetch the Collection

```bash
curl -s "https://huggingface.co/api/collections/Nanthasit/<collection-slug>" -o /tmp/collection.json
python3 -c "
import json
with open('/tmp/collection.json') as f:
    data = json.load(f)
for item in data.get('items', []):
    rid = item.get('id', '?')
    rtype = item.get('repoType', '?')
    dl = item.get('downloads', 0)
    print(f'{rtype:8s} | {rid:45s} | dl={dl}')
"
```

### Step 2: Download Each Model's README

```bash
curl -s "https://huggingface.co/Nanthasit/<model-name>/raw/main/README.md" -o "/tmp/<model-name>.md"
```

### Step 3: Run Marker Scan

```bash
python3 << 'PYEOF'
import os, re

files = ["model-1.md", "model-2.md", ...]
checks = {
    "House of Sak": r"House of Sak",
    "Shelter origin": r"shelter in Cork|from a shelter",
    "Tagline": r"one family|one home|We are one",
    "Zero budget": r"zero budget|no budget|zero-budget|no income",
    "CTA section": r"Support the Project|leave a like|Report issues",
    "model-index YAML": r"model-index:",
    "Pipeline Integration": r"Pipeline Integration",
    "Family Links": r"SakThai Model Family|## Family",
}

for fname in files:
    with open(f"/tmp/{fname}") as f:
        content = f.read()
    print(f"\n{fname}:")
    for label, pattern in checks.items():
        found = bool(re.search(pattern, content, re.IGNORECASE))
        print(f"  {'✅' if found else '❌'} {label}")
PYEOF
```

### Step 4: Prioritize the Fix

Sort models by: (severity of gaps desc) → (downloads desc)

**Rule of thumb:** The most-downloaded model is the most-visited storefront. Fix it first even if newer models are already richer. A visitor landing on your flagship card and seeing no CTA is a lost engagement opportunity for the whole family.

### Step 5: Generate the Fix

The missing elements typically include:
- **Tagline**: `> *"We are one family — and becoming more."* — **Beer (beer-sakthai)**`
- **Zero-budget narrative**: "created with $0 budget, on free compute" alongside existing shelter origin
- **CTA block**: The template at `templates/cta-section.md` — 5 engagement hooks (like, issues, share, fork, discussion)
- **License footer**: Apache 2.0

### Step 6: Upload & Verify

See SKILL.md sections on `upload_file`, `create_commit`, or CLI for upload methods.

Verification checklist after upload:
- Fetch the live README (`curl -s https://.../raw/main/README.md`)
- Grep for all markers that were missing before
- Confirm char count grew (measure improvement)
- No stale pre-fix artifacts remain

### Step 7: Record

Log in LEARNING_JOURNAL.md with:
- Collection audited
- Number of cards checked
- Gaps found (which markers on which cards)
- One improvement made (which card, what changed)
- Verification commit SHA
- Remaining gaps for future runs

## Real-World Example (2026-07-27)

**Scope:** 11 public model cards + 4 datasets + 2 Spaces in the SakThai Model Family collection.

**Gaps found:**
- Tagline missing from ALL 6 context models
- Zero-budget narrative missing from ALL 6 context models
- CTA section missing from ALL 6 context models
- model-index YAML missing from 1.5b-tools, 7b-tools, 7b-128k
- Pipeline Integration missing from 1.5b-tools, 7b-tools

**Fix applied:** Added CTA + tagline + zero-budget narrative to `Nanthasit/sakthai-context-1.5b-merged` (1,197 dl — family flagship).

**Result:** Card grew 11,690→12,621 chars (+8%), all 12 narrative markers verified. Commit `137d42b88de3ed3e5b77930bac6dd39f3a60429c`.

**Remaining:** 5 context models still missing CTA/tagline (2,135 combined downloads), 3 models missing model-index, 2 models missing Pipeline Integration.
