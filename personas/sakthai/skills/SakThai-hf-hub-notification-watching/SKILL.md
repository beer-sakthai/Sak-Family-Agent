---
name: SakThai-hf-hub-notification-watching
description: "name: SakThai-hf-hub-notification-watching"
---

# Hugging Face Hub Notifications & Watching System

## Overview
Complete reference for the Hugging Face Hub's notification and watching system — covering the web UI features, REST API endpoints (`/api/notifications`), and how to programmatically manage notifications. The watching system allows users to follow repos, users, and organizations for activity updates.

## Notification Types
By default, you receive a notification when:
- Someone mentions you in a discussion/PR
- A new comment is posted in a discussion/PR you participated in
- A new discussion/PR or comment is posted in a repo belonging to a watched user/org
- Someone replies to your posts, blog articles, or paper pages

Delivery channels: **Email** and **Web** (both on by default; configurable in settings)

## REST API (`/api/notifications`)

### Authentication
Bearer token auth via `Authorization: Bearer <hf_token>` header.

### GET — List Notifications
```
GET /api/notifications?limit=20&start=0&type=repo&read=false
```

**Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max results (default: 20) |
| `start` | int | Pagination offset |
| `type` | str | Filter: `repo`, `discussion`, `mention`, `all` |
| `read` | bool | Filter by read status |

**Response:**
```json
{
  "notifications": [
    {
      "updatedAt": "2026-07-06T00:10:15.474Z",
      "read": true,
      "discussionEventId": "abc123",
      "repo": {
        "name": "user/repo-name",
        "type": "dataset"
      },
      "type": "repo",
      "discussion": {
        "id": "abc123",
        "num": 1,
        "title": "[bot] Conversion to Parquet",
        "status": "open",
        "isPullRequest": false,
        "participating": [
          {"_id": "...", "user": "username", "avatar": "https://..."}
        ]
      }
    }
  ],
  "count": { "view": 5, "all": 10, "unread": 2 },
  "start": 0
}
```

### POST — Mark as Read
```
POST /api/notifications/mark-as-read
Content-Type: application/json

{ "discussionIds": ["id1", "id2"] }
```
- With `{}` (empty body), marks ALL notifications as read
- With specific `discussionIds`, marks only those
- Returns `{"success": true}`

### DELETE — Delete/Clear Notifications
```
DELETE /api/notifications?applyToAll=true
```
- With `?applyToAll=true`, deletes ALL notifications
- With body `{"discussionIds": ["id1"]}`, deletes specific ones
- Returns `{"success": true}`

## Watching Users, Orgs, and Repos

### Web UI (only method — not available via API token)
The watching feature is a **web-only** UI feature managed through Svelte frontend components. There is no `huggingface_hub` Python library method for watching/unwatching.

**How to watch:**
1. **User/Org profiles** — Click "Watch repos" button on their HF profile
2. **Individual repos** — Use the Watch/unwatch toggle on the repo page
3. **Settings page** — Add/remove watched users/orgs at `https://huggingface.co/settings/notifications`

**Default behavior:** You automatically watch all organizations you are a member of.

### Internal Endpoints (cookie-based auth only)
- `GET /api/watching` — Returns watched users/orgs (requires web session cookie)
- The `/api/watching` endpoint does **not** accept Bearer token auth — only cookie-based web session auth

## Muting

### Mute a Repository
From the repo's contextual menu → "Mute notifications"
- Prevents all notifications from that repo
- Exception: direct mentions and participation still notify
- Unmute via same menu → "Unmute notifications"
- Muted repos list visible in notification settings

### Mute a Discussion or PR
Click the mute icon in the discussion/PR header
- Prevents ALL further notifications from that discussion/PR (including direct mentions)
- Unmute by clicking the same icon again

## Notification Settings
Configure at `https://huggingface.co/settings/notifications`

**Per-activity-type channel configuration:**
| Activity Type | Default Channels |
|--------------|-----------------|
| Direct mentions | Email + Web |
| Participation replies | Email + Web |
| Watched user/org activity | Email + Web |

**Additional settings:**
- Quick search to add users/orgs to watch list
- Checkbox to unsubscribe from specific users/orgs
- List of muted repositories with unmute button

## Integration with Webhooks
For programmatic notification handling, use the **webhook system** instead:
```python
from huggingface_hub import HfApi
api = HfApi()

webhook = api.create_webhook(
    url="https://my-server.com/webhook",
    watched=[{"type": "repo", "name": "user/repo-name"}],
    domains=["repo", "discussion"],
    secret="my-secret"
)
```
Webhooks trigger on repo/discussion events and can call URLs or run Jobs.

## Key Limitations
- **No Python library support:** `huggingface_hub` v1.24.0 has no `watch/unwatch/notification` methods
- **Watching is web-only:** The `/api/watching` endpoint requires cookie-based auth, not Bearer token
- **No fine-grained event filtering:** Webhook system is the only way to get specific event types programmatically
- **Notification retention:** Notifications are stored until manually deleted via web UI or DELETE API

## Usage Patterns

### Poll for Notifications (cron-friendly)
```python
import requests
from huggingface_hub import get_token

headers = {"Authorization": f"Bearer {get_token()}"}

# Check unread count
r = requests.get("https://huggingface.co/api/notifications?limit=1", headers=headers)
count = r.json()["count"]
print(f"Unread: {count['unread']}, Total: {count['all']}")

# Get full notifications
r = requests.get("https://huggingface.co/api/notifications?read=false", headers=headers)
for n in r.json()["notifications"]:
    print(f"  {n['repo']['name']} — {n['discussion']['title']}")

# Mark all as read
requests.post("https://huggingface.co/api/notifications/mark-as-read", headers=headers, json={})

# Delete all
requests.delete("https://huggingface.co/api/notifications?applyToAll=true", headers=headers)
```

### Notification-Driven Agent Workflow
```python
# 1. Check for new notifications
r = requests.get(
    "https://huggingface.co/api/notifications?read=false",
    headers=headers
)
data = r.json()

# 2. Process each notification
for notif in data["notifications"]:
    repo_name = notif["repo"]["name"]
    discussion_id = notif["discussion"]["id"]
    title = notif["discussion"]["title"]
    
    # Take action based on notification type
    if notif["type"] == "repo":
        print(f"New activity in {repo_name}: {title}")
    
    # Mark individual notification as read
    requests.post(
        "https://huggingface.co/api/notifications/mark-as-read",
        headers=headers,
        json={"discussionIds": [discussion_id]}
    )

# 3. Delete processed notifications
requests.delete(
    "https://huggingface.co/api/notifications?applyToAll=true",
    headers=headers
)
```

## See Also
- [Webhooks API](https://huggingface.co/docs/hub/webhooks) for event-driven programmatic notification handling
- Pull Requests & Discussions API for direct discussion management

---
**author**: SakThai
**license**: MIT
**updated**: 2026-07-24
**huggingface_hub_version**: 1.24.0
**feature**: Web-only (no Python library support)
