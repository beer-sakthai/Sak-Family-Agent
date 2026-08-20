# HF Kernels Ecosystem — Deep Dive

**Learned:** 2026-07-25 | **Topic:** `hf-kernels-ecosystem-deep-dive`
**Sources:** HF Kernels docs (main/v0.16.0), huggingface.co/kernels, PyPI, HF blog

---

## 1. What is the Kernel Hub?

The Hugging Face Kernel Hub is a **first-class repository type** on the Hub for distributing pre-built compute kernels. Unlike models or datasets, kernel repos have:

- **Dedicated hardware filter UI** — users can filter kernels by platform (CUDA, ROCm, Metal, XPU, CPU) and specific GPU types (H100, A100, T4, L40s, RTX 4090, V100, MI300, Apple M4/M3, B300, etc.)
- **Kernel-specific pages** showing supported hardware, versions, download stats
- **Version branches** with API compatibility guarantees
- **Signature verification** for security
- **System cards** exposing metadata about kernel interfaces and usage

As of July 2026, there are **221+ kernels** published on the Hub, covering:
- Flash attention variants (flash-attn2, fa2-seqused-runtime, fp8-prefill-attention, flash-attn4)
- GEMM operations (enclosure-gemm, grouped-moe-gemm, binary-gemm)
- Quantization (int4-blackwell, w4a16, kv-quant-attn)
- MoE operations (moe-dispatch)
- Audio processing (stft-mel, rvq-codec, vocoder-ops)
- Model-specific operations (lm-head-topk, mrope, cut-cross-entropy)
- Graph operations (graph-spmm, graph-reduce)

---

## 2. Why Kernels Exist

**The problem:** Compute kernels are a nightmare to distribute. A single CUDA kernel may need to be compiled for dozens of combinations of CUDA versions, PyTorch builds, Python versions, OS/arch, and GPU compute capabilities. Local builds can take hours and break when PyTorch updates.

**The solution:** The Kernel Hub provides:
- **A standard way to structure and build kernels** — declarative build configurations, pre-defined layouts
- **Pre-built binaries for the full compatibility matrix** — users download exactly the right build for their system
- **Dynamic loading** — versioned, isolated, multiple versions can coexist in the same process
- **Hardware transparency** — users know instantly if a kernel supports their hardware, without running any installation

---

## 3. Architecture Overview

The project has two main components:

### 3.1 `kernels` Python Package (v0.16.0)

The runtime loader. Installed via `pip install kernels` or `uv pip install kernels`.

```python
from kernels import get_kernel, has_kernel, get_loaded_kernels
from kernels import get_kernel_variants, VariantAccepted

# Load a kernel from the Hub with specific version
activation = get_kernel(
    "kernels-community/activation",
    version=1  # major version number
)

# Check availability before loading
is_available = has_kernel("kernels-community/activation", version=1)

# Inspect why unavailable variants were rejected
for decision in get_kernel_variants("kernels-community/activation", version=1):
    if isinstance(decision, VariantAccepted):
        print(f"{decision.variant.variant_str}: compatible")
    else:
        print(f"{decision.variant.variant_str}: rejected ({decision.reason})")

# Inspect all loaded kernels
for loaded in get_loaded_kernels():
    print(loaded.package_name, loaded.repo_infos)
```

**Key API classes:**
- `LoadedKernel` — a loaded kernel with attributes `package_name`, `repo_infos`
- `RepoInfo` — information about a kernel's source repository

**Loading methods:**
- `get_kernel(repo_id, version=...)` — load from Hub with version
- `get_local_kernel(path)` — load from local path
- `get_locked_kernel(lockfile)` — load via lockfile (reproducible builds)
- `load_kernel(lockfile)` — load all kernels from a lockfile

### 3.2 `kernel-builder` Package

The build system for creating kernels. Uses **Nix** as the build foundation for reproducible, hermetic builds across the compatibility matrix.

```bash
# Initialize a new kernel project
kernel-builder init my-kernel
cd my-kernel

# Build for all supported platforms
kernel-builder build

# Build for specific variants
kernel-builder build --variant cuda-12.4-py3.11
```

**Kernel requirements:**
- Declarative build config (`kernel.toml` or similar)
- Source code with defined entry points
- Build variants matrix definition
- Must support all recent Python and PyTorch build configurations

### 3.3 `kernels` CLI

Command-line tools for managing kernels:

- `kernels info <repo_id>` — show kernel metadata and available builds
- `kernels versions <repo_id>` — list available versions
- `kernels lock <repo_id> [--output lock.toml]` — create a lockfile for reproducible loading
- `kernels download <repo_id> --version <n>` — pre-download kernel binaries
- `kernels benchmark <repo_id> [--device cuda:0]` — benchmark kernel performance
- `kernels verify-signature <repo_id> --version <n>` — verify kernel authenticity

