# Instagram + LinkedIn Posting Error Transcripts 2026-07-05

This document records the failures, root causes, and workarounds for hosting local images via Composio MCP.

## Session Context

- **User**: Beer (beer-sakthai)
- **Goal**: Post origin story caption + local image `saksit_post_img_v2.png` to Instagram + LinkedIn
- **Date**: 2026-07-05T15:15–15:20 UTC
- **Composio endpoint**: https://connect.composio.dev/mcp

---

## Attempt 1: Direct call with filename

### Request

```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "caption": "...",
    "image_file": {"mimetype": "image/png", "name": "saksit_post_img_v2.png"},
    "media_type": "REELS"
  }
}
```

### Response

```json
{
  "error": "Missing: {'image_file.s3key', 'ig_user_id'}",
  "status_code": 400
}
```

### Root Cause

1. `image_file` requires `s3key` — Composio’s internal file reference, **not** a filename
2. `ig_user_id` must be numeric Instagram ID (`27647006041564332`), not `"me"`

### Fix

- Use `ig_user_id: "27647006041564332"`
- Use `LINKEDIN_REGISTER_IMAGE_UPLOAD` to obtain a reference, then pass `s3key: "<urn>"`

---

## Attempt 2: Add `ig_user_id` only

### Request

```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "caption": "...",
    "ig_user_id": "27647006041564332",
    "image_file": {"mimetype": "image/png", "name": "saksit_post_img_v2.png"},
    "media_type": "REELS"
  }
}
```

### Response

```json
{
  "error": "Missing: {'image_file.s3key'}",
  "status_code": 400
}
```

### Root Cause

`image_file.s3key` is still missing — filename is not sufficient.

### Fix

Use the LinkedIn upload pattern (Strategy B below).

---

## Strategy A: Public HTTPS URL

### Pattern

```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "image_url": "https://example.com/image.png",
    "caption": "...",
    "media_type": "REELS"
  }
}
```

### Requirements

- URL **must** be public, direct HTTPS
- **No** query strings or auth headers
- **No** S3 signed URLs (Instagram rejects tokens)

### Error if violated

```json
{
  "error": "String should match pattern '^https?://'"
}
```

---

## Strategy B: LinkedIn upload workaround

### Step 1: Register upload

```json
{
  "tool_slug": "LINKEDIN_REGISTER_IMAGE_UPLOAD",
  "arguments": {
    "owner_urn": "urn:li:person:GR_0y0zfGl"
  }
}
```

### Response

```json
{
  "asset_urn": "urn:li:digitalmediaAsset:D4D22AQGxFFCV2esNmg",
  "upload_url": "https://www.linkedin.com/dms-uploads/sp/v2/.../upload?...",
  "upload_headers": {"media-type-family": "STILLIMAGE"}
}
```

### Step 2: Upload bytes (outside Composio)

```bash
curl -X PUT \
  -H "Content-Type: image/png" \
  --data-binary @/opt/data/profiles/saksit/saksit_post_img_v2.png \
  "$upload_url"
```

### Step 3: Post using `asset_urn`

Instagram still expects `s3key` — use `asset_urn` instead (Composio maps it).

LinkedIn post:

```json
{
  "tool_slug": "LINKEDIN_CREATE_LINKED_IN_POST",
  "arguments": {
    "author": "urn:li:person:GR_0y0zfGl",
    "commentary": "...",
    "images": [{"name": "saksit_post_img_v2.png", "s3key": "urn:li:digitalmediaAsset:D4D22AQGxFFCV2esNmg"}],
    "visibility": "PUBLIC"
  }
}
```

### Error if skipped

```json
{
  "error": "Missing: {'images.0.s3key'}",
  "status_code": 400
}
```

---

## Current Limitation (2026-M07)

- **Instagram** does **not** accept local file paths or federated file upload like LinkedIn
- **Only workaround** is to use LinkedIn upload infrastructure, then re-use the asset URN
- ** impractical** for one-offs — recommended fallback: text-only, user adds image manually

---

## Recommendation for Future Sessions

When user says "post both with image":

1. **Ask** if image is already a public HTTPS URL
2. If **yes** → use Strategy A (direct, instant)
3. If **no** → explain that Composio requires manual image upload (2 steps), or post text-only now
4. If user insists on image → calculate time/complexity trade-off before proceeding

**Conclusion**: For solo founders (Beer’s use case) with local files, **text-only posting first + manual image later** is the most reliable path.