# Model Compatibility Matrix

## Where Each Model Can Run

| Model | Size | This Machine | GitHub Codespaces | GitHub Actions | Vercel | HF Spaces | 
|-------|:----:|:------------:|:-----------------:|:--------------:|:------:|:---------:|
| **1.5B-merged** | 934 MB | ✅ 9 tok/s | ✅ Similar | ⚠️ 6h limit | ❌ | ✅ ZeroGPU |
| **0.5B-merged** | 380 MB | ✅ 24 tok/s | ✅ Fast | ✅ | ❌ | ✅ Free |
| **Coder 1.5B** | 1.1 GB | ✅ 9 tok/s | ✅ | ⚠️ 6h limit | ❌ | ✅ ZeroGPU |
| **7B-merged** | 15 GB | ❌ RAM | ❌ RAM | ❌ Timeout | ❌ | ✅ ZeroGPU |
| **7B-128k** | 15 GB | ❌ RAM | ❌ RAM | ❌ Timeout | ❌ | ✅ ZeroGPU |
| **Vision 7B** | 3.9 GB | ⚠️ Slow | ⚠️ | ❌ | ❌ | ✅ ZeroGPU |
| **TTS Model** | 141 MB | ✅ Fast | ✅ | ✅ | ❌ | ✅ Free |
| **Embedding** | 80 MB | ✅ 7k/s | ✅ | ✅ | ❌ | ✅ Free |

## Vercel Compatibility

**Vercel can only run the frontend (dashboard HTML/CSS/JS).** 
- ❌ Cannot run any GGUF models (serverless = 1 GB RAM limit, 10s timeout)
- ❌ Cannot run llama.cpp (no binary execution)
- ✅ Can host the dashboard as static site
- ✅ Can proxy API calls to external services (HF Inference API)

## Deployment Options

| Platform | Frontend | Backend/API | Models |
|----------|:--------:|:-----------:|:------:|
| **GitHub Pages** | ✅ Static | ❌ No backend | ❌ None |
| **Vercel** | ✅ Static | ⚠️ Serverless functions (limited) | ❌ None |
| **HF Spaces** | ✅ Gradio/Static | ✅ Yes | ✅ ZeroGPU available |
| **This machine** | ✅ Via browser | ✅ RAG + Model servers | ✅ All small models |