---

## 4. Versioning System

Kernels use **major version numbers** (not semver):

- **Stable versions** (≥1): API stability guaranteed within a major version branch — never break API or remove builds for older PyTorch versions
- **Version 0 kernels**: Alpha/beta quality, may have rapidly changing APIs, no compatibility guarantees
- **Explicit revision resolution**: Hub kernels must be loaded with either a version or an explicit git revision

This design enables multiple major versions of the same kernel to coexist in the same Python process — solving "dependency hell" for kernel libraries.

---

## 5. Layers System

Kernels can also provide **layers** — drop-in replacements for `nn.Module.forward()` methods:

```python
from kernels import use_kernel_forward_from_hub, kernelize

# Make an existing layer extensible with Hub kernels
@use_kernel_forward_from_hub("SiluAndMul")
class SiluAndMul(nn.Module):
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        d = input.shape[-1] // 2
        return F.silu(input[..., :d]) * input[..., d:]

# Or replace forward on an external layer
from somelibrary import SiluAndMul
replace_kernel_forward_from_hub(SiluAndMul, "SiluAndMul")

# Or make a function extensible
@use_kernel_forward_from_hub("silu_and_mul")
def silu_and_mul(x: torch.Tensor) -> torch.Tensor:
    d = x.shape[-1] // 2
    return F.silu(x[..., :d]) * x[..., d:]
```

The `kernelize()` function traverses a model and replaces compatible layer forward methods with Hub-hosted kernel implementations:

```python
from kernels import kernelize
model = MyModel()
kernelize(model)  # replaces compatible layers with Hub kernels
```

**External layer registration** (`replace_kernel_forward_from_hub()`): allows extending third-party libraries without modifying their source code.

---

## 6. Security (v0.16.0+)

### 6.1 Trusted Kernel Publishers

Since kernels execute native code with the same privileges as the Python process, security is paramount. The `kernels` package only loads kernels from **trusted publishers** by default. A trusted publisher is an organization trusted by the community.

To load a kernel from a non-trusted source, users must explicitly opt in:

```python
from kernels import get_kernel
kernel = get_kernel(
    "Atlas-Inference/gdn",
    version=1,
    trust_remote_code=True
)
```

By default, users **cannot** publish kernel repositories on the Hub — they must request publisher access from their account settings.

### 6.2 Sigstore Code Signing

Kernel binaries are signed using **Sigstore's cosign** with ephemeral private keys:

- A digest (hash list) of all kernel files is added to `metadata.json`
- The digest is protected with a detached Sigstore signature in `metadata.json.sigstore`
- Ephemeral signing keys are only valid for a limited time, mitigating key theft
- The signature also verifies the kernel was signed by a trusted GitHub workflow from a trusted GitHub repository

Verify a kernel's signature:

```bash
$ kernels verify-signature kernels-community/flash-attn4 0
✅ torch-cuda: kernel metadata is correctly signed
```

