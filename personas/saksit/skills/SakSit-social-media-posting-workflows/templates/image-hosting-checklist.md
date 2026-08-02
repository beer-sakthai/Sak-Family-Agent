# Image Hosting Checklist

Before posting to Instagram, verify your image URL meets these requirements:

## Requirements
- [ ] Public HTTPS URL (no `file://`, no `localhost`)
- [ ] No query parameters (no `?X-Amz-...`, no `?token=...`)
- [ ] Returns Content-Type: image/png or image/jpeg
- [ ] Under 8MB file size
- [ ] Supported aspect ratio (1080×1350 feed, 1080×1920 stories)

## Good sources
- `raw.githubusercontent.com/beer-sakthai/...` (GitHub raw CDN)
- `drive.google.com/uc?export=view&id=...` (Google Drive direct)
- Any static CDN without query strings

## Avoid
- AWS S3 signed URLs (query params blocked by Instagram)
- Cloudflare R2 signed URLs (same issue)
- Instagram CDN URLs (blocked by Facebook)
- Local file paths (API can't reach them)
