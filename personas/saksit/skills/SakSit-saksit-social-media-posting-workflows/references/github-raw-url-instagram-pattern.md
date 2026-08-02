# GitHub Raw URL as Instagram Media Source

Instagram's Graph API rejects media URLs with query parameters (AWS S3 signed URLs,
CDN auth tokens, etc.). The fix: host images on GitHub and use the raw URL.

## How it works

```text
Good:  https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/ig-card.png
Bad:   https://s3.amazonaws.com/bucket/image.jpg?X-Amz-Signature=abc123
```

## Requirements for the URL to work

1. **No query string** — URL must end with the file extension
2. **Public repository** — private repos return 403
3. **Direct image file** — JPEG or PNG, < 10MB
4. **raw.githubusercontent.com** domain — not github.com, not blob

## How to push images for this

### Method 1: Via Composio GITHUB_COMMIT_MULTIPLE_FILES

Use `GITHUB_COMMIT_MULTIPLE_FILES` via Composio to upsert the image file.
The file ends up at:

```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
```

**Important:** The `content` field must be the actual base64-encoded bytes of the image, NOT a file path string. Passing `/tmp/my-image.png` as content will produce garbage bytes.

### Method 2: Via GitHub REST API (for large files)

When the base64 content is too large (e.g. 112KB+ PNG), use the direct GitHub REST API with the git-credentials token. This avoids truncation issues:

```python
import base64, json, urllib.request

with open('/opt/data/.git-credentials', 'rb') as f:
    data = f.read().decode('utf-8', errors='replace')
for line in data.split('\n'):
    if 'github.com' in line and 'beer-sakthai' in line:
        token = line.split('@')[0].split(':')[2]

# Read image and encode as base64
with open('/tmp/image.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

# Get existing SHA (required for updates to existing files)
url = "https://api.github.com/repos/beer-sakthai/house-of-sak/contents/assets/stories/<filename>.png"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
req = urllib.request.Request(url, headers=headers, method="GET")
try:
    sha = json.loads(urllib.request.urlopen(req).read()).get("sha", "")
except:
    sha = ""

# Upload
body = json.dumps({"message": "add image", "content": b64, "branch": "main", **( {"sha": sha} if sha else {})}).encode()
urllib.request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="PUT")
```

## CDN Cache Propagation

GitHub's raw CDN (`raw.githubusercontent.com`) uses a caching layer. Immediately after uploading, the CDN may serve a stale or incorrect version:

- **Content-Type check:** Run `curl -sI <raw-url> | grep content-type`
- **Before cache clears:** `application/octet-stream` -- Instagram will reject with "image format not supported"
- **After cache clears:** `image/png` -- ready for Instagram use

**Wait 30-60 seconds** after upload before using the URL with Instagram. If Instagram returns "image format not supported," the CDN hasn't propagated yet -- retry after 1-2 minutes.

**Verification:** You can add `?t=<timestamp>` for cache-busting during testing, but use the clean URL (no query params) for the actual Instagram call.

## Typical repo assets

| File | Source | URL Pattern |
|------|--------|-------------|
| `ig-card.png` | Created by SakSee/SakSit | `.../house-of-sak/main/ig-card.png` |
| `og-image.png` | Website OG image | `.../house-of-sak/main/og-image.png` |

## Why this matters

Without this pattern, every Instagram post needs a public HTTP server, a paid
CDN bucket, or the complex LinkedIn upload workaround. With this pattern:
push to GitHub → raw URL → Instagram accepts it.
