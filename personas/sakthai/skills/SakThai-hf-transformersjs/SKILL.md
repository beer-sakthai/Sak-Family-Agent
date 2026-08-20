---
name: SakThai-hf-transformersjs
description: "Comprehensive reference for Hugging Face Transformers.js (v3.x) \u2014 running state-of-the-art\
  \ ML models directly in the browser and Node.js via ONNX Runtime. Covers pipeline\
  \ API, WebGPU acceleration, quantized models (q4/q8/fp16), supported tasks spanning\
  \ NLP, CV, audio, and multimodal, custom usage patterns, React/Next.js/Vanilla JS\
  \ integration, gated model access, and server-side audio processing."
---

# SakThai-hf-transformersjs

## Overview

**Transformers.js** (`@huggingface/transformers`) is the JavaScript port of Hugging Face's Transformers library. It runs pretrained models directly in the browser or Node.js via **ONNX Runtime**, with no server required. Designed to be functionally equivalent to the Python `transformers` library with a near-identical `pipeline` API.

**Key differentiator:** 100% client-side inference — privacy-preserving, zero-latency after model download, works offline via Service Workers + Cache API.

### Backend Matrix

| Backend | Environment | Device | Dtype Default |
|---------|-------------|--------|---------------|
| WASM    | Browser / Node.js | CPU | `q8` |
| WebGPU  | Chromium-based browsers | GPU | `fp32` |
| ONNX Runtime Node.js | Node.js | CPU/GPU | `q8` |

## Quick Start

```js
import { pipeline } from '@huggingface/transformers';

// Allocate a pipeline (downloaded on first call)
const pipe = await pipeline('sentiment-analysis');
const result = await pipe('I love transformers!');
// [{ label: 'POSITIVE', score: 0.999817686 }]
```

## Pipeline API

The `pipeline()` function is the entry point — same design as the Python library.

### Signature

```js
const pipe = await pipeline(task, model?, options?);
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | `string` | required | Task ID (e.g. `'text-classification'`, `'automatic-speech-recognition'`) |
| `model` | `string` | task default | Model ID from Hub (e.g. `'Xenova/bert-base-multilingual-uncased-sentiment'`) |
| `options.device` | `'wasm' \| 'webgpu'` | `'wasm'` | Execution backend |
| `options.dtype` | `'fp32' \| 'fp16' \| 'q8' \| 'q4'` | `'q8'` (WASM) / `'fp32'` (WebGPU) | Quantization level |
| `options.progress_callback` | `function` | — | Download progress callback |

### All Supported Tasks

**Natural Language Processing:**
`fill-mask`, `question-answering`, `sentence-similarity`, `summarization`, `text-classification` / `sentiment-analysis`, `text-generation`, `text2text-generation`, `token-classification` / `ner`, `translation`, `zero-shot-classification`, `feature-extraction`

**Computer Vision:**
`background-removal`, `depth-estimation`, `image-classification`, `image-segmentation`, `image-to-image`, `object-detection`, `image-feature-extraction`

**Audio:**
`audio-classification`, `automatic-speech-recognition`, `text-to-speech` / `text-to-audio`

**Multimodal:**
`document-question-answering`, `image-to-text`, `zero-shot-audio-classification`, `zero-shot-image-classification`, `zero-shot-object-detection`

**Reinforcement Learning:**
`reinforcement-learning` (Decision Transformer)

## WebGPU Acceleration

Run models on GPU via WebGPU for 2–10× speedup over WASM:

```js
const pipe = await pipeline('text-generation', 'Xenova/Qwen2.5-0.5B-Instruct', {
  device: 'webgpu',
});
const result = await pipe('Once upon a time,', { max_new_tokens: 100 });
```

**Requirements:** Chromium-based browser (Chrome 113+, Edge 113+, Opera 99+).
**Not supported:** Firefox, Safari (as of mid-2026).

WebGPU is experimental — file bugs at the Transformers.js repo if you hit issues.

## Quantization (dtypes)

| Dtype | WASM | WebGPU | Bandwidth Saving vs fp32 |
|-------|------|--------|--------------------------|
| `fp32` | ❌ | ✅ (default) | 0% |
| `fp16` | ❌ | ✅ | ~50% |
| `q8` | ✅ (default) | ❌ | ~75% |
| `q4` | ✅ | ❌ | ~88% |

```js
// 4-bit quantized model — smallest download, fastest WASM
const pipe = await pipeline('sentiment-analysis', 'Xenova/distilbert-base-uncased-finetuned-sst-2-english', {
  dtype: 'q4',
});
```

**How it works:** Optimum converts PyTorch/TensorFlow/JAX models to ONNX with quantization baked in. Most models on the Hub tagged `transformers.js` have pre-converted ONNX weights (look for `onnx/` subdirectory).

## Finding Compatible Models

1. Visit [https://huggingface.co/models?library=transformers.js](https://huggingface.co/models?library=transformers.js)
2. Filter by task
3. Look for models uploaded by `Xenova` (the primary converter/maintainer) or those with `transformers.js` library tag

## Vanilla JS (ESM via CDN)

```html
<script type="module">
  import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

  const pipe = await pipeline('text-classification');
  document.getElementById('result').textContent =
    JSON.stringify(await pipe('Hello world!'));
</script>
```

## Node.js Usage

```bash
npm install @huggingface/transformers
```

```js
import { pipeline } from '@huggingface/transformers';

