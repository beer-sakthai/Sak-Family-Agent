# HF Learnings — Spaces Lifecycle Management

## Topic: hf-spaces-lifecycle — Hugging Face Spaces Sleep, Pause, Billing & Duration Management (Topic #268)

### Summary
Comprehensive deep-dive on Hugging Face Spaces lifecycle management — covering
the complete sleep/pause/billing lifecycle for free (cpu-basic) and paid (GPU
upgraded) hardware tiers. Key findings:

- **Free tier**: Auto-sleep after 48h inactivity, no custom sleep time, anyone
  can wake by visiting. Manual pause available.
- **Paid hardware**: Runs indefinitely by default, custom sleep time
  configurable via Settings or API (`sleep_time` param). No billing while asleep.
- **Pause**: Manual pause available on all tiers, only owner can resume, no
  billing while paused.
- **Billing**: Per-minute on `Starting`/`Running` states only. Build time and
  pause/sleep time are NOT billed. Auto-suspend on repeated failures.
- **ZeroGPU**: Free GPU with dynamic allocation via `@spaces.GPU` decorator.
  Daily quotas: Free=5min, PRO=40min, Team=40min, Enterprise=60min.
  Duration configurable (default 60s, dynamic callable supported).
  No `torch.compile()` — use AOT compilation (torch 2.8+).
  Free accounts capped at 2 ZeroGPU Spaces.
- **Programmatic control**: `api.request_space_hardware()`, `api.pause_space()`,
  `api.resume_space()` via `huggingface_hub`.
- **Live monitoring**: SSE streaming endpoints for logs, events, and metrics.
- **Zero-cost strategy**: cpu-basic + ZeroGPU (5min/day) + manual pausing of
  unused Spaces = completely free operation.

### Source
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
- HF Spaces GPU: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Spaces ZeroGPU: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Spaces Settings: https://huggingface.co/docs/hub/en/spaces-settings
- HF Spaces Config: https://huggingface.co/docs/hub/en/spaces-config-reference
- ZeroGPU AOT Blog: https://huggingface.co/blog/zerogpu-aoti

### Skill
mlops/hf-spaces-lifecycle — Complete reference for HF Spaces lifecycle:
auto-sleep (free 48h vs paid custom), manual pause/resume, per-minute billing
model, ZeroGPU dynamic allocation with daily quotas, programmatic hardware
control via HfApi, SSE streaming, and zero-cost operation strategies
