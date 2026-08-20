---
name: SakSit-SakThai-hf-hub-model-card-seo-social-meta-tags
description: How Hugging Face model/dataset/space cards appear in search engines and social media,
  and how to optimize metadata for maximum discoverability.
...
---

# HF Hub Model Card SEO & Social Meta Tags

> **What this covers:** How the Hugging Face Hub generates search-engine indexing signals and social-media previews (Open Graph, Twitter Cards) for model, dataset, and Space repos. How to optimize your card metadata so it ranks higher in HF Hub search, appears correctly when shared on social media, and attracts more organic traffic.

## How HF Hub Cards Appear in Search Engines

Every HF Hub repo page (model, dataset, Space) generates a full HTML page with standard meta tags:

| Tag | Source | Notes |
|-----|--------|-------|
| `<title>` | `{Author}/{RepoName} · Hugging Face` | Auto-generated from repo ID |
| `<meta name="description">` | **Default HF site description** ("We're on a journey to advance and democratize AI…") | **Not customized per repo!** The README content is IN the page but NOT in the meta description tag. |
| `<link rel="canonical">` | `https://huggingface.co/{type}/{author}/{repo}` | Auto-generated |
| Open Graph tags | Auto-generated (see below) | Includes title, description, image, type, URL |

**Critical finding (verified 2026-07-30):** The `og:description` and `<meta name="description">` for model pages use the **generic HF site description**, not the model's own description from the README or YAML metadata. This means:

1. **Search engine snippets** show the generic HF tagline, not what your model does
2. **Social media preview cards** show "We're on a journey to advance and democratize AI" instead of your model's value proposition
3. The **only thing differentiating your model in search snippets** is the title and the page URL

## Open Graph Tags (Social Media Sharing)

When a HF Hub page is shared on social media (Twitter/X, LinkedIn, Facebook, Discord, Slack), these OG tags determine the preview card:

### Auto-generated OG tags (verified on model page, 2026-07-30):

```
<meta property="og:title" content="Nanthasit/sakthai-context-0.5b-tools · Hugging Face" />
<meta property="og:description" content="We're on a journey to advance and democratize artificial intelligence through open source and open science." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools" />
<meta property="og:image" content="https://cdn-thumbnails.huggingface.co/social-thumbnails/models/Nanthasit/sakthai-context-0.5b-tools.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@huggingface" />
<meta name="twitter:image" content="https://cdn-thumbnails.huggingface.co/social-thumbnails/models/Nanthasit/sakthai-context-0.5b-tools.png" />
```

### Key observations:

- **og:title** = `{author}/{repo} · Hugging Face` — always the repo ID
- **og:description** = **always the HF site motto** — NOT customizable per model. The description in the YAML frontmatter does NOT flow into OG tags.
- **og:image** = auto-generated social thumbnail from `cdn-thumbnails.huggingface.co`
- **twitter:card** = `summary_large_image` — large image preview on Twitter/X

### Social thumbnail generation:

Thumbnails are auto-generated at `https://cdn-thumbnails.huggingface.co/social-thumbnails/{type}/{author}/{repo}.png` (verified: 422KB PNG, served with `x-powered-by: hf-social-thumbnails`, cached for 30 min via `s-maxage=1800`). The thumbnail appears to auto-render based on the model card title, tags, and possibly the README's first section.

### The `thumbnail` YAML field

The model card metadata spec includes a `thumbnail` field:
```yaml
thumbnail: "url to a thumbnail used in social sharing"
```

This is documented in the HF Hub model card spec but its exact behavior (whether it overrides the auto-generated OG image) needs per-repo testing. It's listed under "specifying a task" rather than social sharing explicitly.

**Recommendation:** Set the `thumbnail` field in your model card YAML to a custom branded image URL (hosted on HF Spaces, GitHub, or imgur). Monitor whether it overrides the auto-generated OG image by sharing the link in a private message or using a social media preview debugger.

## HF Hub Internal Search Discoverability

### Search API Ranking Factors (verified via live API)