const pipe = await pipeline('automatic-speech-recognition');
const result = await pipe('audio.wav');
console.log(result.text);
```

Server-side: ONNX Runtime Node.js backend uses CPU (WASM) by default. For GPU in Node.js, use `onnxruntime-node` with CUDA/ROCm configuration.

## Models with Custom Sessions

For fine-grained control, bypass `pipeline()` and use lower-level classes:

```js
import { AutoTokenizer, AutoModelForSequenceClassification } from '@huggingface/transformers';

const tokenizer = await AutoTokenizer.from_pretrained('Xenova/bert-base-uncased');
const model = await AutoModelForSequenceClassification.from_pretrained('Xenova/bert-base-uncased');

const inputs = await tokenizer('Hello world!');
const outputs = await model(inputs);
```

## Accessing Private/Gated Models

Set an access token in the environment (Node.js) or via the API:

```js
// Node.js
process.env.HF_ACCESS_TOKEN = 'hf_...';

// Browser — not recommended for production (exposes token)
import { env } from '@huggingface/transformers';
env.HF_ACCESS_TOKEN = 'hf_...';
```

Transformers.js uses `fetch` under the hood. Token can also be passed via session:

```js
const pipe = await pipeline('text-generation', 'organization/gated-model', {
  session_config: { hf_access_token: 'hf_...' },
});
```

## Framework Integrations

### React

```jsx
import { pipeline } from '@huggingface/transformers';

function SentimentAnalyzer() {
  const [result, setResult] = useState(null);
  const pipeRef = useRef(null);

  useEffect(() => {
    pipeline('sentiment-analysis').then(p => { pipeRef.current = p; });
  }, []);

  const analyze = async (text) => {
    const out = await pipeRef.current(text);
    setResult(out);
  };

  return ( /* ... */ );
}
```

### Next.js

```js
// app/api/classify/route.js
import { pipeline } from '@huggingface/transformers';

const pipe = await pipeline('sentiment-analysis');

export async function POST(request) {
  const { text } = await request.json();
  const result = await pipe(text);
  return Response.json(result);
}
```

### Vercel AI SDK

```js
import { pipeline } from '@huggingface/transformers';
import { streamText } from 'ai';

const pipe = await pipeline('text-generation');
export async function POST(req) {
  const { messages } = await req.json();
  // Use Transformers.js as a local model provider
  // Stream tokens via AI SDK's response streaming
}
```

## Browser Extension (Chrome/Edge/Firefox)

Transformers.js models can be bundled into extensions. Use Service Worker background scripts for persistent model loading, and `chrome.storage` for caching ONNX weights.

```json
// manifest.json
{
  "background": { "service_worker": "background.js", "type": "module" },
  "permissions": ["storage"]
}
```

Cache models via Cache API to avoid re-downloading across sessions:

```js
// Service Worker
const cache = await caches.open('transformers-models');
cache.add('https://huggingface.co/Xenova/bert-base-uncased/resolve/main/onnx/model.onnx');
```

## Server-Side Audio Processing

Transformers.js can run Whisper/ASR on Node.js servers:

```js
import { pipeline } from '@huggingface/transformers';

const transcriber = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small');

// From buffer (Multer/Busboy uploads)
const result = await transcriber(audioBuffer, { return_timestamps: true });
```

## Tips & Best Practices

1. **Pre-load models during app initialization** — don't make users wait for first interaction
2. **Use `q8` or `q4` for browser deployments** — WASM + quantization gives the best balance of speed and size
3. **Cache via Service Workers** — ONNX files are large (50–500 MB); browser caching prevents re-download
4. **Fallback gracefully** — detect WebGPU support with `navigator.gpu` and fall back to WASM
5. **Progress indicators** — use `progress_callback` to show model download progress in the UI
6. **Memory management** — large models persist in WASM memory; `pipe.dispose()` to free if dynamically loading/unloading models
7. **Use `Xenova/` namespace** — most pre-converted models are uploaded by Xenova; check their profile for updates

## Architecture

```
┌─────────────────────────────────────────────┐
│              Browser / Node.js               │
│  ┌─────────────────────────────────────┐     │
│  │       @huggingface/transformers     │     │
│  │  ┌─────────┐  ┌──────────────────┐  │     │
│  │  │Pipeline │  │AutoModel / Token.│  │     │
│  │  └────┬────┘  └────────┬─────────┘  │     │
│  │       └────────┬───────┘             │     │
│  │          ┌─────▼──────┐              │     │
│  │          │ ONNX Runtime│             │     │
│  │          └─────┬──────┘              │     │
│  └────────────────┼─────────────────────┘     │
│                   │ HTTP (fetch)              │
│  ┌────────────────▼─────────────────────┐     │
│  │        Hugging Face Hub              │     │
│  │  (ONNX weights + tokenizer files)    │     │
│  └──────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

## Migration from v2 → v3

Key changes in v3.x (current stable: 3.8.1):
- Package renamed from `@xenova/transformers` → `@huggingface/transformers`
- WebGPU backend added (experimental)
- More model architectures supported (Qwen2, Phi-3, Whisper, etc.)
- Environment variables changed (`env.??` → `process.env.HF_ACCESS_TOKEN`)
- CJS/ESM dual package support

## Resources

- Docs: https://huggingface.co/docs/transformers.js/main/en/
- GitHub: https://github.com/huggingface/transformers.js
- NPM: https://www.npmjs.com/package/@huggingface/transformers
- Compatible models: https://huggingface.co/models?library=transformers.js
- Demo gallery: https://huggingface.co/Xenova
- Optimum conversion guide: https://huggingface.co/docs/optimum/main/en/exporters/onnx/usage_guides/export_a_model
