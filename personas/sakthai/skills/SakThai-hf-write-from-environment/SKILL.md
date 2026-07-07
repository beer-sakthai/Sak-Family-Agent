---
name: SakThai-hf-write-from-environment
category: hermes
description: Guidance for writing files to Hugging Face Hub when standard library
  upload path fails, including write-token verification, repo creation via HF API,
  and upload troubleshooting.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    related_skills: []
    source: hermes:hf-write-from-environment
---

# HF write-from-environment

Use when `huggingface_hub` is unavailable but HF write is still required from a constrained environment.

## Approach

1. Verify token role via `https://huggingface.co/api/whoami-v2`.
2. Create repo via `POST https://huggingface.co/api/repos/create` with `{"type":"dataset"}`.
3. Use HF Hub upload path: `https://huggingface.co/api/datasets/<user>/<repo>/upload/main/<file>`.

## Pitfalls

- A valid **write token** can still return `401` on direct API calls if the exact call path is wrong or if token scope differs at the edge.
- Missing `huggingface_hub` locally blocks the clean client path; environment upload via `python -c '...'` can still work.
- Terminal command dumps can expose tokens in logs; avoid showing full auth commands.
