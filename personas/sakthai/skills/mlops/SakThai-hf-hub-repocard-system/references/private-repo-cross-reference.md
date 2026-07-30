# Private Repo Cross-Reference Detection

**Systematic workflow for detecting private repos linked from public model cards.**

Unlike the per-URL HEAD-check approach (which requires iterating every URL in a card), this cross-reference method detects private repos by comparing the full API model listing against the family tables in a card. A model referenced in a card's table that *doesn't appear* in the public API listing is likely private — no need to guess or probe every URL.

## Why This Matters

A private repo linked from a public card returns HTTP 401 for unauthenticated visitors. To a user browsing the card, the link appears broken or gatekept. This creates:

- **Dead-end navigation** — visitor clicks, lands on a 401 page, leaves
- **Trust erosion** — broken links signal poor maintenance
- **Missed discovery** — the visitor was interested but hit a wall

The SakThai ecosystem had exactly this problem: `sakthai-embedding` (private, 34 dl) was linked from the public `sakthai-context-0.5b-tools` (7 dl) card's Family Links table.

## Detection Workflow

### Step 1: Fetch the complete public model listing

Save to a file to avoid pipe-to-interpreter blocks in cron mode:

```bash
curl -s -o /tmp/author_models.json "https://huggingface.co/api/models?author=Nanthasit"
```

Parse the listing to get a set of public model IDs and their download counts:

```bash
python3 -c "
import json
data = json.load(open('/tmp/author_models.json'))
for m in sorted(data, key=lambda x: x.get('downloads',0)):
    print(f\"{m['id'].split('/')[1]}: {m.get('downloads',0)} dl\")
"
```

### Step 2: Download the target card and extract model references

```bash
curl -s -o /tmp/card.md "https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools/raw/main/README.md"
```

Look for model IDs in family tables, related assets sections, and cross-promotion sections. Common patterns:
- Markdown links: `[model-name](https://huggingface.co/org/model-name)`
- Table rows: `| sakthai-embedding | feature-extraction | 34 ⬇ |`
- Inline links: `[sakthai-embedding](https://huggingface.co/Nanthasit/sakthai-embedding)`

### Step 3: Cross-reference against the API listing

For each model ID found in the card, check if it exists in the public API listing:

```bash
# Quick check with grep
grep -c "model-id" /tmp/author_models.json || echo "NOT IN PUBLIC LISTING"
```

If a model doesn't appear in the public listing, it's either:
- **Private** (most common) — returns 401 for unauthenticated users
- **Deleted** — returns 404
- **Gated** — returns 403

### Step 4: Confirm with authenticated API call

The API listing approach can miss private repos. Confirm with an authenticated call:

```bash
# With token — should return full model info
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/Nanthasit/sakthai-embedding" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('Private:', d.get('private',False))"
```

Check:
- `private: true` → the repo exists but is invisible to public users
- `error` key with 401/404 → the repo doesn't exist or is inaccessible

### Step 5: Cross-check card tables

Once identified, check **every** card in the ecosystem that might reference the private model. The most common locations:

- **Family Links tables** — full model listing with download counts
- **Low-Download Gems** — cross-promotion sections
- **Related Assets** — dataset cards linking to sibling models
- **Pipeline Integration** — diagram or stage tables
- **Comparison tables** — model-to-model performance comparisons

## Fix Workflow

### Correction 1: Remove the dead link from the family table

Replace the clickable row with an explanatory note that redirects to the replacement:

**Before:**
```markdown
| [sakthai-embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | sentence-similarity | 34 ⬇ |
```

**After — Option A (note with redirect):**
```markdown
> ℹ️ **Note:** The legacy English-only `sakthai-embedding` model has been superseded by
> [sakthai-embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual)
> (188 ⬇, 50+ languages). The old model is private and kept for internal reference only.
```

**After — Option B (minimal):**
```markdown
| ~~sakthai-embedding~~ | sentence-similarity | _(private, superseded)_ |
```

### Correction 2: Clean up cross-promotion sections

Remove the private model from any "Low-Download Gems" or "Rising Stars" sections. These sections are meant to promote *accessible* assets:

**Before:**
```markdown
| [sakthai-embedding](https://...) | 34 ⬇ | English sentence embeddings |
| [sakthai-tts-model](https://...) | 69 ⬇ | 15-language TTS |
```

**After:**
```markdown
| [sakthai-tts-model](https://...) | 69 ⬇ | 15-language TTS |
| [sakthai-coder-1.5b](https://...) | 70 ⬇ | Code generation |
```

### Correction 3: Update sibling cards

Other model/dataset cards may also link to the private model. For each card that references it:
1. Download the card
2. Fix the reference (remove or replace)
3. Push the fix
4. Verify

Limit to **one sibling per cron cycle** to stay within scope.

## Verification

After fixing, verify with curl + grep:

```bash
# Download the live card
curl -s -o /tmp/verified.md \
  "https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools/raw/main/README.md"

# Check that the dead link is gone — should find 0 clickable references
grep -c "sakthai-embedding" /tmp/verified.md && echo "References exist"
# Acceptable: only in explanatory note, not as a navigable link

# Check the Low-Download Gems section is clean
grep -A 6 "Low-Download Gems" /tmp/verified.md | grep -c "sakthai-embedding" \
  || echo "✅ Private model not in gems section"
```

## Pitfalls

### API model listing may not include all repos
The `?author=username` endpoint returns public repos only. Private repos are invisible in this listing. If you suspect a private repo exists but don't have the token, you cannot confirm — the gap in the listing is the only signal. Fix based on the gap alone if the URL structure clearly points to a repo that doesn't appear.

### The model may be gated, not private
Gated repos (e.g., Meta's Llama models) return a gated-access page, not 401. These are still accessible (users can request access), so they're less problematic than private repos. Don't remove gated model links — add an "Access Required" hint instead.

### Family tables often reference the same model twice
Model cards frequently list sibling models both in the main family table AND in a "Low-Download Gems" section. When fixing, check BOTH locations. Removing from one but not the other leaves a stale reference.

### The explanatory note can itself become stale
If the private model is later made public or deleted permanently, the note becomes outdated. Consider adding a date: "as of July 2026, the legacy model is private."

## Real-World Example

The `sakthai-context-0.5b-tools` card (7 dl) linked to `sakthai-embedding` (private, 34 dl) in two places:

| Location | Before | After |
|----------|--------|-------|
| Family table | Clickable row with download count | Note pointing to multilingual replacement |
| Low-Download Gems | Listed as "English sentence embeddings" | Removed entirely |

**Detection method:** The private model appeared in the card's family table (`sakthai-embedding | feature-extraction | 34 ⬇`) but was absent from the `https://huggingface.co/api/models?author=Nanthasit` public listing. An authenticated API call confirmed `private: true`.

**Commit:** `https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools/commit/a934e30`
