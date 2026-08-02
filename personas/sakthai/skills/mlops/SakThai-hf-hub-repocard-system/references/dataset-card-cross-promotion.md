# Dataset Card Cross-Promotion — From Dead-End to Navigation Hub

A dataset card with only technical quality metrics is a **dead-end page**. The user arrives, reads, and leaves the ecosystem. Cross-promotion elements turn it into a gateway that drives traffic to sibling models, datasets, and Spaces — at zero cost.

This reference is a **complete enrichment toolkit**. Apply all sections to a bare dataset card, or pick individual sections for incremental improvement in cron cycles.

## 1. Badges Row

Add at the top, right after the title `# ...`. Two badges are baseline:

```markdown
<p align="center">
  <img src="https://img.shields.io/endpoint?url=https://huggingface.co/api/datasets/{user}/{repo}&label=Downloads&color=blue" alt="Downloads"/>
  <a href="https://huggingface.co/collections/{user}/{collection-id}"><img src="https://img.shields.io/badge/🏠-{Collection%20Name}-6644cc" alt="Collection"/></a>
</p>
```

**⚠️ Dataset vs model badge URL:** Datasets use `/api/datasets/` — NOT `/api/models/`. Using the model endpoint returns the wrong count (a model with the same name, or 0). Always verify the badge after adding it:

```bash
# Check the badge returns a real number
curl -sL "https://img.shields.io/endpoint?url=https://huggingface.co/api/datasets/Nanthasit/sakthai-combined-v7&label&color=blue" | grep -oP '\d+'
```

## 2. Quick Start Section

Add after the intro paragraph and before the technical content. Gives users instant value without scrolling:

```markdown
## Quick start

```python
from datasets import load_dataset

ds = load_dataset("{user}/{repo}", split="train")
print(len(ds))  # actual count

# Test split (if it exists)
# ds_test = load_dataset("{user}/{repo}", split="test")
```

Pair with the [sibling-dataset-name]({link}) for complementary data.
```

**Key details to verify:**
- Confirm `split="train"` and `split="test"` both actually exist (check repo siblings via API)
- Match the count in the comment to the actual line count
- Link to one relevant sibling dataset if it pairs naturally (e.g., v6 for v7, or a supplement)

## 3. Trained Models Family Table

The highest-leverage cross-promotion element. Links every model that uses this dataset.

### Sourcing accurate counts

Always fetch live, never reuse stale data:

```bash
curl -s "https://huggingface.co/api/models?author={user}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in sorted(data, key=lambda x: x.get('downloads',0), reverse=True):
    n = m['id'].split('/')[1]
    if n != '{user}':  # skip profile repo
        print(f\"{n}: {m.get('downloads',0)} dl | {m.get('pipeline_tag','N/A')}\")
"
```

### Table format

| Model | Pipeline | Size | Downloads | Role |
|:------|:--------:|:----:|:---------:|:-----|
| [name](link) | pipeline-tag | weight-size | 1,269 ⬇ | Description |
| ... | sorted by downloads descending |

**Rules:**
- Sort **downloads descending** — popular models first, natural reading order
- Right-align the Downloads column with `:---------:`
- Include **Size** column (weight in MB/GB, or "LoRA" for adapters)
- Include **Role** column (short one-line description of what the model does)
- Mark models trained on *different* data with a footnote note below the table
- Models with <10 downloads get 🌱 suffix; 0 downloads gets 🌱
- End with a collection line: `**N models · M datasets · K Spaces** — [full collection →](link)`

### Footnote note for unrelated models

If some sibling models are independently trained (not on this dataset), add a note:

```markdown
*Note: [model-A](link) and [model-B](link) are independently trained (not on this dataset).*
```

## 4. Sibling Datasets Table

Adds a second cross-promotion dimension — links sibling datasets that users might also want:

| Dataset | Purpose | Downloads |
|---------|---------|:---------:|
| [name](link) | One-line purpose description | count ⬇ |
| [name](link) | ... | count 🚨 |  <!-- 🚨 for 0 downloads -->

