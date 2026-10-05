# Pinned by digest (Scorecard Pinned-Dependencies). The tag is kept alongside
# the digest so Dependabot's docker ecosystem can bump both together.
FROM python:3.11-slim@sha256:6f31d6e9ba2b0a787a3f81c37b004155b87b9efa1b771182bd550c1615745be5

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
COPY pyproject.toml uv.lock README.md /app/
COPY personas/ /app/personas/
COPY scripts/ /app/scripts/
COPY infra/ /app/infra/

# Install python package. Dependencies come from uv.lock with their hashes, so
# the build installs exactly what CI tested and pip refuses anything else; the
# package itself is then installed --no-deps on top. uv is only needed for the
# export and is deleted afterwards.
COPY --from=ghcr.io/astral-sh/uv:0.8.17@sha256:e4644cb5bd56fdc2c5ea3ee0525d9d21eed1603bccd6a21f887a938be7e85be1 /uv /tmp/uv
RUN /tmp/uv export --frozen --no-emit-project --no-default-groups -o /tmp/requirements.txt && \
    pip install --require-hashes -r /tmp/requirements.txt && \
    pip install --no-deps -e /app && \
    rm /tmp/uv /tmp/requirements.txt

# Create persistent directories and set ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R sakthai:sakthai /app

USER sakthai

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python /app/infra/servicequotebot/docker/healthcheck.py

CMD ["python", "-m", "sakthai.telegram.bot"]