The HF Hub search at `https://huggingface.co/models?search=...` uses the backend API `GET /api/models?search=...` which returns results sorted by **relevance** (the default sort) which factors:

| Factor | Influence | How to optimize |
|--------|-----------|-----------------|
| **Full-text match on repo ID** | High | Include descriptive keywords in repo name (e.g., `sakthai-context-0.5b-tools` better than `model-v4`) |
| **Tags matching search query** | High | Add relevant tags to model card YAML. Tags are indexed and searchable. |
| **README content text** | Medium | The first paragraph and section headers of the README are indexed. Put key terms early. |
| **Downloads** | Medium (sort by relevance) | Higher downloads boost relevance ranking implicitly |
| **Likes** | Low-Medium | Social proof signal |
| **Trending score** | High (on "Trending" sort) | Computed by HF's internal algorithm (see `trendingScore` field in API) |
| **pipeline_tag** | High | Correct pipeline tag ensures the model appears in the right task category (e.g., "text-generation" filter). Wrong tag = wrong audience. |

### Search Sort Options

The HF Hub models page supports these sort parameters (verified via live API):

| Sort | API param | Use case |
|------|-----------|----------|
| **Most Downloads** | `sort=downloads&direction=-1` | Default sort. Favors established, popular models |
| **Newest** | `sort=createdAt&direction=-1` | Favors recently created models |
| **Recently updated** | `sort=lastModified&direction=-1` | Favors actively maintained models |
| **Trending** | CLI only: `hf models list --sort trending_score` | Favors models with recent spikes in activity. **Not available via REST API `sort=trending` (returns 400).** |

### `hf models list` search options (tirith-safe):

```bash
# Full-text search
hf models list --search "tool-calling small model" --limit 20

# Sort by trending score (not available via REST API)
hf models list --sort trending_score --limit 20

# Filter by author
hf models list --author Nanthasit --limit 50
```

## Model Card YAML Metadata for Discoverability

The `README.md` YAML frontmatter is the **primary mechanism** for controlling how your model appears in HF Hub search and filtering.

### Essential fields for discoverability

```yaml
---
language:                               # ISO 639-1 codes. Multi-language = list
  - en
  - fr
tags:                                   # CRITICAL for search filtering
  - transformers                        # Library tag (auto-detect or explicit)
  - text-generation                     # Pipeline tag (or use pipeline_tag field)
  - tool-calling                        # Custom descriptive tags
  - small-language-model                # Descriptive tags for your niche
  - edge                                # Deployment context tags
  - finetune                            # Training approach tags
  - pytorch                             # Framework tags
license: apache-2.0                     # SPDX license identifier
library_name: transformers              # Explicit library name (required for non-transformers)
pipeline_tag: text-generation            # The canonical task tag (sets the model's primary category)
datasets:                               # Links to training datasets (appears as "Datasets used to train:")
  - Nanthasit/sakthai-combined-v7
base_model: Qwen/Qwen2.5-0.5B-Instruct  # Links to base model (enables filtering by base model)
thumbnail: "https://example.com/thumb.png"  # Custom social sharing thumbnail URL
co2_eq_emissions: 0.5                   # Carbon emissions (appears in card)
metrics:                                # Evaluation metrics for leaderboard display
  - accuracy
model-index:                            # Structured evaluation results
  - name: Model Name
    results:
      - task:
          type: text-generation
        dataset:
          type: custom
          name: SakThai Bench v2
        metrics:
          - type: accuracy
            value: 0.918
            name: Selection Accuracy
---
```

### Tag Strategy for Maximum Discoverability

Tags serve **three purposes** on the HF Hub:

1. **Search filtering** — users can filter by tag at `huggingface.co/models`
2. **Category association** — library tags (`transformers`, `safetensors`, `peft`, `gguf`, `sentence-transformers`) determine which ecosystem the model belongs to
3. **Free-text search** — tags are indexed and matched against search queries

**Optimal tag selection rules:**

