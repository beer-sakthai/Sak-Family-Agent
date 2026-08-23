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
# Pinned by digest so a republished tag cannot change the training image.
# Dependabot's docker ecosystem (.github/dependabot.yml) bumps this weekly.
FROM nvidia/cuda:13.3.1-cudnn-devel-ubuntu22.04@sha256:98988ce70187f791feaebd496de6a97eeafcfac866eabbc95ce6a855cc9f7c63

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
# Pinned to the exact jammy/jammy-updates/jammy-security versions available
# when this was written. Unlike the pip pins below, Ubuntu's mirrors drop
# superseded package versions, so this pin can go stale on a future rebuild —
# apt-get fails loudly ("Version 'X' for 'Y' was not found") rather than
# silently, so bump the pin at that point rather than removing it.
# hadolint ignore=DL3013
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9ubuntu3 \
    ca-certificates=20260601~22.04.1 \
    curl=7.81.0-1ubuntu1.25 \
    git=1:2.34.1-1ubuntu1.17 \
    git-lfs=3.0.2-1ubuntu0.3 \
    libaio-dev=0.3.112-13build1 \
    libgomp1=12.3.0-1ubuntu1~22.04.3 \
    ninja-build=1.10.1-1 \
    openssh-client=1:8.9p1-3ubuntu0.16 \
    python3.11=3.11.0~rc1-1~22.04.1 \
    python3.11-dev=3.11.0~rc1-1~22.04.1 \
    python3.11-venv=3.11.0~rc1-1~22.04.1 \
    python3-pip=22.0.2+dfsg-1ubuntu0.7 \
    tmux=3.2a-4ubuntu0.2 \
    vim=2:8.2.3995-1ubuntu2.34 \
    wget=1.21.2-2ubuntu1.4 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && python -m pip install --upgrade \
        "pip==26.2.1" --hash=sha256:71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e \
        "setuptools==84.0.0" --hash=sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670 \
        "wheel==0.48.0" --hash=sha256:3217dcc807155e45db462d7ef2431f5ddda0d7273b700d05a67b271ceb1287ab

# -----------------------------------------------------------------------------
# 2. Core ML stack (pinned for CUDA 12.4)
# -----------------------------------------------------------------------------
# Hash-locked: `torch==2.5.1` alone (the previous pin here) doesn't satisfy
# pip's --require-hashes, and this line was also silently broken before the
# lock — a bare `--index-url` mid-command replaces the index for the *whole*
# pip invocation, and transformers/datasets/etc. were never actually
# resolvable against download.pytorch.org (confirmed: 403 on that index).
# `--extra-index-url` + `--index-strategy unsafe-best-match` is the standard
# way to combine PyTorch's index with PyPI; "unsafe" here just means "don't
# apply the dependency-confusion heuristic", which doesn't matter once every
# package is hash-verified anyway. Regenerate with:
#   python3 scripts/gen_hash_lock.py infra/sakthai-training-space/ml-stack-requirements.in \
#     infra/sakthai-training-space/ml-stack-requirements.lock \
#     --platform x86_64-unknown-linux-gnu --python-version 3.11 \
#     --extra-index-url https://download.pytorch.org/whl/cu124 --index-strategy unsafe-best-match
COPY ml-stack-requirements.lock /tmp/ml-stack-requirements.lock
RUN pip install --require-hashes -r /tmp/ml-stack-requirements.lock \
    --extra-index-url https://download.pytorch.org/whl/cu124 \
    --index-strategy unsafe-best-match

# -----------------------------------------------------------------------------
# 3. DeepSpeed + TRL (install together to avoid ABI/version drift)
# -----------------------------------------------------------------------------
# trl[deepspeed] pulls the deepspeed extra; we also pin deepspeed explicitly.
# Kept as a separate layer from the core stack so ML-stack rebuilds cache.
# Hash-locked and constrained against section 2's resolved versions
# (infra/sakthai-training-space/ml-stack.constraints, derived from
# ml-stack-requirements.lock) — trl/deepspeed's own transitive resolution is
# otherwise unconstrained and silently pulled torch==2.13.0, transformers
# 5.15.0, and 7 other packages newer than what section 2 just installed, when
# this was checked. Needs the same PyTorch index as section 2 for the same
# reason. Regenerate with:
#   python3 scripts/gen_hash_lock.py infra/sakthai-training-space/deepspeed-trl-requirements.in \
#     infra/sakthai-training-space/deepspeed-trl-requirements.lock \
#     --platform x86_64-unknown-linux-gnu --python-version 3.11 \
#     --extra-index-url https://download.pytorch.org/whl/cu124 --index-strategy unsafe-best-match \
#     --constraint infra/sakthai-training-space/ml-stack.constraints
# hadolint ignore=DL3059
COPY deepspeed-trl-requirements.lock /tmp/deepspeed-trl-requirements.lock
RUN pip install --require-hashes -r /tmp/deepspeed-trl-requirements.lock \
    --extra-index-url https://download.pytorch.org/whl/cu124 \
    --index-strategy unsafe-best-match

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
