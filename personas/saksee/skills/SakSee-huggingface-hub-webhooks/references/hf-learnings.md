# HF Learnings — Hugging Face Hub Webhooks & Notifications API (Deep Dive)

**Topic:** hf-hub-webhooks-and-notifications-api-deep-dive  
**Date:** 2026-07-24  
**Author:** SakThai · Main Lead of the House & Master of Hugging Face  
**License:** MIT  
**Sources:**
- Official docs: https://huggingface.co/docs/hub/en/webhooks
- Source code: `huggingface_hub/src/huggingface_hub/hf_api.py` (lines 585–650, 10802–11235)
- OpenAPI spec: `https://huggingface.co/.well-known/openapi.md`
- Jobs-webhooks: https://huggingface.co/docs/hub/en/jobs-webhooks

---

## 1. Webhook Architecture Overview

Webhooks provide real-time HTTP callbacks when events happen on the Hugging Face Hub. They are the foundation for MLOps automation: CI/CD pipelines, discussion bots, auto-retraining, metadata quality checks, and more.

**Key characteristics:**
- **Outbound only** — HF sends POST requests to your endpoint; your handler never calls back
- **Event-scoped** — Each payload describes exactly what changed (scope + action)
- **User-level** — Webhooks are created on your user account, not at the org level
- **Two dispatch modes** — URL-targeted (send to any HTTP endpoint) or Job-triggered (run a serverless Job on HF infra)
- **Rate-limited** — 1,000 triggers per webhook per 24 hours on free tier

### The Two Dispatch Modes

| Mode | Method | Pros | Cons |
|------|--------|------|------|
| **URL-targeted** | `url="https://..."` | Self-hosted, full control, any stack | Need a publicly reachable HTTPS endpoint |
| **Job-triggered** | `job_id="..."` | No server needed, runs on HF infra, env vars injected | Consumes Jobs credits, less control |

---

## 2. Complete Event Scope & Action Matrix

Every webhook payload has `event.scope` and `event.action`. Here is the complete matrix:

| Scope | Actions | Triggered By |
|-------|---------|-------------|
| `repo` | `create`, `delete`, `update`, `move` | Repo lifecycle events |
| `repo.content` | `update` (only) | New commits, tag creation, PR creation (new ref) |
| `repo.config` | `update` (only) | Settings change, secrets update, DOI change, disable/enable |
| `discussion` | `create`, `delete`, `update` | Discussion/PR created, title/status changed, merged |
| `discussion.comment` | `create`, `update` | New comment, comment edited, comment hidden |

**Forward-compatibility rule:** If a new, narrower scope is added in the future (e.g., `repo.config.dois`), your handler can treat any unknown scope as an `"update"` action on the broader parent scope.

### Scope-to-Payload-Property Mapping

| Scope | Present Properties |
|-------|-------------------|
| `repo.*` | `event`, `repo` (includes `headSha`), `updatedRefs` (on content change), `updatedConfig` (on config change) |
| `discussion.*` | `event`, `repo` (NO `headSha`), `discussion`, `comment` (if comment scope) |
| `discussion.comment` | `event`, `repo` (NO `headSha`), `discussion`, `comment` |

**Notable:** `repo.headSha` is **only** sent when `event.scope` starts with `"repo"`. It is absent on discussion/comment events.

---

## 3. Complete Payload Reference

### 3.1 Repo Content Update (push/commit)

```json
{
  "event": { "action": "update", "scope": "repo.content" },
  "repo": {
    "type": "model",
    "name": "user/my-model",
    "id": "6366c000a2abcdf2fd69a080",
    "private": false,
    "headSha": "c379e821c9c95d613899e8c4343e4bfee2b0c600",
    "url": {
      "web": "https://huggingface.co/user/my-model",
      "api": "https://huggingface.co/api/models/user/my-model"
    },
    "owner": { "id": "61d2000c3c2083e1c08af22d" }
  },
  "updatedRefs": [
    { "ref": "refs/heads/main", "oldSha": "ce9a4674...", "newSha": "575db8b7..." },
    { "ref": "refs/tags/v1.0",  "oldSha": null,         "newSha": "575db8b7..." }
  ],
  "webhook": { "id": "6390e855e30d9209411de93b", "version": 3 }
}
```

