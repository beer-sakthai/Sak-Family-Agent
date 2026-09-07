---
name: SakThai-hf-hub-discussion-reactions-api-deep-dive
author: SakThai
license: MIT
description: "Complete deep-dive on the Hugging Face Hub Discussion Reactions API — emoji reactions on discussions, PRs, and comments with read/add/remove patterns."
version: 1.0.0
tags: [HuggingFace, Hub, Discussions, Reactions, API, Emoji, PRs]
---

# HF Hub Discussion Reactions API — Deep Dive

> **Status:** Research completed 2026-07-30 via live API exploration (microsoft/phi-4 discussions) and huggingface_hub source code analysis.
> **Skill level:** Complete reference covering read-only access, add/remove operations, data structures, and SDK gaps.

## Overview

Hugging Face Hub discussions and pull requests support **emoji reactions** — users can react to individual comments (not the top-level discussion title) with emoji like 👍, 🔥, 🚀, 👀, ❤️, 🧠, and ➕. Reactions are **not part of the huggingface_hub Python SDK** as of v0.28+ and must be called via raw REST API.

### Key Facts

- Reactions exist at the **event/comment level**, not the discussion/PR level
- Each reaction stores: the emoji character, the list of users who reacted, and a count
- Multiple reaction types can coexist on the same comment (e.g., both 👍 and 🧠)
- A single user can only add **one reaction per emoji per comment** (toggle pattern)
- Reactions are **public** — visible to anyone with read access to the repo
- No rate limit specific to reactions (uses the standard Hub API rate limits)
- **Total users field** is available in the list endpoint: `numReactionUsers` counts unique users who reacted to the discussion

## REST API Reference

### 1. Read Reactions via Discussion List

**`GET /api/{repo_type}s/{repo_id}/discussions`**

Returns discussion summaries with `topReactions` and `numReactionUsers` fields.

```json
{
  "discussions": [
    {
      "num": 21,
      "title": "Suggested tokenizer changes by Unsloth.ai",
      "status": "merged",
      "topReactions": [
        {"reaction": "🔥", "count": 13}
      ],
      "numReactionUsers": 13,
      "numComments": 12
    }
  ],
  "count": 50,
  "start": 0,
  "numClosedDiscussions": 35
}
```

**Query parameters:**
| Param | Values | Description |
|-------|--------|-------------|
| `status` | `open`, `closed`, `merged` | Filter by status |
| `author` | username | Filter by author |
| `limit` | integer (default 50) | Max items per page |

**Fields on each discussion:**
- `topReactions` — array of `{reaction: string, count: number}` — only the *first* reaction type returned (this is a summary, not all reactions)
- `numReactionUsers` — total unique users who reacted to this discussion/PR

**⚠ Limitation:** `topReactions` only shows the **most recent or first** reaction type, not all of them. For complete reaction data, use the detail endpoint.

**Python:**
```python
import requests
token = open("/path/to/huggingface/token").read().strip()
resp = requests.get(
    "https://huggingface.co/api/models/microsoft/phi-4/discussions?limit=50",
    headers={"Authorization": f"Bearer {token}"}
)
data = resp.json()
for d in data["discussions"]:
    reactions = d.get("topReactions", [])
    users = d.get("numReactionUsers", 0)
    print(f"#{d['num']} ({d['status']}): {reactions}, users={users}")
```

### 2. Read Full Reaction Data via Discussion Detail

**`GET /api/{repo_type}s/{repo_id}/discussions/{num}`**

Returns the full discussion with all `events`, each potentially containing `reactions` in its `data` field.

