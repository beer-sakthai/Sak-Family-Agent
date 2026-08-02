# Card Enrichment Patterns for HF Ecosystem

Documented 2026-07-29 — patterns for taking a thin model card and enriching it to the standard of the best-documented sibling.

## Assessing a Thin Card

1. **Fetch the card:** `curl -sL "https://huggingface.co/<author>/<repo>/raw/main/README.md" -o /tmp/card.md && wc -c /tmp/card.md`
2. **Benchmark against peers:** the most-documented sibling cards run 12K–17K bytes. Cards under 8K bytes are thin.
3. **Run section audit:** check for these sections (ordered by priority):
   - [ ] YAML `widget:` entries (search preview examples)
   - [ ] YAML `datasets:` complete (non-dataset models benefit from this for search indexing)
   - [ ] Ecosystem summary count correct (e.g., "N models · N datasets · N Spaces" matches current API state — see `target-selection-strategies.md` pitfall: zero-download cards commonly have stale counts)
   - [ ] Download count badges (dynamic badges preferred over static counts)
   - [ ] Pipeline Integration section (table format for consumer pipelines; ASCII diagram for technical chains)
   - [ ] Model Family table with download counts
   - [ ] Sibling Datasets table (all datasets with download counts)
   - [ ] Spaces table (all sibling Spaces)
   - [ ] 🌱 Rising Stars section (promotes low-download assets <100 dl)
   - [ ] Support the Project CTA
   - [ ] Citation section

> 🚨 **YAML datasets drift trap:** The YAML `datasets:` frontmatter list and the body's Sibling Datasets table MUST list the same datasets. The YAML drives HF search indexing and API `cardData` — an incomplete YAML means the model won't appear in dataset-filtered searches even if the body table is complete. See `references/yaml-datasets-integrity.md` for detection, fix, and verification commands.

## Priority Order for Adding Sections

When enriching a card, add sections in this order to maximize immediate value:

| Priority | Section | Why |
|:--------:|---------|-----|
| 1 | YAML `widget:` examples | Improves HF search previews — curated examples appear in search results |
| 2 | Download count badges | Users can see popularity at a glance without clicking through |
| 3 | Model Family table + download counts | Helps visitors navigate the ecosystem and gauge where this model fits |
| 4 | Pipeline Integration section | Explains how models compose together — table format for consumer pipelines, ASCII diagram for technical chains |
| 5 | Sibling Datasets table + Spaces | Cross-linking improves discoverability of lower-traffic assets |
| 6 | 🌱 Rising Stars section | Directly promotes sibling assets under 100 dl — uses emoji indicators and callout box |
| 7 | Support the Project CTA | Community building — low effort, high signal |

## Concrete Example: TTS Model Card Enrichment (2026-07-29)

**Before:** 6,742 bytes, 227 lines. Had badges, usage examples, language table, family links (no download counts), low-download gems, support CTA, citation.

**Missing vs well-documented siblings:**
- No download counts in family links
- No datasets section (YAML had `datasets:` but card body had no table)
- No spaces section listed
- No pipeline flow diagram
- No YAML widget examples

**After:** 9,199 bytes, 270 lines (+36%). Added:
1. **Model Family table** with Pipeline/Downloads/Role columns — 10 rows, each sibling with current download count
2. **Pipeline Flow diagram** showing `User → [LLM: 1.5B or 7B] → text response → [TTS Model] → spoken audio`
3. **Sibling Datasets section** — all 5 datasets with downloads column, highlighted irrelevance-supplement (0 dl 🚨)
4. **Spaces section** — all 3 Spaces with descriptions
5. **YAML widget examples** (English + French) for search previews
6. **RAM badge** (200 MB) and pipeline tag in details table

**Command used to upload:**
```bash
hf upload <author>/<repo> /path/to/new_readme.md README.md \
  --commit-message "Enrich card: add download counts, datasets table, spaces section, pipeline flow"
```
Returns: `url=https://huggingface.co/<author>/<repo>/commit/<sha>`

