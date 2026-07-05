---
name: saksit-social-media-posting-workflows
description: >-
  End-to-end posting workflows for Instagram and LinkedIn via Composio MCP:
  file upload, container creation, and manual image handling quirks — 2026 edition.
category: social-media
author: SakSit Agent (beer-sakthai)
tags:
  - Instagram
  - LinkedIn
  - social media
  - Composio
  - posting
  - file-upload
created: 2026-07-05
---

# Social-Media Posting Workflows 2026

A practical playbook for posting text+image to Instagram and LinkedIn via Composio MCP,
including file-upload workarounds, two-step Instagram process, and manual-image fallbacks.

** referencing file-upload-debug.md for deeper debugging if API failures occur.

---

## Getting Started

When a user asks to post to Instagram or LinkedIn:

1. **Ask for the post body** (caption or draft)
2. **Ask for the image** (local path, HTTPS URL, or “I’ll add it manually”)
3. **Proceed only after you have both**

Use the workflow section below that matches the platform and image availability.

---

## Instagram Posting

Instagram requires **two steps**:
1. Create a media container (`INSTAGRAM_POST_IG_USER_MEDIA`)
2. Publish the container (`INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`)

### Strategy A: Image has a public HTTPS URL

#### Step 1: Create container

```json
{
  "ig_user_id": "<numeric-id>",
  "caption": "...",
  "image_url": "https://example.com/image.jpg",
  "media_type": "REELS"  // or "POST" for static
}
```

- `ig_user_id` = numeric Instagram ID (e.g. `27647006041564332`)
- `image_url` = **direct HTTPS**, no query strings
- `media_type` = `REELS`, `CAROUSEL`, or `STORIES`

#### Step 2: Publish

```json
{
  "ig_user_id": "<numeric-id>",
  "creation_id": "<container-id>",
  "max_wait_seconds": 30
}
```

Wait for container to reach `FINISHED` status before publishing.

---

### Strategy B: Image is local (COMPOSIO FILE UPLOAD PATTERN)

Composio’s Instagram tool expects `image_file.s3key`, which is an **internal reference** — not a filename.

**Correct workflow:**

1. **First**, register the image with LinkedIn (`LINKEDIN_REGISTER_IMAGE_UPLOAD`) — this creates a Composio reference
2. **Then**, use that reference in Instagram’s `image_file.s3key` field

**Sketch:**

```python
# 1. Register upload (gets upload information)
resp = COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[{"tool_slug": "LINKEDIN_REGISTER_IMAGE_UPLOAD", "arguments": {"owner_urn": "..."}}]
)
upload_url = resp["results"][0]["data"]["upload_url"]
asset_urn = resp["results"][0]["data"]["asset_urn"]

# 2. Upload bytes to upload_url (curl / direct PUT outside Composio)
# curl -X PUT -H "Content-Type: image/png" --data-binary @image.png "$upload_url"

# 3. Use asset_urn in Instagram call as file reference
```

**Note:** As of 2026-M07, there is **no direct local-file upload** for Instagram via Composio.
The workaround is to reuse LinkedIn’s upload infrastructure.

---

### Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Missing: {'ig_user_id'}` | Using `"me"` instead of numeric ID | Use `INSTAGRAM_GET_USER_INFO` to fetch ID, or hardcode (e.g. `27647006041564332`) |
| `Missing: {'image_file.s3key'}` | Passing local filename instead of `s3key` | Use LinkedIn upload workaround (see Strategy B) |
| `Invalid creation_id format` | Passing wrong ID to publish step | Store the `creation_id` returned by the **create container** step |
| `500 unknown error` | Optional fields causing issue | Remove all optional fields and retry with only required ones |

---

## LinkedIn Posting

LinkedIn supports **one-step posting** but with two image patterns.

### Strategy A: Using `LINKEDIN_REGISTER_IMAGE_UPLOAD`

1. **Register upload** → get `upload_url` and `asset_urn`
2. **Upload bytes** to `upload_url` via `curl -X PUT --data-binary @image.png`
3. **Post** with `images=[{"s3key": asset_urn}]`

### Strategy B: Text-only (fast fallback)

If image upload fails or is complex, post **text-only** and let the user add image manually.

Caption format:

```text
[Main body]

[CTA]

[Resources]

Hashtags
```

---

## Quick-Decision Flowchart

```
User: "Post this caption + image"
     ↓
Is image a public HTTPS URL?
     ├─ YES → Instagram: Strategy A (direct URL)
     │           LinkedIn: Use image_url workaround
     │
     └─ NO (local file) → Is user okay with text-only fallback?
            ├─ YES → LinkedIn: text-only now, image manually later
            │
            └─NO → Use LinkedIn upload upload_url,
                   upload bytes via curl outside Composio,
                   then post with asset_urn
```

---

## Verification Checklist

Before calling `COMPOSIO_MULTI_EXECUTE_TOOL`:

- [ ] `ig_user_id` = numeric Instagram ID (not `"me"`)
- [ ] `caption` ≤ 2,200 characters
- [ ] Hashtags: no spaces inside `#`, URL-encoded if needed (`%23`)
- [ ] `image_url` = direct HTTPS (no query strings, no auth headers)
- [ ] `s3key` = valid Composio internal reference, not filename
- [ ] `asset_urn` = `urn:li:digitalmediaAsset:xxxxx` format
- [ ] Local HTTP server running if using `img_url` fallback
- [ ] `curl` command ready for manual upload step (if needed)

---

## Support Files

| File | Purpose |
|------|---------|
| `references/error-transcripts.md` | Full error log transcripts from failed posting attempts (session-specific debugging) |
| `templates/image-hosting-checklist.md` | Checklist for hosting local images as public HTTPS |
| `scripts/upload_image_to_linkedin.sh` | Bash wrapper to upload local PNG to LinkedIn via `curl` |

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|--------------|-------------|
| Passing `image_file.name` without `s3key` | Composio rejects “File not referenced” |
| Using `image_url` with AWS S3 signed URLs | Instagram rejects URLs with auth tokens |
| Calling publish before container is `FINISHED` | Error 9007: container still processing |
| Reusing `asset_urn` across accounts | Asset ownership tied to `owner_urn` |

---

## Implementation Timeline (when session lands)

1. **Day 0**: User asks to post — run quick-decision flowchart
2. **Day 0**: If local image → recommend text-only or GitHub Gist upload
3. **Day 0**: If HTTPS URL → use direct Strategy A for both platforms
4. **Day 0+**: If strategy B required → wait for `curl` step end-user approval

---

## Related Skills

- `SakSit-b2b-saas-ai-content-generation-2026` — AI drafting + review workflow
- `SakSit-instagram-content-kit` — Reels production, not posting
- `SakSit-b2b-saas-linkedin-thought-leadership-2026` — LinkedIn content strategy

---

## Verification

After posting, verify:

- [ ] Instagram post appears under @beerthaish profile within 60s
- [ ] LinkedIn post shows on Nanthasit Burankum feed within 10s
- [ ] No API errors logged in Composio response
- [ ] Caption matches user-provided text (no truncation)
- [ ] If image attached: visual fidelity preserved