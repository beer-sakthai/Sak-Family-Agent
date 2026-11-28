# HF Hub Model Card SEO & Social Meta Tags Optimization Guide

This reference documents the exact mechanics of search engine indexing, Open Graph tags, badge generation, and social thumbnail behavior for Hugging Face Hub repos.

---

## 1. Hub Search & Social Preview Mechanics

Every HF model, dataset, and Space generates standard Open Graph tags:
```html
<meta property="og:title" content="{Author}/{RepoName} · Hugging Face" />
<meta property="og:description" content="We're on a journey to advance and democratize artificial intelligence..." />
<meta property="og:image" content="https://cdn-thumbnails.huggingface.co/social-thumbnails/models/{Author}/{RepoName}.png" />
<meta name="twitter:card" content="summary_large_image" />
```

### Critical SEO Realities
1. **Generic Meta Description**: Hugging Face auto-generates `og:description` from the site default tagline, not your README.
2. **Title & Tags Drive Discovery**: Repo title, `tags` in YAML frontmatter, and `pipeline_tag` are the primary ranking factors in Hub search.
3. **Thumbnail Generation**: Hugging Face auto-generates dynamic thumbnails showing download and like counts.

---

## 2. Model Card Optimization Checklist

- **Pipeline Tag**: Always declare canonical task (`text-generation`, `image-text-to-text`, `text-to-speech`).
- **Base Model Reference**: Tag exact base model (`base_model: Qwen/Qwen2.5-Coder-7B-Instruct`).
- **License**: Explicit SPDX identifier (`license: apache-2.0` or `mit`).
- **Datasets & Languages**: Declare `datasets:` and `language:` arrays for indexation in HF filtering.
- **Dynamic Badges**: Include live download, like, and model size shields.