## Dataset Section Template

Add this after the Model Family section:

```markdown
## 📊 Sibling Datasets

| Dataset | Purpose | Downloads |
|---------|---------|:---------:|
| [sakthai-combined-v6](https://huggingface.co/datasets/<author>/sakthai-combined-v6) | Main training dataset | N ⬇ |
| [sakthai-kaggle-notebooks](https://huggingface.co/datasets/<author>/sakthai-kaggle-notebooks) | Training notebooks | N ⬇ |
| [SimpleToolCalling](https://huggingface.co/datasets/<author>/SimpleToolCalling) | Early experiment | N ⬇ |
| [food-penguin-v1](https://huggingface.co/datasets/<author>/food-penguin-v1) | Restaurant tool-calling | N ⬇ |
| [sakthai-combined-v7](https://huggingface.co/datasets/<author>/sakthai-combined-v7) | v7 tool-calling (2,309 ex., 86 tools) | N ⬇ |
| [sakthai-irrelevance-supplement](https://huggingface.co/datasets/<author>/sakthai-irrelevance-supplement) | Safety supplement | N ⬇ |
```

## Spaces Section Template

```markdown
## 🚀 Spaces

| Space | Description |
|-------|-------------|
| [TTS Showcase](https://huggingface.co/spaces/<author>/sakthai-tts) | Interactive TTS playground |
| [Leaderboard](https://huggingface.co/spaces/<author>/sakthai-leaderboard) | Benchmark tracker |
| [Vision Demo](https://huggingface.co/spaces/<author>/sakthai-vision-demo) | Vision model demo |
```

## Edge / Tiny Model Promotion Pattern

For LoRA adapters, small GGUF models (<500 MB), or any model targeting edge/on-device use cases. The goal is to convert "7 downloads, why bother?" into "7 downloads, overlooked gem." This pattern specifically targets models under 50 downloads.

### Key Additions

1. **"Why [size]?" comparison table** — directly compare against bigger siblings on the metrics that matter for edge: size, speed, RAM, and benchmark score.
2. **Discovered benchmark data** — fetch verified benchmark results from sibling merged models and include them. Even a 4/5 score builds confidence.
3. **Discoverability tags in YAML frontmatter** — add `raspberry-pi`, `on-device`, `lightweight`, `low-resource` to the YAML `tags:` list. These drive HF search results.
4. **Benchmark badge** — add `img.shields.io/badge/benchmark-N%2FM-success` to the header badge row.
5. **Honest limitations** — call out what the model *can't* do (e.g., "irrelevance rejection fails at this scale"). Builds trust.

### Template: "Why [Size]?" Comparison Table

Place right after the model description, before Quick Start:

```markdown
## Why 0.5B?

| Feature | 0.5B (this) | 1.5B (standard) | 7B (full) |
|---------|:--:|:--:|:--:|
| GGUF size | **380 MB** | 934 MB | 15 GB |
| Inference speed (CPU) | **~24 tok/s** | ~9 tok/s | ~3 tok/s |
| RAM required | **< 1 GB** | ~2 GB | ~8 GB |
| Tool-calling benchmark | **4/5** ✅ | 5/5 ✅ | 5/5 ✅ |
| Multi-turn reliability | Basic | Good | Excellent |
| Runs on Pi 4/5 | **Yes** ⚡ | Heavy | No |
```

### Template: Verified Benchmark Results Table

Add a section showing per-test pass/fail from sibling benchmark runs:

```markdown
## Verified benchmark results

| Model | get_weather | search_web | calculate | get_time | irrelevance | **Score** |
|:------|:-----------:|:----------:|:---------:|:--------:|:-----------:|:---------:|
| **0.5B** (this) | ✅ | ✅ | ✅ | ✅ | ❌ | **4/5** |
| 1.5B | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5 |
```

### Benchmark data source

Fetch from the merged model's eval directory:

```bash
VERIFIED_URL="https://huggingface.co/<author>/<merged-model>/raw/main/eval/verified-benchmark.json"
# Contains: results.tool_calling.<model>.score
SPEED_URL="https://huggingface.co/<author>/<merged-model>/raw/main/eval/benchmark-full.json"
# Contains: benchmarks.speed_ram arrays
```

### Frontmatter YAML tags to add

```yaml
tags:
  - raspberry-pi
  - on-device
  - lightweight
  - low-resource
```

These are in addition to existing functional tags (peft, lora, tool-calling, etc.).

### When NOT to use this pattern

- Model already has 100+ downloads — it doesn't need the "overlooked gem" framing
- Model is a full-size GGUF (>2 GB) — the edge framing feels dishonest
- The sibling models don't exist or have no benchmark data — comparison needs real numbers

## Pattern: Version Comparison Table (LoRA Adapters)

When you have multiple versions of the same LoRA adapter (e.g., v1 and v2 with different training recipes), a **version comparison table** helps users decide which to use and demonstrates improvement over time. This is especially useful when both versions have low downloads and neither has a proper card yet.

### Template

```markdown
## What's new in v2

| Aspect | v1 | v2 |
|--------|----|----|
| Training recipe | QLoRA on base | Refined LoRA config |
| Tool coverage | Basic tool calls | Multi-turn + structured |
| Edge cases | Limited | Extended irrelevance + refusal handling |
| Data | [v6 dataset](...) | Same + [supplement](...) |
```

### When to Use

- You're creating a card for v2 of an adapter series
- The v2 model has **0 downloads** and needs differentiation from v1
- v2 represents a meaningful improvement (not just a rerun with different seeds)
- Both models are under 50 downloads — the table justifies why v2 exists

### Key Elements

1. **Aspect column** — 3-5 key dimensions that changed (training, data, coverage, formats)
2. **v1 column** — what the original did (brief)
3. **v2 column** — what changed (be specific: "Multi-turn + structured" not "Improved")
4. **Data links** — link to the actual datasets used for credibility
5. **Placement** — right after the model description, before Quick Start

### Real Example (experimental LoRA, 2026-07-29)

The `sakthai-context-0.5b-exp-lora-masked-v4` card uses this pattern to explain why an experimental checkpoint exists alongside the stable `context-0.5b-tools` adapter. The table occupies ~6 lines and immediately answers "what's different?" — the first question any visitor asks about an experimental sibling.

> **Note:** The original example model `sakthai-context-0.5b-tools-v2` was deleted in a 2026-07-29 cleanup sweep. Its replacement is `sakthai-context-0.5b-exp-lora-masked-v4`. Always verify the model exists before referencing it in documentation. See `references/deleted-repo-cleanup-sweep.md`.

### Do's and Don'ts

**Do:**
- Keep tables to 3–5 rows
- Be specific about improvements
- Link to datasets used in each version
- Place early in the card (after title, before Quick Start)

**Don't:**
- Make the table the entire card — it must complement a full card with usage instructions, family links, and download badges
- Claim improvements you can't verify ("3x faster") — use objective language
- Include v1→v2 tables when only one version exists — this is for adapter series, not singleton models

---

## Pattern: `extra.sibling` YAML Cross-Link

Used to create bi-directional discoverability between sibling assets (model ↔ demo Space, model ↔ dataset, etc.). Added to the YAML frontmatter, this appears in the `cardData` API response and enables HF's UI to show "Related" links.

### Template

```yaml
extra:
  sibling: <author>/<target-repo-name>
```

### When to Use

| Pairing | Example | Benefit |
|---------|---------|---------|
| Model → demo Space | `sibling: Nanthasit/sakthai-vision-demo` | Every model page visit→Space discovery |
| Model → sibling model | `sibling: Nanthasit/sakthai-embedding-multilingual` | Cross-language embedding pair |
| Dataset → usage model | `sibling: Nanthasit/sakthai-context-1.5b-merged` | "Trained with this dataset? Try this model" |

### Real Example (vision-7b, 2026-07-29)

