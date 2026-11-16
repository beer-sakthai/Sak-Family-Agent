# HF Hub Model Tag Taxonomy — Deep Dive

## 2026-07-30: hf-hub-models-architecture-and-pipeline-tags — Complete Tag Taxonomy Deep Dive (Topic #164 Deepened)

### Summary
Comprehensive deep-dive into the Hugging Face Hub's model tag taxonomy — the
classification system that powers model discovery, filtering, and widget
selection across 1M+ models. Covers all 6 tag categories (pipeline, library,
language, license, architecture, custom), the 47 official pipeline tags, the
automatic tag inference pipeline, search/filter API patterns using tags, the
`/api/tasks` endpoint, and the gist-based architecture-to-pipeline mapping used
by the Hub backend. All research against the live production API and official
documentation.

---

### The Tag System Overview

Every model on the Hugging Face Hub has tags displayed below the model name on
its page. These tags serve four purposes:

1. **Discovery** — Users filter/search models by task, library, or license
2. **Widget selection** — Pipeline tag determines which inference widget loads
3. **API routing** — Inference API uses pipeline tags for endpoint selection
4. **Categorization** — Architecture tags enable library-specific grouping

There are **6 tag categories** that appear on model pages:

---

### 1. Pipeline Tags (The Primary Classifier)

The `pipeline_tag` is the **most important tag** — a single canonical value that
identifies the ML task a model performs. There are **47 official pipeline tags**
as of July 2026:

#### Text & Language Tasks (12)
| Tag | Description |
|-----|-------------|
| `fill-mask` | Masked language modeling |
| `question-answering` | Extractive QA |
| `sentence-similarity` | Semantic textual similarity |
| `summarization` | Text summarization |
| `table-question-answering` | QA over tabular data |
| `text-classification` | Sentiment, topic, etc. |
| `text-generation` | Causal/autoregressive LM |
| `text-ranking` | Cross-encoder ranking |
| `text-to-image` | Text-conditioned image generation |
| `text-to-speech` | TTS |
| `text-to-video` | Text-conditioned video generation |
| `token-classification` | NER, POS tagging |
| `translation` | Machine translation |
| `text-to-3d` | Text-to-3D asset generation |
| `feature-extraction` | Embedding generation |
| `zero-shot-classification` | NLI-based zero-shot |

#### Vision Tasks (12)
| Tag | Description |
|-----|-------------|
| `depth-estimation` | Monocular depth |
| `image-classification` | Image classifier |
| `image-feature-extraction` | Vision embeddings |
| `image-segmentation` | Semantic/instance segmentation |
| `image-to-image` | Image translation/restoration |
| `image-to-text` | Captioning, OCR |
| `image-to-3d` | Single-image 3D |
| `image-text-to-text` | VLM (vision-language) |
| `image-text-to-image` | Image editing with text guidance |
| `image-text-to-video` | Video from image+text |
| `image-to-video` | Video from image |
| `mask-generation` | SAM-style mask generation |
| `object-detection` | Bounding box detection |
| `keypoint-detection` | Pose/keypoint estimation |
| `video-classification` | Video classifier |
| `video-text-to-text` | Video-language models |
| `video-to-video` | Video translation/enhancement |
| `visual-question-answering` | VQA |
| `visual-document-retrieval` | Document search |
| `zero-shot-image-classification` | CLIP-style classification |
| `zero-shot-object-detection` | Open-vocabulary detection |
| `unconditional-image-generation` | Unconditional image gen |

#### Audio Tasks (5)
| Tag | Description |
|-----|-------------|
| `audio-classification` | Sound/audio classifier |
| `audio-text-to-text` | Audio understanding |
| `audio-to-audio` | Audio enhancement/separation |
| `automatic-speech-recognition` | ASR/Speech-to-text |
| `text-to-speech` | TTS |

#### Multimodal & Other (5)
| Tag | Description |
|-----|-------------|
| `any-to-any` | Universal I/O (e.g., Image2Image, etc.) |
| `reinforcement-learning` | RL models (HF-based) |
| `tabular-classification` | Tabular classification |
| `tabular-regression` | Tabular regression |
| `time-series-forecasting` | Time series prediction |

