# HF API: grep Extraction & File Size via Redirect-Following

**Context:** Lighter-weight alternatives to `jq` for quick HF API field checks, plus measuring model file sizes behind CDN redirects without downloading gigabytes. All patterns are tirith-safe in cron mode (no pipes to python).

## 1. grep -o for Single-Field Extraction

When you just need to check if a value exists in a JSON API response, `grep -o` is lighter than `jq` and avoids the pipe-to-interpreter block.

### Check if a filename is in the model's siblings list

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o 'health-check-context-1.5b-merged-v2.yaml' | head -1
```

Returns the filename if present, empty string if not. Exit code 0 on match, 1 on no match.

### Check if a download count is zero

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o '"downloads":0'
```

### Check if a specific tag exists

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o '"safetensors"'
```

### Check model private status

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o '"private":false'
```

### Verify file exists in siblings (for upload confirmation)

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o '.eval_results/health-check-context-1.5b-merged-v2.yaml'
```

**Limitations:** `grep -o` only works for literal string presence checks. If you need arithmetic, transformations, or nested object traversal, use the `curl -o /tmp/ + jq` or `curl -o /tmp/ + python3 -c` patterns instead (see `references/hf-api-jq-patterns.md` and `references/security-scanner-blocked-patterns.md`).

---

## 2. Model File Size via Redirect-Following

HF model files are served behind CDN redirects. Without `-L` (follow redirects), `curl -sI HEAD` returns a stub response (content-length ~1032 bytes). You must follow the redirect to get the real file size.

### Get model.safetensors file size (without downloading the file)

```bash
curl -sL -o /dev/null -w "%{http_code} %{size_download} %{content_type}" \
  "https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged-v2/resolve/main/model.safetensors" \
  -H "Authorization: Bearer $HF_TOKEN"
```

**Output:** `200 3087467144 text/plain; charset=utf-8`

- `-sL`: silent mode + follow redirects
- `-o /dev/null`: discard body (we only want metadata)
- `-w "%{http_code} %{size_download} %{content_type}"`: output format string
  - `http_code`: 200 = success (301/302 = redirect not followed)
  - `size_download`: the actual file size in bytes
  - `content_type`: MIME type

### Decode the size value

The API response's `usedStorage` field gives the **entire repo** storage, not just the model weights. The redirect-following curl gives you the exact file size of `model.safetensors` specifically.

For a 1.5B BF16 model (~1.54B parameters × 2 bytes = ~3.08 GB):
- Model file (actual): ~3,087,467,144 bytes (~2.88 GiB)
- Repo total (usedStorage): ~3,098,889,036 bytes (~2.89 GiB)

The difference is the config, tokenizer, README, and eval results files.

### Pitfall: Without -L you get the redirect stub

```bash
# ❌ WRONG — returns ~1032 bytes (redirect page)
curl -sI "https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged-v2/resolve/main/model.safetensors" \
  -H "Authorization: Bearer $HF_TOKEN" | grep -i content-length

# ✅ CORRECT — follows redirect, returns actual ~3GB size
curl -sL -o /dev/null -w "%{size_download}" \
  "https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged-v2/resolve/main/model.safetensors" \
  -H "Authorization: Bearer $HF_TOKEN"
```

### Check if model uses safetensors (by file extension)

```bash
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-merged-v2" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | grep -o 'model.safetensors'
```

Returns `model.safetensors` if present in siblings, empty otherwise.

---

## 3. Combined Health-Check Pattern

Complete single-curl health check for a model (no jq, no python pipes):

```bash
# Get model metadata + file size in one go
MODEL="Nanthasit/sakthai-context-1.5b-merged-v2"
API_DATA=$(curl -s "https://huggingface.co/api/models/$MODEL" -H "Authorization: Bearer $HF_TOKEN")
FILE_SIZE=$(curl -sL -o /dev/null -w "%{size_download}" "https://huggingface.co/$MODEL/resolve/main/model.safetensors" -H "Authorization: Bearer $HF_TOKEN")

echo "$API_DATA" | grep -o '"downloads":[0-9]*'
echo "$API_DATA" | grep -o '"likes":[0-9]*'
echo "$API_DATA" | grep -o '"private":false'
echo "File size: $FILE_SIZE bytes"
```

---

## When to Use These vs jq

| Task | Tool | Why |
|------|------|-----|
| Check if a string exists in API response | `grep -o` | No dep needed, one-liner |
| Extract a single numeric field | `grep -o` | Works when field value is known |
| Get model.safetensors file size | `curl -sL -w "%{size_download}"` | Only way to get actual size behind CDN |
| Sum, filter, transform, or group-by | `jq` or `python3 -c` | grep can't do arithmetic |
| Upload a file to HF | `uv run python3 -c "from huggingface_hub import HfApi; ..."` | Official SDK, handles auth |
| Parse nested JSON (e.g. config.something) | `python3 -c` via `curl -o + python3` | jq for simple, python for complex |

## Verified

- 2026-07-30: First use of `curl -sL -o /dev/null -w` for HF model file size (sakthai-context-1.5b-merged-v2). Discovered that without `-L`, content-length returns 1032 bytes (redirect stub) instead of the actual ~3GB.
- 2026-07-30: `grep -o` used to verify upload landed in HF siblings (tirith-safe, no pipe block since it doesn't pipe to interpreter).