**`updatedRefs` semantics:**
- Created ref: `oldSha: null`, `newSha: <sha>`
- Deleted ref: `oldSha: <sha>`, `newSha: null`
- Updated ref: both have values
- Branches use `refs/heads/{name}`, tags use `refs/tags/{name}`, PRs use `refs/pr/{num}`

### 3.2 Config Change

```json
{
  "event": { "action": "update", "scope": "repo.config" },
  "repo": { ... },
  "updatedConfig": { "private": false },
  "webhook": { "id": "...", "version": 3 }
}
```

Currently only `private` is exposed in `updatedConfig`. Other config changes send an empty `{}`.

### 3.3 Discussion/PR Created

```json
{
  "event": { "action": "create", "scope": "discussion" },
  "repo": { "type": "model", "name": "user/my-model", ... },
  "discussion": {
    "id": "6399f58518721fdd27fc9ca9",
    "title": "Update co2 emissions",
    "url": {
      "web": "https://huggingface.co/user/my-model/discussions/19",
      "api": "https://huggingface.co/api/models/user/my-model/discussions/19"
    },
    "status": "open",
    "author": { "id": "61d2f90c3c2083e1c08af22d" },
    "num": 19,
    "isPullRequest": true,
    "changes": { "base": "refs/heads/main" }
  },
  "comment": {
    "id": "6399f58518721fdd27fc9caa",
    "author": { "id": "61d2f90c3c2083e1c08af22d" },
    "content": "Add co2 emissions information to the model card",
    "hidden": false,
    "url": {
      "web": "https://huggingface.co/user/my-model/discussions/19#6399f58518721fdd27fc9caa"
    }
  },
  "webhook": { "id": "...", "version": 3 }
}
```

**Note:** When `hidden` is `true`, `content` is undefined (omitted from the payload).

---

## 4. Python API — Complete Reference

All methods are accessible as `HfApi` instance methods OR as module-level functions.

### 4.1 Dataclasses

```python
@dataclass
class WebhookWatchedItem:
    type: Literal["dataset", "model", "org", "space", "user"]
    name: str

@dataclass
class WebhookInfo:
    id: str
    url: str | None           # URL-targeted (mutually exclusive with job)
    job: JobSpec | None       # Job-triggered (mutually exclusive with url)
    watched: list[WebhookWatchedItem]
    domains: list[Literal["repo", "discussion"]]
    secret: str | None
    disabled: bool
```

### 4.2 `create_webhook()` — Create a URL-targeted webhook

```python
from huggingface_hub import create_webhook

webhook = create_webhook(
    watched=[
        {"type": "user", "name": "beer-sakthai"},
        {"type": "org", "name": "HuggingFaceH4"},
        {"type": "model", "name": "meta-llama/Llama-3.1-8B"},
    ],
    url="https://webhook.site/your-uuid-here",
    domains=["repo", "discussion"],  # or just ["repo"]
    secret="my-webhook-secret",      # optional, for payload verification
)
print(f"Created webhook {webhook.id}")
```

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `watched` | `list[dict \| WebhookWatchedItem]` | ✅ | Items to watch (users, orgs, specific repos) |
| `url` | `str` | Either `url` or `job_id` | HTTP endpoint URL |
| `job_id` | `str` | Either `url` or `job_id` | Job ID to trigger |
| `domains` | `list[str]` | Optional | `["repo"]`, `["discussion"]`, or both |
| `secret` | `str` | Optional | ASCII-only webhook secret |
| `token` | `str \| bool` | Optional | HF token |

### 4.3 `create_webhook()` — Create a Job-triggered webhook

```python
from huggingface_hub import create_webhook

# First: create the job spec (or use existing job_id)
# Jobs are created via run_job() — see below

webhook = create_webhook(
    job_id="existing-job-id",
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret="my-secret",
)
```

When the Job runs, these environment variables are injected:

