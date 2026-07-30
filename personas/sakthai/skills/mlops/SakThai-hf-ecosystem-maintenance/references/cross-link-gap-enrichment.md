# Cross-Link Gap Enrichment

Documented 2026-07-29 — adding a missing sibling link to an otherwise well-documented card.

## When to Use This Pattern

The target card already has a full README (family table, usage examples, benchmarks, low-download gems section — the works) but is missing a cross-link to one specific sibling model. This is distinct from full card enrichment (card is thin and needs sections) and from sibling-driven enrichment (card doesn't exist yet).

**Signal:** `grep -c "sibling-name" README.md` returns 0 on a card that otherwise has 8K+ bytes and all standard sections.

## Workflow

### 1. Detect the Gap

```bash
# Fetch current model list from HF API
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1" \
  -o /tmp/hf_models.json

# Process with inline python
python3 << 'PYEOF'
import json
with open('/tmp/hf_models.json') as f:
    models = json.load(f)

# Find models under 50 downloads that are "real" (not profile, not experimental)
low_targets = [m for m in models 
    if m.get('downloads', 0) < 50 
    and '/' in m['modelId']  # has repo name
    and 'exp-' not in m['modelId']  # not experimental
    and 'Nanthasit/' not in m['modelId'][m['modelId'].rfind('/')+1:] == 'Nanthasit']  # not profile

for t in low_targets:
    mid = t['modelId'].split('/')[1]
    print(f"  {mid:40s} {t.get('downloads',0):>4d} dl  created: {t.get('createdAt','?')[:10]}")
PYEOF
```

**Selection criteria (priority order):**
1. 0 downloads (urgent visibility gap)
2. Under 50 downloads, created >7 days ago (stale gap)
3. Under 50 downloads, sibling card has >1K downloads (high-traffic gap)

### 2. Check Which Sibling Cards Are Missing the Link

```bash
TARGET="sakthai-embedding"
for model in \
  sakthai-context-1.5b-merged \
  sakthai-context-0.5b-merged \
  sakthai-context-7b-merged \
  sakthai-context-7b-128k \
  sakthai-context-7b-tools \
  sakthai-context-1.5b-tools \
  sakthai-embedding-multilingual \
  sakthai-context-0.5b-tools \
  sakthai-coder-1.5b \
  sakthai-vision-7b \
  sakthai-tts-model; do
  count=$(curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" | grep -c "$TARGET")
  echo "$model: $count"
done | grep ": 0$"
```

### 3. Patch the Missing Card

Two places to add the cross-link:

**A. Family Table** — add a row for the missing sibling, sorted by downloads descending:

```markdown
| [embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | 80 MB | English-only search, 384d | 34 ⬇ |
```

Insert between the sibling with the next-higher and next-lower download counts.

**B. Low-Download Gems section** — if the card has a 🌱 section, add a row:

```markdown
| [embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | 34 🌱 | English-only search, 80 MB |
```

Insert in download-count ascending order (lowest first).

### 4. Upload

```bash
hf upload "Nanthasit/$target_repo" /local/path/README.md README.md \
  --commit-message "Add sakthai-embedding to family table and low-download gems" \
  --token "$HF_TOKEN"
```

Returns: `url=https://huggingface.co/Nanthasit/$target_repo/commit/<sha>`

### 5. Verify

```bash
curl -s "https://huggingface.co/Nanthasit/$target_repo/raw/main/README.md" | grep -c "$TARGET"
# Expected: ≥3 (family table + gems section + possibly existing mentions)
```

## Pitfalls

- **Don't add the same model to its own card.** The TARGET should be a *different* model from the card being edited.
- **Don't add experimental/placeholder models** (exp-*, v2 models with <100 bytes of card). Only add models with real content.
- **Don't add profile repos** (e.g., `Nanthasit/Nanthasit`). These aren't real models.
- **Update the download count in the table** to match the live API value. A cross-link with a stale count is worse than no cross-link.
- **Keep the low-download gems section compact** — 3–5 rows max. If the section already has 5 rows, consider replacing instead of adding.

## Real Example

| Date | Target Card | Missing Model | Gap | Pre | Post | Commit |
|:----:|-------------|---------------|-----|:---:|:----:|--------|
| 2026-07-29 | `sakthai-context-0.5b-tools` (7 dl) | `sakthai-embedding` (34 dl, 80 MB) | Not in family table, not in gems | 0 | 3 | `5dd831b` |
