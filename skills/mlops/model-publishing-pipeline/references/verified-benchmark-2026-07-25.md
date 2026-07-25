# Verified Benchmark — 2026-07-25

Trust-pass evaluation of all local GGUF models.

## Methodology

- **Engine:** llama.cpp Q4_K_M, 2-core CPU, 2 threads, temp=0.1
- **Prompt format:** ChatML with `<tools>` XML tags
- **Each test:** 1 run, timeout=20s, 64 tokens max
- **Verifier:** SakThai Agent
- **All results saved to:** `eval/verified-benchmark.json` on HF repos

## Results

### Tool-Calling (BFCL-style)

| Model | Score | Details |
|-------|:-----:|---------|
| **1.5B** | **5/5** | get_weather ✅ search_web ✅ calculate ✅ get_time ✅ irrelevance ✅ |
| **0.5B** | **4/5** | get_weather ✅ search_web ✅ calculate ✅ get_time ✅ irrelevance ❌ |

**Improvement:** 1.5B went from 4/5 (previous benchmark) → 5/5 (now handles search_web correctly).

### Coding

| Model | Score | Tasks |
|-------|:-----:|-------|
| **Coder 1.5B** | **5/5** | factorial ✅ debugging ✅ async explain ✅ refactor ✅ primes ✅ |

### Speed

| Model | Size | Time | Speed |
|-------|:----:|:----:|:-----:|
| 0.5B | 380 MB | 2s | **24 tok/s** |
| 1.5B | 934 MB | 5s | 9 tok/s |
| Coder | 1.1 GB | 6s | 9 tok/s |
