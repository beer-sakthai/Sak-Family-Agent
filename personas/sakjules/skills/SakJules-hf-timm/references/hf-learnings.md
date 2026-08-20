# HF Learnings — hf-timm

## 2026-07-24: hf-timm — PyTorch Image Models Deep Dive (Topic #178 — New)

### Summary
Comprehensive deep-dive into `timm` (PyTorch Image Models) v1.0.28 — the library of 1,000+ pretrained vision models now part of the Hugging Face ecosystem. Covers installation, model creation/listing, inference pipeline, feature extraction (penultimate, multi-scale, intermediate), data augmentation and transforms, Hugging Face Hub integration, the official training script, and key configuration parameters.

### Source
- timm docs: https://huggingface.co/docs/timm/en/index
- Quickstart: https://huggingface.co/docs/timm/en/quickstart
- Installation: https://huggingface.co/docs/timm/en/installation
- Feature Extraction: https://huggingface.co/docs/timm/en/feature_extraction
- HF Hub: https://huggingface.co/docs/timm/en/hf_hub
- Training Script: https://huggingface.co/docs/timm/en/training_script
- Reference — Models: https://huggingface.co/docs/timm/en/reference/models
- Reference — Data: https://huggingface.co/docs/timm/en/reference/data
- Reference — Optimizers: https://huggingface.co/docs/timm/en/reference/optimizers
- GitHub: https://github.com/rwightman/pytorch-image-models

### 1. What Is timm?

`timm` (PyTorch Image Models) is an open-source library by Ross Wightman that provides **1,000+ pretrained vision models** across 200+ architectures. It became part of the Hugging Face ecosystem and is available as `timm` on PyPI. It covers CNNs (ResNet, EfficientNet, ConvNeXt), Vision Transformers (ViT, DeiT, Swin), hybrid architectures, and more.

Key design principles:
- **Unified interface** — `timm.create_model(model_name, pretrained=True)` works for ALL models
- **Pretrained weights** for 1,000+ models, cached locally and on HF Hub
- **Feature extraction** — consistent API for penultimate, multi-scale, and intermediate features
- **Data pipeline** — transforms, augmentation (RandAugment, AugMix, random erasing), dataset loading
- **Training infrastructure** — optimizers (AdamW, Lamb, RMSPropTF), schedulers (cosine, step, plateau)
- **Hub integration** — push/share/load models via Hugging Face Hub

### 2. Installation

```bash
pip install timm           # Latest stable
pip install git+https://github.com/rwightman/pytorch-image-models.git  # Bleeding edge
```

Verify installation:
```python
from timm import list_models
print(list_models(pretrained=True)[:5])
# ['adv_inception_v3', 'bat_resnext26ts', 'beit_base_patch16_224', ...]
```

### 3. Model Creation and Listing

#### Listing models

```python
import timm

# All available model names
all_models = timm.list_models()

# Only models with pretrained weights
pretrained = timm.list_models(pretrained=True)

# Wildcard filter
resnets = timm.list_models('*resnet*')

# Filter by module
vit_models = timm.list_models('*vit*', module='vision_transformer')

# Exclude filters
no_legacy = timm.list_models('*resnet*', exclude_filters=['*legacy*'])

# Include pretrained tags (model.tag format)
tagged = timm.list_models(pretrained=True, include_tags=True)
# e.g. 'mobilenetv3_large_100.ra_in1k'
```

#### Creating models

```python
# Basic — no pretrained weights (random init)
m = timm.create_model('mobilenetv3_large_100')

# With pretrained ImageNet weights
m = timm.create_model('mobilenetv3_large_100', pretrained=True)
m.eval()  # Always call .eval() for inference

# Custom number of classes (replaces classifier head)
m = timm.create_model('resnet50', pretrained=True, num_classes=10)

# Remove classifier entirely (for feature extraction)
m = timm.create_model('resnet50', pretrained=True, num_classes=0)

# Remove classifier AND pooling
m = timm.create_model('resnet50', pretrained=True, num_classes=0, global_pool='')

# Load from checkpoint
m = timm.create_model('resnet50', checkpoint_path='./model.pth.tar')

# Custom cache directory
m = timm.create_model('vit_small_patch14_dinov2.lvd142m', pretrained=True, cache_dir='/data/models')

# ONNX exportable configuration
m = timm.create_model('resnet50', exportable=True)

# JIT scriptable configuration
m = timm.create_model('resnet50', scriptable=True)
```