All [kernels-community](https://huggingface.co/kernels-community) kernels are signed. Signature verification on load is not yet enforced (experimental as of v0.16.0).

---

## 7. Nix Build System

Kernels use **Nix** as the underlying build system for:

- **Hermetic builds** — deterministic, reproducible builds regardless of host environment
- **Cross-compilation** — build for multiple targets from a single machine
- **Caching** — shared build caches across developers and CI
- **Dependency management** — exact pinned versions of CUDA toolkit, PyTorch, compilers

The Nix builder design ensures that the same source code produces identical binaries across different build machines.

---

## 8. Key Differentiators vs. Traditional Approaches

| Aspect | Traditional (pip/distutils) | HF Kernels |
|--------|---------------------------|------------|
| Build once per env | ❌ Build on every machine | ✅ Pre-built for all matrices |
| Version isolation | ❌ One version per env | ✅ Multiple versions coexist |
| Hardware detection | ❌ Compile-time or runtime fail | ✅ Pre-check with `has_kernel()` |
| Reproducibility | ❌ Depends on build env | ✅ Nix-based hermetic builds |
| Distribution | PyPI (source wheels) | HF Hub (pre-built binaries) |
| Security | Source verification | Sigstore signing + trusted publishers |

---

## 9. Ecosystem & Integration

Projects using the kernel system:
- **Flash Attention** kernels available via Hub
- **vLLM** integration with HF Kernels for dynamic kernel loading
- **Transformers** exploring kernel-backed layer replacements
- **Diffusers** using Nunchaku/quantization kernels

The kernel ecosystem enables a new distribution model where:
1. Model libraries ship generic PyTorch implementations
2. Performance-critical layers are replaced at load time with Hub-hosted kernels
3. Users get hardware-specific optimizations without any configuration

---

## 10. CLI Reference Summary

```bash
kernels info <repo_id>                    # Show kernel metadata and builds
kernels versions <repo_id>                # List available versions
kernels lock <repo_id>                    # Create reproducible lockfile
kernels download <repo_id>                # Pre-download kernel binaries
kernels benchmark <repo_id>               # Run benchmarks
kernels verify-signature <id> --version N # Verify kernel authenticity
```

---

## 11. Major Updates — July 2026 (v0.16.0+)

### 11.1 Kernels as First-Class Repo Type

Kernels are now a **dedicated repository type** on the Hub with their own namespace (`kernels-community/`) and dedicated pages. Browse all kernels at [https://huggingface.co/kernels](https://huggingface.co/kernels). Making kernels first-class citizens improves discoverability and enables cross-repo trend analysis.

### 11.2 Revamped CLI Separation

A clear separation of concerns between the two packages:

| Package | Role | CLI Examples |
|---------|------|-------------|
| `kernels` | **Loading** kernels | `kernels info`, `kernels download`, `kernels verify-signature` |
| `kernel-builder` | **Building** kernels | `kernel-builder init`, `kernel-builder build` |

This split makes both packages leaner and more focused, and enables better agentic workflows.

### 11.3 New Framework Support

**Torch Stable ABI:** Kernels can now target the Torch Stable ABI, allowing a kernel built for Torch 2.9 Stable ABI to work with any Torch version ≥ 2.9 for approximately two years.

**Apache TVM FFI:** The first non-Torch framework supported. TVM FFI is a standardized ABI for kernels that interoperates across PyTorch, Jax, and CuPy — enabling cross-framework kernels from a single build.

### 11.4 Agentic Kernel Development

Kernel-builder and kernels are designed to support **agent-driven kernel development**:

1. **Scaffold** — Agents scaffold kernel source code using `kernel-builder init`
2. **Build** — Agents run reproducible builds with predictable project layouts
3. **Benchmark** — Agents use `kernels benchmark`, integrated with HF Jobs for multi-hardware evaluation
4. **Iterate** — Performance feedback informs the next optimization cycle

Backend-specific skills (capturing toolchains, compilation paths, performance considerations) help agents navigate different backends programmatically.

Example agent-developed kernels:
- [kernels/drbh/yamoe](https://huggingface.co/kernels/drbh/yamoe)
- [kernels/sayakpaul/qk-norm-rope](https://huggingface.co/kernels/sayakpaul/qk-norm-rope)

### 11.5 System Cards

After building, every kernel gets a **system card** exposing:
- How to use the kernel
- Exposed interfaces (functions, layers)
- Hardware compatibility info

This card becomes the front matter of the kernel's Hub page.

### 11.6 Compatibility APIs

- `has_kernel(repo_id, version=N)` — returns boolean for quick compatibility check
- `get_kernel_variants(repo_id, version=N)` — returns detailed decision list showing why each variant was accepted/rejected (e.g., "CPU (x86_64) does not match system CPU (aarch64)")

### 11.7 Improved manylinux_2_28 Support

Kernels now link `libstdc++` **dynamically** instead of statically, using the official manylinux_2_28 toolchain. This fixes segfaults caused by conflicting libstdc++ global initializations when multiple C++ libraries interact in the same process.

### 11.8 Environment Setup

One-click installation script for building kernels:
```bash
# One-click setup
curl -fsSL https://get.kernel-builder.dev | bash

# Or Terraform for ephemeral instances
# See: https://huggingface.co/docs/kernels/main/en/installation
```

---

## 12. Future Directions

Based on the project roadmap and blog posts:
- Provider dashboard for kernel publishers (analytics, trends)
- Automatic kernel selection based on model architecture detection
- Expanded hardware support (more AMD GPUs, Intel GPUs, NPUs)
- Integration with more HF libraries beyond Transformers and Diffusers
- Community kernel marketplace with reviews and benchmarks
- Full signature verification on load (currently experimental)
- Expanded agentic kernel development tooling

---

## References

- HF Kernels documentation: https://huggingface.co/docs/kernels/main/en
- PyPI: `pip install kernels` (v0.16.0)
- Browse kernels: https://huggingface.co/kernels
- Source: https://github.com/huggingface/kernels
- Blog post: https://huggingface.co/blog/revamped-kernels (July 6, 2026)
- Release notes: https://github.com/huggingface/kernels/releases/tag/v0.16.0
