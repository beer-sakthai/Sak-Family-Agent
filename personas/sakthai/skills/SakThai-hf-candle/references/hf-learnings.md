# HF Learnings — Candle: Rust ML Framework (v0.11.0)

## 2026-07-26: hf-candle — Candle v0.11.0: Hugging Face's Minimalist Rust ML Framework for Serverless Inference (Topic #399)

### Summary
Comprehensive deep-dive into **Candle** — Hugging Face's minimalist ML framework for Rust, focused on serverless inference without Python overhead. Covers architecture (candle-core, candle-nn, candle-transformers, candle-examples), backends (CPU, CUDA, Metal, MKL, WASM), quantization support (llama.cpp GGUF types Q4_0 through Q8_0), weight format compatibility (safetensors, npz, ggml, PyTorch, ONNX), and the full model zoo (30+ models spanning LLMs, vision, audio, and multimodal). Includes PyTorch↔Candle API cheatsheet, zero-cost usage patterns, and comparison with burn/tch-rs/dfdx Rust ML frameworks. Current version: 0.11.0 (2026).

**Files created:**
- `hf-candle/SKILL.md` (author: SakThai, license: MIT) — Complete reference with architecture, model zoo, quantization, installation, zero-cost patterns
- `references/hf-learnings.md` — This learning log entry

**Sources:**
- GitHub README: https://github.com/huggingface/candle
- Candle Book: https://huggingface.github.io/candle/
- crates.io: candle-core 0.11.0
- HF Spaces demos (whisper, llama2, T5, Phi, SAM, yolo)
- Candle FAQ and installation guide
