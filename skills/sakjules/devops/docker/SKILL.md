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

### Basic Build

```bash
# Simple build from Dockerfile in current dir
$SUDO docker build -t myapp:latest .

# Build with a specific Dockerfile
$SUDO docker build -f deploy/Dockerfile.prod -t myapp:prod .

# Build and tag with multiple tags
$SUDO docker build -t myapp:latest -t myapp:1.0.0 .
```

### Multi-Stage Builds

A production-ready Dockerfile pattern:

```dockerfile
# syntax=docker/dockerfile:1
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup --system app && adduser --system app
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

Build the multi-stage image:

```bash
$SUDO docker build -t myapp:latest .
```

### Multi-Architecture Builds

```bash
# Set up QEMU emulators (once per machine)
$SUDO docker run --privileged --rm tonistiigi/binfmt --install all

# Create a builder that supports multi-arch
$SUDO docker buildx create --use --name multiarch --driver docker-container
$SUDO docker buildx inspect --bootstrap

# Build and push for amd64 + arm64
$SUDO docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/beer-sakthai/myapp:latest \
  -t ghcr.io/beer-sakthai/myapp:1.0.0 \
  --push .
```

### Build Best Practices

| Practice | Why |
|----------|------|
| **Pin base images** | Use `node:20-alpine@sha256:...` not `node:20` — avoids surprise upstream changes |
| **Layer ordering** | Copy `package*.json` first, run install, THEN copy source — maximizes cache hits |
| **`.dockerignore`** | Exclude `node_modules`, `.git`, `*.md`, `tests/` to keep context small and secure |
| **Multi-stage** | Separate build deps from runtime — final image is leaner and has no attack surface from build tools |
| **Non-root user** | Always add and switch to a non-root user in the final stage |
| **Healthcheck** | Every service image should declare a HEALTHCHECK for orchestration tools |

### .dockerignore Template

```
node_modules
.git
.gitignore
*.md
tests/
coverage/
.dockerignore
Dockerfile
.env
.env.*
```

---

## 2. Running Containers

### Basic Run

```bash
# Run interactively with port mapping
$SUDO docker run -it --rm -p 3000:3000 myapp:latest

# Detached mode with a name
$SUDO docker run -d --name myapp -p 3000:3000 myapp:latest

# With environment variables
$SUDO docker run -d --name myapp \
  -e NODE_ENV=production \
  -e DATABASE_URL=postgres://... \
  -p 3000:3000 \
  myapp:latest

# Mount a volume
$SUDO docker run -d --name myapp \
  -v /host/path:/container/path \
  -v myapp_data:/data \
  myapp:latest
```

### Resource Limits

```bash
# CPU and memory limits
$SUDO docker run -d --name myapp \
  --memory="512m" \
  --cpus="1.0" \
  --memory-reservation="256m" \
  --oom-kill-disable=false \
  myapp:latest

# Read-only root filesystem (security hardening)
$SUDO docker run -d --name myapp \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  myapp:latest
```

### Logging & Debugging

```bash
# Follow logs
$SUDO docker logs -f myapp

# Tail last N lines
$SUDO docker logs --tail 100 myapp

# Exec into a running container
$SUDO docker exec -it myapp /bin/sh

# Inspect container details
$SUDO docker inspect myapp

# View resource usage
$SUDO docker stats myapp

# Copy files out of a container
$SUDO docker cp myapp:/app/logs/app.log ./app.log
```

---

## 3. Docker Compose

### Basic Compose File

```yaml
# docker-compose.yml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://user:***@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    healtcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    healtcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M

volumes:
  pgdata:
```

### Compose Commands

```bash
# Start all services (build if needed)
$SUDO docker compose up -d

# Build and start
$SUDO docker compose up -d --build

# View logs from all services
$SUDO docker compose logs -f

# View logs from specific service
$SUDO docker compose logs -f app

# Stop and remove
$SUDO docker compose down

# Stop and remove with volumes (DESTRUCTIVE)
$SUDO docker compose down -v

# Restart a specific service
$SUDO docker compose restart app

# Run a one-off command
$SUDO docker compose run --rm app npm test

# Scale a service
$SUDO docker compose up -d --scale app=3
```

### Compose Profiles

```yaml
services:
  app:
    image: myapp:latest
    ports: ["3000:3000"]

  db:
    image: postgres:16-alpine
    profiles: ["dev", "staging"]  # only starts with profile

  redis:
    image: redis:7-alpine
    profiles: ["dev"]  # dev-only cache

  mailhog:
    image: mailhog/mailhog
    profiles: ["dev"]  # dev-only email catcher
