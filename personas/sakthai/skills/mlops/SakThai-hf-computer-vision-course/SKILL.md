---
name: SakThai-hf-computer-vision-course
description: >-
  Complete reference on the Hugging Face Community Computer Vision Course — full unit-by-unit
  syllabus, key models and libraries (timm, transformers, diffusers, datasets), notebook
  inventory with Colab links, and pointers to the HF ecosystem for each CV task.
category: mlops
tags:
  - computer-vision
  - course
  - timm
  - training
  - classification
  - detection
  - segmentation
  - multimodal
  - generative
  - 3d-vision
  - video-processing
  - synthetic-data
  - colab
  - notebook
  - transformer
  - cnn
---

# HF Community Computer Vision Course — Complete Reference

**Course URL:** https://huggingface.co/learn/computer-vision-course
**Source:** Community-driven (not official HF staff); content lives at `/learn/computer-vision-course/unit{N}/{topic}`
**Discourse / community:** Discord — `#computer-vision`, `#cv-study-group`, `#3d` channels
**Notebooks:** Colab-linked notebooks at the [Table of Contents for Notebooks](https://huggingface.co/learn/computer-vision-course/unit0/welcome/table_of_contents) page
**Certification:** None currently

## Overview

The **Community Computer Vision Course** is a community-driven, free, open-source curriculum covering the entire computer vision stack — from the physics of light and image formation all the way to state-of-the-art Vision Transformers, multimodal models, 3D reconstruction, and synthetic data generation. It uses the Hugging Face ecosystem (`transformers`, `timm`, `diffusers`, `datasets`, `accelerate`) extensively for hands-on notebooks.

## Unit-by-Unit Syllabus

### Unit 0 — Welcome
- Course introduction, community guidelines
- Table of Contents for Notebooks (central index of all Colab notebooks)

### Unit 1 — Fundamentals
| Section | Topics |
|---------|--------|
| Vision | Physics of light, human vision vs. computer vision |
| Image | Digital image representation, pixels, color spaces |
| Imaging | Cameras, lenses, sensors, image formation |
| What Is Computer Vision | Definition, deep learning renaissance, image understanding levels |
| Applications of CV | Real-world use cases |
| Pre-processing | Resizing, normalization, augmentation, color space conversion |
| Feature Description | Hand-crafted features (SIFT, SURF, ORB) |
| Feature Matching | Matching features across images |

### Unit 2 — Convolutional Neural Networks
| Section | Key Models / Concepts |
|---------|----------------------|
| Introduction to CNNs | Convolution, pooling, strides, padding |
| VGG | Very Deep Convolutional Networks |
| GoogLeNet | Inception modules |
| MobileNet | Depthwise separable convolutions |
| ConvNeXt | Modernized ConvNet for 2020s |
| Transfer Learning | Fine-tuning pre-trained CNNs |
| ResNet | Residual connections, bottleneck blocks |
| YOLO | Real-time object detection |

**Notebooks:**
- Transfer Learning with VGG19
- Using ResNet with `timm`

### Unit 3 — Vision Transformers
| Section | Key Models / Concepts |
|---------|----------------------|
| ViTs for Image Classification | Patch embedding, transformer encoder, CLS token |
| Swin Transformer | Hierarchical, shifted windows |
| CvT | Convolutional Vision Transformer |
| DiNAT | Dilated Neighborhood Attention Transformer |
| MobileViT v2 | Lightweight ViT for mobile |
| Fine-tuning ViT for Object Detection | ViT + detection heads |
| DETR | DEtection TRansformer — end-to-end object detection |
| ViTs for Image Segmentation | Segmenter, SETR |
| OneFormer | Unified segmentation (semantic, instance, panoptic) |
| Knowledge Distillation with ViTs | Teacher-student training |

**Notebooks:**
- DETR
- Fine-tuning ViT for Object Detection
- Knowledge Distillation
- LoRA Fine-tuning for Image Classification
- Multilabel Image Classification
- Transfer Learning for Image Classification
- Transfer Learning for Image Segmentation
- Swin Transformer

### Unit 4 — Multimodal Models
| Section | Key Models / Concepts |
|---------|----------------------|
| A Multimodal World | Aligning vision and language modalities |
| Introduction to VLMs | Vision-Language Model architectures |
| Multimodal Tasks and Models | VQA, captioning, retrieval, grounding |
| CLIP and Relatives | Contrastive Language-Image Pre-training |
| Losses | Contrastive loss, InfoNCE |
| CLIP | Dual-encoder architecture |
| BLIP | Bootstrapping Language-Image Pre-training |
| OWL-ViT | Open-vocabulary object detection |
| Transfer Learning of Multimodal Models | Adapting CLIP/BLIP to downstream tasks |

**Notebooks:**
- CLIP Crop, CLIP Fine-tuning, CLIP Clustering
- Image Classification with CLIP
- Image Retrieval with Prompts
- Image Similarity

### Unit 5 — Generative Models
| Section | Topics / Models |
|---------|-----------------|
| VAEs | Encoder-decoder, latent space, KL divergence |
| GANs | Generator, discriminator, adversarial training |
| StyleGAN | Style-based generator, adaptive instance normalization |
| CycleGAN | Unpaired image-to-image translation |
| Diffusion Models | Forward/reverse process, DDPM |
| Stable Diffusion | Latent diffusion, UNet, cross-attention |

*No dedicated notebooks — references the HF Diffusion Course.*

### Unit 6 — Basic CV Tasks
| Section | Key Models / Concepts |
|---------|----------------------|
| Object Detection | Bounding boxes, anchor boxes, IoU, NMS |
| Image Segmentation | Semantic, instance, panoptic segmentation |

**Notebooks:** Fine-tune SAM on Custom Dataset

### Unit 7 — Video and Video Processing
| Section | Key Models / Concepts |
|---------|----------------------|
| Video Processing Basics | Frame sampling, optical flow, tracking |
| Multimodal Based Video Models | Video+text models |
| CNN Based Video Models | 3D CNNs, I3D, C3D |
| RNN Based Video Models | LSTM, GRU for video |
| Transformers Based Models | ViViT, TimeSformer, VideoMAE |

**Notebooks:** Fine-tune ViViT for Video Classification

### Unit 8 — 3D Vision, Scene Rendering and Reconstruction
| Section | Key Models / Concepts |
|---------|----------------------|
| Camera Models | Pinhole, intrinsic/extrinsic matrices |
| Representations for 3D Data | Point clouds, meshes, voxels, implicit surfaces |
| Monocular Depth Estimation | Depth from single image |
| Novel View Synthesis | NVS, NeRF-W |
| Stereo Vision | Disparity, epipolar geometry |
| NeRFs | Neural Radiance Fields, positional encoding, volume rendering |

### Unit 9 — Model Optimization
| Section | Tools / Frameworks |
|---------|-------------------|
| Deployment Considerations | Latency, throughput, memory, hardware targets |
| Optimization Tools | Edge TPU, ONNX, OpenVINO, Optimum, TensorRT, TorchScript |

**Notebooks:** Edge TPU, ONNX, OpenVINO, Optimum, TensorRT, TMO, Torch

### Unit 10 — Synthetic Data Creation
| Section | Key Concepts |
|---------|-------------|
| BlenderProc | 3D rendering pipeline for synthetic data |
| DCGAN for Synthetic Data | Lung image generation |
| Diffusion Models for Data Gen | SDXL Turbo pipeline for data |
| Point Clouds | LiDAR data, 3D scanning |

**Notebooks:** OWLv2 labeling, BLIP-2 labeling, BlenderProc, SDXL Turbo

### Unit 11 — Zero Shot Computer Vision
- Zero-shot paradigm, open-vocabulary
- CLIP, OWL-ViT, Grounding DINO for zero-shot tasks

### Unit 12 — Ethics and Biases
- Dataset bias, fairness, transparency
- Hugging Face's Ethics & Society team

### Unit 13 — Outlook
| Architecture | Key Idea |
|-------------|----------|
| Hiera | Hierarchical vision transformer |
| Hyena | Sub-quadratic attention replacement |
| I-JEPA | Image-based Joint Embedding Predictive Architecture |

## Key Models Covered

| Model | Unit | HF Hub ID |
|-------|------|-----------|
| ResNet | U2 | `microsoft/resnet-50` |
| VGG | U2 | `google/vgg16` |
| MobileNetV3 | U2 | `google/mobilenet_v3_*` |
| ConvNeXt | U2 | `facebook/convnext-*` |
| YOLOS | U2 | `hustvl/yolos-*` |
| ViT | U3 | `google/vit-base-patch16-224` |
| Swin Transformer | U3 | `microsoft/swin-*` |
| CvT | U3 | `microsoft/cvt-*` |
| DiNAT | U3 | `shi-labs/dinat-*` |
| MobileViT | U3 | `apple/mobilevit-*` |
| DETR | U3 | `facebook/detr-resnet-50` |
| OneFormer | U3 | `shi-labs/oneformer_*` |
| CLIP | U4 | `openai/clip-vit-base-patch32` |
| BLIP-2 | U4 | `Salesforce/blip2-opt-2.7b` |
| OWL-ViT | U4 | `google/owlvit-base-patch32` |
| SAM | U6 | `facebook/sam-vit-base` |
| ViViT | U7 | `google/vivit-b16x2-kinetics400` |

## Key HF Libraries Used

| Library | Purpose | Units |
|---------|---------|-------|
| `transformers` | ViT, DETR, CLIP, BLIP, OWL-ViT, SAM, ViViT | 3, 4, 6, 7 |
| `timm` | CNN/ViT model zoo, pre-trained backbones | 2, 3 |
| `diffusers` | Stable Diffusion, ControlNet | 5, 10 |
| `datasets` | Dataset loading, image processing, augmentation | All |
| `accelerate` | Multi-GPU training, mixed precision | 3, 9 |
| `optimum` | ONNX, OpenVINO, Intel optimizations | 9 |
| `evaluate` | Metrics (accuracy, IoU, mAP) | 2, 3, 6 |

## When to Use This Skill

Load this skill when:
- The user asks about the HF Computer Vision Course or wants a summary
- You need to reference course material for a CV task (classification, detection, segmentation, multimodal)
- The user wants to know which HF models/libraries to use for a specific CV problem
- You're comparing HF educational resources across courses
- The user needs Colab notebook links for hands-on CV practice

## Quick Reference — Inference Pipelines

```python
from transformers import pipeline

# Image Classification
pipe = pipeline("image-classification", model="google/vit-base-patch16-224")
result = pipe("cat.jpg")  # returns [{"label": "cat", "score": 0.99}, ...]

# Object Detection
pipe = pipeline("object-detection", model="facebook/detr-resnet-50")
results = pipe("scene.jpg")  # returns boxes + labels + scores

# Image Segmentation
pipe = pipeline("image-segmentation", model="facebook/detr-resnet-50-panoptic")
segments = pipe("street.jpg")

# Zero-shot Classification (CLIP)
pipe = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
result = pipe("animal.jpg", candidate_labels=["cat", "dog", "car"])
```

## Fine-tuning a ViT

```python
from transformers import ViTForImageClassification, ViTImageProcessor, Trainer, TrainingArguments
from datasets import load_dataset

dataset = load_dataset("imagefolder", data_dir="./images")
labels = dataset["train"].features["label"].names

model = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=len(labels),
    id2label={i: l for i, l in enumerate(labels)},
    label2id={l: i for i, l in enumerate(labels)}
)

training_args = TrainingArguments(
    output_dir="./vit-finetuned",
    per_device_train_batch_size=16,
    num_train_epochs=3,
    learning_rate=2e-5,
    remove_unused_columns=False,
)
trainer = Trainer(model=model, args=training_args, train_dataset=dataset["train"])
trainer.train()
```

## Relationship to Other HF Courses

| Course | Overlap | Difference |
|--------|---------|------------|
| **Diffusion Course** | Unit 5 (gen models) | CV course covers more than diffusion |
| **LLM Course** | Unit 4 (multimodal) | CV course focuses on vision side of VLMs |
| **ML for 3D Course** | Unit 8 | CV course has shallower 3D coverage |
| **Audio Course** | None | Different modality |

## Pitfalls

- **Unit 5 has NO notebooks** — practical GAN/diffusion work requires the separate Diffusion Course.
- **Unit 8 has NO notebooks** — 3D content is pure theory.
- Some notebook Colab links may be stale — check the GitHub repo at `huggingface/computer-vision-course`.
- ViT models need normalized inputs via their processor, not raw images.
- Zero-shot CLIP performance drops on domain-specific (medical, satellite) images.
- Fine-tuning on <100 images/class overfits — use augmentation.
