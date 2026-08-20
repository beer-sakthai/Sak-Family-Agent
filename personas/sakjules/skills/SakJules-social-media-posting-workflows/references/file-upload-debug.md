# File Upload Debugging — Why Local Paths Don't Work

## The Two-Sandbox Problem

Hermes and Composio run in **separate sandboxes**:

| Sandbox | Root Path | Purpose |
|---------|-----------|---------|
| **Hermes** | `/opt/data/profiles/saksit/` | Main agent session, file generation, editing |
| **Composio remote** | `/mnt/files/` | Composio MCP execution, API calls, Google Drive upload |

**Key fact:** Files in `/opt/data/` are NOT visible in `/mnt/files/`. They’re on different hosts, different sessions.

---

## Why `image_file.s3key` Fails

- `s3key` format: `47563/gmail/GET_ATTACHMENT/response/12345`
- This is a **reference to a previous tool’s output**, not a local path
- Example: `gmail-get_attachment` writes to `/mnt/files/...` and returns `s3key`
- If you pass `"/opt/data/profiles/saksit/saksit_post_img_v2.png"` as `s3key`, Composio looks in `/mnt/files/...` → **no such file** → `Failed to retrieve uploaded file content`

---

## The Fix (Three Paths)

### Path A: Public HTTPS URL (fastest)

1. Upload local image to public host (Imgur, GitHub Gist, etc.)
2. Get raw URL: `https://raw.githubusercontent.com/.../image.png`
3. Use `image_url` instead of `image_file`

### Path B: LinkedIn upload workaround (slow, needs curl)

1. `LINKEDIN_REGISTER_IMAGE_UPLOAD` → get `upload_url` + `asset_urn`
2. **Manually** run: `curl -X PUT -H "Content-Type: image/png" --data-binary @localsource "$upload_url"`
3. Use `asset_urn` in Instagram/LinkedIn post

### Path C: Text-only fallback (guaranteed pass)

Post text-only. User adds image in app.

---

## Quick Decision Tree

```
Post caption + image?
   ├─ Image already has public HTTPS? → YES → use image_url
   ├─ Local file only? → Is user okay with text-only?
        ├─ YES → post text-only now
        └─ NO → upload to public host (GitHub Gist) → get URL → post
```

---

## Debug Checklist

If `COMPOSIO_MULTI_EXECUTE_TOOL` fails with file errors:

1. **Check error message**
   - `Missing: {'image_file.s3key'}` → passed filename, not s3key
   - `Failed to retrieve uploaded file content` → s3key doesn’t exist in `/mnt/files/`
   - `File does not exist in storage, may have expired` → previous tool didn’t write output

2. **Verify sandbox path**
   ```bash
   # In Hermes:
   ls /opt/data/profiles/saksit/saksit_post_img_v2.png  # should exist

   # In Composio sandbox (via COMPOSIO_REMOTE_WORKBENCH):
   os.listdir("/mnt/files")  # won't show Hermes files
   ```

3. **Never pass local path as s3key**
   - ❌ `image_file: {name: "x.png", s3key: "/opt/data/..."}`
   - ✅ `image_url: "https://raw.githubusercontent.com/..."`

---

## Related

- `saksit-social-media-posting-workflows/SKILL.md` — main posting playbook
- `skill:hermes-agent` — Hermes architecture, sandbox layout