| Variable | Description |
|----------|-------------|
| `WEBHOOK_PAYLOAD` | Full JSON payload (stringified) |
| `WEBHOOK_REPO_ID` | e.g., `beer-sakthai/my-model` |
| `WEBHOOK_REPO_TYPE` | `model`, `dataset`, or `space` |
| `WEBHOOK_SECRET` | Webhook secret (if configured) |

### 4.4 `get_webhook()` — Retrieve a webhook by ID

```python
from huggingface_hub import get_webhook

webhook = get_webhook("654bbbc16f2ec14d77f109cc")
print(webhook.url)           # URL or None
print(webhook.job)           # JobSpec or None
print(webhook.watched)       # list of WebhookWatchedItem
print(webhook.domains)       # ["repo", "discussion"]
print(webhook.disabled)      # bool
```

### 4.5 `list_webhooks()` — List all webhooks

```python
from huggingface_hub import list_webhooks

all_webhooks = list_webhooks()
for wh in all_webhooks:
    watched_names = [w.name for w in wh.watched]
    target = wh.url or f"Job({wh.job.docker_image if wh.job else 'N/A'})"
    print(f"{wh.id}: watching {watched_names} → {target} {'[DISABLED]' if wh.disabled else ''}")
```

### 4.6 `update_webhook()` — Modify an existing webhook

```python
from huggingface_hub import update_webhook

updated = update_webhook(
    webhook_id="654bbbc16f2ec14d77f109cc",
    url="https://new-endpoint.example.com/webhook",
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret="new-secret",
)
```

Any parameter you omit stays unchanged. You must pass at least one updatable parameter.

### 4.7 `enable_webhook()` / `disable_webhook()` — Toggle

```python
from huggingface_hub import enable_webhook, disable_webhook

disable_webhook("654bbbc16f2ec14d77f109cc")  # Stop receiving events
enable_webhook("654bbbc16f2ec14d77f109cc")   # Resume receiving events
```

### 4.8 `delete_webhook()` — Permanent removal

```python
from huggingface_hub import delete_webhook

delete_webhook("654bbbc16f2ec14d77f109cc")  # ⚠️ Irreversible
```

---

## 5. Job-Targeted Webhooks Deep Dive

Job-triggered webhooks run a serverless compute Job whenever the watched event fires. This is the **zero-cost** option if you already have Jobs quota.

### Creating a Job webhook in two steps

```python
from huggingface_hub import HfApi

api = HfApi()

# Step 1: Create a Job spec
job = api.run_job(
    image="python:3.12-slim",
    command=[
        "bash", "-c",
        "pip install huggingface_hub && "
        "python -c \""
        "import os, json; "
        "payload = json.loads(os.environ['WEBHOOK_PAYLOAD']); "
        "print(f'Event: {payload[\"event\"][\"scope\"]}:{payload[\"event\"][\"action\"]} on {payload[\"repo\"][\"name\"]}')"
        "\""
    ],
)

# Step 2: Create a webhook that triggers the Job
webhook = api.create_webhook(
    job_id=job.id,
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret="my-secret",
)
```

### Job handler script pattern (recommended)

For anything more complex than a one-liner, create a standalone script and push it as a repo or inline via the image:

```python
# webhook_handler.py
import os
import json

def handle_webhook():
    payload = json.loads(os.environ["WEBHOOK_PAYLOAD"])
    repo_id = os.environ["WEBHOOK_REPO_ID"]
    repo_type = os.environ["WEBHOOK_REPO_TYPE"]
    secret = os.environ.get("WEBHOOK_SECRET")

    event = payload["event"]
    scope = event["scope"]
    action = event["action"]

    print(f"Webhook triggered by {repo_type} repo: {repo_id}")
    print(f"Event: {scope}:{action}")

    if scope == "repo.content" and action == "update":
        # New commit pushed — do something
        head_sha = payload["repo"]["headSha"]
        for ref in payload.get("updatedRefs", []):
            print(f"  Ref {ref['ref']}: {ref['oldSha'][:8]} → {ref['newSha'][:8]}")

    elif scope == "discussion":
        disc = payload["discussion"]
        if disc.get("isPullRequest"):
            print(f"  PR #{disc['num']}: {disc['title']} ({disc['status']})")

if __name__ == "__main__":
    handle_webhook()
```

