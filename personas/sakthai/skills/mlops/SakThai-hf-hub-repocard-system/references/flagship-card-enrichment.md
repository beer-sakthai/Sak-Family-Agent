# Flagship Card Enrichment — Cross-Promoting Zero-Download Assets from High-Traffic Cards

**Pattern:** Use the highest-download model card in the family as a launchpad for promoting zero-download and low-download assets. This is the reverse of `model-card-cross-promotion.md` (which enriches low-download cards themselves).

## Rationale

The flagship card gets the most visitors (download events = proxy for page views). Every visitor landing on the flagship card is a potential discoverer of every other asset. Adding cross-links to underperforming siblings from this card costs nothing but has the highest marginal discoverability of any single-card edit.

| Metric | Value |
|--------|-------|
| Flagship downloads | 1,269 (6× the next card) |
| Zero-download assets reached | 0.5b-tools-v2 (0 dl), combined-v7 (0 dl), irrelevance-supplement (0 dl) |
| Visitors exposed per edit | All 1,269+ future downloaders |

## When to Use

- A new model or dataset was just published with 0 downloads and no README
- Two+ assets have remained at 0 downloads for >24 hours after their README was created
- You're running a one-improvement-per-cycle cron and need the highest-leverage single edit
- The flagship card's family table or "Low-download gems" section hasn't been updated since the last new asset was added

## What to Update (in priority order)

### 1. YAML `datasets:` field

Add any new datasets to the YAML frontmatter so they appear in HF's dataset relationship graph and search:

```yaml
datasets:
- Nanthasit/sakthai-combined-v6
- Nanthasit/sakthai-combined-v7          # ← new
- Nanthasit/sakthai-irrelevance-supplement
```

### 2. Model family table

Add the new model as a dedicated row. If existing rows are grouped (e.g., `context-{7b,1.5b,0.5b}-tools`), split them into individual rows first — grouped rows hide low-download variants.

**Before (grouped):**
```
| [context-{7b,1.5b,0.5b}-tools](...) | LoRA | Tool-calling adapters |
```

**After (individual rows + v2 added):**
```
| [context-7b-tools](...) | 269 MB | Heavy tool-use, multi-step |
| [context-1.5b-tools](...) | 54 MB | Efficient tool-use |
| [context-0.5b-tools-v2](...) | 18 MB | 🆕 Refined edge tool-calling, 0 downloads |
| [context-0.5b-tools](...) | 18 MB | Edge tool-calling, 7 downloads |
```

### 3. Count line

Update the "N models · M datasets · K Spaces" summary to reflect the actual current counts:

```
**12 models · 5 datasets · 3 Spaces**  →  **13 models · 6 datasets · 3 Spaces**
```

This line is often the most stale element on the card because it requires knowing the entire ecosystem count, not just one model's data.

### 4. Low-download gems section

Add new zero-download assets to the gems table. Place them at the TOP of the table (not the bottom) so they're seen first by skimmers:

```
| [context-0.5b-tools-v2 (LoRA)](...) | 0 | 🆕 Refined edge LoRA, improved recipe |
| [combined-v7 (dataset)](...) | 0 | 🆕 v7 tool-calling data, 2,003 examples |
| [context-0.5b-tools (LoRA)](...) | 7 | Raspberry Pi, edge tool-calling |
| ...
```

Use the 🆕 emoji for anything that was just added — it signals freshness and invites exploration.

## Workflow (Cron-Safe)

```bash
# 1. Read current card (for context before editing)
curl -s "https://huggingface.co/{org}/{flagship-repo}/raw/main/README.md" | head -60

# 2. Clone the repo (shallow, with token)
TOKEN=$(cat ~/.cache/huggingface/token)
git clone --depth 1 "https://{user}:${TOKEN}@huggingface.co/{org}/{flagship-repo}" /tmp/repo
cd /tmp/repo

# 3. Apply edits with sed
sed -i '/- Nanthasit\/sakthai-combined-v6/a\- Nanthasit/sakthai-combined-v7' README.md
sed -i 's/| grouped-tools-row |/| individual rows... |/' README.md
sed -i 's/12 models · 5 datasets/13 models · 6 datasets/' README.md
# Add gems rows after the irrelevance-supplement line
sed -i '/irrelevance-supplement (dataset)/i| [new-asset](...) | 0 | 🆕 Description |' README.md

# 4. Commit and push
git config user.email "bot@sakthai.dev"
git config user.name "SakThai Agent"
git add README.md
git commit -m "docs: cross-link {asset-name} from flagship card"
git push origin main
# ^ If push fails with auth error, see git-based-readme-patching.md § Auth Recovery

# 5. Verify (6+ checks)
python3 << 'VERIFY'
import urllib.request
url = "https://huggingface.co/{org}/{flagship-repo}/raw/main/README.md"
req = urllib.request.Request(url, headers={"User-Agent": "Verification/1.0"})
content = urllib.request.urlopen(req).read().decode()
checks = {
    "new-dataset in YAML": "sakthai-combined-v7" in content.split("---")[1],
    "new-model in family table": "context-0.5b-tools-v2" in content,
    "counts updated": "13 models" in content and "6 datasets" in content,
    "new-model in gems": "context-0.5b-tools-v2" in content[content.find("Low-download"):],
    "new-dataset in gems": "combined-v7 (dataset)" in content[content.find("Low-download"):],
}
for name, result in checks.items():
    print(f'  [{"PASS" if result else "FAIL"}] {name}')
VERIFY

# 6. Clean up
cd /opt/data && rm -rf /tmp/repo
```

## Pitfalls

- **Stale token in clone URL:** The token embedded in the clone at step 2 may be sanitized by git display. If `git push` fails with "Invalid username or password", re-set the remote: `git remote set-url origin "https://user:$(cat ~/.cache/huggingface/token)@huggingface.co/{org}/{repo}" && git push`. See `git-based-readme-patching.md` § Auth Recovery.

- **Grouped rows obscure low-download variants:** A single row for `context-{7b,1.5b,0.5b}-tools` hides the 0-download v2 adapter. Always split grouped rows into individual entries so each variant gets its own discoverability.

- **Count line drift:** The "N models · M datasets" line is easy to forget because it's not in a table — it's standalone paragraph text. Set a higher bar for staleness avoidance: keep a mental checklist of (model_count, dataset_count, space_count) before every flagship edit.

- **sed pipe-delimiter collision:** When editing markdown tables with `sed`, the `|` pipe character is both the table column separator and the sed delimiter. Use `@` or `#` as the sed delimiter to avoid collision: `sed -i 's@old-text@new-text@'` instead of `s|old|new|`.

- **Refresh the Low-download gems sort order:** New additions go to the TOP of the table. If you append to the bottom, skimmers may miss them (table rows below the fold get fewer reads). Re-sort the entire table when adding multiple assets.

## Relationship to Other References

| Reference | Relationship |
|-----------|-------------|
| `model-card-cross-promotion.md` | Reverse direction: enriching low-download cards as navigation hubs |
| `git-based-readme-patching.md` | Git workflow details, sed patterns, auth recovery |
| `hf-ecosystem-cron-maintenance.md` | Broader cron toolkit this fits into |
| `card-quality-assessment.md` | How to pick WHICH card to improve next |
