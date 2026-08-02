# Reverse Promotion via Minor Card

Documented 2026-07-29 — promoting zero-download repos by adding cross-links
from the *least* popular model card, not the most popular one.

## When to Use This Pattern

**Standard cross-promotion** adds links from high-traffic cards to low-traffic
ones — drive eyeballs from where the visitors are. **Reverse promotion** does
the opposite: adds links from the lowest-download card to other low-download
repos.

| Aspect | Standard | Reverse (this) |
|--------|----------|----------------|
| Source card | Highest downloads | Lowest downloads |
| Target repos | Low-download models | Zero-download datasets or models |
| Rationale | Maximize reach | Visitors to the edge card are *evaluation-seekers* already looking for niche/lightweight assets — they're more likely to need benchmarks and training data |
| Risk | Visitors ignored the edge card entirely (they came for the flagship) | Visitors to the edge card self-select as edge-curious — showing them evaluation suites is a natural upsell |

### Signal

- The ecosystem has 3+ zero-download repos (datasets or models) that no card
  currently links to
- The lowest-download model card already has a polished main README (family
  table, usage examples, quick-start, badges) but its sibling references are
  stale — counts off, new datasets missing from tables
- Fixing the ecosystem count *and* adding dataset cross-links in one edit
  makes the card feel freshly maintained, signalling active development

## Workflow

### 1. Identify the Minor Card

The "minor card" is the one with the lowest download count among real models
(not profile repos, not experimental checkpoints):

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=1" \
  -o /tmp/hf_models_asc.json

python3 -c "
import json
with open('/tmp/hf_models_asc.json') as f:
    models = json.load(f)
# Skip profile repos and experimental models
real = [m for m in models
    if '/' in m.get('modelId','')
    and m.get('pipeline_tag') is not None
    and not m.get('private', False)]
for m in real[:5]:
    print(f'{m[\"modelId\"]:50s} {m.get(\"downloads\",0):>4d} dl  {m.get(\"pipeline_tag\",\"?\")}')
print(f'\nMinor card: {real[0][\"modelId\"]} ({real[0].get(\"downloads\",0)} dl)')
"
```

### 2. Check for Stale Ecosystem Counts

Before editing, check if the card's ecosystem summary is still accurate:

```bash
# Fetch the card
curl -s "https://huggingface.co/Nanthasit/<minor-card>/raw/main/README.md" \
  -o /tmp/card.md

# Check what the card claims
grep -oiP '\d+\s+(model|dataset|space)s?' /tmp/card.md

# Check actual counts
curl -s "https://huggingface.co/api/models?author=Nanthasit" -o /tmp/actual_models.json
curl -s "https://huggingface.co/api/datasets?author=Nanthasit" -o /tmp/actual_datasets.json
python3 -c "
import json
models = json.load(open('/tmp/actual_models.json'))
datasets = json.load(open('/tmp/actual_datasets.json'))
real_models = [m for m in models if m.get('pipeline_tag')]
print(f'Actual: {len(real_models)} models, {len(datasets)} datasets')
"
```

Common findings:
- Card says "12 models · 5 datasets · 3 Spaces" but actual is "11 models · 8 datasets · 3 Spaces"
- The model count mismatch is often because the private embedding model is counted in the footer but not in the collection
- The dataset count is stale because new datasets were created since the last card edit

### 3. Check Which Zero-Download Datasets Are Missing from the Card

```bash
for ds in combined-v7 irrelevance-supplement bench-v1 bench-v2; do
  count=$(grep -c "$ds" /tmp/card.md)
  echo "$ds: $count mentions"
done
```

### 4. Edit the Raw Content

Apply two changes:

**A. Fix the ecosystem footer count** — change the stale summary line at the
bottom of the card:

```python
# Read card, find the stale count line
# e.g., "**12 models · 5 datasets · 3 Spaces**" → "**11 models · 8 datasets · 3 Spaces**"
text = text.replace(old_count_line, new_count_line)
```

**B. Add dataset rows to the low-download gems / dataset cross-link table**

If the card has a Dataset table, add rows for the missing datasets:

```markdown
| [sakthai-combined-v7](...) | 0 🌱 | v7 tool-calling training, 2,309 examples, 81 tools |
| [sakthai-bench-v1](...) | 0 🌱 | BFCL-style evaluation, 235 rows |
| [sakthai-bench-v2](...) | 0 🌱 | Multi-domain eval, 500 rows, 5 categories |
```

Insert in download-count ascending order (lowest first).

If the card does NOT have a Dataset table, add one — it's a discoverability
gap. Use the sibling datasets template from `card-enrichment-patterns.md`.

### 5. Upload

```python
from huggingface_hub import HfApi
api = HfApi(token=os.environ['HF_TOKEN'])
api.upload_file(
    path_or_fileobj='/tmp/updated_readme.md',
    path_in_repo='README.md',
    repo_id='Nanthasit/<minor-card>',
    commit_message='Update ecosystem counts + add new dataset cross-links'
)
```

### 6. Verify

```bash
curl -s "https://huggingface.co/Nanthasit/<minor-card>/raw/main/README.md" -o /tmp/verified.md
grep -c "new count line" /tmp/verified.md   # expect 1
grep -c "new-dataset-name" /tmp/verified.md # expect >= 1
```

## Pitfalls

- **Don't promote non-real repos.** The `Nanthasit/sakthai-combined-v6` model
  repo (not the dataset — a separate model repo with no pipeline_tag) has 0
  downloads but isn't a real model. Skip it. Only add repos with actual
  content (pipeline_tag for models, data files for datasets).
- **Don't exceed the low-download gems table length.** 3–5 rows max. If the
  table already has 5 rows, replace the least relevant existing row instead
  of appending.
- **Update the download count in the table.** All added rows should show
  current download counts from the API, not zeros you assume. A combined-v7
  dataset might have been downloaded since you last checked.
- **Verify the upload.** The `upload_file` call returns silently even when the
  content hasn't changed. Always re-fetch and grep-count after upload.

## Real Example

| Date | Minor Card | Its Downloads | Added Datasets | Pre-existing | Post |
|:----:|------------|:-------------:|----------------|:------------:|:----:|
| 2026-07-29 | `sakthai-context-0.5b-tools` | 7 | combined-v7 (0 dl), bench-v1 (0 dl), bench-v2 (0 dl) | 3 datasets in table | 6 datasets in table |

**Before fix:** Footer said "12 models · 5 datasets · 3 Spaces"; actual
ecosystem had 11 models, 8 datasets. The three new datasets (combined-v7,
bench-v1, bench-v2) were not referenced anywhere in the card.

**After fix:** Footer says "11 models · 8 datasets · 3 Spaces"; all 6
datasets have rows in the cross-link table. The 7-download card now
functions as a navigation hub for the entire evaluation suite.

**Rationale for picking the 7-dl card:** Visitors to `0.5b-tools` are
edge/tinkerers — exactly the audience that would want benchmark data to
validate a tiny model. Adding eval dataset links to the flagship 1.5B card
would catch general traffic but miss this niche. The reverse promotion
pattern ensures each zero-download dataset gets at least one discoverable
entry point.