---

## 6. Webhook Secret & Verification

The secret serves two purposes:
1. **Authentication** — confirms the payload is genuinely from Hugging Face
2. **Authorization** — you can reject payloads without a valid secret

The secret is sent as the `X-Webhook-Secret` HTTP header on every POST request.

### Handling verification in your handler

```python
import os

EXPECTED_SECRET = os.environ.get("WEBHOOK_EXPECTED_SECRET")

def verify_webhook(headers):
    received_secret = headers.get("X-Webhook-Secret")
    if not received_secret or received_secret != EXPECTED_SECRET:
        raise PermissionError("Invalid webhook secret")
```

### Alternative: Secret as query parameter

If you cannot inspect HTTP headers (e.g., using a serverless function with limited header access), add the secret as a URL query parameter:

```python
webhook = create_webhook(
    url="https://example.com/webhook?secret=my-secret",
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
)
```

**Limitations:**
- Only ASCII characters are supported in the secret
- The secret is sent as a plain header/query param (no HMAC signing)
- Always use HTTPS to prevent secret interception in transit

---

## 7. Rate Limiting & Quotas

| Limit | Value | Notes |
|-------|-------|-------|
| Triggers per webhook per 24h | 1,000 | Strict — 1,001st event is silently dropped |
| Max triggers for PRO/Team | Higher | Contact `website@huggingface.co` to increase |
| Rate limit period | Rolling 24h | Not calendar-day-based |

**Monitoring:** View usage in the Webhook settings page → "Activity" tab. Each event shows HTTP status code, payload, and timestamps.

**Throttling strategy for high-traffic repos:** If you expect >1,000 events/day, consider:
- Filtering events server-side (respond 200 quickly, ignore irrelevant events)
- Using a queue or buffer (SQS, Redis, etc.) to batch-process
- Requesting a limit increase for PRO accounts

---

## 8. Webhook Source Code Internals (`hf_api.py`)

### Class Hierarchy

```
WebhookWatchedItem (dataclass)
  ├── type: Literal["dataset", "model", "org", "space", "user"]
  └── name: str

WebhookInfo (dataclass)
  ├── id: str
  ├── url: str | None        # URL-targeted
  ├── job: JobSpec | None     # Job-triggered
  ├── watched: list[WebhookWatchedItem]
  ├── domains: list[str]
  ├── secret: str | None
  └── disabled: bool
```

### API Endpoints (from OpenAPI spec)

| Method | Endpoint | Python Method |
|--------|----------|---------------|
| GET | `/api/settings/webhooks` | `list_webhooks()` |
| POST | `/api/settings/webhooks` | `create_webhook()` |
| GET | `/api/settings/webhooks/{id}` | `get_webhook(id)` |
| POST | `/api/settings/webhooks/{id}` | `update_webhook(id, ...)` |
| DELETE | `/api/settings/webhooks/{id}` | `delete_webhook(id)` |
| POST | `/api/settings/webhooks/{id}/enable` | `enable_webhook(id)` |
| POST | `/api/settings/webhooks/{id}/disable` | `disable_webhook(id)` |

### Implementation notes

- `get_webhook()` parses the response JSON's `webhook` key, mapping `watched` items from dicts to `WebhookWatchedItem` objects, and parsing `job` as `JobSpec` if present
- `create_webhook()` and `update_webhook()` enforce that one of `url` or `job_id` is specified (but not both)
- `delete_webhook()` raises `HfHubHTTPError` if the webhook ID doesn't exist
- `enable_webhook()`/`disable_webhook()` toggle the `disabled` boolean — they're idempotent (re-enabling an already-enabled webhook succeeds silently)

### Webhook versioning

The payload includes `webhook.version` (currently `3`). This is the webhook **payload schema version**, not an API version. Hugging Face may increment this when adding new fields. Always check for both known and unknown field patterns in your handlers.