**Key create_model kwargs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pretrained` | bool/str | Load pretrained weights (True=ImageNet-1k default, or specific tag) |
| `num_classes` | int | Number of output classes (0 = no classifier, removes head) |
| `global_pool` | str | Pooling type: 'avg', 'max', 'avgmax', 'catavgmax', '' (none) |
| `drop_rate` | float | Classifier dropout for training (0.0–1.0) |
| `drop_path_rate` | float | Stochastic depth drop rate (0.0–1.0) |
| `checkpoint_path` | str | Path to checkpoint to load after init |
| `cache_dir` | str | Override default model cache directory |
| `features_only` | bool | Return multi-scale feature maps (for detection/segmentation) |
| `out_indices` | tuple | Which feature levels to output (for features_only) |
| `output_stride` | int | Limit feature stride via dilation (8, 16, 32) |
| `scriptable` | bool | Configure for JIT scripting |
| `exportable` | bool | Configure for ONNX export |

### 4. Inference Pipeline

```python
import torch
import timm
from PIL import Image
import requests

# 1. Load model
model = timm.create_model('mobilenetv3_large_100', pretrained=True).eval()

# 2. Get the correct transform for this model
data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
transform = timm.data.create_transform(**data_cfg)
# Output: Compose(Resize(256, bicubic), CenterCrop(224), ToTensor(), Normalize(...))

# 3. Load and transform image
url = 'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/timm/cat.jpg'
image = Image.open(requests.get(url, stream=True).raw)
image_tensor = transform(image).unsqueeze(0)  # Add batch dim

# 4. Forward pass
output = model(image_tensor)  # shape: [1, 1000]

# 5. Get probabilities
probs = torch.nn.functional.softmax(output[0], dim=0)

# 6. Get top-k predictions
top5_probs, top5_idxs = torch.topk(probs, 5)
```

**Important:** Resolve data config from `model.pretrained_cfg` — different models use different input sizes, normalization, and interpolation. Never hardcode these values.

### 5. Feature Extraction

#### Penultimate Layer Features (Unpooled)

```python
m = timm.create_model('xception41', pretrained=True)

# Method 1: forward_features() — bypasses classifier and pooling
o = m.forward_features(torch.randn(2, 3, 299, 299))
# Shape: [2, 2048, 10, 10]  (unpooled spatial features)

# Method 2: Create without classifier/pooling
m = timm.create_model('resnet50', pretrained=True, num_classes=0, global_pool='')
o = m(torch.randn(2, 3, 224, 224))
# Shape: [2, 2048, 7, 7]

# Method 3: Remove classifier later
m = timm.create_model('densenet121', pretrained=True)
m.reset_classifier(0, '')
o = m(torch.randn(2, 3, 224, 224))
# Shape: [2, 1024, 7, 7]

# Chain unpooled features through head
model = timm.create_model('vit_medium_patch16_reg1_gap_256', pretrained=True)
features = model.forward_features(torch.randn(2, 3, 256, 256))  # [2, 257, 512]
logits = model.forward_head(features)  # [2, 1000]
```

#### Penultimate Layer Features (Pooled)

```python
# Create with no classifier but keep pooling
m = timm.create_model('resnet50', pretrained=True, num_classes=0)
o = m(torch.randn(2, 3, 224, 224))
# Shape: [2, 2048] — pooled features, ready for your classifier head