**Rules:**
- Sort downloads descending
- Include ALL sibling datasets (from the API `datasets?author={user}`)
- Mark 0-download entries with 🚨 to signal urgency rather than shame
- Each row has a brief "Purpose" so users can decide at a glance

## 5. Growing the Ecosystem Section

A dedicated low-download promotion table. This is the equivalent of the "Rising Stars" section on model cards, adapted for datasets. Place after the main technical content, before the license.

```markdown
## 🌱 Growing the ecosystem

These sibling assets have low downloads but are production-ready. Every download helps validate the whole family:

| Resource | Type | Downloads | Why It Matters |
|----------|:----:|:---------:|:--------------|
| [name](link) 🚨 | Dataset | 0 | One-line reason this matters |
| [name](link) 🌱 | Model | 7 | ... |
```

**Selection criteria for items:**
- **Models** with <100 downloads
- **Datasets** with <50 downloads
- **Spaces** with <10 downloads (or any, since Spaces rarely show downloads)
- Include the **"Why It Matters"** column — tells the reader why they should care about a 0-download resource
- Mark with 🚨 (0 dl, critical) or 🌱 (1-99 dl, growing)
- Limit to 5-7 items max (don't overwhelm)

## 6. Support the Project Section

A donation-free engagement section. Place after Growing the Ecosystem, before Links:

```markdown
## 🤝 Support the Project

Building AI from a shelter in Cork, Ireland with US$0 budget. Every contribution counts:

- ⭐ **Star the [collection](link)** — costs nothing, helps others discover the family
- 🐛 **Report issues** on [GitHub](link)
- 📢 **Share the datasets** — with study groups, friends, or online communities
- 📊 **Run and share benchmarks** — community evals help everyone understand what works

*"We are one family — and becoming more."*
```

**Why no donation links:** The user has $0 income. Asking for money when you can't provide value back feels wrong. Focus on zero-cost engagement: stars, shares, issues, community benchmarks.

## 7. Links Bar

A compact footer navigation row before the license:

```markdown
## Links

[House of Sak](link) ·
[Project GitHub](link) ·
[All models](link) ·
[All datasets](link)
```

## 8. Verification Checklist

After pushing the updated card, verify EVERY element against the live API:

```bash
# 1. Fetch the live card
curl -sL -o /tmp/verified.md "https://huggingface.co/datasets/{user}/{repo}/raw/main/README.md"

# 2. Check each element
for element in "img.shields.io/endpoint" "Quick start" "Trained models" \
               "Sibling datasets" "Growing the ecosystem" "Support the Project"; do
  count=$(grep -c "$element" /tmp/verified.md)
  [ "$count" -gt 0 ] && echo "✅ $element" || echo "❌ MISSING: $element"
done

# 3. Check original technical content preserved
grep -c "Data Quality" /tmp/verified.md && echo "✅ Technical content preserved" \
  || echo "❌ Technical content lost!"

# 4. Verify model links resolve (spot-check top 3 models)
for model in "context-1.5b-merged" "context-0.5b-merged" "vision-7b"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/Nanthasit/$model")
  [ "$status" = "200" ] && echo "✅ $model resolves (200)" || echo "❌ $model returns $status"
done
```

## Ordering the Card

Complete layout (sections you add in bold):

```
--- YAML frontmatter ---
# Title
**Badges row**
Intro paragraph
**Quick start**
**Trained models family table**
**Sibling datasets table**
---
Technical content (Data Quality Card, etc.)
---
**Growing the ecosystem**
**Support the Project**
**Links bar**
License
Collection footer link
```

## When to Use What

| Dataset state | Recommended additions |
|--------------|---------------------|
| Brand new, 0 dl | Badges + Quick start + Trained models table + Growing ecosystem |
| Established, 50+ dl | Badges + Quick start + Trained models table + Sibling datasets |
| Low-dl (<10) | Full treatment: all 7 sections |
| Predecessor/superseded | Badges + Quick start + Sibling datasets (point to successor) |
