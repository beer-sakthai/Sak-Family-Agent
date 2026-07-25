---
name: hf-hub-doi
author: SakThai
license: MIT
description: >
  Complete reference for Digital Object Identifiers (DOIs) on the Hugging Face
  Hub — generation process for models and datasets, DataCite integration,
  versioning (new revision = new DOI), restrictions on DOI-locked repos
  (no deletion, rename, or visibility change without support request),
  and citation workflow.
version: 1.0.0
metadata:
  hermes:
    tags: [huggingface, hub, doi, datasets, models, citation, academic, identifiers]
    category: mlops
---

# HF Hub DOI — Digital Object Identifiers

## Overview

The Hugging Face Hub offers DOI (Digital Object Identifier) generation for
models and datasets. DOIs are persistent identifiers tied to a digital object's
metadata (URL, version, creation date, description). They serve as a stable,
citable reference for ML artifacts in academic publishing — analogous to an
ISBN for books.

DOIs are managed through the **DataCite** registration agency. When you generate
a DOI for a Hub repository, your public profile name is transferred to DataCite
(you can customize the author list before generation).

## Key Features

| Feature | Description |
|---------|-------------|
| Generation | Via repo Settings page in the Hub UI — click "Generate DOI" |
| Author List | Optional customizable authorship credits before generation |
| Versioning | New revision → click "Generate new DOI" — old DOI deprecated, new one assigned |
| Locking | DOI repos cannot be deleted, renamed, or made private without HF support request |
| Visibility | DOI repos stay public permanently |
| Citation Badge | DOI badge appears in model/dataset page header after generation |
| Cost | Free (no charge for DOI generation on HF Hub) |
| Scope | Models and datasets on the Hub (not Spaces) |

## DOI Lifecycle

```mermaid
flowchart LR
    A[Create model/dataset] --> B[Settings → DOI section]
    B --> C[Click 'Generate DOI']
    C --> D[Accept DataCite terms]
    D --> E[Customize authors (optional)]
    E --> F[DOI assigned ✓]
    F --> G[New revision pushed]
    G --> H[Click 'Generate new DOI']
    H --> I[Old DOI deprecated, new DOI issued]
```

## Restrictions When DOI is Active

Once a DOI is generated for a repository:

- ❌ **Cannot delete the repository** — permanently locked
- ❌ **Cannot rename/move the repository** — `move_repo()` will fail
- ❌ **Cannot change visibility to private** — `update_repo_settings(private=True)` is blocked
- ✅ **Can still push commits** and update content
- ✅ **Can generate new DOIs** for new versions
- ✅ **Can add collaborators** with write access

To change these settings, file a support request at `website@huggingface.co`.

## Python / API Notes

The `huggingface_hub` Python library does **not** expose a DOI generation method
in `HfApi`. DOIs are generated exclusively through the Hub web UI (repo Settings
page). The Hub REST API may support DOI status queries but generation requires
the interactive DataCite consent flow.

## Zero-Cost Note

DOI generation on Hugging Face Hub is **free**. There is no charge for generating
a DOI. The only requirement is having a model or dataset hosted on the Hub.

## Sources

- HF Docs: https://huggingface.co/docs/hub/en/doi
- Announcement Blog: https://huggingface.co/blog/introducing-doi
- DataCite: https://datacite.org
