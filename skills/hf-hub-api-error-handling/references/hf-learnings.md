# HF Learnings Log — hf-hub-api-error-handling

## 2026-07-25: hf-hub-notification-and-watching-system — Hugging Face Hub Notifications, Watching & Subscriptions Complete Reference

### Summary
Complete deep-dive into the Hugging Face Hub's notification and watching system — the user-facing notifications page, notification settings (email + web channels), watching users/orgs/repos, muting repos and discussions, and the REST API endpoints that power it all. Researched official hub docs, the OpenAPI spec at `/.well-known/openapi.md`, and the notifications settings schema. This is a user-facing feature with a rich API surface that has no SDK wrapper yet — all calls go direct to the Hub REST API with HF token auth.

### Sources
- HF Hub Notifications docs: https://huggingface.co/docs/hub/en/notifications
- HF Hub Notifications Settings: https://huggingface.co/settings/notifications
- HF Hub notifications page: https://huggingface.co/notifications
- OpenAPI spec (Markdown for agents): https://huggingface.co/.well-known/openapi.md
- OpenAPI spec (JSON): https://huggingface.co/.well-known/openapi.json

---

### 1. How Notifications Work on the Hub

Notifications inform users when new activities (Pull Requests, discussions, comments) happen on models, datasets, and Spaces belonging to users or organizations the user is watching.

**Triggers (you receive a notification when):**
- Someone **mentions** you (@username) in a discussion/PR
- A new **comment** is posted in a discussion/PR you participated in
- A new discussion/PR or comment is posted in a **watched** user/org's repos
- Someone **replies** to one of your posts, blog articles, or paper pages

**Delivery channels:**
- **Web notification** — appears in the notifications page (top-right bell icon)
- **Email notification** — sent to your registered email
- Both channels are independently configurable per event type in settings

---

### 2. Notifications Page UI

Location: https://huggingface.co/notifications

**Filtering options:**
| Filter | Values | Description |
|--------|--------|-------------|
| `repoType` | dataset, model, space, bucket, kernel | Show notifications from specific repo type |
| `readStatus` | all, unread | Toggle read/unread |
| `participation` | all, participating, mentions | Show only discussions you participated in or were mentioned in |
| `repoName` | string | Filter by a specific repository |
| `postAuthor` | string | Filter by who created the post |
| `paperId` | string | Filter by paper page |
| `articleId` | string | Filter by blog article |

