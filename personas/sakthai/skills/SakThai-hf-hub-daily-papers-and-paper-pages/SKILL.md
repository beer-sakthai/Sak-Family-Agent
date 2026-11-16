---
name: SakThai-hf-hub-daily-papers-and-paper-pages
version: 1.0.0
description: Complete deep-dive reference on Hugging Face Daily Papers and Paper Pages
  ecosystem, APIs, linking papers to models/datasets, and research discovery workflows.
category: mlops
tags:
- api
- arxiv
- daily
- daily-papers
- hf
- hub
- huggingface
- pages
- paper
- paper-pages
- papers
- research
author: SakThai
license: MIT
---

# HF Hub Daily Papers & Paper Pages Ecosystem

Programmatic reference for querying, browsing, and linking research publications on Hugging Face Hub Daily Papers.

## Overview

Hugging Face provides dedicated REST API endpoints for Daily Papers and Paper Pages (`/api/daily_papers`, `/api/papers/{arxivId}`). These endpoints allow agents to track state-of-the-art research, identify community upvotes, and associate papers with models and datasets.

## Key API Endpoints

| Endpoint | Method | Purpose |
|:---|:---|:---|
| `/api/daily_papers` | GET | List latest submitted daily papers (up to 50 entries). |
| `/api/daily_papers?date=YYYY-MM-DD` | GET | Filter daily papers for a specific date. |
| `/api/papers/{arxivId}` | GET | Retrieve metadata, authors, abstract, and linked Hub repos for a paper. |
| `/api/papers?sort=upvotes` | GET | Browse papers sorted by community upvotes. |

## Querying Daily Papers via Python

```python
import requests

def fetch_top_daily_papers(limit=10):
    url = "https://huggingface.co/api/daily_papers"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    papers = response.json()
    return [
        {
            "id": p["paper"]["id"],
            "title": p["paper"]["title"],
            "upvotes": p["paper"].get("upvotes", 0),
            "summary": p["paper"].get("summary", "")[:200] + "..."
        }
        for p in papers[:limit]
    ]
```

## Linking Papers to Models & Datasets

Add an `arxiv` tag in the model card YAML header:
```yaml
---
tags:
  - arxiv:2401.12345
---
```
Once pushed, the Hugging Face Hub automatically bidirectionally links the model repository with the paper page (`hf.co/papers/2401.12345`).

## References
- Full API schema and Svelte state scraping details: [`references/hf-learnings.md`](./references/hf-learnings.md).