- Include **library tags** (auto-detected but set explicitly: `transformers`, `safetensors`, `peft`)
- Include **pipeline tag synonyms** (e.g., `text-generation`, `conversational`)
- Include **deployment context** (`edge`, `cpu`, `mobile`, `raspberry-pi`, `on-device`, `local-ai`)
- Include **training method** (`finetune`, `merged`, `lora`, `qlora`, `sft`)
- Include **framework** (`pytorch`, `tf`, `jax`, `llama.cpp`)
- Include **task keywords** (`tool-use`, `tool-calling`, `function-calling`, `rag`, `retrieval`, `chat`)
- Include **model family** (`qwen`, `qwen2.5`, `llama`, `phi`, `mistral`)
- Include **custom project tag** for grouping (`sakthai`, `house-of-sak`)
- Include **domain tags** (`small-language-model`, `slm`, `lightweight`, `low-resource`)
- Include **benchmark/eval tags** (`benchmark`, `eval`)
- Include **dataset references** (`dataset:Nanthasit/sakthai-combined-v7`)
- Include **base model references** (`base_model:Qwen/Qwen2.5-0.5B-Instruct`, `arxiv:...`)

**Anti-patterns:**
- Don't add irrelevant tags just for reach (will hurt click-through)
- Don't add the same meaning in different cases (tags are case-sensitive but search is case-insensitive)
- Don't skip `library_name` — without it, models created after August 2024 won't auto-detect as transformers

### Verified tag behavior (via API, 2026-07-30)

Tags appear in the API response as a flat string array:
```json
{
  "tags": [
    "transformers",
    "safetensors",
    "qwen2",
    "text-generation",
    "sakthai",
    "house-of-sak",
    "tool-calling",
    "dataset:Nanthasit/sakthai-combined-v7",
    "base_model:Qwen/Qwen2.5-0.5B-Instruct",
    "license:apache-2.0",
    "endpoints_compatible",
    "region:us"
  ]
}
```

Tags prefixed with `dataset:`, `base_model:`, `license:`, `arxiv:` are auto-generated from the YAML metadata but appear in the same tags array.

## Pipeline Tags (Task Classification)

The `pipeline_tag` field is the **single most important discoverability field**. It determines:

- Which category the model appears under (e.g., "Text Generation" vs "Image Classification")
- Which inference widget is shown on the model page
- Which provider integrations are available

**Selecting the right pipeline_tag:**

| Your model does... | Use this pipeline_tag |
|--------------------|----------------------|
| Text generation / chat / LLM | `text-generation` |
| Text classification (sentiment, etc.) | `text-classification` |
| Token classification (NER, POS) | `token-classification` |
| Image classification | `image-classification` |
| Image generation | `image-generation` (or `text-to-image`) |
| Image segmentation | `image-segmentation` |
| Object detection | `object-detection` |
| Image-to-text (captioning, VQA) | `image-to-text` |
| Text-to-speech | `text-to-speech` |
| Automatic speech recognition | `automatic-speech-recognition` |
| Sentence similarity / embeddings | `sentence-similarity` |
| Feature extraction | `feature-extraction` |
| Fill-Mask (masked LM) | `fill-mask` |
| Question answering | `question-answering` |
| Summarization | `summarization` |
| Translation | `translation` |
| Zero-shot classification | `zero-shot-classification` |
| Table question answering | `table-question-answering` |
| Document question answering | `document-question-answering` |
| Text-to-video | `text-to-video` |
| Reinforcement learning | `reinforcement-learning` |
| Other / unknown | `other` |

Full canonical list: https://huggingface.co/docs/hub/en/models-pipeline

## README Content for Search Rankings

While the `<meta name="description">` tag isn't customized per repo, the **page body content IS indexed** by search engines. This means:

1. **First paragraph** of your README appears in search snippets if the search engine extracts from the body
2. **Section headings** (h1, h2, h3) help search engines understand page structure
3. **Keywords early** in the README improve search relevance

**Recommended README structure for SEO:**