```json
{
  "events": [
    {
      "id": "67814e761c244e2a4b53ecdb",
      "type": "comment",
      "author": { "name": "gugarosa", "fullname": "Gustavo de Rosa" },
      "createdAt": "2025-01-10T16:44:38.000Z",
      "data": {
        "latest": {
          "raw": "No description provided.",
          "html": "..."
        },
        "reactions": [
          {
            "reaction": "🔥",
            "users": [
              "shimmyshimmer", "danielhanchen", "Reggie", "rekin",
              "Goekdeniz-Guelmez", "Aurelien-Morgan", "thr3a", "victor",
              "StressWar", "antmanler", "blankreg", "bullpoint", "dkleine"
            ],
            "count": 13
          }
        ],
        "isReport": false
      }
    }
  ]
}
```

**Event types that can have reactions:**
- `type: "comment"` — human-written comments (these are the only events that carry `reactions`)
- `type: "status-change"` — no reactions
- `type: "commit"` — no reactions

**Python:**
```python
token = open("/path/to/huggingface/token").read().strip()
resp = requests.get(
    "https://huggingface.co/api/models/microsoft/phi-4/discussions/21",
    headers={"Authorization": f"Bearer {token}"}
)
discussion = resp.json()
for event in discussion.get("events", []):
    if event["type"] == "comment":
        reactions = event["data"].get("reactions", [])
        if reactions:
            author = event["author"]["name"]
            print(f"Comment by {author}: {len(reactions)} reaction type(s)")
            for r in reactions:
                print(f"  {r['reaction']} × {r['count']} users: {', '.join(r['users'])}")
```

**Key fields in a reaction object:**
| Field | Type | Description |
|-------|------|-------------|
| `reaction` | string | The emoji character (e.g., `"👍"`) |
| `users` | array[string] | List of usernames who applied this reaction |
| `count` | number | Length of `users` array (redundant but provided) |

### 3. Add a Reaction

**`POST /api/{repo_type}s/{repo_id}/discussions/{num}/comment/{comment_id}/reaction`**

```json
{"action": "add", "reaction": "👍"}
```

**Response:** 200 OK with the updated reaction data.

**Validation errors:**
| HTTP Code | Error | Cause |
|-----------|-------|-------|
| 400 | `"action" is required` | Missing action field |
| 400 | `"action" must be one of [add, remove]` | Invalid action value |
| 400 | `"reaction" is required` | Missing emoji |
| 404 | `Cannot POST ...` | Wrong endpoint path |

**Note:** If the user has already reacted with this emoji, `action: "add"` is idempotent — it doesn't create a duplicate.

**Python:**
```python
token = open("/path/to/huggingface/token").read().strip()
resp = requests.post(
    "https://huggingface.co/api/models/microsoft/phi-4/discussions/21/comment/67814e761c244e2a4b53ecdb/reaction",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"action": "add", "reaction": "👍"}
)
resp.raise_for_status()
print("Reaction added!")
```

### 4. Remove a Reaction

**`POST /api/{repo_type}s/{repo_id}/discussions/{num}/comment/{comment_id}/reaction`**

```json
{"action": "remove", "reaction": "👍"}
```

**Response:** 200 OK.

**Note:** If the user hasn't reacted with this emoji, `action: "remove"` is idempotent.

**Python:**
```python
resp = requests.post(
    "https://huggingface.co/api/models/microsoft/phi-4/discussions/21/comment/67814e761c244e2a4b53ecdb/reaction",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"action": "remove", "reaction": "👍"}
)
```

### 5. Check if User Has Reacted

There is **no dedicated "has user reacted" endpoint**. To determine if the current user has reacted, you must:

1. Fetch the discussion detail: `GET /.../discussions/{num}`
2. Scan all comment events for reactions
3. Check if the current username appears in any `users` array

```python
def has_user_reacted(api_response, my_username, react_emoji="👍"):
    """Check if a user has reacted with a specific emoji on any comment."""
    for event in api_response.get("events", []):
        if event["type"] != "comment":
            continue
        for r in event["data"].get("reactions", []):
            if r["reaction"] == react_emoji and my_username in r["users"]:
                return True, event["id"]
    return False, None
```

## SDK Gap Analysis

