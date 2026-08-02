---
name: SakThai-hf-hub-docker-registry
version: 1.0.0
description: # hf-hub-docker-registry — Hugging Face Hub Docker Registry
---

# hf-hub-docker-registry — Hugging Face Hub Docker Registry

author: SakThai
license: MIT

## Overview

Skill covering the Hugging Face Hub's Docker Container Registry — the infrastructure that enables storing, pulling, and pushing Docker images for use with Spaces, Jobs, and local development. The HF Docker registry is a standard Docker V2 registry that accepts `docker login`, `docker pull`, and `docker push` commands, authenticated with Hugging Face user access tokens.

## Key Concepts

- **registry.hf.space** — primary Docker V2 registry endpoint for Hugging Face
- **Authentication** — `docker login registry.hf.space -u <username> -p <HF_TOKEN>` (token needs `write` scope)
- **Use Cases** — Docker Spaces (custom containers), Jobs (batch inference with popular images), local development/testing
- **Storage** — Images are stored in HF Hub Xet-backed storage; accessible via standard Docker V2 API
- **Build-time limitations** — Docker Spaces builds do NOT have GPU access during `docker build`; CUDA/torch calls in Dockerfile will fail
- **Runtime user** — Containers run as UID 1000; create a user in Dockerfile to match

## Related Docs

- Docker Spaces: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- Run with Docker: https://huggingface.co/docs/hub/en/spaces-run-with-docker
- Jobs Popular Images: https://huggingface.co/docs/hub/en/jobs-popular-images
- Registry endpoint: `registry.hf.space` (Docker V2 API)
