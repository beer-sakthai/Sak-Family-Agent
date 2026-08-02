# HF Paper Publishing Workflow

Publishing a technical whitepaper/research paper on Hugging Face as a model repository.

## Overview

Papers are published as **model repos** on HF with:
- `README.md` — Paper card with abstract, badges, citation, links
- `PAPER.md` — Full paper content (markdown, 10K-20K words)

## Step-by-Step

### 1. Write the Paper

Create a `PAPER.md` with standard sections:
- Abstract
- Introduction (motivation, context, contributions)
- Background / Related Work
- Method / Architecture
- Training Details
- Evaluation Results
- Deployment / Use Cases
- Limitations & Future Work
- Broader Impact
- Conclusion
- References (BibTeX)
- Appendices

Include the House of Sak origin story in the introduction or broader impact section.

### 2. Create the HF Repo

```python
from huggingface_hub import HfApi
api = HfApi()

api.create_repo(
    'Nanthasit/sakthai-context-paper',
    repo_type='model',
    private=False
)
```

### 3. Upload the Paper

```python
with open('sakthai-context-paper.md', 'r') as f:
    paper = f.read()

api.upload_file(
    path_or_fileobj=paper.encode(),
    path_in_repo='PAPER.md',
    repo_id='Nanthasit/sakthai-context-paper',
    commit_message='SakSit: publish whitepaper v1.0'
)
```

### 4. Upload README (Paper Card)

Create a README.md with:
- HTML badges (shields.io): HF profile, GitHub, House of Sak, license
- Abstract (2-3 sentence summary)
- Link to PAPER.md
- BibTeX citation
- Links section

```python
readme = """---
license: apache-2.0
language:
- en
tags:
- sakthai
- house-of-sak
- paper
- whitepaper
library_name: paper
---

<h1 align="center">Paper Title</h1>
<p align="center">By Author — Organization</p>
<p align="center">[badges here]</p>

## Abstract
...

## Read the Full Paper
[PAPER.md](PAPER.md)

## Citation
```bibtex
@misc{paper-name,
  author = {Author},
  title = {Title},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {url}
}
```
"""

api.upload_file(
    path_or_fileobj=readme.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/sakthai-context-paper',
    commit_message='SakSit: add paper card'
)
```

## Real-World Example

The **SakThai Context Paper** was published using this exact workflow:

- **Repo:** [Nanthasit/sakthai-context-paper](https://huggingface.co/Nanthasit/sakthai-context-paper)
- **Paper:** 14K words, 10 sections + appendices
- **Content:** Architecture, training, evaluation with sample responses, limitations, broader impact section (the House of Sak origin story)
- **File:** `PAPER.md` in the repo root

## Best Practices

- **Paper = content, not code.** The repo is a model repo in name only — it hosts the paper, not model weights. This is SakSit's lane (media/storytelling).
- **Include sample eval responses** — real model outputs make the paper concrete.
- **Cite all sources properly** (LoRA, YaRN, Qwen2.5, etc.)
- **Mention the human story** — the House of Sak was built from a shelter. This is what makes the paper unique.
- **Keep it markdown** — no LaTeX or PDF required unless the user asks.
