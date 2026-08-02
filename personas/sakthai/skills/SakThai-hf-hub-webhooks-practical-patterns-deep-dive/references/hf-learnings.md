# HF Learnings: Webhooks Practical Patterns Deep-Dive

## 2026-07-25: HF Hub Webhooks — Event Payloads, Receivers, and Automation Patterns (Topic #362)

### Summary

Deep-dive into Hugging Face Hub webhooks beyond the CRUD API surface — covering event payload structure for all event types, building production-ready receivers with FastAPI, handling delivery failures, replay mechanisms, and integration patterns for agent automation, CI/CD, and monitoring. Builds on the existing `hf-hub-webhooks-and-notifications-api-deep-dive` (topic #163) which covered the CRUD API surface.

---

### 1. Webhook Event Payload Structure

When a watched event occurs, Hugging Face sends an HTTP POST to the webhook URL with a JSON body. The payload structure varies by event domain and type.

#### 1.1 Common Envelope

Every webhook POST shares this top-level structure:

```json
{
  "event": {
    "id": "evt_abc123def456",
    "type": "update",
    "repo": {
      "type": "model",
      "name": "Nanthasit/sakthai-model-v0.5b",
      "private": false,
      "headSha": "a1b2c3d4e5f6..."
    },
    "payload": { ... },
    "timestamp": "2026-07-25T12:00:00Z"
  },
  "signature": {
    "sha256": "abc123..."
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `event.id` | `string` | Unique event ID (use for deduplication) |
| `event.type` | `string` | Event type: `"create"`, `"update"`, `"delete"`, `"comment"`, `"merge"` |
| `event.repo.type` | `string` | `"model"`, `"dataset"`, `"space"`, `"bucket"`, `"kernel"` |
| `event.repo.name` | `string` | Full repo ID (`namespace/repo-name`) |
| `event.repo.private` | `bool` | Privacy status at event time |
| `event.repo.headSha` | `string \| null` | Git commit SHA at event time |
| `event.payload` | `object` | Event-specific payload (varies by type) — see below |
| `event.timestamp` | `string` (ISO 8601) | When the event was generated |
| `signature.sha256` | `string` | HMAC-SHA256 hex digest (if secret configured) |

#### 1.2 Payload by Event Type

##### `"update"` — Repo push/commit

```json
{
  "event": {
    "type": "update",
    "repo": { "type": "model", "name": "user/my-model" },
    "payload": {
      "action": "push",
      "ref": "refs/heads/main",
      "commits": [
        {
          "id": "abc123def456",
          "title": "Update config.json",
          "message": "Updated model configuration\n\nDetails here",
          "timestamp": "2026-07-25T11:55:00Z",
          "author": {
            "name": "beer-sakthai",
            "email": "beer@example.com",
            "username": "beer-sakthai"
          },
          "modified": ["config.json", "model.safetensors"],
          "added": ["vocab.json"],
          "removed": []
        }
      ],
      "head_commit": "abc123def456",
      "before": "000000000000",
      "after": "abc123def456"
    }
  }
}
```

##### `"create"` — New branch/tag or repo creation

```json
{
  "event": {
    "type": "create",
    "repo": { "type": "dataset", "name": "user/new-dataset" },
    "payload": {
      "ref": "refs/heads/experiment",
      "ref_type": "branch"
    }
  }
}
```

`ref_type` can be `"branch"`, `"tag"`, or `"repo"`.

##### `"delete"` — Branch/tag deletion

```json
{
  "event": {
    "type": "delete",
    "repo": { "type": "space", "name": "user/my-space" },
    "payload": {
      "ref": "refs/heads/feature-x",
      "ref_type": "branch"
    }
  }
}
```

##### `"comment"` — New comment on discussion/PR

```json
{
  "event": {
    "type": "comment",
    "repo": { "type": "model", "name": "user/my-model" },
    "payload": {
      "discussion_id": 42,
      "discussion_title": "Add support for Qwen3",
      "discussion_status": "open",
      "comment_id": 1234,
      "comment": "I've added support for Qwen3 in this PR",
      "author": "contributor-user",
      "is_pr": true
    }
  }
}
```

##### `"merge"` — Pull request merged

```json
{
  "event": {
    "type": "merge",
    "repo": { "type": "model", "name": "user/my-model" },
    "payload": {
      "discussion_id": 42,
      "discussion_title": "Add support for Qwen3",
      "action": "merge",
      "merged_by": "beer-sakthai",
      "merge_commit_sha": "fedcba987654"
    }
  }
}
```

##### `"discussion"` — Discussion status change

```json
{
  "event": {
    "type": "discussion",
    "repo": { "type": "dataset", "name": "user/my-dataset" },
    "payload": {
      "discussion_id": 7,
      "discussion_title": "License clarification",
      "status": "closed",
      "updated_by": "beer-sakthai"
    }
  }
}
```

---

### 2. Building a Webhook Receiver

#### 2.1 Minimal FastAPI Receiver

```python
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

WEBHOOK_SECRET = "your-webhook-secret"  # From HF Settings > Webhooks

def verify_signature(body: bytes, signature_header: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    if not WEBHOOK_SECRET:
        return True  # No secret configured — accept all
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)

@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(body)
    event_type = event["event"]["type"]
    repo_name = event["event"]["repo"]["name"]
    repo_type = event["event"]["repo"]["type"]

    print(f"Received {event_type} event for {repo_type}/{repo_name}")

    # Route to handler
    if event_type == "update":
        await handle_repo_update(event)
    elif event_type == "comment":
        await handle_comment(event)
    elif event_type == "merge":
        await handle_merge(event)

    return {"status": "ok"}

async def handle_repo_update(event: dict):
    """Process a repo push/update event."""
    payload = event["event"]["payload"]
    commits = payload.get("commits", [])
    for commit in commits:
        print(f"  Commit {commit['id'][:8]}: {commit['title']}")
        print(f"  Modified files: {', '.join(commit['modified'])}")

async def handle_comment(event: dict):
    """Process a new comment on a discussion/PR."""
    payload = event["event"]["payload"]
    print(f"  New comment by {payload['author']} on \"{payload['discussion_title']}\"")
    print(f"  Comment: {payload['comment'][:200]}...")

async def handle_merge(event: dict):
    """Process a PR merge."""
    payload = event["event"]["payload"]
    print(f"  PR \"{payload['discussion_title']}\" merged by {payload['merged_by']}")
```

#### 2.2 Deploying on HF Spaces

The receiver can run on **HF Spaces** (zero-cost with persistent storage or ZeroGPU as needed):

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

```python
# requirements.txt
fastapi>=0.110.0
uvicorn>=0.29.0
```

**Key considerations:**
- Space must be **running** (not paused) to receive webhooks — use a persistent Space (stays awake) or set up a health-check
- Use **Space secrets** (`$SECRET_WEBHOOK_SECRET`) for the webhook secret — never hardcode
- Only expose the webhook endpoint — use FastAPI prefix or separate routes
- Pin dependency versions to avoid breakage on Space rebuild

#### 2.3 Flask Alternative

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data()
    signature = request.headers.get("X-Webhook-Signature", "")

    if WEBHOOK_SECRET:
        expected = hmac.new(
            WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({"error": "invalid signature"}), 401

    event = request.json
    print(f"Event: {event['event']['type']} on {event['event']['repo']['name']}")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000)
```

#### 2.4 Serverless (Cloudflare Workers) Alternative

Zero-cost, no persistent server needed:

```javascript
// Cloudflare Worker — HF Webhook Receiver
export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const body = await request.text();
    const signature = request.headers.get('X-Webhook-Signature') || '';

    // Verify HMAC signature
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw', encoder.encode(env.WEBHOOK_SECRET),
      { name: 'HMAC', hash: 'SHA-256' },
      false, ['verify']
    );
    const expected = await crypto.subtle.sign(
      'HMAC', key, encoder.encode(body)
    );
    const expectedHex = [...new Uint8Array(expected)]
      .map(b => b.toString(16).padStart(2, '0')).join('');

    if (env.WEBHOOK_SECRET && !crypto.subtle.timingSafeEqual(
      new TextEncoder().encode(expectedHex),
      new TextEncoder().encode(signature)
    )) {
      return new Response('Invalid signature', { status: 401 });
    }

    const event = JSON.parse(body);
    // Process event...
    console.log(`Event: ${event.event.type}`);

    return new Response(JSON.stringify({ status: 'ok' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
};
```

---

### 3. Webhook Delivery Behavior

#### 3.1 Delivery Mechanics

| Property | Value |
|----------|-------|
| **Protocol** | HTTP POST with JSON body |
| **Timeout** | 10 seconds for response |
| **Retries** | Up to 3 times with exponential backoff (~30s, ~2m, ~5m) |
| **Success** | Any 2xx response counts as delivered |
| **Redelivery** | Manual via Hub UI or API (see replay below) |
| **Ordering** | Not guaranteed — use `event.id` for ordering and dedup |
| **Concurrency** | Events delivered as they occur; multiple events can arrive simultaneously |
| **IP ranges** | Dynamic (not fixed) — verify via HMAC signature, not IP |

#### 3.2 Logging and Monitoring

**Hub UI:** `Settings > Webhooks > {webhook} > Logs`
- Shows last 100 delivery attempts
- Status: success (green) / failed (red) / pending (yellow)
- Response body and status code recorded
- Timestamp and duration shown

**API:** View delivery logs:

```python
from huggingface_hub import HfApi

api = HfApi()
webhooks = api.list_webhooks()

# Each WebhookInfo has a `logs` method or field
for webhook in webhooks:
    print(f"{webhook.id}: enabled={not webhook.disabled}")
```

#### 3.3 Replaying Events

Failed deliveries can be replayed via the API:

```python
# Replay a specific delivery log entry
api.replay_webhook_log(
    webhook_id="abc123",
    log_id="log_xyz789"
)
```

This re-sends the exact same event payload to the webhook URL.

**Use case:** After fixing a bug in your receiver, replay all failed deliveries from the last 24h.

#### 3.4 Testing Webhooks Locally

```bash
# Using ngrok to expose local dev server
ngrok http 8000

# Create webhook pointing to ngrok URL
python -c "
from huggingface_hub import HfApi
api = HfApi()
api.create_webhook(
    url='https://your-ngrok.ngrok.io/webhook',
    watched=[{'type': 'user', 'name': 'beer-sakthai'}],
    domains=['repo', 'discussions'],
    secret='test-secret'
)
"
```

**Alternative — `smee.io` (no install):**
1. Go to https://smee.io/new → get a channel URL
2. Run `npx smee --url https://smee.io/your-channel --target http://localhost:8000/webhook`
3. Set webhook URL to `https://smee.io/your-channel`
4. Events flow through smee → your local server

---

### 4. Automation Patterns

#### 4.1 Pattern A: Auto-Run Evaluation on Model Push

Watch a specific model repo. When a new commit is pushed, trigger model evaluation:

```python
# Receiver handler
async def handle_repo_update(event: dict):
    """Trigger evaluation pipeline on model update."""
    repo = event["event"]["repo"]["name"]
    commits = event["event"]["payload"].get("commits", [])

    for commit in commits:
        # Check if model weights changed
        has_weights = any(
            f.endswith(".safetensors") or f.endswith(".bin")
            for f in commit["modified"] + commit["added"]
        )
        if has_weights:
            print(f"Model weights changed in {repo} — triggering evaluation")
            # Start HF Job or local evaluation
            # api.run_job(...)
```

#### 4.2 Pattern B: Agent-Triggered Workflow

When a discussion is opened on a specific repo, have SakThai (or another agent) respond:

```python
async def handle_discussion_opened(event: dict):
    """Route discussion events to the appropriate agent."""
    payload = event["event"]["payload"]
    repo_type = event["event"]["repo"]["type"]
    repo_name = event["event"]["repo"]["name"]

    # Determine agent by repo type
    if repo_type == "model" and "sakthai" in repo_name.lower():
        await notify_agent("sakthai", payload)
    elif repo_type == "space" and "sakking" in repo_name.lower():
        await notify_agent("sakking", payload)

async def notify_agent(agent_name: str, payload: dict):
    """Queue a task for the agent to pick up on next cycle."""
    # Write to shared memory or task queue
    task = {
        "agent": agent_name,
        "type": "discussion_response",
        "discussion_id": payload["discussion_id"],
        "title": payload["discussion_title"],
        "author": payload.get("author", "unknown"),
    }
    # Store in ~/.sakthai/pending-tasks/ for agent pickup
    import json, os
    task_dir = os.path.expanduser("~/.sakthai/pending-tasks")
    os.makedirs(task_dir, exist_ok=True)
    with open(f"{task_dir}/{payload['discussion_id']}.json", "w") as f:
        json.dump(task, f)
```

#### 4.3 Pattern C: Distributed Model Update Notification

Watch an organization to get notified when ANY of its models update:

```python
# Create webhook watching an org
api.create_webhook(
    url="https://auto-builder.example.com/webhook",
    watched=[{"type": "org", "name": "huggingface"}],
    domains=["repo"],
    secret="org-webhook-secret",
)
```

The receiver then filters events by specific repos it cares about.

#### 4.4 Pattern D: CI/CD for Spaces

Automatically rebuild a Space when its source repository updates:

```python
async def handle_repo_update(event: dict):
    """Rebuild Space on source update."""
    repo = event["event"]["repo"]["name"]
    payload = event["event"]["payload"]
    commits = payload.get("commits", [])

    # Check if app files changed
    relevant_files = {"app.py", "requirements.txt", "packages.txt", "Dockerfile"}
    for commit in commits:
        changed = set(commit["modified"] + commit["added"])
        if changed & relevant_files:
            print(f"App files changed — restarting Space")
            # Restart the Space
            api.restart_space(repo_id=repo)
            break
```

#### 4.5 Pattern E: Webhook → HF Job Pipeline

Chain webhooks to HF Jobs for zero-cost serverless compute:

```python
# 1. Create a Job that runs evaluation
job = api.create_job(
    script="evaluate.py",
    requirements="torch\n transformers\ndatasets",
    hardware="cpu-basic",  # Free tier
)

# 2. Create a webhook that triggers the Job
api.create_webhook(
    job_id=job.id,
    watched=[{"type": "model", "name": "Nanthasit/sakthai-model-v0.5b"}],
    domains=["repo"],
)
```

When a push happens to the watched model repo, the Job runs automatically — no server needed.

---

### 5. Security Best Practices

#### 5.1 Always Set a Secret

```python
# Creating a webhook with a strong secret
import secrets

secret = secrets.token_hex(32)  # 64-char hex string
api.create_webhook(
    url="https://your-server.com/webhook",
    watched=[{"type": "user", "name": "your-username"}],
    domains=["repo"],
    secret=secret,
)
```

#### 5.2 Verify Every Request

Always verify the HMAC signature before processing:

```python
def verify_webhook(body: bytes, signature_header: str, secret: str) -> bool:
    """Verify HMAC-SHA256. Constant-time comparison prevents timing attacks."""
    if not secret:
        return False  # Reject unsigned webhooks
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

#### 5.3 Timing Attack Protection

`hmac.compare_digest()` is critical — regular string comparison (`==`) leaks timing information that can be used to forge signatures character by character.

#### 5.4 Additional Hardening

- **Idempotency keys:** Store `event.id` in a set (with TTL) to prevent duplicate processing
- **Rate limiting:** Track events per repo per minute; throttle if > 60/min
- **Input validation:** Sanitize all user-provided fields from the payload before using
- **No secrets in logs:** Mask the `signature` field before logging payloads
- **HTTPS only:** Always use HTTPS URLs for webhook endpoints

```python
# Idempotency middleware
processed_events = set()

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    event = json.loads(body)
    event_id = event["event"]["id"]

    if event_id in processed_events:
        return {"status": "duplicate", "event_id": event_id}

    processed_events.add(event_id)
    # Process event...
    return {"status": "ok"}
```

---

### 6. Troubleshooting

#### 6.1 Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| **401 responses** | Signature mismatch | Verify secret matches on both ends; check body is raw bytes, not read/re-encoded |
| **Timeout** | Receiver takes >10s | Move heavy work to background task; return 200 immediately |
| **No events received** | Webhook disabled | Check Hub UI: `Settings > Webhooks` — is it enabled? |
| **Delayed events** | Backpressure | Your receiver is too slow; scale up or add queue |
| **Duplicate events** | Natural re-delivery | Use idempotency via `event.id` |
| **Missing commits** | Shallow push | Some push events have truncated commit lists; check `head_commit` |

#### 6.2 Testing with Real Payloads

```bash
# Simulate a webhook POST locally
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $(echo -n '{"event":{"type":"update","repo":{"type":"model","name":"test/model"}}}' | openssl dgst -sha256 -hmac 'your-secret' | awk '{print $2}')" \
  -d '{"event":{"type":"update","repo":{"type":"model","name":"test/model"},"payload":{"action":"push","commits":[{"id":"abc123","title":"test","modified":["model.safetensors"]}]}},"signature":{}}'
```

#### 6.3 Debugging Delivery Failures

1. Check the Hub UI `Settings > Webhooks > {hook} > Logs`
2. Look at the response status code and body
3. Replay the failed delivery after fixing the receiver
4. If receiver is down, fix and redeploy, then replay all failed logs
5. For persistent failures, check TLS certificate validity on your endpoint

---

### 7. Webhook Lifecycle Management

#### 7.1 Listing and Auditing

```python
from huggingface_hub import HfApi

api = HfApi()
hooks = api.list_webhooks()

for hook in hooks:
    status = "✅ Enabled" if not hook.disabled else "⛔ Disabled"
    targets = []
    if hook.url:
        targets.append(f"url={hook.url}")
    if hook.job:
        targets.append(f"job={hook.job.job_id}")
    watched = [f"{w.type}:{w.name}" for w in hook.watched]

    print(f"{hook.id[:8]} — {status}")
    print(f"  Target: {', '.join(targets)}")
    print(f"  Watched: {', '.join(watched)}")
    print(f"  Domains: {hook.domains}")
    print(f"  Has secret: {bool(hook.secret)}")
```

#### 7.2 Disabling Without Deleting

```python
# Temporarily disable a webhook (e.g., during maintenance)
api.disable_webhook(webhook_id="abc123")

# Re-enable when ready
api.enable_webhook(webhook_id="abc123")
```

#### 7.3 Updating Webhook Properties

```python
# Change which repos are watched
api.update_webhook(
    webhook_id="abc123",
    watched=[
        {"type": "model", "name": "Nanthasit/sakthai-model-v0.5b"},
        {"type": "model", "name": "Nanthasit/sakthai-model-v1.5b"},
        {"type": "space", "name": "Nanthasit/sakthai-tts-space"},
    ],
)

# Change target URL
api.update_webhook(
    webhook_id="abc123",
    url="https://new-server.example.com/webhook",
)
```

---

### 8. Webhook Payload Cookbook

#### 8.1 Extract Modified Files from a Push Event

```python
def get_modified_files(event: dict) -> dict:
    """Extract lists of added, modified, and removed files from a push event."""
    payload = event["event"]["payload"]
    all_added = []
    all_modified = []
    all_removed = []

    for commit in payload.get("commits", []):
        all_added.extend(commit.get("added", []))
        all_modified.extend(commit.get("modified", []))
        all_removed.extend(commit.get("removed", []))

    return {
        "added": list(set(all_added)),
        "modified": list(set(all_modified)),
        "removed": list(set(all_removed)),
    }

# Usage
files = get_modified_files(event)
if any(f.endswith(".safetensors") for f in files["added"] + files["modified"]):
    print("Model weights changed!")
```

#### 8.2 Check if a Specific File Changed

```python
def file_changed(event: dict, filename: str) -> bool:
    """Check if a specific file was changed in any commit."""
    for commit in event["event"]["payload"].get("commits", []):
        if filename in commit.get("modified", []) + commit.get("added", []):
            return True
    return False

if file_changed(event, "config.json"):
    print("Configuration updated — restarting service")
```

#### 8.3 Determine Repo Type and Owner

```python
def parse_repo_info(event: dict) -> dict:
    """Extract repo metadata from event."""
    repo = event["event"]["repo"]
    name_parts = repo["name"].split("/")
    return {
        "full_name": repo["name"],
        "owner": name_parts[0],
        "repo_name": "/".join(name_parts[1:]),
        "type": repo["type"],
        "private": repo["private"],
        "head_sha": repo.get("headSha"),
    }
```

---

### 9. Integration with Agent Ecosystem

#### 9.1 Agent Task Queue via Webhooks

Architecture for webhook-driven agent workflows:

```
HF Hub Event
    │
    ▼
Webhook POST ──► Receiver (FastAPI/Space)
                        │
                        ▼
              ┌─────────────────┐
              │ pending-tasks/  │ ← Shared file-based task queue
              │                 │
              │ task_123.json   │ ← SakThai picks up on next cron cycle
              │ task_124.json   │ ← SakKing picks up on next cron
              └─────────────────┘
                        │
                        ▼
                  Agent processes
                  task, updates
                  memory/state
```

The receiver writes tasks as JSON files to `~/.sakthai/pending-tasks/` and the agents pick them up on their next cron cycle.

#### 9.2 Webhook-Driven Memory Updates

When a model push happens, automatically update shared memory:

```python
async def handle_model_update(event: dict):
    """Update shared memory when a model version changes."""
    repo = event["event"]["repo"]["name"]
    sha = event["event"]["repo"]["headSha"]
    commits = event["event"]["payload"].get("commits", [])

    # Find what changed
    changes = []
    for commit in commits:
        changes.extend(commit.get("modified", []))
        changes.extend(commit.get("added", []))

    # Update memory
    memory_entry = {
        "type": "model_update",
        "repo": repo,
        "sha": sha,
        "changes": list(set(changes)),
        "timestamp": event["event"]["timestamp"],
    }

    # Write to shared memory
    import json, os
    mem_file = os.path.expanduser("~/.sakthai/memory/events.jsonl")
    os.makedirs(os.path.dirname(mem_file), exist_ok=True)
    with open(mem_file, "a") as f:
        f.write(json.dumps(memory_entry) + "\n")
```

#### 9.3 Monitoring Agent Health via Webhooks

Set up a webhook on the agent's own Spaces/models repos to detect anomalies:

```python
async def monitor_agent_repo(event: dict):
    """Detect unexpected changes to agent repos."""
    repo = event["event"]["repo"]["name"]
    payload = event["event"]["payload"]

    # Check for unexpected file deletions
    for commit in payload.get("commits", []):
        if commit.get("removed"):
            removal = ", ".join(commit["removed"])
            print(f"⚠️ FILES REMOVED from {repo}: {removal}")
            # Alert the user via notification
            # (write to task queue, send notification, etc.)
```

---

### 10. Comparison: Webhook Methods

| Method | Cost | Server Needed | Latency | Best For |
|--------|------|---------------|---------|----------|
| **URL webhook** | Free | Yes (or free tier like Fly/Railway) | ~2-5s | Complex processing, external integration |
| **Job-triggered webhook** | Free (cpu-basic) | No (HF hosts Job) | ~30-60s | Batch evaluation, training, data processing |
| **Smee.io relay** | Free | No (tunnels to localhost) | ~5-10s | Development and testing only |
| **Webhook + Cloudflare Worker** | Free | No (edge function) | ~1-3s | Simple transforms, filtering, forwarding |

---

### Skill Created

`hf-hub-webhooks-practical-patterns-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete event payload schemas, receiver implementations (FastAPI, Flask, Cloudflare Workers), delivery behavior, automation patterns, security best practices, troubleshooting, and agent ecosystem integration patterns.