# Remove classifier later, keep pooling
m = timm.create_model('ese_vovnet19b_dw', pretrained=True)
m.reset_classifier(0)  # keeps default pooling
o = m(torch.randn(2, 3, 224, 224))
# Shape: [2, 1024]
```

#### Multi-Scale Feature Maps (Feature Pyramid)

For object detection and segmentation — get feature maps at multiple scales:

```python
# Create with features_only=True
m = timm.create_model('resnest26d', features_only=True, pretrained=True)
outputs = m(torch.randn(2, 3, 224, 224))
for x in outputs:
    print(x.shape)
# torch.Size([2, 64, 112, 112])    Stride 2
# torch.Size([2, 256, 56, 56])     Stride 4
# torch.Size([2, 512, 28, 28])     Stride 8
# torch.Size([2, 1024, 14, 14])    Stride 16
# torch.Size([2, 2048, 7, 7])      Stride 32

# Query feature info
print(m.feature_info.channels())   # [64, 256, 512, 1024, 2048]
print(m.feature_info.reduction())  # [2, 4, 8, 16, 32]

# Select specific levels with out_indices
m = timm.create_model('regnety_032', features_only=True, out_indices=(0, 2, 4))
outputs = m(torch.randn(2, 3, 224, 224))
# Returns features at indices 0, 2, 4 only

# out_indices supports negative indexing
m = timm.create_model('regnety_032', features_only=True, out_indices=(-2,))
# Returns penultimate feature map

# Output stride dilation (for dense prediction)
m = timm.create_model('ecaresnet101d', features_only=True, output_stride=8, out_indices=(2, 4))
outputs = m(torch.randn(2, 3, 320, 320))  # Both outputs at stride 8
print(m.feature_info.reduction())  # [8, 8]
```

#### Flexible Intermediate Feature Maps (forward_intermediates)

Newer method for extracting intermediate layer outputs:

```python
model = timm.create_model('vit_medium_patch16_reg1_gap_256', pretrained=True)

# Return all intermediates
output, intermediates = model.forward_intermediates(torch.randn(2, 3, 256, 256))
for i, o in enumerate(intermediates):
    print(f'Feat {i}: shape {o.shape}')
# 12 intermediate features for ViT, all [2, 512, 16, 16]

# Select specific intermediates by index
output, intermediates = model.forward_intermediates(
    torch.randn(2, 3, 256, 256), indices=[0, 4, 8]
)

# Prune layers not needed + return only intermediates
indices = model.prune_intermediate_layers(indices=(-2,), prune_head=True, prune_norm=True)
intermediates = model.forward_intermediates(
    torch.randn(2, 3, 256, 256), indices=indices, intermediates_only=True
)
```

### 6. Data Pipeline

#### create_transform — Build Image Transform

```python
# From model config (recommended)
transform = timm.data.create_transform(**timm.data.resolve_data_config(model.pretrained_cfg))
# Output: Resize(256, interpolation=bicubic) → CenterCrop(224) → ToTensor() → Normalize(mean, std)

# Training transform with augmentation
train_transform = timm.data.create_transform(
    input_size=(3, 224, 224),
    is_training=True,
    auto_augment='rand-m9-mstd0.5',  # RandAugment
    re_prob=0.25,                     # Random erasing probability
    re_mode='pixel',                  # Random erasing fill mode
)

# Inference transform (test time)
eval_transform = timm.data.create_transform(
    input_size=(3, 224, 224),
    is_training=False,
    crop_pct=0.875,          # Override crop percentage
    interpolation='bicubic',
)
```

#### create_dataset — Dataset Factory

```python
from timm.data import create_dataset, create_loader

# Folder-based dataset (expects train/ and val/ subdirs)
dataset = create_dataset(
    name='',                  # Empty for folder-based
    root='/data/imagenet',
    split='train',
    is_training=True,
)

