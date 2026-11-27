---
name: SakSee-transformers-js
version: 1.0.0
description: Use Transformers.js to run state-of-the-art machine learning models directly
  in JavaScript/TypeScript. Supports NLP (text classification, translation, summarization),
  computer vision (image classification, object detection), audio (speech recognition
category: web-browser
tags:
- browser
- js
- transformers
---

# Transformers.js - Machine Learning for JavaScript

Transformers.js enables running state-of-the-art machine learning models directly in JavaScript across browsers and server-side runtimes (Node.js, Bun, Deno), with no Python server required.

## When to Use This Skill

Use this skill when you need to:
- Run ML models for text analysis, generation, or translation in JavaScript
- Perform image classification, object detection, or segmentation
- Implement speech recognition or audio processing
- Build multimodal AI applications (text-to-image, image-to-text, etc.)
- Run models client-side in the browser without a backend

## Installation

### NPM Installation
```bash
npm install @huggingface/transformers
```

### Browser Usage (CDN)
```javascript
<script type="module">
  import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers';
</script>
```

## Core Concepts

### 1. Pipeline API
The pipeline API is the easiest way to use models. It groups together preprocessing, model inference, and postprocessing:

```javascript
import { pipeline } from '@huggingface/transformers';

// Create a pipeline for a specific task
const pipe = await pipeline('sentiment-analysis');

// Use the pipeline
const result = await pipe('I love transformers!');
// Output: [{ label: 'POSITIVE', score: 0.999817686 }]

// IMPORTANT: Always dispose when done to free memory
await pipe.dispose();
```

**⚠️ Memory Management:** All pipelines must be disposed with `pipe.dispose()` when finished to prevent memory leaks. See examples in [Code Examples](./references/EXAMPLES.md) for cleanup patterns across different environments.

### 2. Model Selection
You can specify a custom model as the second argument:

```javascript
const pipe = await pipeline(
  'sentiment-analysis',
  'Xenova/bert-base-multilingual-uncased-sentiment'
);
```

**Finding Models:**

Browse available Transformers.js models on Hugging Face Hub:
- **All models**: https://huggingface.co/models?library=transformers.js&sort=trending
- **By task**: Add `pipeline_tag` parameter
  - Text generation: https://huggingface.co/models?pipeline_tag=text-generation&library=transformers.js&sort=trending
  - Image classification: https://huggingface.co/models?pipeline_tag=image-classification&library=transformers.js&sort=trending
  - Speech recognition: https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&library=transformers.js&sort=trending

**Tip:** Filter by task type, sort by trending/downloads, and check model cards for performance metrics and usage examples.

### 3. Device Selection
Choose where to run the model:

```javascript
// Run on CPU (default for WASM)
const pipe = await pipeline('sentiment-analysis', 'model-id');

// Run on GPU (WebGPU)
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  device: 'webgpu',
});
```

### 4. Quantization Options
Control model precision vs. performance:

```javascript
// Use quantized model (faster, smaller)
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  dtype: 'q4',  // Options: 'fp32', 'fp16', 'q8', 'q4'
});
```

## Supported Tasks & Reference Documentation

Transformers.js supports NLP, Computer Vision, Audio Processing, Multimodal, and Feature Extraction. For complete task walkthroughs, code samples, pipeline options, and model registry tables, refer to:
- [`references/EXAMPLES.md`](./references/EXAMPLES.md)
- [`references/PIPELINE_OPTIONS.md`](./references/PIPELINE_OPTIONS.md)
- [`references/TEXT_GENERATION.md`](./references/TEXT_GENERATION.md)
- [`references/MODEL_REGISTRY.md`](./references/MODEL_REGISTRY.md)
- [`references/CONFIGURATION.md`](./references/CONFIGURATION.md)
- [`references/CACHE.md`](./references/CACHE.md)
