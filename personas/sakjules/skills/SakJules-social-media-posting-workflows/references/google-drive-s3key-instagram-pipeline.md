# Google Drive → s3key → Instagram Posting Pipeline

**Confirmed working:** 2026-07-07
**Session context:** House of Sak architecture post to @beerthaish

## The Problem

Instagram's `INSTAGRAM_POST_IG_USER_MEDIA` requires images via either:
- `image_url` — a clean public HTTPS URL with NO query parameters
- `image_file` — a Composio internal S3 reference (`s3key`)

Google Drive download links always include query parameters (?id=...&export=download), so they fail on `image_url`. The `GOOGLEDRIVE_DOWNLOAD_FILE` returns an `s3url` (a signed S3 URL with query params), but the **path portion** of this URL can be extracted and used as the `s3key` for `image_file`.

## Full Pipeline (confirmed working)

### Step 1: Find the image in Drive
```bash
GOOGLEDRIVE_FIND_FILE
  q: "mimeType contains 'image/' and trashed = false"
  OR
  q: "name contains '<keyword>'"
  folder_id: "<folder-id>"  # optional, scope to a specific folder
```

### Step 2: Download via authenticated API
```json
{
  "tool_slug": "GOOGLEDRIVE_DOWNLOAD_FILE",
  "arguments": {
    "fileId": "<file-id-from-step-1>"
  }
}
```

Response structure:
```json
{
  "id": "<file-id>",
  "name": "<filename.png>",
  "mimeType": "image/png",
  "downloaded_file_content": {
    "name": "<filename.png>",
    "mimetype": "image/png",
    "s3url": "https://temp.bucket.r2.cloudflarestorage.com/<account-id>/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/<hash>?X-Amz-Algorithm=...&X-Amz-Signature=..."
  }
}
```

### Step 3: Extract s3key from s3url

The s3url format is:
```
https://temp.<bucket>.r2.cloudflarestorage.com/<ACCOUNT_ID>/<TOOLKIT>/<TOOL_SLUG>/response/<HASH>?X-Amz-...
```

The s3key is the path **after the leading slash**:
```
<ACCOUNT_ID>/<TOOLKIT>/<TOOL_SLUG>/response/<HASH>
```

Python extraction:
```python
from urllib.parse import urlparse
parsed = urlparse(s3url)
s3key = parsed.path.lstrip('/')
# Result example: "631637/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/a7307c1dd7a7f95ff8e7f3eef21e9cf0"
```

### Step 4: Create Instagram container
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "caption": "Your caption here...",
    "image_file": {
      "name": "<filename-from-drive>",
      "mimetype": "image/png",
      "s3key": "<extracted-s3key>"
    }
  }
}
```

### Step 5: Publish
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "creation_id": "<container-id-from-step-4>",
    "max_wait_seconds": 60
  }
}
```

## Key Facts

| Fact | Detail |
|------|--------|
| **s3key expiry** | The signed s3url expires in ~3600s, but the s3key reference persists as long as Composio retains the file |
| **Instagram ig_user_id** | 27647006041564332 (Beer's Business account) |
| **Drive account to use** | `googledrive_firk-topper` (default, beernanthasit@gmail.com) |
| **Image format** | PNG confirmed working; JPEG should also work with `mimetype: "image/jpeg"` |
| **Caption length** | Max ~2200 chars for Instagram |
| **Rate limit** | 25 API-published posts per 24h window |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `downloaded_file_content` missing from response | File is a Google Workspace doc (not a direct image) | Use `GOOGLEDRIVE_EXPORT_GOOGLE_WORKSPACE_FILE` instead |
| s3key fails with 400 | Extracted key includes leading `/` or bucket name | Strip leading `/` from path, use everything after bucket |
| Instagram 400 "invalid media" after submission | Container still processing | Wait 30-60s before publish, or increase `max_wait_seconds` |
