---
name: saksit-docker-compose-business-deploy
title: Docker Compose for Business Services
description: Practical Docker Compose patterns for containerizing Python/FastAPI backend services with databases, networking, and secrets management. Mirrors Beer's WorkFlow-SakThai deployment style.
---

# Docker Compose Business Deployment

Patterns for containerizing business backend services (APIs, webhooks, data pipelines) using Docker Compose. Designed for Beer's style — lightweight, Python-first, zero-platform-dependency.

## When to use

- Beer asks to **containerize** a new service or existing project
- You need to set up **multi-service** architecture (API + DB + cache)
- You're **deploying** something that will outlive a single terminal session
- Beer asks for a **production-like setup** without cloud lock-in

## Core Structure

```
project/
├── docker-compose.yml        # Main compose file
├── Dockerfile                # For the app service
├── .env                      # Local secrets (gitignored)
├── .env.example              # Template for .env
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── requirements.txt      # Python dependencies
│   └── ...
└── data/                     # Volume mount for SQLite / uploads
```

## Dockerfile Template

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy and install dependencies
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml Template

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data          # SQLite / persistent data
      - ./app:/app/app            # Hot-reload in dev
    command: ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Optional: add a lightweight DB or cache
  # db:
  #   image: postgres:16-alpine
  #   env_file:
  #     - .env
  #   volumes:
  #     - pgdata:/var/lib/postgresql/data
  #   healthcheck:
  #     test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
  #     interval: 10s

volumes:
  pgdata:
```

## .env.example

```
# App
PORT=8000
LOG_LEVEL=info
SECRET_KEY=change-me
ALLOWED_ORIGINS=http://localhost:3000

# Database (optional)
# POSTGRES_USER=app
# POSTGRES_PASSWORD=change-me
# POSTGRES_DB=app
# DATABASE_URL=postgresql+asyncpg://app:change-me@db:5432/app
```

## Commands Reference

```bash
# Build and start
docker compose up --build -d

# View logs
docker compose logs -f

# Restart a single service
docker compose restart api

# Run a one-off command inside the container
docker compose exec api python -c "from app.models import do_migration; do_migration()"

# Stop everything
docker compose down

# Full teardown (removes volumes)
docker compose down -v

# Rebuild without cache
docker compose build --no-cache
```

## Pitfalls

- **File permissions:** SQLite files written by container are owned by root. Use a Dockerfile USER directive or chown after first run.
- **Hot reload:** Requires bind-mounting the app directory. Don't use in production.
- **Secrets:** Never commit `.env` to git. Use `.env.example` as the committed template.
- **Port conflicts:** Always use `${PORT:-8000}` pattern so Beer can override without editing files.
- **Health checks:** Always add one. Docker won't restart a crashed container without it.
- **Cross-machine:** This uses the local Docker socket. For remote deployment, pair with `docker compose -H ssh://user@host`.

## Verification

```bash
# Service is up
curl -f http://localhost:8000/health

# Check container is running
docker compose ps

# Confirm data persistence
docker compose down && docker compose up -d
curl -f http://localhost:8000/health   # Should still work
```