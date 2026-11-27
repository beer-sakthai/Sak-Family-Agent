---
name: SakThai-huggingface-spaces
version: 1.0.0
description: Build, deploy, and maintain applications on Hugging Face Spaces — Gradio
  / Docker / Static SDKs, ZeroGPU and dedicated hardware, model loading, debugging,
  buckets, inference providers, community grants. Use whenever the user asks to create
  or host an
category: mlops
tags:
- huggingface
- spaces
---

# Hugging Face Spaces

Hugging Face Spaces host machine-learning applications. There are 1M+ today; each Space is a git repo. This skill covers creating, building, debugging, and maintaining them.

## 0. Getting ready

Before anything else:

1. Check the `hf` CLI is installed: `which hf`. If not, `pip install -U huggingface_hub`.
2. Check the user is logged in: `hf auth whoami`. If not, run `hf auth login` — it prints a URL and a one-time code; ask the user to open the URL and enter the code, then login completes automatically (OAuth, no token needed). Alternatively, pass a write-scoped token from https://huggingface.co/settings/tokens with `--token`.
3. Note `whoami`'s `canPay` and `isPro` flags — they gate hardware choices below.

The `hf-cli` skill teaches an agent every `hf` command and is the recommended companion to this one. Install it with `hf skills add hf-cli` (add `--claude --global` to install for Claude Code as well, user-level).

## 1. What a Space is

A Space is a git repo with three possible SDKs:

- **Gradio** — most Spaces. Python, fast iteration, supports ZeroGPU.
- **Docker** — arbitrary container. Use when you need a non-Python stack or a pre-built template (Streamlit, Argilla, Shiny, etc. — full list at https://huggingface.co/docs/hub/spaces-sdks-docker). Does **not** support ZeroGPU.
- **Static** — plain HTML, or a React/Svelte/Vue project built at deploy time. Use for in-browser ML (transformers.js / WebGPU / WebAssembly / onnxruntime-web), project pages, interactive reports, or Spaces that orchestrate other Spaces. No hardware needed.

### Hardware tiers

Free, no creator cost: **`cpu-basic`** and **`zero-a10g`** (ZeroGPU). Static Spaces are also free and don't need hardware.

**`cpu-basic`** — 2 vCPU / 16 GB. For data viz, API-proxy Spaces, small CPU-bound models.

**ZeroGPU (`zero-a10g`)** — dynamic, per-request GPU allocation on NVIDIA RTX PRO 6000 Blackwell (sm_120). Two sizes: `large` (half MIG, 48 GB, 1× quota) and `xlarge` (full, 96 GB, 2× quota). Free for the Space creator; Space visitors consume their own daily quota (~5 min free / 40 min Pro / 60 min Enterprise). **Gradio-only**, **PyTorch-first**. Requires the creator to be on a PRO / Team / Enterprise plan.

**Dedicated GPU** (T4, L4, A10G, L40S, A100, H200) — billed to the Space creator by the hour. List + pricing: `hf spaces hardware`. Only the creator can attach these, and only if `canPay=True`. Use when ZeroGPU genuinely doesn't fit — non-PyTorch main model with heavy init, very-large-model long-context inference, etc.

If a non-PRO user has a use case that wants ZeroGPU, you can still build it: create a `cpu-basic` Space, code the app for ZeroGPU, push, then request a community grant. See [`references/grants.md`](references/grants.md).

For the authoritative reference: https://huggingface.co/docs/hub/spaces-overview

## 2. Look for an existing demo first

Before deciding how to build anything, search for prior art:

```bash
hf spaces search "<model name or task>" --sdk gradio --limit 10
```

If someone has built a similar Space, read its `app.py` and `requirements.txt` — that gives you the working pattern. Saves a lot of blind iteration. Mention to the user what you found before committing to an approach.

## 3. Decide SDK and hardware

Follow the user's explicit request first. If they were vague:

- **Default for a public ML demo**: Gradio + ZeroGPU. Use this unless something below applies.
- **The model's only inference path is non-PyTorch** (ONNX / TF / JAX / vLLM as the MAIN model, with heavy init): dedicated GPU.
  - But: marginal non-torch tools (a small ONNX preprocessor, a TF utility) inside a torch-main pipeline are fine on ZeroGPU. The hijack only patches torch; init the non-torch lib inside `@spaces.GPU` and pay the short per-call init cost.
- **Tiny / CPU-bound model, or API-proxy Space**: `cpu-basic` (`hardware`-free isn't applicable to Gradio).
- **Browser-side ML or project page**: Static.
- **Container with non-Python stack**: Docker.

### Sourcing the model

- **GitHub repo** — clone locally to read structure. If it already has a Gradio demo, the minimal viable path is to adapt it onto ZeroGPU (see [`references/zerogpu.md`](references/zerogpu.md)). Otherwise: read the README + inference code, prefer the PyTorch path, estimate VRAM (bf16 ≈ `params_B × 2` GB; 48 GB fits ≤24B params at bf16, or much larger with quantization — see [`references/zerogpu.md`](references/zerogpu.md) for quantization on ZeroGPU).
- **HF model repo** — read its README, follow any linked GitHub.
- **Paper / blog post** — look for an official or unofficial implementation. Don't reimplement unless trivial or the user explicitly asks.
- **Vague request** — search Spaces first; surface results.

If the model genuinely won't fit, check **Inference Providers** as an alternative: see [`references/inference-providers.md`](references/inference-providers.md). This avoids hosting the model at all.

## 4. Create the Space

```bash
hf repos create <namespace>/<name> --type space --space-sdk <gradio|docker|static> \
    [--flavor zero-a10g|cpu-basic|<paid-flavor>] \
    [--secrets KEY=val] [--env KEY=val] \
    --public|--private|--protected \
    --exist-ok
```

- `--space-sdk` is required.
- `--flavor` selects hardware. `zero-a10g` is the (legacy) identifier for ZeroGPU. Omit for `cpu-basic`. Run `hf spaces hardware` for the full paid list and pricing.
- Visibility: `--public` (anyone can view), `--private` (only you), `--protected` (app is reachable but git repo / Files tab is private).
- `--secrets KEY=val` becomes an environment variable inside the Space and is **not** visible to visitors. Use for API keys, gated-repo tokens (`HF_TOKEN=hf_…`), etc. Can also be set later via `hf spaces secrets set <id> KEY=val`.
- `--env KEY=val` is **visible to visitors** — use only for non-sensitive config (`GRADIO_SSR_MODE=false`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, etc.).

> Note: `hardware:` in the README YAML is silently ignored — hardware is only set via `--flavor` at creation, or later via `hf spaces settings <id> --hardware <name>`.

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Spaces App Architecture Patterns, Docker & Hardware Secrets](./references/spaces-app-patterns-and-hardware.md).
