# Deleted Repo Cleanup Sweep

Documented 2026-07-29 — pattern for systematically purging references to deleted repos from all ecosystem cards after mass cleanup.

## The Problem

When experimental or snapshot repos are deleted from HF (e.g., v2 variants, masked-loss experiments), every ecosystem card that referenced them retains dead links. Unlike individual broken links (which can be fixed one at a time), mass deletion creates a **cascade effect** — one cleanup action breaks N cards simultaneously.

**Example (2026-07-29):** 8 repos were deleted (3 v2 + 5 experimental). Their links remained on **7 cards** with cumulative 1,195 downloads. Every visitor clicking those links got a 404.

## Detection: Find ALL Cards Referencing Deleted Repos

### Step 1: Determine which repos are gone

```bash
# Check a set of known-deleted repos
for repo in "Nanthasit/sakthai-context-0.5b-tools-v2" "Nanthasit/sakthai-context-1.5b-tools-v2"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/models/$repo")
  echo "$code - $repo"
done
# ⚠️ Deleted repos return 401, NOT 404.
# Without auth token: 200=public, 401=deleted OR private (ambiguous)
# With auth token (-H "Authorization: Bearer $HF_TOKEN"): 200=exists (public/private), 401=definitely deleted
# Always re-check suspicious 401s with the authenticated request before concluding deletion.
```

### Step 2: Grep every ecosystem card for references

```bash
# All public models with READMEs
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
  count=$(curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" \
    | grep -c "tools-v2\|merged-v2\|exp-")
  [ "$count" -gt 0 ] && echo "$model: $count refs to deleted repos"
done

# Also check datasets
for ds in \
  sakthai-combined-v6 \
  sakthai-irrelevance-supplement \
  sakthai-combined-v7 \
  sakthai-bench-v1 \
  sakthai-bench-v2; do
  count=$(curl -s "https://huggingface.co/datasets/Nanthasit/$ds/raw/main/README.md" \
    | grep -c "tools-v2\|merged-v2\|exp-")
  [ "$count" -gt 0 ] && echo "dataset/$ds: $count refs to deleted repos"
done
```

### Step 3: Prioritize by traffic

Sort affected cards by download count. Fix highest-traffic first:

| Priority | Card | Downloads | Impact |
|:--------:|------|:---------:|:------:|
| 1 | context-7b-128k | 382 | Most visitors hit dead links |
| 2 | context-7b-tools | 219 | Second highest |
| 3 | embedding-multilingual | 188 | Third highest |
| ... | (descending) | ... | ... |

## Fix: Remove Rows, Update Counts, Add Note

### Per-card changes needed

For each affected card:

1. **Remove dead rows** from the family table — delete the entire `| [dead-repo](...) | 0 🌱 | ... |` line
2. **Update ecosystem count** — `"18 models"` → `"12 models"` (subtract deleted count)
3. **Remove dead entries** from the "Growing the ecosystem" or equivalent section
4. **Add cleanup note** — brief documentation of what was removed and why

### Template: Cleanup note

Insert after the Growing the Ecosystem table:

```markdown
> **Note:** N experimental/snapshot repos (v2 variants and masked-loss experiments) were cleaned up. Only the M active production models remain in the family.
```

### Template: Fixed family table

Before cleanup, the table might have 20 rows (12 real + 8 deleted). After:
- Keep only rows whose repos return HTTP 200
- Verify each remaining link: `curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/models/Nanthasit/$name"`

### Template: Updated ecosystem count line

```markdown
This model is part of the **SakThai Model Family** — X models, Y datasets, and Z Spaces built by a single AI agent team.
```

Where X = count of models with pipeline_tag that actually exist on HF. Fetch:

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit" \
  -o /tmp/current_models.json && \
python3 -c "
import json
with open('/tmp/current_models.json') as f:
    models = json.load(f)
real = [m for m in models if m.get('pipeline_tag') and m['id'] != 'Nanthasit/Nanthasit']
print(f'{len(real)} real models with pipeline tags')
"
```

## Commit Pattern

```bash
cd /tmp/repo && \
git add README.md && \
git commit -m "Fix: Remove dead links to N deleted repos, correct model count X->Y" && \
git push
```

## Verification

After pushing each card:

```bash
# Confirm no dead references
curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" \
  | grep -c "tools-v2\|merged-v2\|exp-"
# Expected: 0

# Confirm count matches API
curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" \
  | grep "models" | head -1
# Expected: "X models · Y datasets · Z Spaces" where X == API count
```

## Prevention: Pre-Publish Verification

To prevent this problem from recurring:

**Rule:** Before publishing any card that references a repo by name, verify the target exists:

```bash
check_repo() {
  local repo=$1
  local type=${2:-model}
  local base_url="https://huggingface.co/api"
  [ "$type" = "model" ] && url="$base_url/models/$repo" || url="$base_url/${type}s/$repo"
  local code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HF_TOKEN" "$url")
  if [ "$code" = "401" ] || [ "$code" = "404" ]; then
    echo "❌ $repo ($code — DOES NOT EXIST)"
    return 1
  elif [ "$code" = "200" ]; then
    echo "✅ $repo (exists)"
    return 0
  else
    echo "⚠️ $repo (unexpected HTTP $code)"
    return 2
  fi
}

# Check every row in the family table before upload (WITH auth token so 401=deleted, not ambiguous)
check_repo "Nanthasit/sakthai-context-1.5b-merged"
check_repo "Nanthasit/sakthai-context-0.5b-merged"
# ... all rows ...
```

If any row returns 401 or 404 (with auth token), do NOT publish the card until the row is removed or corrected. See `verification-patterns.md` for the bidirectional absence+presence check pattern.

## Relation to Other References

- `cross-link-validity-check.md` — detects broken links one-at-a-time; this covers mass deletion cascades
- `card-enrichment-patterns.md` — covers adding sections; this covers removing them
- `target-selection-strategies.md` — picks which card to improve; this picks which card to FIX based on broken-link density
