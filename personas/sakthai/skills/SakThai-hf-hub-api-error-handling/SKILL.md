---
name: SakThai-hf-hub-api-error-handling
version: 1.0.0
description: Complete reference on error handling when working with the Hugging Face
  Hub REST API and the huggingface_hub Python library, covering status codes, X-Error-Code,
  and backoff retries.
category: mlops
tags:
- api
- error
- error-handling
- exceptions
- handling
- hf
- http-status
- hub
- hub-api
- huggingface
- retries
- retry
author: SakThai
license: MIT
---

# HF Hub API Error Handling & Exception Management

Master error handling across the Hugging Face Hub REST API, `huggingface_hub` Python SDK, and automated retry/backoff layers.

## Overview

Working with the Hugging Face Hub requires handling HTTP status codes, Hub-specific `X-Error-Code` headers, rate limits, and network anomalies gracefully. `huggingface_hub` provides a structured exception hierarchy rooted in `HfHubHTTPError`.

## Core Exception Categories

```python
from huggingface_hub.errors import (
    HfHubHTTPError,
    RepositoryNotFoundError,
    EntryNotFoundError,
    GatedRepoError,
    RevisionNotFoundError,
    OfflineModeIsEnabled,
)
```

| Exception | HTTP Status / Cause | Resolution / Handling Strategy |
|:---|:---|:---|
| `RepositoryNotFoundError` | 404 (Repo missing or private) | Verify repo ID spelling and check `HF_TOKEN` permissions. |
| `GatedRepoError` | 403 (Gated model/dataset) | Prompt user to accept terms of service on the web Hub first. |
| `RevisionNotFoundError` | 404 (Commit / Branch missing) | Verify git tag or commit hash ref on the Hub. |
| `OfflineModeIsEnabled` | Local network / env gate | Check if `HF_HUB_OFFLINE=1` is unintentionally active. |

## Production Retry Pattern

```python
import time
from huggingface_hub.utils import HfHubHTTPError

def resilient_hub_call(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except HfHubHTTPError as err:
            status = getattr(err.response, "status_code", 500)
            if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = (2 ** attempt) + 1
                time.sleep(wait)
                continue
            raise
```

## References
- Full 40+ exception hierarchy and source code analysis: [`references/hf-learnings.md`](./references/hf-learnings.md).