# Hugging Face datasets
dataset = create_dataset(
    name='dataset_name',
    root='huggingface/dataset-name',
    split='train',
    is_training=True,
    trust_remote_code=True,
)
```

#### create_loader — Full DataLoader with Augmentation

```python
loader = create_loader(
    dataset,
    input_size=(3, 224, 224),
    batch_size=64,
    is_training=True,
    auto_augment='rand-m9-mstd0.5',
    re_prob=0.25,
    interpolation='bicubic',
    mean=(0.485, 0.456, 0.406),
    std=(0.229, 0.224, 0.225),
    num_workers=4,
    pin_memory=True,
    distributed=False,
)
```

#### Available Augmentations

| Augmentation | Parameter | Description |
|-------------|-----------|-------------|
| RandAugment | `auto_augment='rand-m9-mstd0.5'` | Random magnitude augmentation (9 ops, magnitude 0.5) |
| AugMix | `auto_augment='augmix'` | Mix of augmented images + JSD loss |
| Random Erasing | `re_prob=0.25, re_mode='pixel'` | Cutout-style erasing |
| Color Jitter | `color_jitter=0.4` | Brightness/contrast/saturation/hue |
| Horizontal Flip | `hflip=0.5` | Random horizontal flip |
| Vertical Flip | `vflip=0.0` | Random vertical flip |
| Gaussian Blur | `gaussian_blur_prob=0.0` | SimCLR-style blur |
| Grayscale | `grayscale_prob=0.0` | SimCLR-style grayscale |
| Three Augment Split | `num_aug_splits=3` | Split augmentations across batch |
| Repeated Aug | `num_aug_repeats=1` | Same aug across distributed GPUs |

### 7. Hugging Face Hub Integration

timm models integrate with the Hugging Face Hub for sharing and loading.

#### Sharing a model to the Hub

```python
import timm

model = timm.create_model('resnet18', pretrained=True, num_classes=4)
# Train/fine-tune the model...

# Push to Hub (creates repo at <your-username>/<model_name>)
model_cfg = dict(label_names=['cat', 'dog', 'bird', 'fish'])
timm.models.push_to_hf_hub(
    model,
    'my-finetuned-resnet18',
    model_config=model_cfg,
)
```

#### Loading a model from the Hub

```python
# Load any timm model from the Hub
model = timm.create_model('hf_hub:username/model-name', pretrained=True)

# Load a model pushed via timm with its custom head
model = timm.create_model('hf_hub:nateraw/resnet18-random', pretrained=True)
```

#### Authentication

```bash
huggingface-cli login
# Or in notebooks:
# from huggingface_hub import notebook_login
# notebook_login()
```

#### Model Name Format on Hub

The `include_tags=True` flag enables the `model.tag` naming convention:
```python
models = timm.list_models(pretrained=True, include_tags=True)
# ['mobilenetv3_large_100.ra_in1k', 'resnet50.a1_in1k', ...]
```

The tag suffix indicates the training recipe / dataset:
- `.ra_in1k` — RandAugment, ImageNet-1k
- `.a1_in1k` — A1 training recipe, ImageNet-1k
- `.lvd142m` — DINOv2 self-supervised on LVD-142M
- `.in22k` — ImageNet-22k pretrained
- `.ft_in1k` — Fine-tuned to ImageNet-1k from 22k

### 8. Training Script

The official training script (`train.py`) from the timm GitHub repo supports distributed training with extensive hyperparameters.

**Basic usage:**
```bash
./distributed_train.sh 2 --data-dir /data/imagenet --model seresnet34 \
    --sched cosine --epochs 150 --warmup-epochs 5 --lr 0.4 \
    --reprob 0.5 --remode pixel --batch-size 256 --amp -j 4