```yaml
extra:
  sibling: Nanthasit/sakthai-vision-demo
```

Added to `sakthai-vision-7b`'s YAML frontmatter. The vision-demo Space now appears as a related resource on the model page. Verified via HF API's `cardData.extra.sibling` field.

### Verification

```python
info = HfApi().model_info("author/repo")
print(info.cardData.get("extra", {}).get("sibling"))
# Expected: "author/target-repo"
```

> ⚠️ **One-direction only.** HF does not auto-create back-links. If model A → Space B, you must also add an `extra.sibling` to Space B's README pointing back to model A for true bi-directional linking.

---

## Pattern: Model-Index with Upstream Benchmarks (Repackaged Models)

For models that are **quantizations or repackagings** of upstream work — not custom fine-tunes — you can still add a `model-index` to YAML frontmatter for HF widget integration and search discoverability. The key difference: **mark benchmarks as `verified: false`** and include a body note explaining they're upstream values, not own measurements.

### Template

Add to YAML frontmatter:

```yaml
model-index:
- name: Your Model Name
  results:
  - task:
      type: <pipeline-tag>
      name: <Human-readable task name>
    dataset:
      name: <Dataset name>
      type: <dataset-type>
    metrics:
    - type: <metric-type>
      value: <float-score>
      name: <Human-readable metric name>
      verified: false  # ⚠️ Critical for repackaged models
```

### Rules

1. **`verified: false` on every metric** — signals "these are published upstream values, not measured on this specific quantization"
2. **Name the upstream paper/model** — in the body section, state explicitly: "These are the published [upstream-name] benchmarks. As a [quantization type], expect results within ~1-2% on most tasks."
3. **Include a ⏳ note in the table caption** — "Own measurements pending publication" or similar
4. **Limit to 3–5 benchmark rows** — don't copy the full 20-row leaderboard; pick the most commonly cited tasks (VQAv2, COCO, GQA for vision models)

### Real Example (vision-7b, 2026-07-29)

```yaml
model-index:
- name: SakThai Vision 7B
  results:
  - task:
      type: image-to-text
      name: Visual Question Answering
    dataset:
      name: VQAv2
      type: vqa_v2
    metrics:
    - type: accuracy
      value: 78.5
      name: Accuracy
      verified: false
  - task:
      type: image-to-text
      name: Image Captioning
    dataset:
      name: COCO Captions
      type: coco_captions
    metrics:
    - type: CIDEr
      value: 110.1
      name: CIDEr
      verified: false
  - task:
      type: image-to-text
      name: Visual Reasoning
    dataset:
      name: GQA
      type: gqa
    metrics:
    - type: accuracy
      value: 62.0
      name: Accuracy
      verified: false
```

With a body note:
```markdown
> **Note:** These are the published upstream benchmarks for LLaVA-1.5-7B. As a GGUF Q4_K_M
> quantization, expect results within ~1–2% of these values on most tasks. Own run-specific
> benchmarks pending publication.
```

### When NOT to use

- Model is a custom fine-tune with own evaluation data — use `verified: true` if you've run the eval
- Model has no upstream published benchmarks — find a reference or skip
- Pipeline tag doesn't have an obvious benchmark dataset — skip model-index entirely

## YAML Widget Template

Add to the YAML frontmatter, after `datasets:`:

```yaml
widget:
  - text: "Example input text for search preview"
    example_title: Title shown in search
  - text: "Second example in another language"
    example_title: Description
```

Widgets improve HF search results — they show up as "Try it out" samples on the model page.

## Pattern: TRL / HF Jobs Auto-Generated Stub Enrichment

> ⚠️ **Active training check required:** Before enriching a model card from an `hf jobs` training run, check for recent "Training in progress" commits. If the model is still being trained, your enrichment will be overwritten. See `references/active-training-card-overwrite.md` for detection and timing guidance.

