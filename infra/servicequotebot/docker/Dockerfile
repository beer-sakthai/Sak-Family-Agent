FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    SAKTHAI_HOME=/app/data

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user
RUN groupadd -g 10001 sakthai && \
    useradd -u 10001 -g sakthai -s /bin/bash -m sakthai

# Copy project files
COPY pyproject.toml README.md /app/
COPY personas/ /app/personas/
COPY scripts/ /app/scripts/
COPY infra/ /app/infra/

# Install python package
RUN pip install --upgrade pip && \
    pip install -e /app

# Create persistent directories and set ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R sakthai:sakthai /app

USER sakthai

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python /app/infra/servicequotebot/docker/healthcheck.py

CMD ["python", "-m", "sakthai.telegram.bot"]
