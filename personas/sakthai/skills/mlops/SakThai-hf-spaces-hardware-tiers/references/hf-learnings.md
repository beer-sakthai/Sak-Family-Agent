# HF Learnings: Hugging Face Spaces Hardware Tiers — Complete Reference

## 2026-07-25: hf-spaces-hardware-tiers-deep-dive

### Summary
Comprehensive deep dive into all Hugging Face Spaces hardware options: CPU tiers, GPU accelerators, ZeroGPU, billing model, programmatic configuration, replicas, streaming telemetry, and best practices. Based on the official HF Spaces doc, pricing page, and GPU upgrades guide.

### Complete Hardware Tier Reference

**CPU Tiers:**

| Name | vCPU | Memory | Disk | Hourly Price | Notes |
|------|------|--------|------|-------------|-------|
| CPU Basic | 2 vCPU | 16 GB | 50 GB | **Free** | Goes to sleep after 48h inactivity. Creating new Spaces on compute requires paid plan; Static Spaces are always free. |
| CPU Upgrade | 8 vCPU | 32 GB | 50 GB | $0.03/hr | Runs indefinitely by default. Can set custom sleep time. |

**GPU Tiers:**

| Name | vCPU | Memory | GPU | VRAM | Disk | Hourly Price |
|------|------|--------|-----|------|------|-------------|
| Nvidia T4 - small | 4 vCPU | 15 GB | 1× T4 | 16 GB | 50 GB | $0.40 |
| Nvidia T4 - medium | 8 vCPU | 30 GB | 1× T4 | 16 GB | 100 GB | $0.60 |
| 1× Nvidia L4 | 8 vCPU | 30 GB | 1× L4 | 24 GB | 400 GB | $0.80 |
| 4× Nvidia L4 | 48 vCPU | 186 GB | 4× L4 | 96 GB | 3200 GB | $3.80 |
| 1× Nvidia L40S | 8 vCPU | 62 GB | 1× L40S | 48 GB | 380 GB | $1.80 |
| 4× Nvidia L40S | 48 vCPU | 382 GB | 4× L40S | 192 GB | 3200 GB | $8.30 |
| 8× Nvidia L40S | 192 vCPU | 1534 GB | 8× L40S | 384 GB | 6500 GB | $23.50 |
| Nvidia A10G - small | 4 vCPU | 15 GB | 1× A10G | 24 GB | 110 GB | $1.00 |
| Nvidia A10G - large | 12 vCPU | 46 GB | 1× A10G | 24 GB | 200 GB | $1.50 |
| 2× Nvidia A10G - large | 24 vCPU | 92 GB | 2× A10G | 48 GB | 1000 GB | $3.00 |
| 4× Nvidia A10G - large | 48 vCPU | 184 GB | 4× A10G | 96 GB | 2000 GB | $5.00 |
| Nvidia A100 - large | 12 vCPU | 142 GB | 1× A100 | 80 GB | 1000 GB | $2.50 |
| 4× Nvidia A100 | 48 vCPU | 568 GB | 4× A100 | 320 GB | 4000 GB | $10.00 |
| 8× Nvidia A100 | 96 vCPU | 1136 GB | 8× A100 | 640 GB | 8000 GB | $20.00 |

**H100 removed December 2025.** No longer available for Spaces.

**ZeroGPU (PRO required, $9/mo):**

| Property | Value |
|----------|-------|
| Accelerator | Nvidia RTX Pro 6000 Blackwell (dynamic allocation) |
| VRAM | Up to 96 GB (shared dynamic pool) |
| Cost | **Free** with PRO subscription ($9/mo) |
| PRO Quota | 8× higher quota than free users, highest queue priority |
| Free Quota | Very limited (shared queue, lower priority) |
| Best for | Demos, experimentation, small-to-medium models |

### Billing Model

- **Billed by the minute** on the selected hardware
- **Only Starting and Running states are billed** — building, paused, and sleep are free
- **Free hardware (CPU Basic):** Space auto-sleeps after 48h of inactivity, woken by any visitor
- **Paid hardware:** Runs indefinitely by default; can set custom sleep time in settings (not billed while sleeping)
- **Pausing:** Can pause from repo settings — paused Spaces are not billed. Only owner can restart.
- **Auto-suspension:** If a running Space starts to fail, it's automatically suspended → billing stops
- **Replicas:** Each replica is billed independently at the hourly rate

