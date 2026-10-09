# sakthai-training-space Dockerfile
# Docker GPU Space for TRL + DeepSpeed RLHF/GRPO training on Hugging Face Spaces
#
# Base image: NVIDIA CUDA 12.4 + Ubuntu 22.04 + Python 3.11
# Pre-installed: PyTorch 2.5.1 (CUDA 12.4), DeepSpeed 0.15.4, TRL 0.15 (see requirements.in)
#
# Hugging Face Docker Space expects the container to listen on the port
# declared in README.md (default 7860). For a training Space, we keep the
# container alive with `sleep infinity` and run training via attached Jobs,
# SSH Dev Mode, or an entry script controlled by environment variables.

#
# checkov:skip=CKV_DOCKER_2: Training Space kept alive via sleep infinity; no service endpoint to health-check
# checkov:skip=CKV_DOCKER_3: HF Spaces/Jobs manage the runtime user; training needs root for CUDA tooling
# Pinned by digest (Scorecard Pinned-Dependencies). The tag is kept alongside
# the digest so Dependabot's docker ecosystem can bump both together.
FROM nvidia/cuda:13.4.2-cudnn-devel-ubuntu22.04@sha256:d9e285e3bb16630c577e71070ea73f7b37ea2a2928c64902e340507c640b9618

# Build-time args / env
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_HOME=/tmp/.huggingface
ENV TRANSFORMERS_CACHE=/tmp/.huggingface/transformers
ENV HUGGINGFACE_HUB_CACHE=/tmp/.huggingface/hub

# -----------------------------------------------------------------------------
# 1. System dependencies + Python 3.11
# -----------------------------------------------------------------------------
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    git-lfs \
    libaio-dev \
    libgomp1 \
    ninja-build \
    openssh-client \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    tmux \
    vim \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# -----------------------------------------------------------------------------
# 2. Python packages, every one pinned by hash (Scorecard Pinned-Dependencies)
# -----------------------------------------------------------------------------
# The locks are generated from requirements.in; the command is in each header.
# --require-hashes makes pip refuse any file whose hash is not in the lock, and
# --no-deps keeps it from resolving anything the lock does not already list.
COPY build-requirements.lock requirements.lock deepspeed.lock /tmp/requirements/

# Toolchain first: Ubuntu 22.04's pip predates some of the wheels below.
RUN python -m pip install --no-cache-dir --require-hashes \
    -r /tmp/requirements/build-requirements.lock

# Core ML stack (torch/vision/audio from the CUDA 12.4 index), TRL and the
# rest of DeepSpeed's dependencies. Kept as its own layer so it caches.
RUN python -m pip install --no-cache-dir --require-hashes --no-deps \
    -r /tmp/requirements/requirements.lock

# DeepSpeed ships only as an sdist whose build imports torch, so it installs
# after torch and against it, rather than in an isolated build environment.
# hadolint ignore=DL3059
RUN python -m pip install --no-cache-dir --require-hashes --no-deps --no-build-isolation \
    -r /tmp/requirements/deepspeed.lock \
    && rm -rf /tmp/requirements

# Optional: vLLM for fast generation in online RL (GRPO/RLOO). Version pinned
# to TRL-supported range. Disable if not needed to save build time/image size.
# RUN pip install vllm==0.7.3

# -----------------------------------------------------------------------------
# 3. Workspace layout
# -----------------------------------------------------------------------------
WORKDIR /workspace
RUN mkdir -p /workspace/scripts /workspace/configs /workspace/outputs /workspace/data

# Copy training scripts/configs if they exist in the repo
COPY scripts/ /workspace/scripts/
COPY configs/ /workspace/configs/

# -----------------------------------------------------------------------------
# 4. Runtime defaults for a Docker GPU Space
# -----------------------------------------------------------------------------
# Docker Spaces expect a process that keeps running. For a training Space we:
#   - expose port 7860 (conventional; not used by training unless you serve logs)
#   - sleep until an external command/Jobs/SSH drives training
# Override with `SAKTHAI_TRAIN_SCRIPT` to auto-start a training run on boot.
EXPOSE 7860

ENV SAKTHAI_TRAIN_SCRIPT=""
ENV SAKTHAI_TRAIN_ARGS=""
ENV NCCL_DEBUG=INFO
ENV PYTHONPATH=/workspace

# Health-ish keepalive: if no train script is set, hold the Space open.
CMD ["/bin/bash", "-c", \
    "if [ -n \"$SAKTHAI_TRAIN_SCRIPT\" ]; then \
        echo \"Starting SakThai training: $SAKTHAI_TRAIN_SCRIPT $SAKTHAI_TRAIN_ARGS\"; \
        python \"$SAKTHAI_TRAIN_SCRIPT\" $SAKTHAI_TRAIN_ARGS; \
     else \
        echo 'sakthai-training-space ready. Set SAKTHAI_TRAIN_SCRIPT to auto-train, or attach via Dev Mode/SSH/Jobs.'; \
        sleep infinity; \
     fi"]
