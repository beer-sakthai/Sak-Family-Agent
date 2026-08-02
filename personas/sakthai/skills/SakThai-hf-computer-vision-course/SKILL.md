---
name: SakThai-hf-computer-vision-course
author: SakThai
license: MIT
description: "Computer vision with HF — classification, detection, more."
version: 1.0.0
tags: [ComputerVision, ImageClassification, ObjectDetection, HuggingFace, ViT]
---
# Computer Vision with Hugging Face

Based on the [Community HF Computer Vision Course](https://huggingface.co/learn/computer-vision-course). Covers CNNs, Vision Transformers (ViT), multimodal models, generative CV, object detection, segmentation, video processing, 3D vision, optimization, and synthetic data.

## When to Use

- User wants to "classify images" or "detect objects"
- User asks about Vision Transformers (ViT) or image segmentation
- User needs to train/fine-tune a CV model
- User wants zero-shot classification or synthetic data generation

## Prerequisites

```bash
pip install transformers datasets torch torchvision timm Pillow
# For video processing:
pip install opencv-python av
```

## Quick Reference

| Task | Recommended Model | Pipeline ID | Model Size |
|------|-------------------|-------------|------------|
| Image Classification | `google/vit-base-patch16-224` | `image-classification` | 330MB |
| Object Detection | `facebook/detr-resnet-50` | `object-detection` | 164MB |
| Image Segmentation | `facebook/detr-resnet-50-panoptic` | `image-segmentation` | 169MB |
| Depth Estimation | `Intel/dpt-hybrid-midas` | `depth-estimation` | 530MB |
| Zero-shot Classification | `openai/clip-vit-base-patch32` | `zero-shot-image-classification` | 600MB |
| Image-to-Text (Captioning) | `Salesforce/blip-image-captioning-base` | `image-to-text` | 990MB |
| Video Classification | `MCG-NJU/videomae-base` | `video-classification` | 460MB |
| Semantic Segmentation | `nvidia/segformer-b0-finetuned-ade-512-512` | `image-segmentation` | 14MB |

## Inference Examples

### Image Classification
```python
from transformers import pipeline
from PIL import Image
import requests

url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/cat.png"
image = Image.open(requests.get(url, stream=True).raw)
pipe = pipeline("image-classification", model="google/vit-base-patch16-224")
result = pipe(image)
for r in result:
    print(f"{r['label']}: {r['score']:.4f}")
```

### Object Detection
```python
from transformers import pipeline
pipe = pipeline("object-detection", model="facebook/detr-resnet-50")
results = pipe("image.jpg")
for r in results:
    box = r["box"]
    print(f"{r['label']} ({r['score']:.2f}): [{box['xmin']:.0f}, {box['ymin']:.0f}, {box['xmax']:.0f}, {box['ymax']:.0f}]")
```

### Image Segmentation (Panoptic)
```python
from transformers import pipeline
pipe = pipeline("image-segmentation", model="facebook/detr-resnet-50-panoptic")
segments = pipe("street_scene.jpg")
for s in segments:
    print(f"Segment: {s['label']} (score: {s['score']:.2f})")
```

### Depth Estimation
```python
from transformers import pipeline
pipe = pipeline("depth-estimation", model="Intel/dpt-hybrid-midas")
result = pipe("indoor_room.jpg")
result["depth"].save("depth_map.png")
```

### Zero-shot Classification (CLIP)
```python
from transformers import pipeline
pipe = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
result = pipe("animal.jpg", candidate_labels=["cat", "dog", "car", "tree"])
for r in result:
    print(f"{r['label']}: {r['score']:.4f}")
```

## Model Recommendations by Use Case

| Use Case | Model | Why |
|----------|-------|-----|
| General classification | `google/vit-base-patch16-224` | Best accuracy/speed tradeoff |
| High-accuracy classification | `google/vit-large-patch16-224` | Bigger ViT, better results |
| Lightweight mobile | `microsoft/resnet-18` | 45MB, fast inference |
| Real-time detection | `facebook/detr-resnet-50` | End-to-end, no NMS needed |
| Small object detection | `hustvl/yolos-tiny` | 28MB, transformer-based |
| Self-supervised features | `facebook/dinov2-base` | Strong feature extractor |
| Fine-grained classification | Fine-tune ViT on your data | Adapt to specific domains |
| Medical imaging | Fine-tune ViT on your data | Domain-specific > general |

## Fine-tuning a ViT

```python
from transformers import (
    ViTForImageClassification, ViTImageProcessor,
    Trainer, TrainingArguments, DefaultDataCollator
)
from datasets import load_dataset

dataset = load_dataset("imagefolder", data_dir="./images")
labels = dataset["train"].features["label"].names

model = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=len(labels),
    id2label={i: l for i, l in enumerate(labels)},
    label2id={l: i for i, l in enumerate(labels)}
)
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

def preprocess(batch):
    inputs = processor(images=batch["image"], return_tensors="pt")
    inputs["labels"] = batch["label"]
    return inputs

ds = dataset.with_transform(preprocess)

training_args = TrainingArguments(
    output_dir="./vit-finetuned",
    per_device_train_batch_size=16,
    evaluation_strategy="steps",
    num_train_epochs=3,
    save_steps=500, eval_steps=500,
    logging_steps=100, learning_rate=2e-5,
    remove_unused_columns=False,
)
trainer = Trainer(
    model=model, args=training_args, data_collator=DefaultDataCollator(),
    train_dataset=ds["train"], eval_dataset=ds["test"],
)
trainer.train()
```

## Video Processing

```python
from transformers import pipeline
from decord import VideoReader, cpu
import numpy as np

vr = VideoReader("video.mp4", ctx=cpu(0))
indices = np.linspace(0, len(vr) - 1, 16).astype(int)
frames = vr.get_batch(indices).asnumpy()
pipe = pipeline("video-classification", model="MCG-NJU/videomae-base")
result = pipe(frames)
print(result[0]["label"], result[0]["score"])
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OOM on large images | Use processor resizing |
| Wrong label names | Check model's `id2label` config on the Hub |
| Slow detection | Try `hustvl/yolos-tiny` or use half-precision |
| Poor zero-shot results | CLIP works best on natural images; fine-tune for domain-specific |
| Video processing crashes | Install `decord` or `av`, process frame-by-frame |

## Pitfalls

- Detection/segmentation models expect specific input sizes — use the model's processor.
- ViT models need normalized inputs — use the processor, not raw images.
- Zero-shot CLIP works best with natural images; performance drops on medical/domain-specific images.
- Video processing is memory-intensive — process frame-by-frame or use temporal pooling.
- Fine-tuning on small datasets (<100 images per class) may overfit — use data augmentation.

## Verification

```python
from transformers import pipeline
pipe = pipeline("image-classification")
print(pipe("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/cat.png"))
```
