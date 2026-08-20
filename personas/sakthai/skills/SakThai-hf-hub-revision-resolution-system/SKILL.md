---
name: SakThai-hf-hub-revision-resolution-system
author: SakThai
license: MIT
description: "A skill for Hf Hub Revision Resolution System."
version: 0.1.0
---

# HF Hub Revision Resolution System

**Skill:** Complete understanding of how the Hugging Face Hub resolves Git revisions (branches, tags, commit SHAs, special refs) across REST APIs, file downloads, file system operations, and local cache.

author: SakThai
license: MIT

## Overview

Every Hub repository is a Git repository. When you access content at a specific revision — a branch name (`"main"`), a tag (`"v1.0"`), a full commit hash (`"e7da7f2..."`), or a special ref (`"refs/pr/5"`) — the Hub must resolve that string to a concrete commit SHA. This resolution happens at multiple layers:

- **REST API endpoints** (`/api/models/{repo_id}/revision/{revision}`)
- **File download URLs** (`/resolve/{revision}/{filename}`)
- **File system** (`hf://` URIs with `@{revision}`)
- **Local cache** (`refs/` directory mapping names → commit hashes)

### Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `DEFAULT_REVISION` | `"main"` | Default revision when none provided |
| `REGEX_COMMIT_HASH` | `r"^[0-9a-f]{40}$"` | Detect if revision IS a commit SHA |
| `SPECIAL_REFS_REVISION_REGEX` | `r"(^refs\/convert\/\w+)\|(^refs\/pr\/\d+)"` | Match special refs that skip quoting |
| `REPO_TYPES_URL_PREFIXES` | `{"dataset": "datasets/", "space": "spaces/", "kernel": "kernels/"}` | Used in URL construction |

## Reference

- Source: `huggingface_hub/file_download.py`, `hf_api.py`, `hf_file_system.py`, `_snapshot_download.py`, `constants.py`
- Docs: https://huggingface.co/docs/hub/en/repositories