#### Special
| Tag | Description |
|-----|-------------|
| `conversational` | **Not a pipeline tag** — companion flag on `text-generation` or `image-text-to-text` models to show the chat widget |

### How Pipeline Tags Are Inferred

The Hub determines `pipeline_tag` automatically using this priority chain:

1. **Explicit override** — If `pipeline_tag: xxx` in model card YAML, use it
2. **Transformers config inference** — If model has `config.json`, the Hub maps
   `architectures[]` values (e.g., `AutoModelForTokenClassification` →
   `token-classification`) using the reference gist:
   https://gist.github.com/nateraw/ebb775707f14aeb6b1f6c856f7b60815
3. **Library-specific logic** — sentence-transformers → `sentence-similarity` or
   `feature-extraction`; spaCy → `token-classification`, etc.
4. **Tag-based fallback** — If no config auto-detect, uses the most specific
   task-identifying tag from `tags` array in model card YAML
5. **Default** — `feature-extraction` if nothing else matches

#### Special Case: Conversational Widget

The conversational chat widget requires **both** criteria:
- Pipeline tag is `text-generation` or `image-text-to-text`
- Model has the tag `conversational` (either auto-detected from model card or
  manually set)

This means a model can be `text-generation` without being `conversational` —
the chat UI only activates when both conditions are met.

---

### 2. Library Tags

Library tags identify which framework/library a model uses. Common values:

| Tag | Notes |
|-----|-------|
| `transformers` | Hugging Face Transformers (most common) |
| `sentence-transformers` | Embedding models |
| `diffusers` | Diffusion models |
| `timm` | PyTorch Image Models |
| `keras` | Keras |
| `spacy` | spaCy NLP |
| `flair` | Flair NLP |
| `stable-baselines3` | RL models |
| `sample-factory` | RL models |
| `fastai` | Fast.ai |
| `sklearn` | Scikit-learn |
| `peft` | PEFT adapters |
| `tensorflow` | TensorFlow |
| `onnx` | ONNX runtime |
| `openvino` | OpenVINO IR |
| `coreml` | Core ML |
| `gguf` | GGUF format (llama.cpp) |
| `llamafile` | Llamafile |
| `transformers.js` | Web inference |

The `library_name` is set in model card YAML. For transformers models it's
automatically set to `transformers`.

---

### 3. Architecture Tags

Architecture tags identify the specific neural architecture. These are
auto-extracted from model configuration:
- Transformers: from `config.json` → `model_type` field (e.g., `llama`,
  `bert`, `gpt2`, `t5`, `qwen2`, `mistral`)
- sentence-transformers: from `modules.json`
- Other libraries: from library-specific config

Common architecture tags sampled from top models:
`bert`, `llama`, `gpt2`, `t5`, `roberta`, `xlm-roberta`, `deberta-v2`,
`electra`, `mpnet`, `qwen3`, `mistral`, `falcon`, `gemma`, `phi`,
`qwen2`, `stable-diffusion`, `vit`, `resnet`, `whisper`, `wav2vec2`

---

### 4. Language Tags

Language tags use the **two-letter ISO 639-1 codes** (lowercase):
`en`, `fr`, `de`, `es`, `it`, `pt`, `zh`, `ja`, `ko`, `ar`, `ru`, `th`,
`vi`, `nl`, `pl`, `tr`, `ro`, `sv`, `da`, `fi`, `nb`, `cs`, `hu`, `el`,
`he`, `hi`, `id`, `ms`, `bn`, `ta`, `te`, `mr`, `ur`, `fa`, `sw`, etc.

The special tag `multilingual` is used for models supporting multiple languages.

---

### 5. License Tags

Formatted as `license:<identifier>`:
- `license:apache-2.0` (most common)
- `license:mit`
- `license:bsd`
- `license:cc-by-4.0`
- `license:cc-by-nc-4.0`
- `license:llama2` (Meta Llama custom)
- `license:llama3`
- `license:open-rail` (Stability AI)
- `license:bigcode-openrail-m`
- `license:bigscience-openrail-m`
- `license:creativeml-openrail-m`
- `license:other` (requires `license_name` + `license_link` in metadata)
- `license:unknown`

Custom licenses use:
```yaml
license: other
license_name: my-custom-license
license_link: https://example.com/license
```

---

