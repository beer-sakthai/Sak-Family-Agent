---
name: SakJules-SakThai-hf-spaces-lifecycle
description: ">   Complete reference for Hugging Face Spaces lifecycle management — auto-sleep   behavior on free vs paid hardware, custom sleep time configuration, manual   pause/resume workflow, billing model (per-minute billing, no-cost build phase,   no billin"
---

# HF Spaces Lifecycle Management — Sleep, Pause, Billing & Duration

## Overview

Hugging Face Spaces provides a comprehensive lifecycle management system
controlling when Spaces run, sleep, and bill. Understanding these mechanics is
critical for zero-cost operation — especially for users with no budget for paid
hardware.

## Free Tier (cpu-basic) Behavior

| Aspect | Detail |
|--------|--------|
| **Auto-sleep** | Space goes to sleep after 48 hours of inactivity |
| **Wake trigger** | Any visitor to the Space URL automatically restarts it |
| **Custom sleep time** | Not available on free tier |
| **Max ZeroGPU Spaces** | 2 per free personal account (30+ days old, verified email) |
| **Pause** | Manual pause available from Settings tab |

## Paid Hardware (GPU Upgraded) Behavior

| Aspect | Detail |
|--------|--------|
| **Default** | Runs indefinitely, never sleeps |
| **Custom sleep time** | Configurable in hardware settings — choose from preset intervals |
| **Sleep behavior** | Space enters `stopped` stage; no billing while asleep |
| **Wake trigger** | Automatic on next visitor request |
| **Replicas** | Horizontal scaling available (each billed independently) |
| **Pause** | Manual pause available; only owner can restart; no billing while paused |

## Pause/Resume Flow

1. Navigate to Space **Settings** tab
2. Click **Pause** at the bottom of the page
3. Space stops executing immediately
4. Only the Space owner can restart (click **Resume**)
5. Paused time is **not billed**
6. Pause is available on **all hardware tiers** (free + paid)

## Billing Model

- **Per-minute billing**: Charged for every minute the Space is in `Starting`
  or `Running` state
- **Build time**: Not billed — only runtime counts
- **Auto-suspend on failure**: Repeatedly failing Spaces are automatically
  suspended to stop billing
- **Free tier auto-sleep**: After ~48 hours of inactivity on cpu-basic
- **Paid hardware**: Run indefinitely unless custom sleep time is set
- **Downgrading**: To stop billing, change to CPU basic or pause the Space

## ZeroGPU Dynamic GPU Allocation

ZeroGPU provides **free GPU compute** with dynamic allocation per-request:

### Daily Quota Tiers

| Account Type | Daily GPU Quota | Queue Priority |
|---|---|---|
| Unauthenticated | 2 minutes | Low |
| Free account | 5 minutes | Medium |
| PRO account | 40 minutes (extensible) | Highest |
| Team org member | 40 minutes (extensible) | Highest |
| Enterprise org member | 60 minutes (extensible) | Highest |

- Quota resets 24 hours after first GPU usage
- PRO/Team/Enterprise can extend quota at $1/10 min with credits

### Duration Management

Default GPU function runtime: **60 seconds**. Configure via decorator:

```python
@spaces.GPU(duration=120)
def generate(prompt):
    return pipe(prompt).images
```

**Dynamic duration** — pass a callable returning the needed duration:

```python
def get_duration(prompt, steps):
    return steps * 3.75

@spaces.GPU(duration=get_duration)
def generate(prompt, steps):
    return pipe(prompt, num_inference_steps=steps).images
```

Shorter durations → better queue priority for visitors.

### GPU Size Selection

- `large` (default): Half NVIDIA RTX Pro 6000 Blackwell
- `xlarge`: Full GPU (2× quota consumption, higher queue probability)

### Hosting Limitations

| Account | Max ZeroGPU Spaces |
|---|---|
| Free personal | 2 |
| PRO personal | 10 |
| Team/Enterprise org | 50 |

### Compilation

- `torch.compile()` NOT supported on ZeroGPU
- Use **ahead-of-time (AOT) compilation** (torch 2.8+)
- See [ZeroGPU AOT blogpost](https://huggingface.co/blog/zerogpu-aoti)

## Programmatic Hardware Configuration

The `huggingface_hub` library's `HfApi` provides hardware management:

```python
from huggingface_hub import HfApi
api = HfApi()

# Change hardware (paid only for GPU)
api.request_space_hardware(
    repo_id="user/my-space",
    hardware="t4-medium",
    sleep_time=30  # custom sleep time in seconds (0 = never)
)

# Or set hardware to cpu-basic (free)
api.request_space_hardware(
    repo_id="user/my-space",
    hardware="cpu-basic"
)

# Pause a Space
api.pause_space("user/my-space")

# Resume a Space
api.resume_space("user/my-space")
```

## Sleep Time Options (Paid Hardware)

When using upgraded hardware, sleep time can be configured:
- **Never** (default): Space runs indefinitely
- **Custom intervals**: Preset options in the Settings UI dropdown
- Sleep time is billed only when Space is active
- Space auto-wakes on visitor request

## Built-in Environment Variables

Spaces expose runtime environment variables useful for lifecycle-aware apps:

| Variable | Description |
|---|---|
| `ACCELERATOR` | GPU type (e.g. `t4-medium`) or `none` |
| `CPU_CORES` | 4 (default) |
| `MEMORY` | 15Gi (default) |
| `SPACE_AUTHOR_NAME` | Username of Space author |
| `SPACE_REPO_NAME` | Repo name |
| `SPACE_TITLE` | Title from README |
| `SPACE_ID` | Full `author/repo` identifier |
| `SPACE_HOST` | Subdomain hostname |
| `SPACE_CREATOR_USER_ID` | User ID (useful for org Spaces) |

## Streaming Logs & Events (SSE)

Real-time monitoring endpoints (require authentication):

| Endpoint | Description |
|---|---|
| `GET /api/spaces/{ns}/{repo}/logs/build` | Build logs |
| `GET /api/spaces/{ns}/{repo}/logs/run` | Runtime logs |
| `GET /api/spaces/{ns}/{repo}/events` | Status events |
| `GET /api/spaces/{ns}/{repo}/metrics` | Performance metrics |

Optional query param: `?tail=100` for last N lines.

## Zero-Cost Strategy Summary

1. **Use cpu-basic** for always-on Spaces → auto-sleeps after 48h
2. **Pause unused Spaces** manually → zero billing while paused
3. **Use ZeroGPU** for GPU demos → 5 min/day free quota
4. **Keep duration short** on ZeroGPU → better queue priority
5. **Free account limit**: max 2 ZeroGPU Spaces
6. **No paid hardware needed** if you can tolerate sleep/wake cycles

## Sources

- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
- HF Spaces GPU: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Spaces ZeroGPU: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Spaces Settings: https://huggingface.co/docs/hub/en/spaces-settings
- HF Spaces Config: https://huggingface.co/docs/hub/en/spaces-config-reference
- HF Spaces Changelog: https://huggingface.co/docs/hub/en/spaces-changelog
- ZeroGPU AOT Blog: https://huggingface.co/blog/zerogpu-aoti
- HF Inference Providers Docs: https://huggingface.co/docs/inference-providers/en/index