```

**Key training arguments:**
| Arg | Default | Description |
|-----|---------|-------------|
| `--model` | required | Model architecture name |
| `--sched` | `cosine` | LR schedule: cosine, step, plateau |
| `--epochs` | 300 | Number of training epochs |
| `--lr` | 0.05 | Base learning rate |
| `--opt` | `adamw` | Optimizer: adamw, sgd, rmsproptf, lamb |
| `--weight-decay` | 0.05 | Weight decay |
| `--warmup-epochs` | 5 | LR warmup epochs |
| `--warmup-lr` | 1e-6 | Initial warmup LR |
| `--aa` | None | Auto-augment policy (e.g., `rand-m9-mstd0.5`) |
| `--reprob` | 0. | Random erasing probability |
| `--remode` | `pixel` | Random erasing fill mode |
| `--drop` | 0. | Classifier dropout |
| `--drop-path` | 0. | Stochastic depth rate |
| `--model-ema` | False | Enable EMA of model weights |
| `--model-ema-decay` | 0.9998 | EMA decay factor |
| `--amp` | False | Enable mixed precision (PyTorch native AMP) |
| `--dist-bn` | `reduce` | Distributed BN stats |

**Example — EfficientNet-B2 (80.4 top-1):**
```bash
./distributed_train.sh 2 --data-dir /imagenet --model efficientnet_b2 -b 128 \
    --sched step --epochs 450 --decay-epochs 2.4 --decay-rate .97 \
    --opt rmsproptf --opt-eps .001 -j 8 --warmup-lr 1e-6 --weight-decay 1e-5 \
    --drop 0.3 --drop-path 0.2 --model-ema --model-ema-decay 0.9999 \
    --aa rand-m9-mstd0.5 --remode pixel --reprob 0.2 --amp --lr .016
```

### 9. Key Configuration and Data Models

#### pretrained_cfg attributes

Every model exposes its pretrained config via `model.pretrained_cfg`:
```python
{
    'url': 'https://github.com/.../weights.pth',
    'num_classes': 1000,
    'input_size': (3, 224, 224),
    'pool_size': (7, 7),
    'crop_pct': 0.875,
    'interpolation': 'bicubic',
    'mean': (0.485, 0.456, 0.406),
    'std': (0.229, 0.224, 0.225),
    'first_conv': 'conv_stem',
    'classifier': 'classifier',
    'architecture': 'mobilenetv3_large_100',
}
```

#### feature_info attributes

When `features_only=True`, the model has `.feature_info`:
```python
m = timm.create_model('resnet50', features_only=True)
m.feature_info.channels()   # [64, 256, 512, 1024, 2048]
m.feature_info.reduction()  # [2, 4, 8, 16, 32]
```

### 10. Architectures Covered (Examples)

| Family | Examples | Use Case |
|--------|----------|----------|
| ResNet | resnet18, resnet50, resnet101, wide_resnet50_2 | General classification, detection backbones |
| EfficientNet | efficientnet_b0-b8, efficientnet_lite0-4 | Mobile/edge, speed-accuracy tradeoff |
| ConvNeXt | convnext_tiny, convnext_base, convnext_large | Modern CNN, strong ImageNet acc |
| ViT | vit_base_patch16_224, vit_large_patch14_336 | Vision Transformers, scalable |
| DeiT | deit_tiny, deit_small, deit_base | Data-efficient ViTs, distillation |
| Swin | swin_tiny, swin_base, swin_large | Hierarchical Transformer, dense prediction |
| MobileNet | mobilenetv2_100, mobilenetv3_large/small | Mobile optimized |
| RegNet | regnety_002, regnety_032, regnety_160 | Design-space exploration, FLOP-optimal |
| DINOv2 | vit_small_patch14_dinov2, vit_giant_patch14_dinov2 | Self-supervised features |
| BEiT | beit_base_patch16_224, beit_large_patch16_512 | Masked image modeling |
| MaxViT | maxvit_tiny, maxvit_base | Multi-axis attention, efficient |

### Key Takeaways
1. timm provides 1,000+ pretrained models from 200+ architectures with a unified `create_model()` interface
2. Always call `.eval()` for inference; configure transforms via `resolve_data_config(model.pretrained_cfg)`
3. Feature extraction: `forward_features()` for penultimate, `features_only=True` for multi-scale, `forward_intermediates()` for flexible layer access
4. Hub integration: `push_to_hf_hub()` to share, `hf_hub:user/model` to load
5. Data pipeline: `create_dataset()` + `create_loader()` + `create_transform()` with built-in RandAugment, random erasing, Mixup
6. Training script supports distributed training with AMP, EMA, and extensive augmentation config
7. Models cache to Hugging Face Hub cache directory by default; override with `cache_dir`
8. `out_indices` supports negative indexing for convenient last/penultimate feature selection
