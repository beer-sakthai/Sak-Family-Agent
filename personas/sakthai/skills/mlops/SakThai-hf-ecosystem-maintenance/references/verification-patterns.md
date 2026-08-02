# Verification Patterns for HF Ecosystem Maintenance

Documented 2026-07-29 — lessons from a false-completion claiming 12/12 cards enriched when 3 were still missing.

## The Trap: Trusting Journal Entries Over Live State

The enrichment cycle declared "All 12 functional model cards now have Support the Project CTA" in LEARNING_JOURNAL.md. Grep-verifying the actual HF READMEs revealed that **3 cards** (1.5B-tools, 7B-tools, 7B-128K) had 0 matches for "Support the Project" — they never received the section.

**Root cause:** The journal tracked which cards were *supposed* to be fixed but the Jira-board-style tracking never closed the loop on the last 3 tool-adapter cards. They remained in "remaining gaps" lists perpetually.

**Rule:** After every enrichment cycle, grep-verify against **live HF READMEs**, not journal entries.

## Batch Parallel Verification

Before declaring a section "done on all cards", run parallel greps on every model:

```bash
# Check all 12 functional cards in parallel
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
  count=$(curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" | grep -c "Support the Project")
  echo "$model: $count"
done
```

Any card with 0 matches still needs the section.

## Standard Checks Before Closing a Cycle

| Check | Grep Pattern | Expected |
|-------|-------------|----------|
| Support the Project CTA | `grep -c "Support the Project"` | ≥1 per card |
| irrelevance-supplement YAML ref | `grep -c "irrelevance-supplement"` | ≥1 per card (or YAML check) |
| No deprecated stigma | `grep -ci "deprecated"` | 0 on embedding cards |
| No dead private links | `grep -c "sakthai-embedding)"` | 0 (use "sakthai-embedding)" with paren) |
| Card grew (vs previous) | `wc -c` | size increased |
| Collection UUID consistency | `grep -oP 'sakthai-model-family-[a-f0-9]{24}' \| sort -u` | exactly 1 unique UUID across all cards |
| YAML datasets count = 6 | API `cardData.datasets` `len()` | 6 datasets per model card |

## Collection UUID Consistency Check

Collection links can go stale if the collection was recreated (UUID changes). A single card with a different UUID than all siblings is the likely broken one.

### Detection: Extract UUIDs from all ecosystem cards

```bash
# Download all ecosystem READMEs and extract collection UUIDs
UUID_PATTERN='sakthai-model-family-[a-f0-9]{24}'
for repo in \
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
  uuid=$(curl -s "https://huggingface.co/Nanthasit/$repo/raw/main/README.md" \
    | grep -oP "$UUID_PATTERN" | head -1)
  echo "$repo: $uuid"
done

# Also check datasets and profile
for repo in \
  sakthai-combined-v6 \
  sakthai-kaggle-notebooks \
  food-penguin-v1 \
  sakthai-irrelevance-supplement; do
  uuid=$(curl -s "https://huggingface.co/datasets/Nanthasit/$repo/raw/main/README.md" \
    | grep -oP "$UUID_PATTERN" | head -1)
  echo "dataset/$repo: $uuid"
done
```

### Analysis

1. **Collect all UUIDs** from the output above
2. **Find the mode** (most common UUID) — that's the correct collection
3. **Flag outliers** — any card with a different UUID is likely broken
4. **Verify each UUID** by hitting the HF API:
   ```bash
   curl -s "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-$UUID" \
     | python3 -c "import json,sys; d=json.load(sys.stdin); print('VALID' if 'title' in d else 'BROKEN: '+d.get('error','?'))"
   ```

### Fix

Replace the broken UUID with the correct one across the card. Use `huggingface_hub` Python API:

```python
from huggingface_hub import HfApi, hf_hub_download
api = HfApi()
path = hf_hub_download(repo_id='Nanthasit/<repo>', filename='README.md', repo_type='dataset')
with open(path) as f:
    content = f.read()
content = content.replace('broken-uuid-here', 'correct-uuid-here')
api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/<repo>',
    repo_type='dataset',
)
```

### Verify

Re-run the detection script above and confirm all cards report the same UUID:

```bash
# Cross-check all ecosystem cards reference the SAME collection UUID
# The mode (most common UUID) must be the only UUID present
unique_uuids=$(for repo in ...; do curl -s ... | grep -oP "$UUID_PATTERN"; done | sort -u)
echo "Unique UUIDs in ecosystem: $unique_uuids"
# Expected: 1 unique UUID. If >1, something is broken.
```

### Root cause

Collection UUIDs change when the owner recreates the collection (e.g., to rename or reorder). Cards that were forked from templates using the old UUID or created before the recreation retain the stale link. Always use the slug returned by `get_collection().slug` as the canonical reference.

## Git Push Verification: Clone Fresh, Don't Trust the Raw Endpoint

**Critical lesson from Cron #033 (2026-07-29):** A `git push` that reports success (`1 file changed, 117 insertions(+), 33 deletions(-)`) can silently land the WRONG content. The first attempt to enrich the v7 model card replaced enriched content with a minimal stub because `cp` copied a stale source file. The commit message and diff count looked correct; only a fresh clone revealed the truth.

