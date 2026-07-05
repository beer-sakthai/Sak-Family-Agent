# Instagram API: File Hosting Reference

## Background

Instagram's Graph API does NOT accept local file paths, `data:` URIs, or private URLs. When using `INSTAGRAM_POST_IG_USER_MEDIA` with an `image_url` parameter, the URL must point to a **publicly accessible** image that Instagram's servers can fetch directly — no auth headers, no session cookies, no redirect chains.

## Tested Hosting Services

| Service | Works? | Notes |
|---------|--------|-------|
| **uguu.se** | ✅ Yes | Upload via `curl -F "files[]=@file.png" https://uguu.se/upload`. Returns `{"success":true,"files":[{"url":"https://n.uguu.se/xxx.png"}]}`. Serves raw image with correct `Content-Type`. Free, no auth needed. |
| **filebin.net** | ⚠️ Partial | Upload works but the URL returns a 302 redirect to S3, which Instagram may reject. The final S3 URL has query params (signed) which Instagram's API does not support. Avoid if possible. |
| **catbox.moe** | ❌ Broken | Returns "Invalid uploader" with curl. Requires a registered user-agent. |
| **0x0.st** | ❌ Broken | Uploads disabled due to AI botnet spam. |
| **imgbb** | ❌ Broken | API key required and may require paid tier. |
| **sm.ms** | ❌ Broken | Returns 308 permanent redirect (cloudflare). |
| **transfer.sh** | ❌ Broken | Timed out during tests. |

## Recommended Workflow

1. Upload the image to uguu.se first.
2. Capture the returned `url` from the response.
3. Verify the URL returns `200 OK` and `Content-Type: image/png` (or `image/jpeg`).
4. Pass that URL as `image_url` to `INSTAGRAM_POST_IG_USER_MEDIA`.
5. URL-encode the caption with `urllib.parse.quote()` before sending.

## Fallback (when no file hosting works)

If ALL public file hosts are unavailable:

1. Generate assets locally (Pillow cards, caption text, hashtags)
2. Save as files in a deliverable directory (`ig-card.png`, `ig-caption.txt`, `hashtags.txt`, `reddit-post.md`)
3. Deliver the files to Beer as downloadable assets so they can post manually

This was tested and confirmed working on 2026-07-04.
