---
license: mit
language:
  - en
pretty_name: SimpleToolCalling (archived)
tags:
  - sakthai
  - house-of-sak
  - tool-calling
  - function-calling
  - synthetic
  - seed-data
  - deprecated
  - model:Nanthasit/sakthai-context-0.5b-tools
  - model:Nanthasit/sakthai-context-0.5b-tools-sft
  - model:Nanthasit/sakthai-context-0.5b-tools-sft-grpo
  - model:Nanthasit/sakthai-context-1.5b-tools
  - model:Nanthasit/sakthai-context-1.5b-tools-v2
  - model:Nanthasit/sakthai-context-7b-tools
  - model:Nanthasit/sakthai-context-7b-tools-grpo
task_categories:
  - text-generation
task_ids:
  - tool-use
annotations_creators:
  - machine-generated
language_creators:
  - machine-generated
multilinguality:
  - monolingual
size_categories:
  - n<1K
source_datasets:
  - original
---

[![Download dataset](https://img.shields.io/badge/Download_dataset-Nanthasit%2FSimpleToolCalling-yellow)](https://huggingface.co/datasets/Nanthasit/SimpleToolCalling)

# SimpleToolCalling — ARCHIVED (no data files hosted)

> **⚠️ DEPRECATED — ARCHIVED 2026-07-31.** This repository is kept for
> provenance and license continuity only. It hosts **no data files** — the
> repo contains just this card and the MIT license. Do not train on this
> dataset; use the live successors listed below.

**Verification:** Datasets Server `/is-valid` shows `viewer: false` and `/splits`
returns `No (supported) data files found`, confirming no hosted data.

## Dataset Summary

SimpleToolCalling was the first seed dataset for structured tool-calling data in
the SakThai model family. It is retained for provenance and license continuity
only; the actual data lives in successor datasets.

## Loading

This repo has no data files, so `load_dataset()` is not applicable. Use the Hub
file APIs to inspect the repo metadata:

```python
from huggingface_hub import HfApi

api = HfApi()
files = api.list_repo_files("Nanthasit/SimpleToolCalling", repo_type="dataset")
print(files)
```

## Splits

| Split | Rows | Notes |
|:------|-----:|:------|
| *(none)* | 0 | No data files hosted |

## Usage

Do not use this dataset for training. See the live successors below.

## Related

- **Live data:** [sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6), [sakthai-combined-v7](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7)
- **Models:** [SakThai Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)

## License

MIT

## Citation

```bibtex
@misc{simple-tool-calling,
  title  = {SimpleToolCalling},
  author = {Beer / Nanthasit},
  year   = {2026},
  url    = {https://huggingface.co/datasets/Nanthasit/SimpleToolCalling}
}
```

## Verified Snapshot

Live Datasets Server state at time of last update:

```
preview=false, viewer=false, search=false, filter=false, statistics=false
splits=No (supported) data files found
repo_files=["README.md", "LICENSE"]
```
