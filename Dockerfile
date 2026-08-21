# Runtime image for the six Sak Family Telegram personas.
#
# This is the image `infra/vm-agents/systemd/sakthai-telegram@.service` and
# `infra/vm-agents/docker-compose.yml` run. One image serves every persona; the
# persona is selected at runtime by SAKTHAI_PERSONA + SAKTHAI_SYSTEM_PROMPT_FILE,
# so there is nothing persona-specific baked in here.
#
# Not to be confused with `Dockerfile.sandbox`, which backs `sakthai run
# --sandbox`: that one is an ephemeral task container that deliberately enables
# shell execution. This one is a long-lived service reachable from Telegram and
# deliberately does not — see the SAKTHAI_SHELL_ALLOW note below.
#
# checkov:skip=CKV_DOCKER_2: the container's health is supervised by systemd
# (Restart=always) / compose, and the bot has no HTTP surface to probe.
#
# Pinned by digest, not just tag, so a compromised or silently-republished
# `python:3.14-slim` cannot change what the deployed agents execute. Kept in
# lockstep with Dockerfile.sandbox; Dependabot's docker ecosystem bumps both.
FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4

# The memory shard is bind-mounted from the host and must stay writable by the
# host user that owns it, so the container user's UID has to match. Override at
# build time when the VM account is not 1000: --build-arg UID=$(id -u).
ARG UID=1000
ARG GID=1000

# ca-certificates only: this image talks to a model provider and to Telegram
# over HTTPS and needs nothing else. `run_command` is disabled here, so the
# sandbox image's git/curl/jq/make toolchain would be attack surface with no use.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The package sources live under personas/sakthai/sakthai (see
# [tool.setuptools.packages.find] in pyproject.toml), so mirror that layout.
# personas/ also carries each persona's SOUL.md, skills/ and config/ —
# SAKTHAI_SYSTEM_PROMPT_FILE points at personas/<agent>/SOUL.md, so a persona
# started from an image without them would run with no identity.
# .dockerignore drops the symlinked/shadowing copies of the package.
COPY pyproject.toml README.md ./
COPY personas/ ./personas/
COPY library/ ./library/

RUN pip install --no-cache-dir -e "."

# Non-root. The sandbox image runs as root on purpose (CKV_DOCKER_3) so the
# bind-mounted memory.db keeps host-writable ownership; here the same goal is
# met by matching the host UID instead, which does not need root.
RUN groupadd --gid "${GID}" sakthai \
    && useradd --uid "${UID}" --gid "${GID}" --create-home --shell /usr/sbin/nologin sakthai \
    && chown -R sakthai:sakthai /app
USER sakthai

# Note what is deliberately NOT set: SAKTHAI_SHELL_ALLOW. Dockerfile.sandbox
# sets it because shell execution inside that throwaway container is the whole
# point. Setting it here would hand `run_command` to anyone who can message the
# bot on Telegram.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "-m", "sakthai.telegram.bot"]