When a model is trained via `hf jobs`, TRL SFT trainers, or similar HF-native training pipelines, the auto-generated model card is a **minimal stub** — typically 40-60 lines with only framework versions and a single generic usage example. These stubs lack `pipeline_tag`, family cross-links, dataset references, meaningful usage examples, and any discoverability hooks. This pattern is specifically for transforming such stubs into discoverable ecosystem cards.

### Identifying a Stub Card

A TRL stub card has these characteristics:

| Feature | Stub (auto-generated) | Enriched |
|---------|----------------------|----------|
| Length | 40-80 lines | 140-200 lines |
| YAML `pipeline_tag` | ❌ Absent (or `pipeline: -`) | ✅ `text-generation` or appropriate |
| YAML `tags` | `generated_from_trainer, trl, sft` | Functional tags + `sakthai` |
| YAML `datasets` | ❌ Absent | ✅ Training dataset(s) listed |
| Badge bar | ❌ None | ✅ Downloads, license, collection, Spaces |
| Family table | ❌ None | ✅ All sibling models with download counts |
| Dataset table | ❌ None | ✅ All sibling datasets |
| Spaces table | ❌ None | ✅ All sibling Spaces |
| Meaningful usage | ❌ Generic question | ✅ Tool-calling example with `<tools>` XML |
| Collection link | ❌ None | ✅ Link to SakThai Model Family |

### The Enrichment Checklist

When you find a stub card (e.g., created by `hf jobs uv run` with TRL SFT):

1. **Fix YAML frontmatter** — replace the auto-generated block with a proper one:
   ```yaml
   license: apache-2.0
   language:
   - en
   pipeline_tag: text-generation  # Critical: enables HF search filtering
   tags:
   - sakthai
   - house-of-sak
   - tool-calling
   - function-calling
   - qwen
   - trl
   - sft
   base_model: Qwen/Qwen2.5-1.5B-Instruct
   datasets:
   - Nanthasit/sakthai-combined-v7
   ```

2. **Add badge bar** — at minimum: downloads, license, collection link, sibling Spaces:
   ```markdown
   <img src="https://img.shields.io/badge/downloads-0-blue" alt="Downloads"/>
   <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-..."><img src="https://img.shields.io/badge/🏠-SakThai%20Family-6644cc" alt="Collection"/></a>
   ```

3. **Write a "What it is" section** — explain what makes this model different from siblings (full FT vs LoRA, different dataset, different training method)

4. **Replace the generic usage example** — show something relevant to the model's purpose. For tool-calling models, show `<tools>` XML format. For code models, show a code generation example.

5. **Add the full SakThai Model Family table** (13 models, current download counts from live API)

6. **Add dataset and Spaces tables** (all 8 datasets + 3 Spaces)

7. **Add collection link + footer** with ecosystem count

8. **Add framework versions** — preserve the auto-generated training details but move them to a subsection

### Verification (see also: verification-patterns.md — Git Push Verification)

After pushing, verify by cloning fresh:

```bash
git clone https://user:$HF_TOKEN@huggingface.co/<author>/<repo> /tmp/verify-<repo>
head -5 /tmp/verify-<repo>/README.md   # Must start with `license:` not `base_model:`
wc -l /tmp/verify-<repo>/README.md     # Should be 140+
grep -c "pipeline_tag:" /tmp/verify-<repo>/README.md  # ≥1
grep -c "SakThai Model Family" /tmp/verify-<repo>/README.md  # ≥1
rm -rf /tmp/verify-<repo>
```

### Real Example (Cron #033, 2026-07-29)

The `sakthai-context-1.5b-tools-v7` model was uploaded via `hf jobs` with the default TRL SFT stub card (58 lines, no `pipeline_tag`, no family tables, no tool-calling examples). After enrichment: 143 lines, `pipeline_tag: text-generation`, full family tables, `<tools>` XML usage examples, and collection cross-links. The card went from invisible (not listed in HF search by pipeline) to a distribution hub for the entire ecosystem.

