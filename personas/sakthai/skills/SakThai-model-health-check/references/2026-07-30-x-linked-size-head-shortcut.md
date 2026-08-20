# `x-linked-size` HEAD shortcut for Xet GGUF files

## Problem

HF API returns `size: null` for all LFS/Xet-backed sibling files in `/api/models/{id}`.
The tree endpoint (`/api/models/{id}/tree/main`) also returns `null` for weight blobs.
Following the full CAS redirect chain with `curl -sIL` works but makes 3+ requests.

## Solution

A single `HEAD` request returns `x-linked-size` in the response headers for Xet-backed
files. No redirect following needed.

```bash
curl -sI -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/sakthai-coder-1.5b/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
```

Key header returned:

```
x-linked-size: 1117320768
x-linked-etag: "cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046"
x-repo-commit: 6878af60d00ab587c1cceadfc532ef5dd86bf2f5
```

## Advantages over `curl -sIL` redirect chain

| Approach | Requests | Time |
|----------|----------|------|
| `HEAD` → `x-linked-size` | 1 | ~0.3s |
| `curl -sIL` → follow 302 → CAS → Content-Length | 3+ | ~1.5s |

## Caveats

- `x-linked-size` appears only on Xet-backed repos, not plain LFS.
- `Content-Length` on a HEAD response will be small (the redirect page body), not the file.
- Use `x-linked-size` when available; fall back to `curl -sIL | grep content-length | tail -1` for plain LFS.
- Confirmed working 2026-07-30 on `Nanthasit/sakthai-coder-1.5b` (GGUF, 1.04 GB).

## See also

`SKILL.md` → "Xet/CAS storage — definitive file-size extraction" section.