**Actions available:**
- **Mark as read/unread** — per notification or batch
- **Mark as done** — notifications marked done are deleted from the notification center (like Gmail archive)
- **Apply to all matching** — actions can apply to all notifications matching the current filter (like Gmail's "select all conversations that match this search")

---

### 3. Watching Users, Orgs & Repos

**By default:** You are watching all organizations you are a member of.

**Watching a user/org:**
- Click "Watch repos" button on their HF profile page
- Also manageable from notifications settings page (search bar + checkbox)

**Watching a specific repository:**
- Use the "Watch" button on any model, dataset, or Space page
- This scopes notifications to just that repo without watching the whole org/user

**Unwatching:**
- Untick the checkbox in notifications settings
- Or use the "Unwatch" button on profile/repo pages

**API watch targets** (from OpenAPI spec): `org`, `user`, `repo`

---

### 4. Muting Notifications

#### Mute a repository
Use the "Mute notifications" action in the repository's contextual menu. This prevents all new notifications for that repo EXCEPT:
- Direct mentions (@username)
- Discussions you're actively participating in

Muted repos are listed in notifications settings under "Muted repositories." Unmute anytime via the same menu.

#### Mute a specific discussion or PR
Click the mute icon in the discussion/PR header. This stops ALL further notifications from that specific discussion, **including** direct mentions. Unmute anytime by clicking the same icon.

---

### 5. Notification Settings (API Schema)

Location: https://huggingface.co/settings/notifications

Settings are updated via `PATCH /api/settings/notifications`. Each setting is a boolean controlling whether notifications are sent for that event type. Email and web channels are controlled by parallel settings:

| Setting (email_) | Setting (web_) | Description |
|---|---|---|
| `announcements` | — | Product announcements and platform news |
| `arxiv_paper_activity` | — | Activity on ArXiv paper pages you follow |
| `daily_papers_digest` | — | Daily ArXiv paper digest email |
| `discussions_participating` | `web_discussions_participating` | New comments in discussions you're part of |
| `discussions_watched` | `web_discussions_watched` | New discussions/comments in watched repos |
| `gated_user_access_request` | — | Someone requests access to your gated repo |
| `inference_endpoint_status` | — | Inference endpoint status changes |
| `launch_autonlp` | — | AutoNLP launch/status |
| `launch_spaces` | — | Space build/deploy updates |
| `launch_prepaid_credits` | — | Prepaid credits low/expiring |
| `launch_training_cluster` | — | Training cluster status |
| `org_request` | — | Organization join requests |
| `org_suggestions` | — | Org suggestions |
| `org_verified_suggestions` | — | Verified org suggestions |
| `org_suggestions_to_create` | — | Suggestions to create org |
| `posts_participating` | `web_posts_participating` | Comments on your community posts |
| `user_follows` | — | Someone follows you |
| `secret_detected` | — | Secret detected in your repo |
| `product_updates_after` | (datetime) | Receive product updates after this date |
| `api_inference_sunset` | — | API inference deprecation notices |
| `locked_out` | — | Account locked out notifications |
| `repo_release` | — | Repository release notifications |

**Note:** Email and web settings are independent — you can receive email notifications for direct mentions but only web notifications for watched discussions.

---

### 6. Notifications REST API

All endpoints require authentication via a **user access token** (fine-grained or write/read scope). There is no huggingface_hub SDK wrapper — calls go direct to `https://huggingface.co`.

#### GET /api/notifications — List notifications

```
GET https://huggingface.co/api/notifications?readStatus=unread&mention=mentions
```

**Query parameters:**
| Parameter | Type | Values | Required |
|-----------|------|--------|----------|
| `p` | integer | page number | No |
| `readStatus` | enum | `all`, `unread` | No |
| `repoType` | enum | `dataset`, `model`, `space`, `bucket`, `kernel` | No |
| `repoName` | string | repository name (e.g. `beer-sakthai/my-model`) | No |
| `postAuthor` | string | filter by author of the post | No |
| `paperId` | string | filter by paper page | No |
| `articleId` | string | filter by blog article | No |
| `mention` | enum | `all`, `participating`, `mentions` | No |
| `lastUpdate` | string | ISO datetime filter | No |

**Response:** `200` — JSON array of notification objects.

#### DELETE /api/notifications — Delete notifications

```
DELETE https://huggingface.co/api/notifications?applyToAll=true&readStatus=unread
```

**Query parameters:** Same as GET filtering params, plus `applyToAll`.

**Request body** (optional — specify specific discussion IDs to delete):
```json
{
  "discussionIds": ["24-char-hex-id-here"]
}
```

**Note:** `discussionIds` items must match `^[0-9a-f]{24}$` (24 hex characters).

#### POST /api/notifications/mark-as-read — Change read status

```
POST https://huggingface.co/api/notifications/mark-as-read?applyToAll=true&readStatus=unread
```

**Query parameters:** Same as GET filtering params, plus `applyToAll`.

**Request body:**
```json
{
  "discussionIds": [],
  "read": true
}
```
- `discussionIds`: Array of discussion IDs (optional — empty means apply to filtered set)
- `read`: `true` = mark as read, `false` = mark as unread

#### PATCH /api/settings/notifications — Update notification settings

```
PATCH https://huggingface.co/api/settings/notifications
```

**Request body:**
```json
{
  "notifications": {
    "announcements": false,
    "discussions_watched": true,
    "web_discussions_watched": true,
    "discussions_participating": false,
    "web_discussions_participating": true,
    "daily_papers_digest": false
  }
}
```

All fields are optional — only changed fields need to be sent. `"notifications"` is required.

#### PATCH /api/settings/watch — Update watch settings

```
PATCH https://huggingface.co/api/settings/watch
```

Add or remove watched users, orgs, or repos:

```json
{
  "add": [
    {"id": "beer-sakthai", "type": "user"},
    {"id": "HuggingFaceH4", "type": "org"}
  ],
  "delete": [
    {"id": "some-user", "type": "user"}
  ]
}
```

**Types:** `org`, `user`, `repo`

---

### 7. Practical Automation Patterns

Since no SDK wrapper exists for the notifications API, automation requires direct HTTP calls. A complete pattern:

```python
import httpx

HF_TOKEN = "hf_..."  # user access token with appropriate scopes
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# List unread notifications
resp = httpx.get(
    "https://huggingface.co/api/notifications",
    params={"readStatus": "unread"},
    headers=HEADERS,
)
notifications = resp.json()

# Mark all as read
httpx.post(
    "https://huggingface.co/api/notifications/mark-as-read",
    params={"applyToAll": "true", "readStatus": "unread"},
    json={"discussionIds": [], "read": True},
    headers=HEADERS,
)

# Watch a user
httpx.patch(
    "https://huggingface.co/api/settings/watch",
    json={"add": [{"id": "beer-sakthai", "type": "user"}]},
    headers=HEADERS,
)
```

**Important notes:**
- The notifications API can trigger rate limits — see `/api/settings/rate-limits` for your account's limits
- `applyToAll=true` is powerful — use with caution since it affects all matching notifications
- The `discussionIds` in DELETE endpoint are exactly 24 hex characters (MongoDB ObjectID format)
- There is no GET endpoint for watch/notification settings — only PATCH to update
- No webhook integration exists for notifications (webhooks are separate — they watch repo events, not user notifications)

---

### 8. Key Limitations & Observations

1. **No SDK support** — huggingface_hub has no `get_notifications()`, `mark_read()`, or `get_watch_settings()` methods. All notification management must go through raw HTTP.
2. **Settings are read-only through PATCH** — to read current settings, you'd need to scrape the settings page or extract from the page's client-side state (no documented GET endpoint).
3. **Email vs Web are fully independent** — you can configure deeply granular control over which events trigger email vs web notifications.
4. **Muting is repository-scoped or discussion-scoped** — there's no global "mute all notifications" toggle except disabling each notification type individually.
5. **`applyToAll` is powerful** — when `applyToAll=true` is set with a filter like `readStatus=unread`, the action applies to ALL matching notifications, not just the current page. This is the equivalent of Gmail's "Select all conversations that match this search."
6. **Notifications are user-level** — there's no org-level notification management. Each user configures their own settings.
7. **Watch settings persist** — watching a user/org means you get notifications for ALL their new repos and repo activity. This is a broad permission.