```markdown
# Model Name — Descriptive Tagline

[![Model badge](https://img.shields.io/badge/🤗-Model-blue)]

**Short value prop** — one or two sentences describing what the model does, its
architecture, and its key differentiator. This paragraph is what search engines
will extract for snippets.

## Model Details

- Architecture: [base model]
- Parameters: N
- Context length: N
- Language: English
- License: [SPDX identifier]

## Intended Use

[Describe what the model is designed for and how to use it.]

## Benchmark Results

| Category | Score |
|----------|-------|
| Metric A | XX%   |

## Training Data

[Describe training dataset and link to it.]

## How to Use

```python
from transformers import pipeline
...
```

## Model Card Contact

[Author/house information, links to other models, collection]
```

## README Badges for Visual SEO

Badges (shields.io images) in the README provide:
- **Visual signals** for human readers (download count, license, framework)
- **Alt text** for search engines (the badge label text is indexed)

### Static badges

These are fixed — the number in the URL is what displays. Update manually when the count changes:

```markdown
![Downloads](https://img.shields.io/badge/downloads-NNN-lightblue)
![License](https://img.shields.io/badge/license-apache--2.0-green)
![Framework](https://img.shields.io/badge/🤗-Transformers-FF6F00)
```

### Dynamic download badges (auto-updating)

Use shields.io's `dynamic/json` badge format to query the HF API for live download counts.
**Crucially, the badge URL format matters:**

| Format | Works? | Why |
|--------|--------|-----|
| `img.shields.io/endpoint?url=https://huggingface.co/api/...` | ❌ Broken | `endpoint` expects the URL to return shields.io's custom JSON schema (`{schemaVersion, label, message, color}`). The HF API returns its own JSON — so the badge renders as an error. |
| `img.shields.io/badge/dynamic/json?url=...&query=downloads` | ✅ Correct | `dynamic/json` extracts a field from an arbitrary JSON API response using a JSONPath `query=` parameter. Works with any API that returns JSON. |

**Correct dynamic badge patterns:**

```markdown
<!-- Models -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue)

<!-- Datasets -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue)

<!-- Spaces -->
![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fspaces%2F{author}%2F{repo}&label=Downloads&query=downloads&color=blue)
```

