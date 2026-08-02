# Benchmark Data Cross-Referencing

**Trigger:** When reviewing model card content for consistency, or after discovering a model card's benchmark scores contradict each other or the authoritative README.

## Why It Matters

Model cards are often enriched across multiple cron runs by different agents. Over time, their benchmark data drifts independently:
- The card's "Benchmark Results" table gets updated from one run
- The "Benchmark Comparison" table gets written from a different template/run
- The "Verified Results" section is written by yet another agent
- **None of them may match the authoritative README** (the single source of truth)

A visitor seeing contradictory scores on the same page loses trust instantly.

## The Pattern: Duplicate Benchmark Sections

The most common source of drift is **duplicate overlapping benchmark sections on a single card**. When a card has both a "Benchmark Results" table AND a "Benchmark Comparison vs Similar-Sized Models" table, the overlap creates two maintenance points that inevitably diverge.

### Real-world example (0.5B-merged, 2026-07-26)

Three conflicting scores on the same page:

| Section | 1.5B Score | 0.5B Score |
|---------|:----------:|:----------:|
| "Benchmark Results" table | 4/5 | 3/5 |
| "Benchmark Comparison" table | *pending* | *Pending — see note* |
| "Verified Results" section | — | 1/5 |
| **Authoritative README** | **5/5 🏆** | **1/5** |

None matched. Three different claims for the same models — on the same page.

## YAML model-index: The Hidden Drift Vector

Beyond body tables, benchmark scores are also declared in the **YAML frontmatter `model-index:` block** — metadata that HF search indexes, model cards render, and API responses surface. This block is set once at card creation and is **never revisited** when benchmarks are verified or updated later.

### Real-world example (1.5B-merged, 2026-07-26)

The `Nanthasit/sakthai-context-1.5b-merged` card had three independent sources of truth, all stale:

| Source | Claimed | Actual |
|--------|:-------:|:------:|
| `model-index` YAML: `value: 0.8`, `name: Score (4/5)` | 4/5 | ❌ |
| "Benchmark Results" body table | 4/5 | ❌ |
| "Benchmark Comparison" body table | 4/5 | ❌ |
| **Authoritative README** | **5/5 🏆** | ✅ |

All three locations showed 4/5 while the verified BFCL benchmark is 5/5. The YAML metadata meant HF search and API consumers also saw the wrong number.

### Why YAML model-index Drifts

1. **Set-once behavior**: model-index is typically written when the card template is first created with preliminary or expected scores. It is never updated by subsequent content-editing cycles.
2. **Not visible in body reviews**: When an agent reviews the card for narrative consistency, it scans the body markdown but rarely re-checks the YAML frontmatter metadata block.
3. **Different code path**: Fixing body tables (`sed`, `patch` on body text) doesn't touch the YAML frontmatter above the `---` delimiter. The YAML block must be edited explicitly.

### Detection: How to Catch Stale YAML model-index

```bash
# Fetch the card
curl -s -o /tmp/card.md "https://huggingface.co/Nanthasit/<model-name>/raw/main/README.md"

# Extract the YAML frontmatter (everything between first --- delimiters)
sed -n '1,/^---/p' /tmp/card.md | head -n -1

# Within the YAML, look for the model-index block and check:
# 1. Does 'value' match the verified benchmark?
# 2. Does 'name' (human-readable score) match?
# 3. Is 'verified: true' accurate?
grep -A5 "model-index:" /tmp/card.md | head -20
```

**Key warning signs:**
- `value: 0.xx` with `verified: true` but the authoritative README says something different
- `name: Score (X/5)` where X doesn't match the README
- `verified: true` on a score that was never actually verified
- A model-index block that exists alongside body benchmark tables but differs from them

### Fix: Edit YAML Frontmatter Directly

The YAML block lives between the first `---` and second `---` delimiters at the top of the file. Unlike body tables, you can't just grep for text that happens to be unique — the YAML keys (`value`, `name`) are generic. Use **surrounding YAML context** for a unique match:

```bash
# BEFORE (stale — 4/5 instead of 5/5)
#     metrics:
#     - type: accuracy
#       value: 0.8
#       name: Tool-Calling Score (4/5)

# Fix both value and name in one edit
sed -i '/^    metrics:/,/^      verified:/s/value: 0.8/value: 1.0/' /tmp/card.md
sed -i '/^    metrics:/,/^      verified:/s/Score (4\/5)/Score (5\/5)/' /tmp/card.md
```

**Verification after fix:**
```bash
grep "value: 0.8" /tmp/card.md && echo "STILL STALE" || echo "✅ value fixed"
grep "Score (4/5)" /tmp/card.md && echo "STILL STALE" || echo "✅ name fixed"
grep "value: 1.0" /tmp/card.md && echo "✅ correct value"
grep "Score (5/5)" /tmp/card.md && echo "✅ correct name"
```

**Important:** After fixing the YAML, also fix any body tables that show the stale score — two independent fixes in the same card. The `sed -i` commands above only touch the YAML frontmatter.

## Detection Procedure

### Step 1: Establish the Authoritative Source

The README (`/opt/data/Sak-Family-Agent/README.md`) is the single source of truth for benchmark scores:
- **1.5B tool-calling**: 5/5 🏆 (requires `<tools>` block in prompt)
- **0.5B tool-calling**: 1/5 (base model limitation)
- **Coder**: 5/5 🏆