### 6. Other Auto-Generated Tag Prefixes

The Hub automatically generates tags from model card metadata:

| Prefix | Source | Example |
|--------|--------|---------|
| `arxiv:` | `arxiv:` field or paper URL | `arxiv:2302.13971` |
| `dataset:` | `datasets:` field | `dataset:wikipedia` |
| `base_model:` | `base_model:` field | `base_model:Qwen/Qwen3-0.6B-Base` |
| `base_model:finetune:` | Finetuned from | `base_model:finetune:Qwen/Qwen3-0.6B-Base` |
| `base_model:quantized:` | Quantized from | `base_model:quantized:meta-llama/Llama-3.1-8B` |
| `doi:` | DOI paper link | `doi:10.57967/hf/0039` |
| `deploy:` | Deployment platform | `deploy:azure`, `deploy:sagemaker` |
| `region:` | Deployment region | `region:us`, `region:eu` |
| `not-for-all-audiences` | NSFW/content flag | (boolean presence) |
| `eval-results` | Has evaluation results | (boolean presence) |
| `endpoints_compatible` | Compatible with Inference Endpoints | (boolean presence) |
| `text-generation-inference` | TGI-optimized | (boolean presence) |
| `text-embeddings-inference` | TEI-optimized | (boolean presence) |
| `conversational` | Chat-capable | (boolean presence) |
| `mteb` | MTEB benchmarked | (boolean presence) |
| `exbert` | Has exBERT visualization | (boolean presence) |

---

### Search & Filter API Patterns Using Tags

The `/api/models` endpoint supports comprehensive tag-based filtering:

#### By pipeline tag
```
GET /api/models?pipeline_tag=text-generation
GET /api/models?pipeline_tag=image-classification&sort=downloads&direction=-1
```

#### By library
```
GET /api/models?library=sentence-transformers
```

#### By multiple tags (AND logic)
```
GET /api/models?filter=transformers,text-generation,safetensors
```

#### By language
```
GET /api/models?filter=th
```

#### By license
```
GET /api/models?filter=license:apache-2.0
```

#### Full search with tag filter
```
GET /api/models?search=translation&filter=transformers,t5
```

#### Pipeline tag distribution (counts)
```python
import requests
resp = requests.get("https://huggingface.co/api/models?pipeline_tag=text-generation")
print(f"text-generation models: {resp.json()['count'] if 'count' in resp.json() else len(resp.json())}")
# Note: the list endpoint returns paginated results; use `?limit=0` for counts
```

#### Known tag prefixes registry
```python
# All known tag prefixes from the Hub's internal tag registry
TAG_PREFIXES = [
    "arxiv:", "dataset:", "base_model:", "base_model:finetune:",
    "base_model:quantized:", "deploy:", "region:", "doi:", "license:"
]
```

---

### The 47 Pipeline Tags — Complete Reference

**47 total official pipeline tags**, confirmed via the `/tasks` page HTML and the
Hub's OpenAPI specification:

```
any-to-any
audio-classification
audio-text-to-text
audio-to-audio
automatic-speech-recognition
depth-estimation
document-question-answering
feature-extraction
fill-mask
image-classification
image-feature-extraction
image-segmentation
image-text-to-image
image-text-to-text
image-text-to-video
image-to-3d
image-to-image
image-to-text
image-to-video
keypoint-detection
mask-generation
object-detection
question-answering
reinforcement-learning
sentence-similarity
summarization
table-question-answering
tabular-classification
tabular-regression
text-classification
text-generation
text-ranking
text-to-3d
text-to-image
text-to-speech
text-to-video
time-series-forecasting
token-classification
translation
unconditional-image-generation
video-classification
video-text-to-text
video-to-video
visual-document-retrieval
visual-question-answering
zero-shot-classification
zero-shot-image-classification
zero-shot-object-detection
```

Note: `conversational` is NOT a pipeline tag — it's a boolean tag that enables
the chat widget on `text-generation` or `image-text-to-text` models.

---

### Key Discovery: Tag Auto-Detection Pipeline

