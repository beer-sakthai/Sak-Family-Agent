# LinkedIn vs Instagram Asset Differences

## Session: July 5, 2026 — Origin Story Post

| Requirement | LinkedIn | Instagram |
|-------------|----------|-----------|
| **Image upload mode** | `images[].s3key` (Composio S3) OR presigned PUT upload + REST API | `image_url` (public HTTPS) OR `image_file.s3key` (Composio S3 only) |
| **Local file support** | ❌ No — `LINKEDIN_CREATE_LINKED_IN_POST` fails 404 with local path | ❌ No — requires HTTPS URL or `s3key` |
| **Caption length** | ≤ 3,000 chars (API limit) | No strict cap (but keep < 2,200 for UI safety) |
| **Author/IG User ID** | `"author": "urn:li:person:GR_0y0zfGl"` (person URN) | `"ig_user_id": "27647006041564332"` (numeric Business ID) |
| **Image type Allowed** | PNG, JPEG | PNG, JPEG (no query params on URLs) |
| **Media type** | N/A (image = attachment) | Must be `"REELS"`, `"CAROUSEL"`, or `"STORIES"` — **never `"POST"`** |
| **Post visibility** | `"visibility": "PUBLIC"` | N/A (visibility set at account level) |
| **Footprint** | Link preview card (1200×627 recommended) | Portrait 1080×1350 for feed/Reels |

## Key Takeaway

- **Instagram** is stricter on exact schema (`image_url` vs `image_file`, `media_type` must be enum value).  
- **LinkedIn** is more flexible on upload (can use presigned PUT, Composio s3key, or direct upload via REST).  
- Never copy-paste a LinkedIn payload into Instagram without checking `media_type` and image field types.