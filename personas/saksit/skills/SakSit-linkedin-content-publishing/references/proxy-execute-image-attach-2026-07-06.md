# proxy_execute Image Attach — Empty Result (2026-07-06)

## Attempted flow

1. Initialized image upload via `LINKEDIN_INITIALIZE_IMAGE_UPLOAD`
   - `owner: "urn:li:person:GR_0y0zfGl"`
   - Returned: `{"image": "urn:li:image:D4D10AQGVAKsCjKSCGQ", "upload_url": "https://www.linkedin.com/dms-uploads/..."}`

2. Uploaded image bytes via curl PUT to the presigned URL
   - `Content-Type: image/jpeg`
   - HTTP 201 — upload succeeded

3. Tried posting with image via `proxy_execute("POST", "/rest/posts", "linkedin")`
   - Payload included `content.media.id = "urn:li:image:D4D10AQGVAKsCjKSCGQ"`
   - Headers: `LinkedIn-Version: 202604`, `X-Restli-Protocol-Version: 2.0.0`
   - **Result: empty** — both `result` and `error` returned as empty strings

## Conclusion

`proxy_execute` with the LinkedIn REST API returning empty strings means the connection's OAuth scope may not include the `w_member_social` permission the v2/rest/posts endpoint needs, OR the `content.media` field structure was rejected silently.

## Current reliable path

1. Post text-only via `LINKEDIN_CREATE_LINKED_IN_POST` (works)
2. Tell Beer to edit the post manually and attach the image

## Alternative path (untested)

1. Get the image into Composio's workbench sandbox
2. Call `upload_local_file()` to get an s3key
3. Pass that s3key to `LINKEDIN_CREATE_LINKED_IN_POST` via `images[]`