### Programmatic Configuration

**Set hardware** (via huggingface_hub Python library):
```python
from huggingface_hub import HfApi
api = HfApi()
api.request_space_hardware(
    repo_id="username/my-space",
    flavor="t4-small",
    sleep_time=3600  # seconds before auto-sleep, 0 = never sleep
)
```

**Available `flavor` values:** `"cpu-basic"`, `"cpu-upgrade"`, `"t4-small"`, `"t4-medium"`, `"l4x1"`, `"l4x4"`, `"l40sx1"`, `"l40sx4"`, `"l40sx8"`, `"a10g-small"`, `"a10g-large"`, `"a10g-largex2"`, `"a10g-largex4"`, `"a100-large"`, `"a100x4"`, `"a100x8"`.

**Set replicas:**
```bash
curl -X POST https://huggingface.co/api/spaces/{namespace}/{repo}/replicas \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"replicas": 2}'
```

### Built-in Environment Variables (at runtime)

| Variable | Example | Description |
|----------|---------|-------------|
| `ACCELERATOR` | `t4-medium`, `a10g-small`, `none` | Type of accelerator available |
| `CPU_CORES` | `4` | Number of CPU cores |
| `MEMORY` | `15Gi` | Available memory |
| `SPACE_AUTHOR_NAME` | `osanseviero` | Space author |
| `SPACE_REPO_NAME` | `i-like-flan` | Space repo name |
| `SPACE_TITLE` | `I Like Flan` | From README metadata |
| `SPACE_ID` | `osanseviero/i-like-flan` | Full space identifier |
| `SPACE_HOST` | `osanseviero-i-like-flan.hf.space` | Public hostname |

### Streaming Telemetry (SSE, authenticated)

- **Build/Run Logs:** `GET /api/spaces/{namespace}/{repo}/logs/{build|run}?tail=100`
- **Status Events:** `GET /api/spaces/{namespace}/{repo}/events`
- **Metrics:** `GET /api/spaces/{namespace}/{repo}/metrics`
- All require `Authorization: Bearer {token}` header
- Return data via Server-Sent Events (SSE) protocol

### Community GPU Grants

HF offers free GPU upgrade grants for innovative side projects. Apply from Space Settings → lower left corner under "sleep time settings". No official cap on grant value mentioned — case-by-case.

### Networking Rules

- Allowed ports: HTTP (80), HTTPS (443), and 8080
- All other outbound ports are blocked

### PRO Plan Impact on Spaces

| Feature | Free | PRO ($9/mo) |
|---------|------|-------------|
| ZeroGPU | Very limited | 8× quota, highest priority |
| Gradio/Docker Spaces | Requires paid plan to create new | Included |
| Spaces Dev Mode (SSH/VS Code) | Not available | Included |
| Custom sleep time | Not available on free | Available on paid hardware |
| Persistent storage | ~10 GB | 10× private storage |

### Key Takeaways for Zero-Cost Users

1. **CPU Basic** is the only truly free always-on compute tier — 2 vCPU, 16 GB RAM, 50 GB disk, auto-sleeps
2. **Static Spaces** (pure HTML/JS/CSS) are always free for everyone regardless of plan
3. **ZeroGPU** is the cheapest GPU option but requires PRO ($9/mo) — use only if $9/mo budget exists
4. **Existing free Spaces continue running** even without a paid plan (you just can't create new compute Spaces)
5. **Pause unused paid Spaces** immediately to avoid billing — paused time is not charged
6. **Community GPU Grants** — apply for free GPU upgrades on side projects from Space Settings
7. **Sleep time on paid hardware** — set this to auto-pause after inactivity; sleeping is not billed

### Skill Created
`mlops/hf-spaces-hardware-tiers/` — complete reference with full hardware spec tables, billing model, programmatic configuration API, environment variables, and zero-cost optimization strategies.