### The Trap: Trusting the Raw Endpoint

The raw `raw/main/README.md` endpoint can return **cached**, **stale**, or **server-rendered** content that does not match what `git clone` produces. A grep against the raw endpoint may show the intended content even when the actual pushed content is wrong (if the cache hasn't invalidated yet) — or may show old content when the push actually succeeded (stale cache).

**Rule:** After any git push to a Hugging Face repo, verify by cloning FRESH, not by grepping the raw endpoint.

### The Verification Workflow

After every model card push, run this sequence:

```bash
# 1. Clone to a fresh temp directory
git clone https://user:$HF_TOKEN@huggingface.co/<author>/<repo> /tmp/verify-<repo>
cd /tmp/verify-<repo>

# 2. Check basic metrics
head -5 README.md      # Does the YAML frontmatter start correctly?
wc -l README.md        # Is the card the expected length?

# 3. Check for CONTENT markers not STRUCTURE markers
grep -c "pipeline_tag: text-generation" README.md  # Expected: 1
grep -c "SakThai Model Family" README.md            # Expected: ≥1

# 4. Negative check: ensure old/bad content is GONE
grep -c "tools-v2\|merged-v2" README.md             # Expected: 0

# 5. Clean up
rm -rf /tmp/verify-<repo>
```

### Real Example: Cron #033 Failure

**What happened:**
1. Intended to push enriched card (143 lines, `pipeline_tag: text-generation`, family tables)
2. `cp /path/to/new_readme.md README.md` silently copied old content instead of new
3. `git push` reported success with plausible diff stats
4. Fresh clone confirmed: 58 lines, `base_model:` frontmatter — NOT the intended card

**Root cause:** The `cp` source file was silently wrong — write_file had written to a different resolved path. No shell error was raised.

**Corrective push:** `b923775` after verifying source file with `head -5` + `wc -l`, then clone-verified showing 143 lines + correct frontmatter + family tables.

### Verification Protocol for Git Pushes

| Step | Command | What It Guards Against |
|------|---------|----------------------|
| Pre-push: verify source file | `head -5 <file>` + `wc -l <file>` | Wrong file being staged |
| Pre-push: verify content markers | `grep -c "unique-keyword" <file>` | Stale/template content |
| Post-push: clone fresh | `git clone ... /tmp/verify-<repo>` | Wrong content landed |
| Post-push: check frontmatter | `head -5 README.md` | YAML structure wrong |
| Post-push: check key sections | `grep -c` for 2-3 unique markers | Content didn't land |
| Post-push: negative check | `grep -c` for old content markers | Bad content persisted |

**Policy:** For any ecosystem maintenance commit that modifies a model/dataset/Space card, the final verification MUST include a fresh clone. Grepping the raw endpoint is a useful intermediate check but does NOT replace a clone.

## What to Do When a Card Fails Verification

Stop. Do not update the journal. Fix the card first:

1. Fetch the live README: `curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md"`
2. Add the missing section (YAML reference, CTA block, etc.)
3. Upload: `hf upload Nanthasit/$model /tmp/fixed.md README.md --commit-message "docs: add missing section"`
4. Re-verify with the same grep
5. **Then** record in the journal

## Bidirectional Verification (Absence + Presence)

A common verification trap: confirming that NEW content was added (positive check) but forgetting to confirm that OLD/BAD content was removed (negative check). This leaves dead refs, stale counts, or broken links silently in place.

### The Pattern

After any edit that removes AND adds content, verify BOTH:

```bash
# NEGATIVE check: old/bad content is ABSENT
grep -c "tools-v2\\|merged-v2\\|exp-"
# Expected: 0 (no dead repo references remain)

# POSITIVE check: new/good content is PRESENT
grep -c "bench-v1\\|bench-v2\\|exp-lora-masked-v4"
# Expected: ≥1 (new entries actually landed)
```

### Why single-direction fails

| Check Only | Leak | Example |
|-----------|------|---------|
| Positive only | Old bad content persists alongside new | Card still links to deleted v2 repo but also has v4 experiment — 404 still there |
| Negative only | New content never got added | Card cleaned dead refs but didn't add the v4 experiment |
| Neither | No idea if upload worked | Assuming it did without checking |

### Real example (2026-07-29, Cron #029)

After cleaning dead v2 refs from `context-7b-tools`:

```bash
# Negative: confirm dead refs GONE
curl -s "https://huggingface.co/Nanthasit/sakthai-context-7b-tools/raw/main/README.md" \
  | grep -c "tools-v2"
# → 0 ✅

# Positive: confirm new additions LANDED
curl -s "https://huggingface.co/Nanthasit/sakthai-context-7b-tools/raw/main/README.md" \
  | grep -c "bench-v1"
# → ≥1 ✅
```

### Checklist integration

The standard checks table should include BOTH directions for compound edits:

| Check | Direction | Grep Pattern | Expected |
|-------|-----------|-------------|----------|
| No dead v2 refs | Negative | `tools-v2\|merged-v2` | 0 |
| v4 experiment added | Positive | `exp-lora-masked-v4` | ≥1 |
| bench-v1/v2 datasets | Positive | `bench-v1\|bench-v2` | ≥1 |
| Ecosystem count correct | Positive | `grep -oP '\d+ models'` | matches API |
