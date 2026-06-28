---
name: hf-inference-endpoints
description: "Hugging Face Inference Endpoints: dedicated, scalable model hosting on HF infrastructure — hardware selection, autoscaling, private networking, custom handlers, and the deployment lifecycle."
tags: [huggingface, inference, endpoints, deployment, serving, autoscaling, gpu, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face Inference Endpoints

Dedicated, scalable model hosting on Hugging Face infrastructure — distinct from Inference Providers (serverless, third-party) and Inference API (shared free tier). Inference Endpoints gives you a **private, reserved URL** for your model with configurable hardware, autoscaling, and enterprise-grade networking.

## Endpoints vs Providers vs API

| Product | Hosting | Hardware | Pricing | Best for |
|---------|---------|----------|---------|----------|
| **Inference Endpoints** | Dedicated HF infra | Choose GPU/CPU/ZeroGPU | Per-second, reserved | Production, private models, predictable latency |
| **Inference Providers** | Third-party serverless | Partner-selected | Per-request | Experimentation, broad model access without infra |
| **Inference API (free)** | Shared HF pool | Mixed | Free / rate-limited | Quick tests, non-commercial |

## Hardware Options

- **CPU** — cheap, good for small models or batch tasks.
- **GPU** (A10G, T4, L4, A100, H100, etc.) — standard choice for LLMs and diffusion.
- **ZeroGPU** — dynamic GPU allocation with fallback to CPU; lower cost, ideal for Gradio Spaces with intermittent GPU needs.
- **Custom** — select exact instance type from HF catalog at deploy time.

## Autoscaling & Replicas

- **Min replicas** — warm pool kept alive for zero cold-start latency.
- **Max replicas** — upper bound for load-based scaling.
- **Scale-to-zero** — endpoint spins down when idle (no billing), but incurs a cold start on next request.
- **Cooldown period** — controls how long the endpoint waits before scaling down after the last request.

### Cold Starts

A cold start happens when no warm replica exists. Variables:
1. **Image pull** — pulling the base runtime image (usually ~1–3s after first boot).
2. **Model download / cache load** — pulling weights from Hub into local disk; mitigated when weights are pre-cached in the image.
3. **Framework boot** — importing `transformers`, `diffusers`, loading model into VRAM.

Tips to reduce cold starts:
- Use `min_replicas >= 1` during business hours.
- Pin a specific `runtime` tag to avoid pulling latest on every scale event.
- Keep model weights small or use CPU offload for memory-bound cases.

## Deployment Lifecycle

### 1. Create via UI or CLI

```python
from huggingface_hub import HfApi

api = HfApi()

endpoint = api.create_inference_endpoint(
    model="meta-llama/Llama-2-7b-chat-hf",
    name="llama-2-7b-endpoint",
    provider={
        "region": "us-east-1",
        "vendor": "aws",
        "instance_type": "g5.xlarge",  # A10G GPU
    },
    framework="pytorch",
    task="text-generation",
    min_replicas=1,
    max_replicas=3,
)
```

### 2. Runtime & Custom Code

- **Framework** — choose `pytorch`, `tensorflow`, `pytorch-lts`, `text-generation-inference` (TGI), etc.
- **Custom handler** — drop a `handler.py` next to your model repo on the Hub to override inference logic (pre/post processing, custom tokenization).
- **Environment variables** — inject API keys, thresholds, or flags via endpoint settings.
- **Secrets** — store sensitive strings (e.g., other API keys) in Hub secrets and reference them.

### 3. Call the Endpoint

Once deployed, Hugging Face gives you a unique URL:

```
https://<your-endpoint-id>.<region>.inference.endpoints.huggingface.cloud
```

Call it like any OpenAI-compatible or HF Inference API endpoint:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(model="<endpoint-url>", token="<hf_token>")
output = client.text_generation("Hello world")
```

## Key Configuration Fields

| Field | Example | Notes |
|-------|---------|-------|
| `model` | `org/repo` | Must be a Hub model repo (can be private). |
| `framework` | `text-generation-inference` | Determines the Docker runtime. |
| `instance_type` | `g5.xlarge` | Cloud vendor instance; pick from HF catalog. |
| `region` | `us-east-1` | AWS / GCP / Azure region. |
| `min_replicas` / `max_replicas` | 1 / 5 | Autoscaling bounds. |
| `scale_to_zero` | `true` | Enable / disable idle spin-down. |
| `timeout` | `60` | seconds before request aborts. |

## Security & Networking

- **Private networking** — VPC peering or PrivateLink available on Enterprise plans.
- **IAM / tokens** — endpoint accepts standard HF tokens (`read` for inference).
- **Webhooks & monitoring** — HF Posts usage metrics; Enterprise tier exposes Prometheus / Grafana endpoints.
- **Model access control** — if the underlying model repo is private, only users with `read` access can call the endpoint.

## Cost Model

- **Compute**: per-second billing for the selected instance type.
- **Traffic**: ingress is free; egress billed at cloud provider rates.
- **Storage**: model weights stored in Hub repos (no extra charge beyond regular Hub storage).
- **ZeroGPU**: billed per-second only when GPU is allocated; falls back to CPU during idle.

## When to Use Endpoints

| Scenario | Choose Endpoints? |
|----------|-------------------|
| Production LLM serving | Yes — dedicated, autoscaling, private URL. |
| Batch processing / offline inference | Yes — min_replicas=0 to save cost. |
| Internal corporate models | Yes — private repos + private networking. |
| Interactive demos | Consider ZeroGPU or Gradio Space for cheaper, simpler UX. |
| Third-party model access | No — use Inference Providers instead. |

## References

- **Docs**: https://huggingface.co/docs/inference-endpoints/index
- **Hardware catalog**: https://huggingface.co/docs/inference-endpoints/hardware
- **Python SDK**: https://huggingface.co/docs/huggingface_hub/package_reference/inference_endpoints
- **Custom handlers**: https://huggingface.co/docs/inference-endpoints/custom-handlers