```

```bash
# Start with dev profile
$SUDO docker compose --profile dev up -d

# Start with specific services only
$SUDO docker compose up -d app db
```

---

## 4. Registry Operations

### Container Registry Auth

```bash
# Docker Hub
$SUDO docker login -u beer-sakthai

# GitHub Container Registry
$SUDO docker login ghcr.io -u beer-sakthai

# Private registry
$SUDO docker login registry.example.com
```

### Push & Pull

```bash
# Tag for a registry
$SUDO docker tag myapp:latest ghcr.io/beer-sakthai/myapp:latest

# Push to registry
$SUDO docker push ghcr.io/beer-sakthai/myapp:latest
$SUDO docker push ghcr.io/beer-sakthai/myapp:1.0.0

# Pull from registry
$SUDO docker pull ghcr.io/beer-sakthai/myapp:latest
```

### CI/CD Registry Pattern

In GitHub Actions, use the built-in token:

```yaml
- name: Login in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    push: true
    tags: ghcr.io/beer-sakthai/myapp:${{ github.sha }}
```

---

## 5. Health Checks & Monitoring

### Container Health Check Commands

```bash
# Check container health status
$SUDO docker inspect --format='{{.State.Health.Status}}' myapp

# Wait for healthy
$SUDO docker wait myapp  # waits for exit
# For health: poll manually
until [ "$($SUDO docker inspect --format='{{.State.Health.Status}}' myapp)" = "healthy" ]; do
  sleep 2
done
```

### Cleanup Commands

```bash
# Remove stopped containers
$SUDO docker container prune -f

# Remove unused images
$SUDO docker image prune -a -f

# Remove unused volumes (DESTRUCTIVE)
$SUDO docker volume prune -f

# Full system cleanup
$SUDO docker system prune -a --volumes -f

# Remove dangling build cache
$SUDO docker builder prune -f
```

---

## 6. CI/CD Integration

### GitHub Actions — Docker Build & Push

```yaml
name: Docker Build & Push
on:
  push:
    branches: [main]
    tags: ["v*"]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitLab CI — Docker Build

```yaml
docker-build:
  stage: build

  image: docker:27
  services:
    - docker:27-dind

  variables:
    DOCKER_HOST: tcp://docker:2375
    DOCKER_TLS_CERTDIR: ""
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

---

## 7. Troubleshooting

### Common Issues

| Symptom | Limkely Cause | Fix |
|---------|-------------|---------|
| `permission denied` | User not in docker group | `$SUDO usermod -aG docker $UNERX` or prefix with `sudo` |
| `no matching manifest` | Wrong platform | Use `--platform linux/amd64` or build multi-arch |
| `Cannot connect to Docker daemon` | Daemon not running | `sudo systemctl start docker` |
| Build cache not used | Changed layer order | Reorder COPY/install to maximise cache |
| Image too large (1GB+) | Single-stage build | Refactor to multi-stage, use alpine base |
| `port is already allocated` | Port conflict | Change host port or stop the other container |
| Disk full from dangling images | Build artifacts accumulate | `docker system prune -a -f` periodically in CI |

### Diagnosing a Failing Container

```bash
# Check exit code and logs
$SUDO docker ps -a --filter name=myapp
$SUDO docker logs myapp

# Inspect last N lines of a stopped container
$SUDO docker logs --tail 50 $(docker ps -aq --filter name=myapp | head -1)

# Check resource constraints
$SUDO docker inspect myapp | jq '.[0].HostConfig.Memory, .[0].HostConfig.NanoCpus'

# Test network connectivity between containers
$SUDO docker exec myapp ping -c 2 db

# Check for OOM kills
$SUDO docker inspect myapp | jq '.[0].State.OOMKilled'
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker build -t name .` | Build image from Dockerfile |
| `docker run -d --name n -p H:C image` | Run container in background |
| `docker compose up -d` | Start all services |
| `docker compose logs -f` | Stream logs from all services |
| `docker exec -it name sh` | Shell into running container |
| `docker logs -f name` | Follow container logs |
| `docker system prune -af` | Clean everything (careful!) |
| `docker buildx build --platform ...` | Multi-arch build |
