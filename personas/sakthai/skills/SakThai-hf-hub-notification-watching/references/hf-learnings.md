# HF Learnings: Hugging Face Hub Notifications & Watching System

## 2026-07-24: hf-hub-notification-and-watching-system

### Summary
Deep dive into the Hugging Face Hub's notification and watching system — the web UI features for watching users/orgs/repos, the `/api/notifications` REST API (list, mark-read, delete), muting repositories and discussions, and notification settings. The watching feature is web-only (no Python `huggingface_hub` library support); the notifications API however works with Bearer token auth and is fully programmable.

### Key API Surface (`/api/notifications`)

**GET — List notifications:**
```
GET /api/notifications?limit=20&start=0&type=repo&read=false
```
- Params: `limit`, `start`, `type` (repo/discussion/mention/all), `read` (bool)
- Response: `{notifications: [...], count: {view, all, unread}, start}`
- Each notification: `{updatedAt, read, discussionEventId, repo: {name, type}, type, discussion: {id, num, title, status, isPullRequest, participating}}`

**POST /mark-as-read — Mark notifications as read:**
```
POST /api/notifications/mark-as-read
{"discussionIds": ["id1"]}  # specific, or {} for all
→ {"success": true}
```

**DELETE — Delete/clear notifications:**
```
DELETE /api/notifications?applyToAll=true    # all
DELETE /api/notifications  {"discussionIds": ["id1"]}  # specific
→ {"success": true}
```

### Watching Mechanism
- **Web-only feature** — no `huggingface_hub` library methods for watch/unwatch
- `/api/watching` endpoint exists but requires **cookie-based web session auth**, not Bearer token
- Watch users/orgs via "Watch repos" button on their profile, or from settings page
- Default: auto-watch all orgs you're a member of
- Watch individual repos independently of user/org watches

### Muting
- **Mute a repo:** Context menu → "Mute notifications" (exceptions: direct mentions & participation still notify)
- **Mute a discussion/PR:** Mute icon in discussion header (blocks ALL notifications including direct mentions)
- Muted repos list visible in notification settings

### Notification Settings (`/settings/notifications`)
- Per-activity-type channel config (email, web, or both)
- Quick search to add users/orgs to watch list
- Checkbox to unsubscribe from users/orgs
- Muted repos management

### Key Limitations
- No Python library support for watching/notifications in `huggingface_hub` v1.24.0
- Watching is web-only (cookie auth, not token)
- For programmable event handling, use Webhooks API instead

### Skill Created
`hf-hub-notification-watching/` — complete reference with API endpoints, web UI patterns, and usage examples.

---
