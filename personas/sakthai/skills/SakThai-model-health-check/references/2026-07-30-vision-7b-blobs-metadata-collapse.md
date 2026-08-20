# GGUF-Only Vision Model: `?blobs=true` Metadata Collapse

**Date:** 2026-07-30
**Model:** `Nanthasit/sakthai-vision-7b` (LLaVA-1.5-7b GGUF Q4_K_M)

## Symptom

Fetching model info with `?blobs=true&expand[]=siblings` returned only 3 keys:
```json
{
  "_id": "6a645d87f31e79c78d907627",
  "id": "Nanthasit/sakthai-vision-7b",
  "siblings": [...]
}
```

All metadata fields absent: `downloads`, `likes`, `tags`, `cardData`, `config`, `pipeline_tag`, `library_name`, `createdAt`, `lastModified`, `usedStorage`, `gguf`.

The bare API (no query params) returned the full 2969-byte response with all fields.

## Root Cause

The HF blob-cache layer appears to short-circuit metadata population when a repo has LFS blobs but NO `safetensors` top-level key. The `?blobs=true` parameter triggers a different code path in the API that skips the metadata aggregation for repos that are not safetensors-based.

## Key Stats

| Metric | Value |
|--------|-------|
| usedStorage | 4,705,804,416 bytes (4.71 GB) |
| GGUF file | 4,081,370,080 bytes (4.08 GB) |
| mmproj file | 624,434,336 bytes (624 MB) |
| safetensors key in API | absent |
| gguf key in API | present |
| bare API response | 2,969 bytes, all fields |
| `?blobs=true` response | 1,508 bytes, stripped |

## Fix Applied

Made TWO API calls and merged data:
1. `GET /api/models/{REPO_ID}` → metadata (downloads, likes, tags, cardData, ...)
2. Both `GET /api/models/{REPO_ID}?blobs=true&expand[]=siblings` AND `GET /api/models/{REPO_ID}/tree/main` could give file sizes — used the blobs response for sizes since it DID have sibling data.

Then combined: metadata from call 1 + file sizes from call 2.

## Lesson

Do NOT trust `?blobs=true` responses for metadata on any repo that lacks a top-level `safetensors` key — regardless of `usedStorage` or actual weight content. Use base API (no query params) for metadata.
