# sakthai-training-space Dockerfile
# Docker GPU Space for TRL + DeepSpeed RLHF/GRPO training on Hugging Face Spaces
#
# Base image: NVIDIA CUDA 12.4 + Ubuntu 22.04 + Python 3.11
# Pre-installed: PyTorch 2.5.1 (CUDA 12.4), DeepSpeed 0.15.4, TRL 0.15+ (latest stable)
#
# Hugging Face Docker Space expects the container to listen on the port
# declared in README.md (default 7860). For a training Space, we keep the
# container alive with `sleep infinity` and run training via attached Jobs,
# SSH Dev Mode, or an entry script controlled by environment variables.

#
# checkov:skip=CKV_DOCKER_2: Training Space kept alive via sleep infinity; no service endpoint to health-check
# checkov:skip=CKV_DOCKER_3: HF Spaces/Jobs manage the runtime user; training needs root for CUDA tooling
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

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
# hadolint ignore=DL3008,DL3013
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
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && python -m pip install --upgrade pip setuptools wheel

# -----------------------------------------------------------------------------
# 2. Core ML stack (pinned for CUDA 12.4)
# -----------------------------------------------------------------------------
# hadolint ignore=DL3013
RUN pip install \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124 \
    transformers==4.47.1 \
    datasets==3.2.0 \
    accelerate==1.2.1 \
    peft==0.14.0 \
    bitsandbytes==0.45.0 \
    evaluate==0.4.3 \
    wandb==0.19.1 \
    tensorboard \
    scipy \
    scikit-learn \
    ninja

# -----------------------------------------------------------------------------
# 3. DeepSpeed + TRL (install together to avoid ABI/version drift)
# -----------------------------------------------------------------------------
# trl[deepspeed] pulls the deepspeed extra; we also pin deepspeed explicitly.
# Kept as a separate layer from the core stack so ML-stack rebuilds cache.
# hadolint ignore=DL3013,DL3059
RUN pip install \
    deepspeed==0.15.4 \
    "trl[deepspeed]>=0.15.0,<0.16.0" \
    sentencepiece \
    protobuf

# Optional: vLLM for fast generation in online RL (GRPO/RLOO). Version pinned
# to TRL-supported range. Disable if not needed to save build time/image size.
# RUN pip install vllm==0.7.3

# -----------------------------------------------------------------------------
# 4. Workspace layout
# -----------------------------------------------------------------------------
WORKDIR /workspace
RUN mkdir -p /workspace/scripts /workspace/configs /workspace/outputs /workspace/data

# Copy training scripts/configs if they exist in the repo
COPY scripts/ /workspace/scripts/
COPY configs/ /workspace/configs/

# -----------------------------------------------------------------------------
# 5. Runtime defaults for a Docker GPU Space
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
