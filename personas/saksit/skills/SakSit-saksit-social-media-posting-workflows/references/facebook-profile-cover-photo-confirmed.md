# Facebook Profile Picture & Cover Photo — API Behavior (Confirmed 2026-07-07)

## Profile Picture (`POST /{page-id}/picture`)

- **VERDICT: WORKS** ✅
- Endpoint: `POST https://graph.facebook.com/v23.0/{page-id}/picture`
- Permission required: `pages_manage_posts` (granted by Composio OAuth)
- Method: Multipart form with `source=@image.png`
- Returns: `{"success": true}`
- Verification: Call `FACEBOOK_GET_PAGE_DETAILS` — `picture.data.is_silhouette` flips from `true` to `false`
- No additional fields needed — just source + access_token

## Cover Photo (`POST /{page-id}/cover`)

- **VERDICT: BLOCKED** ❌
- Endpoint: `POST https://graph.facebook.com/v23.0/{page-id}/cover`
- Permission required: `pages_manage_metadata` (NOT granted by current Composio OAuth)
- Error: `{"error":{"code":3,"message":"Application does not have the capability to make this API call."}}`
- Accepted params: `source=@image.png`, `offset_y=50`
- **Workaround:** Beer must set manually via Facebook UI:
  1. Go to facebook.com/{page-id}
  2. Hover cover area → "Add Cover Photo"
  3. Upload image

## Regular Photo Post (`POST /{page-id}/photos`)

- **VERDICT: WORKS** ✅
- Endpoint: `POST https://graph.facebook.com/v23.0/{page-id}/photos`
- Permission required: `pages_manage_posts` (granted)
- Method: Multipart form with `source=@image.png` + `message=caption`
- Returns: `{"id":"...photo_id...","post_id":"PageID_PostID"}`

## Key Workflow

All three operations require the same pattern:
1. Get a fresh page access token via `proxy_execute("GET", "/{page_id}", "facebook", query_params={"fields": "id,name,access_token"})`
2. Download image to sandbox filesystem
3. Use `curl -F source=@/path/to/image -F access_token={token}` to POST to the respective endpoint

## Page Access Token Notes

- Token is tied to the Composio-connected app — expires when the OAuth session expires
- Always fetch fresh each session via proxy_execute — never hardcode
- The token returned by `FACEBOOK_LIST_MANAGED_PAGES` also works but is stale after page refreshes