---

## 9. CLI Reference (`hf webhooks`)

```bash
# List all webhooks
hf webhooks list

# Get webhook details
hf webhooks get <webhook-id>

# Create a URL-targeted webhook
hf webhooks create \
  --url https://example.com/webhook \
  --watched user:beer-sakthai \
  --domains repo,discussion \
  --secret my-secret

# Create a Job-triggered webhook
hf webhooks create \
  --job-id <job-id> \
  --watched user:beer-sakthai \
  --domains repo

# Update a webhook
hf webhooks update <webhook-id> \
  --url https://new-endpoint.com/webhook

# Enable/disable
hf webhooks enable <webhook-id>
hf webhooks disable <webhook-id>

# Delete
hf webhooks delete <webhook-id>
```

---

## 10. Practical Patterns for the Sak Family

### Pattern A: Watch Beer's repos for new commits → trigger benchmark

```python
from huggingface_hub import create_webhook, run_job

# Create a benchmark Job
job = run_job(
    image="python:3.12-slim",
    command=["bash", "-c", "pip install lm-eval && python run_benchmark.py"],
)

# Trigger it on every push to any SakThai repo
webhook = create_webhook(
    job_id=job.id,
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret=os.environ.get("HF_WEBHOOK_SECRET"),
)
```

### Pattern B: Notification bot — new discussion → Telegram message

```python
import requests
import os
from huggingface_hub import create_webhook

# This would be the handler running at the webhook URL
def handle_discussion_created(event):
    """Handler code (run in your server/webhook endpoint)."""
    if event["event"]["scope"] == "discussion" and event["event"]["action"] == "create":
        repo_name = event["repo"]["name"]
        disc = event["discussion"]
        pr_label = "PR" if disc.get("isPullRequest") else "Discussion"
        message = f"New {pr_label} on {repo_name}: \"{disc['title']}\""
        # Send to Telegram
        requests.post(
            f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}/sendMessage",
            json={"chat_id": os.environ["TG_CHAT_ID"], "text": message},
        )
```

### Pattern C: Auto-retrain — dataset update triggers fine-tuning Job

```python
from huggingface_hub import create_webhook, run_job

retrain_job = run_job(
    image="huggingface/trl-latest:gpu",
    command=["bash", "-c",
        "cd /workspace && "
        "python train.py --dataset $WEBHOOK_REPO_ID --output /output"
    ],
)

webhook = create_webhook(
    job_id=retrain_job.id,
    watched=[{"type": "dataset", "name": "beer-sakthai/training-data"}],
    domains=["repo"],       # triggers on any push to the dataset
    secret="retrain-secret",
)
```

### Pattern D: Multi-webhook orchestration (fan-out)

Create multiple webhooks watching different scopes of the same repo:

```python
# Webhook 1: Watch for content pushes → trigger build
webhook_build = create_webhook(
    url="https://my-ci.example.com/build",
    watched=[{"type": "model", "name": "beer-sakthai/my-model"}],
    domains=["repo"],
)

# Webhook 2: Watch for discussions → trigger review notification
webhook_discuss = create_webhook(
    url="https://my-ci.example.com/discussion-notify",
    watched=[{"type": "model", "name": "beer-sakthai/my-model"}],
    domains=["discussion"],
)
```

---

## 11. Debugging & Development Tools

| Tool | Use Case | Cost |
|------|----------|------|
| **Webhook.site** | Catch-all endpoint — inspect payloads + headers in browser | Free |
| **Beeceptor** | Temporary HTTP endpoint with payload inspector | Free |
| **ngrok** | Expose localhost → public URL for local handler testing | Free tier (limited) |
| **localtunnel** | Lightweight alternative to ngrok | Free |
| **HF Activity tab** | Built-in event history with Replay button | Free (in Hub UI) |

### Debugging workflow

1. Create a webhook pointing to `https://webhook.site/your-uuid`
2. Trigger the event (push to a watched repo, create a discussion)
3. Inspect payload on webhook.site
4. Once the payload structure is confirmed, point your handler URL to a local server exposed via ngrok
5. Test handler logic locally
6. Update the webhook URL to production

