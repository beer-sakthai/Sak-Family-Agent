# API Quirk: Xet-backed repos report size=0 for siblings

**Affects:** `GET /api/models/{id}` and `GET /api/datasets/{id}` — the siblings array.

## Symptom

All siblings show `"size": 0` even though the files clearly exist (confirmed by HEAD request returning 200, or by downloading successfully).

## Root Cause

Xet storage uses content-addressable chunking and does not store file metadata as Git LFS does. The `siblings[].size` field in the HF REST API is not populated for Xet-backed files. The `siblings[].lfs` field is also `null` (no LFS metadata).

## Workaround: Get actual file size

Send a HEAD request to the resolve URL and read `x-linked-size`:

```bash
curl -sI "https://huggingface.co/{REPO_ID}/resolve/main/{FILENAME}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -i x-linked-size
```

In Python:

```python
import requests
resp = requests.head(
    f"https://huggingface.co/{repo_id}/resolve/main/{filename}",
    headers={"Authorization": f"Bearer {token}"}
)
size = resp.headers.get("x-linked-size")
```

## Detection

Check if all non-trivial files have `size == 0` and `lfs is None` in the API response. If so, the repo is Xet-backed.

## Real-world example

`Nanthasit/sakthai-coder-1.5b` (2026-07-30): GGUF file showed 0 bytes in API but was actually 1,117,320,768 bytes (1.04 GB) per `x-linked-size` header.