**Explanation of the URL parts:**
- `dynamic/json` — tells shields.io to query the URL and extract a value from the JSON response
- `url=...` — the target API URL (URL-encoded so `://` / `&` don't break the badge URL)
- `query=downloads` — JSONPath expression selecting the field to display (the HF API's `downloads` field is at the top level)
- `label=Downloads` — the label text shown on the left side of the badge
- `color=blue` — badge color (any shields.io color name or hex)

**Real example for a dataset** (from `Nanthasit/food-penguin-v1`):
```markdown
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2FNanthasit%2Ffood-penguin-v1&label=Downloads&query=downloads&color=blue" alt="Downloads"/>
```

**References:**
- `references/dynamic-badge-urls.md` — full reference with all badge patterns

## Social Media Sharing Optimization

### What you can control:
1. **Model repo name** — appears as the OG title. Use descriptive naming: `project-purpose-size-task` (e.g., `sakthai-context-0.5b-tools`)
2. **Social thumbnail** — set via `thumbnail:` YAML field (needs verification that it overrides auto-generated thumbnail)
3. **README first content** — may be used by some social platforms for preview text
4. **Tags** — appear in the page body and may be indexed/referenced by social crawlers

### What you CANNOT control:
- The `og:description` content (always HF's generic tagline)
- The `og:image` generation (auto-generated by `hf-social-thumbnails`)
- The `twitter:site` attribution (always `@huggingface`)

### Workaround for better social previews:
Since the official `og:description` can't be customized, consider:
1. Making the repo name as descriptive as possible (it's the only unique text in the preview)
2. Testing the `thumbnail` YAML field to see if it overrides auto-generated OG images
3. Using a **Space as a landing page** — Spaces pages may have different OG tag behavior
4. Sharing via a **link shortener with custom preview text** (e.g., sharing on Twitter with your own tweet text as context)

## HF Hub Profile as Portfolio Landing Page

Your user profile at `huggingface.co/{username}` serves as a portfolio. Key optimization points:

- **Profile README** — accepted and rendered on your profile page (create `huggingface.co/{username}/profile/README.md`)
- **Organization profile** — same pattern for org pages
- **Pinned repos** — you can feature specific repos on your profile

Profile README best practices:
```markdown
## Hi there 👋

I build [type of models/ecosystem description].

### Featured Models

- **[Model 1](link)** — one-line description
- **[Model 2](link)** — one-line description

### Portfolio Stats

![HF Downloads](https://img.shields.io/badge/dynamic/json?...)
```

## Publisher Analytics

The HF Hub provides a Publisher Analytics dashboard at `https://huggingface.co/publisher-analytics` that shows:

- Total downloads across all your repos
- Per-repo download trends (time-series chart)
- Search/filter by repo name
- CSV export of all analytics

**Use Publisher Analytics to measure discoverability:**

1. Track which repos get the most **organic** vs linked traffic
2. Identify repos with **high downloads but low likes** (usage without social engagement)
3. Identify repos with **high likes but low downloads** (social proof without usage — good review but needs better search presence)
4. Export CSV for trend analysis over time

## Programmatic SEO Checks

### Verify your model card's meta tags:

```bash
# Fetch a model page and extract SEO-relevant meta tags
curl -s "https://huggingface.co/{author}/{repo}" | python3 -c "
import sys, re
html = sys.stdin.read()
for tag in re.findall(r'<meta[^>]+>', html):
    if any(x in tag.lower() for x in ['og:', 'twitter:', 'description', 'title']):
        print(tag)
"
```

### Check your model's ranking in search results:

```bash
# Search for your model by tag/name
hf models list --search "your model keyword" --limit 20

# Check your position in the results
hf models list --search "tool-calling" --limit 50 | grep -n "your-model-id"
```

### Verify tags are being indexed:

```bash
# Fetch model API data and check tags
curl -s "https://huggingface.co/api/models/{author}/{repo}" \
  -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Tags:', d.get('tags', []))
print('Pipeline:', d.get('pipeline_tag', 'N/A'))
print('Downloads:', d.get('downloads', 0))
print('Likes:', d.get('likes', 0))
"
```

## Reference — Verified API Behavior

| Endpoint | Response format | SEO-relevant fields |
|----------|----------------|---------------------|
| `GET /api/models?search={q}` | `[{modelId, downloads, likes, trendingScore, pipeline_tag, tags, createdAt}]` | `trendingScore` (ranking), `tags` (discoverability), `downloads` (popularity) |
| `GET /api/models?author={user}` | `[{modelId, downloads, likes, ...}]` | All metadata for portfolio |
| `GET /api/models?sort=downloads&direction=-1` | Same list, sorted by downloads | Default sort — favors established models |
| `GET /api/models?sort=createdAt&direction=-1` | Same list, newest first | Favors new releases |
| `hf models list --sort trending_score` | TSV output via CLI | Trending sort (not available via REST API) |
| `GET /api/trending?type=model` | `{recentlyTrending: [{repoData: {id, downloads, likes, ...}, repoType}]}` | Trending models (limit 20 max) |

## Reference Files

- `references/verified-og-tag-behavior.md` — Live-captured OG/Twitter tag data from a real model page (verified 2026-07-30). Raw HTTP headers, tag structure, thumbnail server behavior.

## References

- [HF Hub Model Cards docs](https://huggingface.co/docs/hub/en/model-cards)
- [HF Hub Model Card Metadata Spec](https://huggingface.co/docs/hub/en/model-card-metadata)
- [HF Hub Pipeline Tags](https://huggingface.co/docs/hub/en/models-pipeline)
- [HF Publisher Analytics](https://huggingface.co/publisher-analytics)
- [HF Hub Models API](https://huggingface.co/docs/hub/en/api)
- [Open Graph Protocol](https://ogp.me/)
- [Twitter Card docs](https://developer.twitter.com/en/docs/twitter-for-websites/cards/overview/abouts-cards)
