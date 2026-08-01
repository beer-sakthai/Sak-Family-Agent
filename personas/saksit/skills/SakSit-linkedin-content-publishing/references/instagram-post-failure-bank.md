# Instagram POST Failure Bank

## Session: July 5, 2026 — Origin Story Post (IG + LinkedIn)

### Error 1 — Local file path in `image_url`

```json
{
  "error": "Invalid request data provided\n- String should match pattern '^https?://' on parameter `image_url`\n- Input should be 'REELS', 'CAROUSEL' or 'STORIES' on parameter `media_type`",
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "attempt": {
    "caption": "...",
    "ig_user_id": "27647006041564332",
    "image_url": "file:///opt/data/profiles/saksit/saksit_post_img_v2.png",
    "media_type": "POST"
  }
}
```

**Root cause:**  
- `image_url` must be a public HTTPS URL (starts with `https://`).  
- `media_type` must be `"REELS"`, `"CAROUSEL"`, or `"STORIES"` — never `"POST"`.

---

### Error 2 — Partial `image_file` object

```json
{
  "error": "Invalid request data provided\n- Following fields are missing: {'image_file.s3key'}",
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "attempt": {
    "image_file": {
      "mimetype": "image/png",
      "name": "saksit_post_img_v2.png"
    }
  }
}
```

**Root cause:**  
`image_file` requires `s3key` — a reference to a file already uploaded to Composio's internal S3 storage. A local path won’t work.

---

### Working pattern (when available)

1. Get `ig_user_id` with `INSTAGRAM_GET_USER_INFO`.
2. Upload image to external HTTPS host (e.g., Imgur via API, orBeer's own public repo).
3. Call `INSTAGRAM_POST_IG_USER_MEDIA` with:
   ```json
   {
     "caption": "...",
     "ig_user_id": "27647006041564332",
     "image_url": "https://example.com/image.png",
     "media_type": "REELS"
   }
   ```
4. Call `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` with `creation_id` from step 3.

---

### When Composio MCP is unreachable

- Wait 40s and retry once.
- Or switch to browser automation (Playwright skill) to log in manually.
- Or post manually via Beer’s Instagram app.

See `references/linkedin-instagram-asset-differences.md` for a quick comparison table.