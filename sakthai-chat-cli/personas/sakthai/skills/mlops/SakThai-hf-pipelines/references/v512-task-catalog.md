# Transformers Pipeline Task Catalog (v5.12.0)

Excerpt from official docs for quick reference. For parameter details see SKILL.md.

## NLP
- `text-classification` / `sentiment-analysis`
- `token-classification` / `ner`
- `fill-mask`
- `text-generation`
- `text2text-generation`
- `question-answering`
- `summarization`
- `translation`
- `feature-extraction`
- `zero-shot-classification`

## Audio
- `audio-classification`
- `automatic-speech-recognition` — supports CTC and Whisper timestamp modes (`"char"`, `"word"`, `True`)
- `text-to-audio` / `text-to-speech`
- `zero-shot-audio-classification` — uses `ClapModel`

## Computer Vision
- `image-classification`
- `image-segmentation` — supports `semantic`, `instance`, `panoptic` subtasks
- `object-detection`
- `depth-estimation`
- `mask-generation` — v5-era addition
- `keypoint-matching` — v5-era addition
- `zero-shot-image-classification`
- `zero-shot-object-detection`
- `image-feature-extraction`

## Multimodal
- `image-text-to-text` — v5-era addition
- `document-question-answering`
- `table-question-answering`
- `video-classification`

## Batch Performance Notes (from docs)
- Batching can yield 10× speedup OR major slowdown depending on sequence length regularity.
- If one sample in a batch is 400 tokens and the rest are 4, the whole tensor pads to 400 → possible OOM.
- Policy: start at `batch_size=1`, tentatively raise to 8 → 64 → 256, always OOM-guard.
- `KeyDataset` and `KeyPairDataset` live in `transformers.pipelines.pt_utils`.

## ChunkPipeline Special Cases
- `zero-shot-classification` and `question-answering` are `ChunkPipeline`.
- Internally iterate over multiple preprocessed chunks per input, but API is identical.
- `batch_size` controls the *forward* batch; chunking is transparent.

## Custom Pipeline Hook
```python
from transformers import TextClassificationPipeline

class MyPipe(TextClassificationPipeline):
    def postprocess(self, model_outputs, **kwargs):
        scores = super().postprocess(model_outputs, **kwargs)
        return [{"percent": round(s["score"] * 100, 1), "label": s["label"]} for s in scores]

pipe = pipeline(model="x", pipeline_class=MyPipe)
```
