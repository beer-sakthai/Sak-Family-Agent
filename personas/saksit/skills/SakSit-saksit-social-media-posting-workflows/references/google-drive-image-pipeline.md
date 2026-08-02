# Google Drive → Instagram Image Pipeline

When Beer creates his own image and supplies it via Google Drive for Instagram posting.

## Flow

1. **Connection pre-flight** — verify Composio MCP, Supermemory, and Google Drive connections are all active
2. **Find the file** — search Drive by filename or list recent files
3. **Get it accessible** — either:
   - Use `GOOGLEDRIVE_GET_FILE` to retrieve metadata
   - Make file shareable (anyone with link) to get a public URL
   - Or download it if the file is local (sent via Telegram)
4. **Check dimensions** — Instagram portrait needs 1080×1350 (4:5). If landscape, ask Beer if he wants to crop or add bars
5. **Upload to Composio sandbox** — the image must reach the Composio workbench (isolated from local filesystem)
6. **Two-step Instagram publish:**
   - `INSTAGRAM_POST_IG_USER_MEDIA` — creates container with image + caption
   - `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` — publishes using returned `creation_id`
7. **Verify** — call `INSTAGRAM_GET_IG_USER_MEDIA` (limit=10) to confirm post is in the feed
8. **Verbal playback** — describe the image content and read the caption aloud to Beer

## Key details

- Instagram API does 2-step publish (container → publish), NOT 1-step
- Caption must be URL-encoded with `urllib.parse.quote()`
- Hashtags (`#`) must be `%23`
- Image URL must be a stable, directly-fetchable public URL with proper Content-Type
- Composio sandbox cannot read local filesystem — always use `upload_local_file()` inside workbench
- 25 API posts per 24-hour limit on Instagram