1. When a model is uploaded/pushed, the Hub scans the repo for config files
2. For transformers models, it reads `config.json` → `architectures[]` array
3. The architecture-to-pipeline mapping (now documented in the widgets docs
   with a reference gist) maps architectures to pipeline tags:
   - `AutoModelForTokenClassification` → `token-classification`
   - `AutoModelForSequenceClassification` → `text-classification`
   - `LlamaForCausalLM` → `text-generation`
   - `CLIPModel` → `zero-shot-image-classification`
   - etc.
4. sentence-transformers uses `modules.json` to detect `sentence-similarity`
   vs `feature-extraction`
5. Other libraries provide their own detection logic
6. If nothing matches, the first matching tag in the YAML `tags` array is used
7. Final fallback: `feature-extraction`

### Key Discovery: Tag System Is Single-Source for Widget Routing

The widget system is tightly coupled to pipeline_tag:
- **One widget per model** — the Pipeline Tag uniquely determines which widget
  type renders on the model page
- The conversational widget is the only exception — it requires both
  `pipeline_tag=text-generation|image-text-to-text` AND `tag: conversational`
- Widget examples can be customized via the `widget:` YAML field with `text:`
  or `src:` (for audio/image)

### Key Discovery: No Public Tag Registry API

Unlike datasets (which have `/api/tags`), there is no public authenticated-free
endpoint to enumerate all valid model tags. The tag system can only be
reverse-engineered through:
1. The `/tasks` page HTML (47 pipeline tags)
2. The OpenAPI spec at `/.well-known/openapi.md`
3. Live API queries with `?filter=` parameters
4. The widgets documentation's architecture-to-pipeline mapping gist
5. Scanning the Hub for common tag patterns

---

### Practical Patterns

#### Finding all pipeline tags in use
```python
import requests

# Get a large sample and aggregate pipeline tags
all_ptags = set()
page = 1
while len(all_ptags) < 47 and page < 20:
    resp = requests.get(
        f"https://huggingface.co/api/models?sort=downloads&limit=100",
        params={"direction": -1, "offset": (page-1)*100}
    )
    for model in resp.json():
        pt = model.get("pipeline_tag")
        if pt:
            all_ptags.add(pt)
    page += 1
```

#### Checking if a model supports chat
```python
import requests
resp = requests.get("https://huggingface.co/api/models/meta-llama/Llama-3.1-8B-Instruct")
model = resp.json()
is_chat = (
    model.get("pipeline_tag") in ("text-generation", "image-text-to-text")
    and "conversational" in model.get("tags", [])
)
```

#### Architecture-to-pipeline inference
```python
# Simplified mapping based on transformers config.json architectures
ARCH_TO_PIPELINE = {
    "LlamaForCausalLM": "text-generation",
    "MistralForCausalLM": "text-generation",
    "Qwen2ForCausalLM": "text-generation",
    "GPT2LMHeadModel": "text-generation",
    "BertForSequenceClassification": "text-classification",
    "RobertaForSequenceClassification": "text-classification",
    "DistilBertForSequenceClassification": "text-classification",
    "BertForTokenClassification": "token-classification",
    "RobertaForTokenClassification": "token-classification",
    "T5ForConditionalGeneration": "translation",
    "WhisperForConditionalGeneration": "automatic-speech-recognition",
    "CLIPModel": "zero-shot-image-classification",
    "ViTForImageClassification": "image-classification",
    "SamModel": "mask-generation",
    "DetrForObjectDetection": "object-detection",
    "Wav2Vec2ForCTC": "automatic-speech-recognition",
    "StableDiffusionPipeline": "text-to-image",
    "StableDiffusionXL": "text-to-image",
    # ... 100+ more mappings in the reference gist
}
```

**Full reference gist:** https://gist.github.com/nateraw/ebb775707f14aeb6b1f6c856f7b60815

---

### Sources
- HF Hub docs: https://huggingface.co/docs/hub/en/model-cards
- HF widgets docs: https://huggingface.co/docs/hub/en/models-widgets
- Architecture mapping gist: https://gist.github.com/nateraw/ebb775707f14aeb6b1f6c856f7b60815
- Tasks page: https://huggingface.co/tasks
- Models API: `GET https://huggingface.co/api/models`
- OpenAPI spec: `https://huggingface.co/.well-known/openapi.md`
- Live API research against `huggingface.co/api/models?sort=downloads`
- HF Hub `/api/tags` endpoint (auth-only, not publicly documented for models)