### Replay feature

The Hub UI's Activity tab has a **Replay** button for each event. When clicked, it re-sends the exact same payload to the **current** target URL. This is useful for:
- Testing handler changes against real historical events
- Debugging after changing the handler URL
- Re-triggering failed webhook deliveries

**Note:** Replaying sends to the updated URL, not the original URL at event time.

---

## 12. FAQ & Known Limitations

### Webhooks are user-level, not org-level

You can only create webhooks on your own user account (`/api/settings/webhooks`). There is no org-level webhook endpoint. Workaround: create webhooks under a bot/CI user account.

### Cannot watch "all of HF" (wildcard)

There is no API to subscribe to `all models` or `all datasets`. Wildcard subscriptions must be requested by emailing `website@huggingface.co`. This is typically granted for community bots and research projects.

### Secret is ASCII-only

Non-ASCII characters (Unicode, emoji, etc.) in the secret will cause API errors. Keep secrets to alphanumeric ASCII.

### Job webhooks cost

Each triggered Job consumes HF Jobs credits or billing. On the free tier, Jobs resources are limited. Always verify cost before using Job-triggered webhooks for high-frequency events.

### Payload versioning

The `webhook.version` field (currently `3`) indicates the payload schema version. New fields may be added in future versions. Design your handlers to be lenient about unexpected fields.

### Replay sends to updated URL

If you change the target URL and replay an event, the payload goes to the new URL — not the one that was active when the event originally fired.

### No HMAC signing

Unlike GitHub webhooks (which use HMAC-SHA256), Hugging Face webhooks send the secret as a plain header (`X-Webhook-Secret`). There is no payload body signing. This means:
- You can verify the secret, but cannot verify payload integrity
- Always use HTTPS to protect the secret and payload in transit
- Consider adding your own HMAC if payload integrity is critical

---

## 13. Comparison: HF Webhooks vs GitHub Webhooks

| Feature | HF Webhooks | GitHub Webhooks |
|---------|-------------|-----------------|
| Protocol | HTTP POST (JSON) | HTTP POST (JSON) |
| Signature | Plain secret header | HMAC-SHA256 |
| Event types | 5 scopes × actions | 30+ event types |
| Rate limit | 1,000/day per webhook | 5,000/hr per hook (GitHub.com) |
| Org-level | ❌ User only | ✅ Repo + Org |
| Wildcard subscribes | ❌ (email request) | ✅ `*` event |
| Job trigger | ✅ Run HF serverless Jobs | ❌ (use Actions) |
| UI replay | ✅ Built-in | ❌ (manually resend via API) |
| Retry on failure | ❌ (no automatic retry) | ✅ 3 retries with exponential backoff |
| Delivery guarantees | At most once | At least once |

**Key gap:** HF webhooks do not automatically retry on delivery failure. If your handler returns a non-2xx status, the event is lost. Design your handlers to be idempotent and consider using the Replay button manually for missed events.

---

## 14. Resources

- **Official docs:** https://huggingface.co/docs/hub/en/webhooks
- **Jobs-webhooks integration:** https://huggingface.co/docs/hub/en/jobs-webhooks
- **Webhooks guide: Auto-retrain on dataset update:** https://huggingface.co/docs/hub/en/webhooks-guide-auto-retrain
- **Webhooks guide: Discussion bot:** https://huggingface.co/docs/hub/en/webhooks-guide-discussion-bot
- **Webhooks guide: Metadata review:** https://huggingface.co/docs/hub/en/webhooks-guide-metadata-review
- **Python `huggingface_hub` webhooks docs:** https://huggingface.co/docs/huggingface_hub/en/guides/webhooks
- **Source:** `huggingface_hub/src/huggingface_hub/hf_api.py` (lines 585–650, 10802–11235)
- **OpenAPI spec:** https://huggingface.co/.well-known/openapi.md
- **Webhook settings UI:** https://huggingface.co/settings/webhooks
- **Webhook.site:** https://webhook.site/