Any model card score that deviates from these is stale or preliminary.

### Step 2: Scan Every Benchmark Section

Download each model card's README from HF and grep for ALL benchmark-related tables:

```bash
curl -s "https://huggingface.co/Nanthasit/<model-name>/raw/main/README.md" \
  | grep -n -E '(Benchmark|5/5|4/5|3/5|pending|Score|Coding)'
```

Look for these patterns:
- A "Benchmark Results" table and a "Benchmark Comparison" table on the same card — **overlap detector**
- Any score labeled "*pending*" when verified scores exist in the README
- The same model listed with different scores in different tables

### Step 3: Classify Discrepancies

| Discrepancy Type | Example | Fix |
|-----------------|---------|-----|
| Card table says "pending" but README has verified score | 1.5B=*pending* in Comparison table | Replace with verified score |
| Card table has different number than README | 1.5B=4/5 in Results table vs README=5/5 | Update to README's number |
| Two card sections contradict each other | Results table says 4/5, Comparison says pending | Update BOTH sections in one pass |
| Card lists the wrong model's score | 0.5B=3/5 (base Qwen is 2/5, fine-tune is 1/5) | Correct to verified 1/5 |

## Fix Procedure

### Step 1: Download the Full Card

```bash
curl -s "https://huggingface.co/Nanthasit/<model-name>/raw/main/README.md" \
  -o /tmp/card-readme.md
```

### Step 2: Edit in Python (all changes at once)

Apply all substitutions in a single pass to avoid partial-update drift:

```python
with open('/tmp/card-readme.md', 'r') as f:
    content = f.read()

# Fix 1: Benchmark Results table
content = content.replace(
    "| BFCL Tool-Calling (1.5B) | 4/5 |",
    "| BFCL Tool-Calling (1.5B) | 5/5 🏆 |"
)
content = content.replace(
    "| BFCL Tool-Calling (0.5B) | 3/5 |",
    "| BFCL Tool-Calling (0.5B) | 1/5 |"
)

# Fix 2: Comparison table
content = content.replace(
    "| **SakThai 1.5B (ours)** | — | — | *pending* ⭐ |",
    "| **SakThai 1.5B (ours)** | — | — | **5/5** 🏆 |"
)
content = content.replace(
    "| **SakThai 0.5B (ours)** | — | — | *Pending — see note* ⭐ |",
    "| **SakThai 0.5B (ours)** | — | — | **1/5** |"
)

# Fix 3: Key finding note — update to explain scores
content = content.replace(
    "**Key finding:** SakThai models excel at **tool-calling** — the area most 1-3B models struggle with.",
    "**Key finding:** SakThai 1.5B achieves **5/5 on BFCL tool-calling** when given the `<tools>` prompt block — surpassing all similarly-sized models. The 0.5B variant (1/5) is best suited for direct Q&A."
)

with open('/tmp/card-readme.md', 'w') as f:
    f.write(content)
```

### Step 3: Upload via HF API

```python
from huggingface_hub import HfApi

with open('/tmp/card-readme.md', 'r') as f:
    content = f.read()

api = HfApi()
api.upload_file(
    repo_id="Nanthasit/<model-name>",
    path_in_repo="README.md",
    path_or_fileobj=content.encode(),
    repo_type="model",
    commit_message="fix: align benchmark scores with verified results (1.5B=5/5 🏆, 0.5B=1/5)"
)
```

### Step 4: Verify Live Readback

```bash
# Fetch the uploaded card and check every changed section
curl -s "https://huggingface.co/Nanthasit/<model-name>/raw/main/README.md" \
  | grep -E '5/5|1/5|Key finding|BFCL'
```

Expected output:
- `| BFCL Tool-Calling (1.5B) | 5/5 🏆 |`
- `| BFCL Tool-Calling (0.5B) | 1/5 |`
- `| **SakThai 1.5B (ours)** | — | — | **5/5** 🏆 |`
- `| **SakThai 0.5B (ours)** | — | — | **1/5** |`
- Key finding mentioning `<tools>` block and 5/5

## Root Cause Analysis

**Why duplicate benchmark sections exist:** The 0.5B-merged card was apparently created by composing content from multiple earlier templates:
1. A template with a "Benchmark Results" table (showing preliminary 4/5 / 3/5 scores)
2. A template with a "Benchmark Comparison" table (showing "pending" — written before benchmarks were run)
3. A hand-edited "Verified Results" section (showing the correct 1/5 for 0.5B)

These three sources were never reconciled into a single consistent narrative.

**Why this goes unnoticed:** Each edit targets one section. No single agent or cron cycle re-reads the entire card and cross-checks all benchmark numbers against the authoritative README until a dedicated audit like this one.

## Prevention

1. **Consolidate benchmark sections** — If a card has both a "Benchmark Results" table and a "Benchmark Comparison vs Similar-Sized Models" table, the scores overlap. Consider removing one or clearly scoping each (e.g., "Results" = our models only, "Comparison" = our models vs competitors — but even then, the "our models" columns duplicate "Results").

2. **Centralize benchmark data** — Store verified benchmark scores in one place (the README or a `benchmarks.json` reference file) and cite it from all cards. When benchmarks change, update the central source and regenerate cards from it.

3. **Cross-reference during audits** — Every narrative consistency audit should include a "benchmark cross-reference" step: for each card with benchmark data, verify every claimed score matches the README. Flag any that don't.
