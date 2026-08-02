# HF Learnings Log — hf-hub-spaces-custom-domains-replicas-streaming

## 2026-07-25: Hugging Face Spaces — Custom Domains, Replicas, & Streaming Logs/Metrics

### Summary
Deep-dive into three Spaces features not yet covered in existing learnings: custom domain configuration (DNS CNAME setup, verification, removal), horizontal scaling via replicas, and real-time streaming of logs/events/metrics via SSE. Also covers GPU sleep time configuration for cost optimization on paid hardware. Researched official HF docs (spaces-custom-domain, spaces-gpus, spaces-overview, spaces-config-reference).

### Key Findings

#### 1. Custom Domains for Spaces

**Requirement**: PRO or Team/Enterprise plan. NOT available on free tier.

**Visibility constraint**: Custom domains require **public** or **protected** visibility — NOT supported on private Spaces.

**Setup flow**:
1. Go to Space Settings → "Custom Domain" section
2. Enter your domain (e.g., `yourdomain.example.com`)
3. Add a **CNAME record** pointing your domain to `hf.space` at your DNS provider
4. Status shows "pending" until DNS propagates
5. Once DNS resolves correctly, status changes to "ready"

**Verification**: Use Google Dig tool (https://toolbox.googleapps.com/apps/dig/#CNAME/) to confirm your CNAME resolves to `hf.space`.

**Removal**: Delete button in the Custom Domain section of Space Settings. Works for both pending and ready states.

**Key limitations**:
- Only one custom domain per Space
- No wildcard/subdomain wildcards — exact DNS name only
- HTTPS is automatically provisioned (Let's Encrypt via HF proxy)
- Custom domain uses HF's reverse proxy, so your app still runs on HF infrastructure

---

#### 2. Replicas (Horizontal Scaling)

**Availability**: Paid (upgraded) hardware only. Each replica is billed independently.

**API endpoint**:
```
POST https://huggingface.co/api/spaces/{namespace}/{repo}/replicas
Content-Type: application/json

{
  "replicas": 2
}
```

**Behavior**:
- Distributes traffic across multiple instances of your Space
- Improves availability and throughput
- Each replica runs on identical hardware
- No auto-scaling — replicas are set manually and remain fixed
- Billing is per-replica per-hour of the chosen hardware tier

**Use cases**:
- High-traffic demos that outgrow single-instance capacity
- Production-facing applications needing redundancy
- Load-balanced inference endpoints

---

#### 3. Streaming Logs, Events, and Metrics

Three SSE (Server-Sent Events) endpoints for real-time monitoring:

| Endpoint | Purpose | Path |
|----------|---------|------|
| Build/run logs | Live streaming of build or runtime logs | `GET /api/spaces/{namespace}/{repo}/logs/{build\|run}` |
| Status events | Real-time Space lifecycle events | `GET /api/spaces/{namespace}/{repo}/events` |
| Metrics | Real-time hardware/usage metrics | `GET /api/spaces/{namespace}/{repo}/metrics` |

**Authentication**: All three endpoints require HF authentication (token).

**Tail parameter**: `?tail=100` limits response to last N lines (logs endpoint only).

**Protocol**: Standard SSE format — `text/event-stream` content type.

**Use cases**:
- Debugging build failures without refreshing the UI
- Monitoring Space health programmatically
- Building custom dashboards for Space observability
- Alerting on Space restarts or failures

---

#### 4. GPU Sleep Time Configuration

**Default behavior**:
- CPU Basic (free): Sleeps after 48 hours of inactivity
- Paid hardware: Runs indefinitely by default

**Custom sleep time** (paid hardware only):
- Accessible in Space Settings → "Sleep Time" section
- Can set any duration or "never sleep"
- When asleep: Space enters `stopped` stage, billing stops
- On visitor request: Space automatically wakes and restarts
- Wake time depends on Space complexity (build + startup)

**Community GPU Grants**: Available for innovative Spaces needing GPU but unable to pay — application link in Space Settings lower left corner.

---

#### 5. Space Visibility & Network Configuration Summary

| Feature | Public | Protected | Private |
|---------|--------|-----------|---------|
| Source code visibility | Everyone | Owner/collaborators only | Owner/collaborators only |
| App via embed URL | Yes | Yes | No |
| App via custom domain | Yes | Yes | No |
| Clonable by others | Yes | No | No |

**Networking restrictions**: Spaces can make HTTP/HTTPS requests on ports 80, 443, and 8080 only. Other ports blocked.

### Key Takeaways for Zero-Cost Users

- **Custom domains**: Require PRO plan — not available on free tier. Not applicable for Beer's setup.
- **Replicas**: Paid hardware only — each replica adds full billing cost. Not relevant without budget.
- **SSE streaming**: Works on any Space, including CPU Basic. Useful for debugging ZeroGPU Spaces programmatically.
- **Sleep time**: CPU Basic auto-sleeps after 48h — this is fine for free-tier Spaces. No extra config needed.
- **Community GPU grants**: Worth applying for if a ZeroGPU Space grows beyond the 2-Space limit.

### References
- https://huggingface.co/docs/hub/en/spaces-custom-domain
- https://huggingface.co/docs/hub/en/spaces-gpus (sleep time, replicas, streaming sections)
- https://huggingface.co/docs/hub/en/spaces-overview (visibility, networking)
- https://huggingface.co/docs/hub/en/spaces-config-reference (YAML options)