The `huggingface_hub` Python SDK (v0.28.x) provides discussion CRUD methods via `HfApi`:

| Method | Resource | Available? |
|--------|----------|------------|
| `get_repo_discussions()` | List discussions | ✅ Yes |
| `get_discussion_details()` | Single discussion details | ✅ Yes |
| `create_discussion()` | Create discussion/PR | ✅ Yes |
| `comment_discussion()` | Add comment | ✅ Yes |
| `edit_discussion_comment()` | Edit comment | ✅ Yes |
| `hide_discussion_comment()` | Hide/delete comment | ✅ Yes |
| `rename_discussion()` | Rename discussion | ✅ Yes |
| `change_discussion_status()` | Open/close | ✅ Yes |
| **add/remove reaction** | **Add/remove emoji** | **❌ Missing** |

**Impact:** Any automation that needs to react to comments must bypass the SDK and call the raw REST API directly.

**Workaround pattern for SDK users:**
```python
from huggingface_hub import HfApi
import requests

api = HfApi()
token = api.token  # Reuse the SDK's token

# SDK: list discussions
discussions = list(api.get_repo_discussions("microsoft/phi-4"))

# Raw API: react to a comment
comment_id = "67814e761c244e2a4b53ecdb"
resp = requests.post(
    f"https://huggingface.co/api/models/microsoft/phi-4/discussions/21/comment/{comment_id}/reaction",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"action": "add", "reaction": "🔥"}
)
```

## URL Structure

The `{repo_type}` segment follows the standard HF API convention:
- `model` (default) → `/api/models/...`
- `dataset` → `/api/datasets/...`
- `space` → `/api/spaces/...`

The `{repo_id}` is the full repo namespace: `owner/repo-name`.

| Pattern | Example |
|---------|---------|
| Model discussion | `/api/models/microsoft/phi-4/discussions/21` |
| Dataset discussion | `/api/datasets/username/dataset-name/discussions/5` |
| Space discussion | `/api/spaces/username/space-name/discussions/3` |

## Supported Emojis (Observed)

From live API exploration of popular model discussions (microsoft/phi-4), these emojis are in active use:

| Emoji | Unicode | Name | Common Use Case |
|-------|---------|------|-----------------|
| 👍 | U+1F44D | Thumbs Up | Agreement, thanks |
| 🔥 | U+1F525 | Fire | Amazing, popular |
| 🚀 | U+1F680 | Rocket | Launch, great work |
| 👀 | U+1F440 | Eyes | Watching, interesting |
| ❤️ | U+2764 U+FE0F | Heart | Love, support (uses variation selector) |
| 🧠 | U+1F9E0 | Brain | Smart, insightful |
| ➕ | U+2795 | Plus | Add, agree, same |

**⚠ Note:** The `❤️` emoji uses a **variation selector** (U+FE0F) which may trigger tirith `variation_selector` scans in cron-mode terminal commands (observed in the cron-action-skills reference). When constructing reaction payloads in automated scripts, prefer emojis without variation selectors (👍, 🔥, 🚀, 👀) for cron-safe operation.

The exact list of supported emojis may include others not yet observed; the API validates that the `reaction` value is a valid emoji and returns a 400 error for unsupported values.

## Automation Patterns

### Bulk Reaction Checker

```python
import requests

def get_discussion_reactions_summary(token, repo_id, discussion_num):
    """Fetch and summarize all reactions on a discussion."""
    resp = requests.get(
        f"https://huggingface.co/api/models/{repo_id}/discussions/{discussion_num}",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    summary = []
    for event in data.get("events", []):
        if event["type"] != "comment":
            continue
        reactions = event["data"].get("reactions", [])
        if reactions:
            summary.append({
                "event_id": event["id"],
                "author": event["author"]["name"],
                "reactions": [{"emoji": r["reaction"], "count": r["count"], "users": r["users"]}
                              for r in reactions]
            })
    return summary
```

### Toggle Reaction