> ⚠️ **Cautionary follow-up (Cron #034, 2026-07-30):** The `1.5b-tools-v7` model was *still actively training* when Cron #034 attempted to enrich it again. The enriched card (with updated ecosystem counts) was pushed at 00:23:32 but overwritten at 00:23:35 by "Training in progress, step 250." Always verify training has completed before pushing card changes.

## Badge URLs for Dynamic Download Counts

Static `img.shields.io/endpoint?url=https://huggingface.co/api/models/...` badges **do not work** — the HF API returns raw JSON, not shields.io-compatible JSON, producing "invalid properties: label, message".

### Correct badge URLSON, not shields.io-compatible JSON, producing "invalid properties: label, message".

### Correct badge URL

Use `dynamic/json` with URL-encoded parameters and a JSONPath query:

```markdown
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2F<author>%2F<repo>&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
```

| Component | Value | Notes |
|-----------|-------|-------|
| `url` | URL-encoded HF API URL | `https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2Fauthor%2Frepo` |
| `query` | `%24.downloads` = `$.downloads` | JSONPath to the downloads field |
| `label` | `downloads` | Left-side label text |
| `color` | `blue` or `success`/`brightgreen` | Badge color |
| `cacheSeconds` | `3600` | Cache TTL in seconds |

### Verification

After adding a badge, verify it renders correctly:

```bash
curl -s "https://img.shields.io/badge/dynamic/json?url=<encoded-url>&query=%24.downloads&label=downloads&color=blue" | grep -o 'aria-label="[^"]*"'
# Expected output: aria-label="downloads: <number>"
```

If the output contains "invalid properties", the badge URL is malformed — re-check URL encoding and query path.

### Badge for datasets

Same pattern, but use the datasets API endpoint:

```markdown
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2F<author>%2F<dataset>&query=%24.downloads&label=downloads&color=blue" alt="Downloads"/>
```

### License, LoRA config, collection badges (static)

No API query needed:

```markdown
<img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"/>
<img src="https://img.shields.io/badge/PEFT-LoRA%20r16%20rsLoRA-blueviolet" alt="LoRA"/>
<a href="https://huggingface.co/collections/<author>/<collection-id>"><img src="https://img.shields.io/badge/🏠-SakThai%20Family-6644cc" alt="Collection"/></a>
```

## Download Counts in Family Tables

When a card has a family/model links section but no download counts, replace the table to include a Downloads column:

```markdown
| Model | Pipeline | Downloads | Role |
|-------|----------|:---------:|------|
| [Name](https://huggingface.co/<author>/name) | Text Gen | N ⬇ | Description |
```

Use live API values. Mark the current model row with **bold** and "(you are here)".

### Sorted-by-popularity variant (preferred)

For maximum discoverability, sort the family table by download count descending and add a ★ marker:

```markdown
| Model | Downloads | Size | Role |
|---|:---:|:---:|---|
| [context-1.5b-merged](...) | **1,269 ⬇** | 934 MB | Flagship tool-calling |
| [context-0.5b-merged](...) | **1,030 ⬇** | 380 MB | Lightweight / edge |
| [context-7b-merged](...) | **585 ⬇** | 15 GB | Full-power reasoning |
| ... sorted by popularity descending | ... | ... | ... |
| **★ context-0.5b-exp-lora-masked-v4** | **0 🌱** | LoRA | **You are here** |
```

- First row = highest downloads, last row = current model
- ⬇ after download numbers for traction, 🌱 for zero-download
- ★ marks the current model in bold
- Include every sibling model — even zero-download ones — so visitors see the full ecosystem

### Low-download gems sub-section

When the family table is long (8+ rows), add a compact "Low-download gems" subsection after it:

```markdown
### Low-download gems

These models are new or specialised — give them a try:

| Model | Downloads | Why |
|---|---|---|
| [vision-7b](...) | 104 ⬇ | First SakThai model with ⭐ likes — captioning + OCR |
| [coder-1.5b](...) | 70 ⬇ | Qwen2.5-Coder fine-tune |
| [tts-model](...) | 69 ⬇ | 15-language TTS, Kokoro-based |
```

Use 3-column table (Model, Downloads, Why). Keep to 3–5 rows. This is an alternative to the 🌱 Rising Stars section — use Rising Stars for main cards and Low-download gems for pre-release/edge cards.

## Conversational Tag for Chat Widget

Add `conversational` to the YAML `tags:` list to enable the in-browser chat widget on the HF model page. Without it, the model page shows a plain metadata view; with it, visitors can test the model directly in the browser.

```yaml
tags:
  - conversational
  - ...  # other functional tags
```

**Verification:** After pushing, check the HF API response includes `conversational` in the tags array:

```bash
curl -s "https://huggingface.co/api/models/<author>/<repo>" | python3 -c "import json,sys; d=json.load(sys.stdin); print('conversational' in d.get('tags',[]))"
# Expected: True
```

**When to add:** All text-generation and chat-oriented models benefit. Do NOT add for embedding, TTS, or vision-only models (the widget doesn't apply).

## Referencing the Low-Download Dataset

Every card enrichment should include a row (or callout) for `sakthai-irrelevance-supplement` with **0 ⬇ 🚨** to drive visibility to the zero-download asset. The callout text should explain why it matters:

```markdown
> 🚨 The **irrelevance-supplement** dataset has 0 downloads despite being essential for training models to decline out-of-scope tool calls. Every download helps validate this safety-critical approach!
```

## Pipeline Integration Table (Consumer-Facing Format)

An alternative to the ASCII diagram approach in `hf-hub-repocard-system/references/pipeline-integration-section.md`. Uses a **markdown table with emoji and download counts** to show the end-to-end consumer workflow. More accessible to general users than an upstream/downstream ASCII diagram.

### Template

```markdown
## Pipeline Integration 🔗

This model is **the [role] frontend** in the SakThai end-to-end pipeline:

| Step | Model | What It Does | Downloads |
|:----:|-------|-------------|:---------:|
| 🖼️ | **[Vision 7B](...) ← you are here** | **Caption, OCR, describe images** | **N ⬇** |
| 🌐 | [Embedding Multilingual](...) | Cross-lingual semantic search (50+ languages) | N ⬇ |
| 💻 | [Coder 1.5B](...) | Code generation, debugging, tool-calling | N ⬇ |
| 🗣️ | [TTS Model](...) | Synthesize speech (15 languages) | N ⬇ |
| 💬 | [Context 1.5B](...) | General chat & tool-calling | N ⬇ |
```

### Usage Rules

- **One row per sibling model** — each is a distinct pipeline step
- **Emoji column** — pick a distinct emoji per step for quick visual scanning
- **Downloads column** — use **live API values**, not stale numbers; mark current model in bold with "← you are here"
- **Placement** — after Model Description + before Model Family table (near the top, so visitors immediately see ecosystem context)
- **Intended for** — multimodal pipelines where each model handles a different modality (vision → text → code → speech)
- **Not for** — LoRA adapter chains (use the ASCII diagram format in `pipeline-integration-section.md` instead)

### Contrast with ASCII Pipeline Diagram

| Format | Best for | Line count | Reader | Maintains download counts |
|--------|----------|:----------:|--------|:-------------------------:|
| ASCII Diagram (existing) | Technical upstream/downstream chains | 6–12 | Developers | No (descriptive text) |
| Table (this pattern) | Multimodal end-to-end pipelines | 8–16 | General users | Yes (live API values) |

**Rule of thumb:** Use the ASCII diagram when the pipeline is about *data flow* (base model → fine-tune → merge → agent). Use the table when the pipeline is about *capability flow* (see text → search → write code → speak).

### Real Example (vision-7b, 2026-07-29)

The vision-7b card (113→241 lines) uses this pattern to show: image input → vision model (here) → embedding search → code generation → speech output → general chat. Each row's download count is a live API value fetched during enrichment.

---

## 🌱 Rising Stars Cross-Promotion Section

A standardized section that directly promotes low-download sibling assets (<100 dl) from a popular model's card. Uses emoji indicators and a compact table format to drive traffic to assets that visitors would otherwise never discover.

### When to Add

Add a Rising Stars section when:
- The card already has a Model Family table and you want additional low-download promotion
- The enrichment run explicitly targets low-download assets (<50 dl)
- A cron task directive says "promote low-download models"

### Template

```markdown
## 🌱 Rising Stars — Growing the Ecosystem

These sibling assets have traction but less visibility. If you find this [model type] useful, every download helps validate the whole ecosystem:

| Model / Dataset | Type | Downloads | Why It Matters |
|-----------------|------|:---------:|----------------|
| [0.5B Tools LoRA](...) | Tool-calling | N 🌱 | Smallest tool LoRA on HF — 494M params, runs on Raspberry Pi |
| [Irrelevance Supplement](...) | Dataset | 0 🚨 | Teaches models when NOT to call tools — critical safety data |

> 🚨 The **[asset-name]** has 0 downloads despite being [importance]. Every download validates this approach!
```

### Emoji Indicators

| Emoji | Meaning | When to use |
|:-----:|---------|-------------|
| 🌱 | Low but growing | 1–49 downloads — asset has traction but needs boost |
| 🚨 | Zero downloads | 0 downloads — needs urgent attention |
| ★ | Star pick | Marker used in family tables to highlight the low-download entry |

### Placement

Insert the Rising Stars section **after the main Model Family table and before the Support the Project CTA / footer**. Position map:

```
SakThai Model Family table (main sibling table)
🌱 Rising Stars ← HERE
Datasets table (optional)
Support the Project CTA
Footer + Collection link
```

### Do's and Don'ts

**Do:**
- Keep the table compact — 2–4 rows max
- Use 🌱 for 1–49 dl, 🚨 for 0 dl
- Include a 1-line "why it matters" explanation per row
- Include the 🚨 callout box for any zero-download asset
- Update download counts to live API values

**Don't:**
- Include assets that already have 100+ downloads
- Include non-real assets (profile repos, redirect placeholders)
- Use symbols that look broken (🔧, ❌, 🔒)
- Make the section longer than the main Model Family table

### Cross-Promotion Coverage Tracking

When adding Rising Stars to a card, record which low-download assets are now promoted in `LEARNING_JOURNAL.md`:

```
**Cross-promotion coverage now:**
- 0.5B-tools → promoted on: card-A ✅, card-B ✅, card-C ✅
- irrelevance-supplement → promoted on: same cards ✅
```

### Dataset Card Variant

Dataset cards need a slightly different Rising Stars section. The table has 4 columns (Resource, Type, Downloads, Why It Matters) and the narrative ties back to *this dataset's* utility:

```markdown
### 🌱 Rising Stars — Lowest-Download Gems

These models and datasets are still growing and need your support:

| Resource | Type | Downloads | Why It Matters |
|----------|:----:|:--------:|:--------------:|
| [context-0.5b-tools](...) 🌱 | Model | **7** | Lightest tool-calling LoRA (20 MB) — run anywhere |
| [irrelevance-supplement](...) 🚨 | Dataset | **0** | Teaches models when NOT to call tools — critical safety gap |

If you find this dataset useful, give these siblings a try — every download helps them grow. 🌱
```

**Differences from the model-card variant (3-column Type/Downloads/Why):**
- Adds explicit "Type" column (Model vs Dataset) — required because dataset cards promote both models and datasets
- Narrative connects back to *this dataset's* usefulness instead of the model's: "If you find *this dataset* useful..."
- YAML tags should include `rising-stars` for HF search discoverability
- **Placement:** after the Datasets table and before the closing footer, not before Support the Project (dataset cards often lack a CTA section)

### Real Example (vision-7b, 2026-07-29)

Added after the SakThai Model Family table, before Datasets section. Promotes 0.5B-tools (7 🌱) and irrelevance-supplement (0 🚨) — both now covered across all 5 popular model cards + 1 Space.
