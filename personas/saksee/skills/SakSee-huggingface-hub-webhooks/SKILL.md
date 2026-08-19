---
name: SakSee-SakThai-huggingface-hub-webhooks
description: "Hugging Face Hub Webhooks \u2014 create, manage, and debug webhooks programmatically\
  \ via the SDK, CLI, and UI. Covers event types, payload structure, watched items,\
  \ secrets, rate limiting, and Job integration."
---

# Hugging Face Hub Webhooks

Webhooks let you receive real-time HTTP callbacks when events happen on the Hub — repo pushes, discussion activity, PR merges, and more. You can either send payloads to a URL or trigger a Hugging Face Job (serverless compute) automatically.

> **Zero-cost notice**: Webhook targets (URL handlers) must be self-hosted or use free-tier tools like Beeceptor, webhook.site, or ngrok. Job-triggered webhooks consume HF Jobs credits — verify costs before recommending.

## API Reference

The `huggingface_hub` Python SDK exposes 7 methods for webhook lifecycle management on `HfApi`:

| Method | Description |
|--------|-------------|
| `create_webhook()` | Create a new webhook (URL or Job target) |
| `get_webhook(id)` | Get webhook details by ID |
| `list_webhooks()` | List all configured webhooks |
| `update_webhook(id, ...)` | Update URL, watched items, domains, secret |
| `delete_webhook(id)` | Permanently remove a webhook |
| `enable_webhook(id)` | Re-enable a disabled webhook |
| `disable_webhook(id)` | Temporarily disable a webhook |

## Creating a Webhook

### URL-targeted webhook (send payload to an HTTP endpoint)

```python
from huggingface_hub import HfApi

api = HfApi()
webhook = api.create_webhook(
    url="https://webhook.site/your-uuid-here",
    watched=[
        {"type": "user", "name": "julien-c"},
        {"type": "org", "name": "HuggingFaceH4"},
        {"type": "model", "name": "meta-llama/Llama-3.1-8B"},
    ],
    domains=["repo", "discussion"],  # watch both repo events and discussions
    secret="my-webhook-secret",       # optional, for payload verification
)
print(f"Created webhook {webhook.id}")
```

### Job-targeted webhook (trigger a serverless Job)

```python
from huggingface_hub import HfApi

api = HfApi()
# First, create a Job specification
job = api.run_job(
    image="ubuntu",
    command=["bash", "-c", "echo Event in $WEBHOOK_REPO_ID: $WEBHOOK_PAYLOAD"],
)

# Then create a webhook that triggers the Job
webhook = api.create_webhook(
    job_id=job.id,
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret="my-secret",
)
```

When the Job runs, these environment variables are available:
- `WEBHOOK_PAYLOAD` — full JSON payload
- `WEBHOOK_REPO_ID` — repo ID (e.g., `beer-sakthai/my-model`)
- `WEBHOOK_REPO_TYPE` — repo type (model/dataset/space)
- `WEBHOOK_SECRET` — webhook secret (if set)

## Webhook Payload Structure

Every webhook POST contains these top-level keys:

| Field | Description |
|-------|-------------|
| `event` | Event metadata: `action` (create/delete/update/move), `scope` (repo/repo.content/repo.config/discussion/discussion.comment) |
| `repo` | Repo info: `type` (model/dataset/space), `name` (full ID), `url` (web + api), `private`, `headRevision` (SHA) |
| `discussion` | (if scope is discussion/*) Discussion/PR metadata: `id`, `title`, `url`, `status`, `isPullRequest`, `changes.base` |
| `comment` | (if scope is discussion.comment) Comment content: `id`, `author.id`, `content`, `hidden` |

### Event actions by scope

| Scope | Actions |
|-------|---------|
| `repo` | `create`, `delete`, `update`, `move` |
| `repo.content` | `update` (file push/commit) |
| `repo.config` | `update` (metadata, card, settings change) |
| `discussion` | `create`, `delete`, `update` (new/edit/close discussion or PR) |
| `discussion.comment` | `create`, `update` (new/edit comment) |

### Example payload (repo push)

```json
{
  "event": {
    "action": "update",
    "scope": "repo.content"
  },
  "repo": {
    "type": "model",
    "name": "beer-sakthai/my-model",
    "headRevision": "abc123def456",
    "private": false,
    "url": {
      "web": "https://huggingface.co/beer-sakthai/my-model",
      "api": "https://huggingface.co/api/models/beer-sakthai/my-model"
    }
  }
}
```

## Watched Items

You can watch any combination of:

| Type | What it matches | Example |
|------|----------------|---------|
| `user` | All repos owned by a user | `beer-sakthai` |
| `org` | All repos in an org | `HuggingFaceH4` |
| `model` | A specific model repo | `meta-llama/Llama-3.1-8B` |
| `dataset` | A specific dataset repo | `beer-sakthai/my-dataset` |
| `space` | A specific Space repo | `beer-sakthai/my-space` |

Items can be passed as dicts or `WebhookWatchedItem` objects:

```python
from huggingface_hub import WebhookWatchedItem

item = WebhookWatchedItem(type="model", name="Qwen/Qwen2.5-7B-Instruct")
```

## Domains

- `"repo"` — all repository-related events (create, delete, content update, config change)
- `"discussion"` — all discussion and PR events (create, comment, close, merge)

You can watch both by passing `domains=["repo", "discussion"]`.

## Webhook Secret & Verification

Set a secret when creating a webhook. Hugging Face sends it as the `X-Webhook-Secret` HTTP header on every request.

```python
webhook = api.create_webhook(
    url="https://example.com/webhook?secret=XXX",  # or set as query param
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo"],
    secret="my-super-secret-key",
)
```

The secret can also be passed as a URL query parameter if header access is inconvenient.

## Rate Limits

- **1,000 triggers per 24 hours** per webhook on free tier
- PRO/Team/Enterprise: contact HF to increase limit
- Monitor usage in the Webhook settings page → "Activity" tab

## Managing Webhooks

### List all webhooks

```python
from huggingface_hub import list_webhooks

webhooks = list_webhooks()
for wh in webhooks:
    print(f"{wh.id}: watching {[w.name for w in wh.watched]} → {wh.url or 'Job ' + wh.job.docker_image}")
```

### Update an existing webhook

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

### Enable/Disable

```python
from huggingface_hub import enable_webhook, disable_webhook

disable_webhook("654bbbc16f2ec14d77f109cc")  # stop receiving events
enable_webhook("654bbbc16f2ec14d77f109cc")   # resume receiving events
```

### Delete

```python
from huggingface_hub import delete_webhook

delete_webhook("654bbbc16f2ec14d77f109cc")  # permanent removal
```

## Debugging & Development Tools

| Tool | Use |
|------|-----|
| **Webhook.site** | Free catch-all endpoint that captures request payloads and headers. Inspect event structure live. |
| **Beeceptor** | Temporary HTTP endpoint + payload inspector. |
| **ngrok** | Expose localhost to the internet for testing webhook handlers locally. |
| **localtunnel** | Lightweight alternative to ngrok for local dev. |

The Hub UI also provides an **Activity** tab per webhook showing recent events, HTTP status codes, payloads, and a **Replay** button to resend events.

## `hf` CLI Commands

The `hf` CLI (Hugging Face CLI v2) supports webhook management:

```bash
# List webhooks
hf webhooks list

# Get webhook details
hf webhooks get <webhook-id>

# Create a webhook
hf webhooks create \
  --url https://example.com/webhook \
  --watched user:beer-sakthai \
  --domains repo,discussion \
  --secret my-secret

# Update a webhook
hf webhooks update <webhook-id> \
  --url https://new-endpoint.com/webhook

# Delete a webhook
hf webhooks delete <webhook-id>

# Enable/disable
hf webhooks enable <webhook-id>
hf webhooks disable <webhook-id>
```

## Use Cases for Sak Family Agents

1. **CI/CD trigger**: Watch a model repo → on `repo.content.update`, trigger a benchmark or evaluation Job
2. **Discussion monitoring**: Watch an org → on `discussion.create`, post notification to Telegram/email
3. **Dataset update sync**: Watch datasets → on `repo.content.update`, auto-pull latest version
4. **Space deployment**: Watch a Space → on `repo.config.update`, verify hardware/secrets didn't change unexpectedly

## Pitfalls

- **Webhooks are user-level, not org-level**: You can create webhooks on your user account only. Org-level webhooks are not currently supported.
- **Cannot watch "all of HF"**: Wildcard/repo-type-wide subscriptions require emailing HF Support to enable.
- **Rate limit is strict**: At 1,000/day, use high-traffic repos sparingly. A single push triggers one event.
- **Secret only supports ASCII**: Non-ASCII characters in the secret will fail.
- **Job-triggered webhooks cost**: Each triggered Job runs on HF infrastructure. Verify zero-cost constraints before using this mode.
- **Replay sends to updated URL**: If you change the target URL and replay, the payload goes to the new URL.