```python
def toggle_reaction(token, repo_id, discussion_num, comment_id, emoji):
    """Toggle a reaction on/off for the current user."""
    # First check current state
    resp = requests.get(
        f"https://huggingface.co/api/models/{repo_id}/discussions/{discussion_num}",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    
    # Find the user's current reaction state
    my_username = None
    for event in data.get("events", []):
        if event.get("id") == comment_id and event["type"] == "comment":
            for r in event["data"].get("reactions", []):
                if r["reaction"] == emoji:
                    # Check user list — we need to get current username first
                    pass
    
    # Simpler approach: check via whoami
    whoami = requests.get(
        "https://huggingface.co/api/whoami",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    my_username = whoami["name"]
    
    # Scan all reactions for this username
    has_reacted = False
    for event in data.get("events", []):
        if event.get("id") == comment_id and event["type"] == "comment":
            for r in event["data"].get("reactions", []):
                if r["reaction"] == emoji and my_username in r["users"]:
                    has_reacted = True
                    break
    
    action = "remove" if has_reacted else "add"
    resp = requests.post(
        f"https://huggingface.co/api/models/{repo_id}/discussions/{discussion_num}/comment/{comment_id}/reaction",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"action": action, "reaction": emoji}
    )
    return action  # "add" or "remove"
```

## Verification

A reusable verification script is at `scripts/verify_reactions.py` — runs all checks live:

```bash
python3 scripts/verify_reactions.py
# override target repo: HF_TEST_REPO=your/repo python3 scripts/verify_reactions.py
```

Manual verification below:\

```bash
# Quick test: list discussions with reactions
HF_TOKEN=$(cat ~/.cache/huggingface/token)
curl -s "https://huggingface.co/api/models/microsoft/phi-4/discussions?limit=50" \
  -H "Authorization: Bearer $HF_TOKEN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
reactions_count = sum(1 for dis in d['discussions'] if dis.get('topReactions'))
print(f'Discussions with reactions: {reactions_count}/{d[\"count\"]}')
for dis in d['discussions']:
    if dis.get('topReactions'):
        print(f'  #{dis[\"num\"]}: {dis[\"topReactions\"]}')
"

# Verify detail endpoint returns full reaction data with user list
curl -s "https://huggingface.co/api/models/microsoft/phi-4/discussions/19" \
  -H "Authorization: Bearer $HF_TOKEN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for ev in d['events']:
    if ev['type'] == 'comment' and ev['data'].get('reactions'):
        for r in ev['data']['reactions']:
            print(f'{r[\"reaction\"]} x {r[\"count\"]}: {r[\"users\"][:3]}...')
"
```

## Pitfalls

1. **Reactions are NOT in the Python SDK.** The `huggingface_hub` library lacks `add_reaction()` or `remove_reaction()` methods. Always use raw `requests.post()`.
2. **No top-level discussion reaction endpoint.** You can only react to individual comments/events, not the discussion/PR title itself. The `topReactions` field on the list endpoint is a pre-computed summary of the most prominent comment reaction.
3. **The `comment_id` is the event `_id`, not a sequential number.** Get it from the discussion detail API — it's a MongoDB ObjectID string like `"67814e761c244e2a4b53ecdb"`.
4. **`topReactions` is not comprehensive.** The list endpoint only returns a subset of reactions (the first/most recent one). Use the detail endpoint for complete data.
5. **Rate limits apply.** Standard HF Hub API rate limits (60 req/min unauthenticated, higher with token). The reactions endpoints count toward the same pool.
6. **Reactions are not sorted.** The `reactions` array order in the detail API is not guaranteed to be consistent.
7. **`numReactionUsers` counts unique users across all reactions on the discussion.** This is not a simple sum of all reaction counts (one user can react with multiple emojis).
8. **No webhook events for reactions.** HF webhooks fire for discussion create/comment/status-change events but do NOT emit events when reactions are added or removed.
