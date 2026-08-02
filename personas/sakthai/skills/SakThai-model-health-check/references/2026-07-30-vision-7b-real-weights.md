# Vision-7b Health Check: LFS Pointer → Real Weights Transition (2026-07-30)

## Summary

`Nanthasit/sakthai-vision-7b` (LLaVA-1.5-7b, GGUF Q4_K_M) transitioned from non-functional LFS pointers
to real weight files between the previous health check and this session. The demo Space
(`Nanthasit/sakthai-vision-demo`) was also discovered to be deleted (404 from API).

## Key Delta

| Metric | Previous Check | This Check |
|--------|---------------|------------|
| GGUF weight | LFS pointer (1,050 bytes) | Real file (4,081,370,080 bytes) |
| mmproj | LFS pointer (1,038 bytes) | Real file (624,434,336 bytes) |
| Total weights | 0 bytes | 4.39 GB |
| Demo Space | Presumed active | 404 (deleted/missing) |
| Downloads | 186 | 186 (unchanged) |
| Score | 4/100 (STUB) | 70/100 (fair) |

## Detection Method

The previous health check relied on HTTP `Content-Length` from HEAD requests, which returned
LFS pointer sizes (~1 KB). This session used the `/api/models/{id}/tree/main` endpoint instead,
which always returns the LFS content size in `size + lfs.size` fields even for pointer-only
checkouts. When `lfs.pointerSize` is present and `lfs.size` is >100 MB, the file on HF is a
real weight — regardless of whether the local checkout has the pointer or the content.

## Demo Space Check

```bash
curl -s -o /dev/null -w '%{http_code}' \
  "https://huggingface.co/api/spaces/Nanthasit/sakthai-vision-demo" \
  -H "Authorization: Bearer $HF_TOKEN"
# → 404
```

The cardData still references the space in `extra.sibling` but it no longer exists.
Recommendation: re-create or remove the reference.

## YAML Construction Lessons

Building the health-check YAML via Python f-strings caused two YAML parse errors:
1. `gguf_weights: LFS_POINTER_ONLY -> REAL_WEIGHTS` — `->` broke YAML scalar parsing
2. `downloads_same: true (186)` — `true` parsed as boolean, then `(186)` was unexpected

Both fixed by quoting the values. See the skill's Pitfalls section for the full YAML quoting rules.
