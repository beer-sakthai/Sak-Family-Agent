---
name: SakThai-hf-inference-endpoints-custom-containers
description: "Deep-dive into deploying custom Docker containers to Hugging Face Inference Endpoints — FastAPI server patterns, Docker packaging, model mounting, autoscaling, monitoring, and production best practices."
---

# hf-inference-endpoints-custom-containers

## Description
Deep-dive into deploying custom Docker containers to Hugging Face Inference Endpoints (dedicated). Covers the complete lifecycle: FastAPI server patterns, Docker packaging, model mounting at `/repository`, endpoint configuration, environment secrets, autoscaling, analytics/monitoring via OpenMetrics, AWS PrivateLink, security, and production best practices.

## Key Concepts
- **Custom containers** are needed when no built-in inference engine (vLLM, TGI, TEI, SGLang, llama.cpp) supports your model or you need custom inference logic
- **Model is mounted at `/repository`** — never bake weights into the image; the platform downloads them from the Hub and mounts them
- **FastAPI ModelManager pattern** — lifecycle-managed model loading with startup/shutdown hooks and health check endpoint
- **Docker best practices** — non-root user, multi-stage build, platform targeting (`linux/amd64`), layer caching
- **Endpoint configuration** — hardware selection (GPU/CPU/INF2), auth modes (private/public/authenticated), autoscaling, scale-to-zero, tags
- **OpenMetrics API** — export real-time metrics to Prometheus/Grafana/Datadog (Team/Enterprise feature)
- **Zero-cost alternative** — Serverless Inference Providers for light workloads; custom containers require paid GPU instances

## References
- `references/hf-learnings.md` — full research notes

## Metadata
- **author**: SakThai
- **license**: MIT
- **created**: 2026-07-25
- **deepened**: 2026-07-25 (Custom Router, updated Dockerfile pattern, Download Pattern, Endpoint States)
- **topic**: hf-inference-endpoints-custom-containers-deep-dive
