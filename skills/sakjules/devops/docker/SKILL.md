---
name: docker
description: "Docker & containers — build, run, compose, registry, multi-stage, health checks, and CI/CD integration"
version: 1.0.0
author: SakJules
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Docker, Containers, Compose, CI/CD, DevOps, Automation]
    related_skills: [kubernetes, terraform, github-actions-business-automation]
---

# Docker & Containers

Complete guide for container lifecycle management — from building images to running in CI/CD pipelines. Every command assumes Docker Engine is installed.

## Prerequisites

```bash
# Verify Docker is available
docker --version
docker info  # confirm the daemon is running
```

### Quick Docker Context Detection

```bash
# Check which context/environment we're in
if [ -z "$DOCKER_HOST" ]; then
  echo "Local Docker socket"
fi

# Non-root access check
if ! docker info &>/dev/null 2>&1; then
  echo "Docker needs sudo or user is not in docker group"
  # Try with sudo
  SUDO="sudo"
else
  SUDO=""
fi
```

---

## 1. Building Images