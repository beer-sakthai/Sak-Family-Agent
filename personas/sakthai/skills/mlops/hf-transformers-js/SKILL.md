---
name: hf-transformers-js
description: "Hugging Face Transformers.js — run LLMs, vision, speech, and diffusion models directly in the browser via ONNX Runtime Web (WASM / WebGPU). Covers pipeline API, quantization, model caching, and deployment patterns."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, transformers.js, onnx, webgpu, wasm, browser, client-side, inference]
platforms: [linux, macos, windows]
---

# Hugging Face Transformers.js

Transformers.js brings the Hugging Face ecosystem to the browser. Using ONNX Runtime Web, it runs PyTorch / TensorFlow models entirely client-side — no Python, no server, no GPU required.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **ONNX Runtime Web** | The execution engine compiled to WebAssembly and WebGPU. |
| **WebGPU backend** | Fastest option (Chrome 113+), offloads compute to GPU via WGSL. |
| **WASM backend** | Broadest compatibility; slower but memory-efficient for small models. |
| **IndexedDB cache** | Models persist in the browser across reloads; avoids re-downloading. |
| **Quantization** | Pre-requantized ONNX weights (INT4 / INT8) are essential for browser RAM. |

## Installation & Use

### CDN (no build step)

```html
<script type="module">
  import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2';

  const classifier = await pipeline('sentiment-analysis', 'Xenova/bert-base-uncased');
  const result = await classifier('I love Transformers.js!');
  console.log(result);
</script>
```

### npm

```bash
npm install @xenova/transformers
```

```js
import { pipeline, env } from '@xenova/transformers';

// Optional: skip local-model checks if you only want Hub models
env.allowLocalModels = false;
env.useBrowserCache = true;
```

## Pipeline API

Mirrors the Python `transformers` API:

```js
import { pipeline } from '@xenova/transformers';

// Text generation
const generator = await pipeline('text-generation', 'Xenova/LaMini-Flan-T5-783M');
const out = await generator('Explain quantum computing.');
```

Supported tasks:
- `feature-extraction`
- `fill-mask`
- `question-answering`
- `sentiment-analysis`
- `summarization`
- `text-generation`
- `text2text-generation`
- `token-classification` (NER)
- `translation`
- `zero-shot-classification`
- `automatic-speech-recognition`
- `image-classification`
- `image-segmentation`
- `object-detection`
- `text-to-image` (via diffusion pipelines)

## Device Selection & Acceleration

```js
// WebGPU (fastest)
const generator = await pipeline('text-generation', 'Xenova/LaMini-Flan-T5-783M', {
  device: 'webgpu',
});

// Explicit WASM
const generator = await pipeline('text-generation', 'Xenova/LaMini-Flan-T5-783M', {
  device: 'wasm',
});
```

- If the browser does not support WebGPU, the runtime falls back to WASM automatically.
- `webgpu` requires GPU-appropriate drivers and modern browser flags relaxed in Chrome 113+.

## Model Format & Quantization

Models must be in ONNX format. Preferred sources:
- **Official Xenova port** — models on Hub under the `Xenova/` namespace pre-converted to ONNX + quantized (e.g., `Xenova/distilgpt2`).
- **Custom conversion** — use Python `transformers` + `optimum` or the `transformers-cli export` path to create ONNX, then quantize with ONNX Runtime tools.

**Why quantization matters in the browser:**
- A 7B model in FP32 needs ~28 GB VRAM — impossible in-browser.
- INT4 quantized 7B ≈ ~3.5 GB; still large but feasible for desktop browsers with large RAM.
- WASM memory must be contiguous; WebGPU uses separate GPU memory.

## Caching & Proxying

### Automatic caching
`env.useBrowserCache = true` (default) stores downloaded models in IndexedDB under `transformers-cache`.

```js
import { env } from '@xenova/transformers';
console.log(env.cacheDir); // e.g., indexeddb://transformers-cache
```

### Manual cache control
```js
const model = await pipeline('text-generation', 'Xenova/distilgpt2');
// ...
// Check size
const cacheInfo = await env.listCacheContents();
console.log(cacheInfo);
```

## Progressive Loading & UI Feedback

Long model downloads need UI feedback:

```js
const classifier = await pipeline('sentiment-analysis', 'Xenova/bert-base-uncased', {
  progress_callback: (progress) => {
    if (progress.status === 'progress') {
      console.log(`${progress.file} ${progress.progress.toFixed(2)}%`);
      document.querySelector('#bar').value = progress.progress;
    }
  },
});
```

## Security & Privacy

- **No data leaves the browser** unless you explicitly send it elsewhere.
- `env.allowLocalModels = false` prevents loading arbitrary local file paths.
- `env.allowRemoteModels = false` forces fully offline usage after initial cache.
- Useful for healthcare, education, and privacy-preserving demos.

## Performance Tips

1. **Start with small models:** distilGPT2, BERT-base, or quantized TinyLlama for quick demos.
2. **Prefer WebGPU:** ~2–10x faster than WASM for attention-heavy workloads.
3. **Cache aggressively:** every page load re-downloads unless IndexedDB is used.
4. **Use workers:** offload ONNX Runtime to a Web Worker to avoid blocking the main thread.
5. **Avoid streaming over network:** static hosting on a CDN or Vercel Netlify is ideal; no Python backend.

## Streaming Text Generation

```js
import { AutoTokenizer, AutoModelForCausalLM } from '@xenova/transformers';

const tokenizer = await AutoTokenizer.from_pretrained('Xenova/LaMini-Flan-T5-783M');
const model = await AutoModelForCausalLM.from_pretrained('Xenova/LaMini-Flan-T5-783M', { device: 'webgpu' });

const inputs = tokenizer('Hello!', { return_tensors: true });
const streamer = model.generate(inputs, { max_new_tokens: 50, do_sample: true, streamer: true });

for await (const token of streamer) {
  process.stdout.write(tokenizer.decode(token));
}
```

## Known Limitations

- **RAM limits:** typical desktop browser tab is limited to ~2–4 GB for a single WASM heap. WebGPU relaxes this somewhat but shared GPU memory still has bounds.
- **Model size:** models > 4 GB quantized (e.g., 7B INT4) may not load on mobile devices.
- **Task coverage:** very new architectures may lack an ONNX export; Transformers.js depends on community conversions.
- **No PPO / RLHF training:** the library is inference-only.

## When to Use Transformers.js

| Scenario | Good fit? | Reason |
|----------|-----------|--------|
| Public demos that must respect privacy | Yes | Everything stays client-side. |
| Offline / air-gapped kiosks | Yes | Cache once, run forever. |
| Mobile-first AI apps | Sometimes | RAM constraints; small quantized models only. |
| Production LLM serving | No | No load-balancing, limited memory, per-client model loading. |
| Batch or high-throughput inference | No | Single-threaded per tab, high overhead from browser sandbox. |

## References

- **Docs:** https://huggingface.co/docs/transformers.js
- **GitHub:** https://github.com/huggingface/transformers.js
- **Model gallery:** https://huggingface.co/models?library=transformers.js
- **ONNX Runtime Web:** https://onnxruntime.ai/docs/tutorials/web/
