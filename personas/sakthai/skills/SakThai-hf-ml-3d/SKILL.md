---
name: SakThai-hf-ml-3d
author: SakThai
license: MIT
description: "3D machine learning on Hugging Face — multi-view diffusion, Gaussian splatting, mesh generation, and the HF ML for 3D Course ecosystem."
version: 1.0.0
tags: [3D, GaussianSplatting, NeRF, MultiviewDiffusion, Meshes, LGM, Diffusers3D, HuggingFace]
---

# 🤗 Machine Learning for 3D — Full Ecosystem Guide

Based on the [HF ML for 3D Course](https://huggingface.co/learn/ml-for-3d-course) (by Dylan Ebert / IndividualKex) and the Diffusers 3D pipeline ecosystem.

## When to Use

- User wants to "generate 3D models with AI"
- User asks about Gaussian splatting, NeRF, or triplanes
- User needs multi-view diffusion for 3D asset creation
- User wants to deploy a 3D Space on HF Hub
- User asks about image-to-3D or text-to-3D pipelines
- User needs mesh processing, reconstruction, or optimization
- User wants to understand the 3D generation pipeline from text/image to renderable 3D asset

## The Generative 3D Pipeline

```
Text/Image → Multi-view Diffusion → ML-friendly 3D → Mesh/Splat → Render/Export
```

Three main stages:
1. **Multi-view Diffusion** — Generate 4–6 consistent views of an object
2. **ML-friendly 3D** — Convert to Gaussian Splats, Triplanes, or NeRFs
3. **Meshing** — Extract mesh via Marching Cubes or direct mesh generation

## Course Structure (5 Units)

| Unit | Topic | Key Content |
|------|-------|-------------|
| 0 | Introduction | Big picture, why ML for 3D matters |
| 1 | What is 3D? | Point clouds, meshes, voxels, 3D representations |
| 2 | Multi-view Diffusion | MVDream, Zero123++, custom Diffusers pipelines |
| 3 | Gaussian Splatting | 3D Gaussians, differentiable rendering, LGM |
| 4 | Meshes | Marching Cubes, MeshAnything, low-poly conversion |
| 5 | Capstone | Build your own generative 3D demo on HF Spaces |

## Core Libraries

```bash
pip install torch diffusers trimesh
# For Gaussian splatting (needs CUDA):
# pip install diff-gaussian-rasterization
# For mesh processing:
pip install trimesh pytorch3d  # pytorch3d needs conda often
# For 3D visualization in notebooks:
pip install plotly
```

## Model Recommendations

### Image-to-3D Models

| Model | Description | Quality | Speed | VRAM | Link |
|-------|-------------|---------|-------|------|------|
| `stabilityai/stable-fast-3d` | Fast 3D mesh from single image | Good | Very Fast (1-2s) | 4GB | [HF Hub](https://huggingface.co/stabilityai/stable-fast-3d) |
| `stabilityai/stable-point-aware-3d` | Point-aware 3D generation | High | Fast | 8GB | [HF Hub](https://huggingface.co/stabilityai/stable-point-aware-3d) |
| `dylanebert/LGM` | Large Gaussian Model — text/splat | High | Moderate | 12GB | [HF Hub](https://huggingface.co/dylanebert/LGM) |
| `dylanebert/multi-view-diffusion` | MVDream mirror for multi-view generation | High | Moderate | 12GB | [HF Hub](https://huggingface.co/dylanebert/multi-view-diffusion) |
| `ashawkey/mvdream-sd2.1-diffusers` | Original MVDream multi-view diffusion | High | Moderate | 12GB | [HF Hub](https://huggingface.co/ashawkey/mvdream-sd2.1-diffusers) |
| `tencent/TRELLIS-image-large` | Large-scale image-to-3D (Tencent) | Very High | Slow | 24GB | [HF Hub](https://huggingface.co/tencent/TRELLIS-image-large) |
| `facebook/sam-3d-objects` | SAM for 3D object understanding | Research | N/A | N/A | [HF Hub](https://huggingface.co/facebook/sam-3d-objects) |

### Text-to-3D Models

| Model | Description | Quality | Link |
|-------|-------------|---------|------|
| `dylanebert/LGM` (text mode) | Text-to-splat via LGM | High | [HF Hub](https://huggingface.co/dylanebert/LGM) |
| Point-E / Shap-E (OpenAI) | Text-conditional 3D (via HF) | Moderate | [HF Hub](https://huggingface.co/openai) |
| Zero123++ | Novel view synthesis (text+image) | High | [HF Hub](https://huggingface.co) |

## Multi-view Diffusion Pipeline (Unit 2)

Uses Diffusers with custom pipelines (3D isn't natively supported by diffusers yet):

### Basic Multi-View Generation
```python
import torch
from diffusers import DiffusionPipeline
import numpy as np
from PIL import Image

# Load multi-view diffusion model
pipeline = DiffusionPipeline.from_pretrained(
    "dylanebert/multi-view-diffusion",
    custom_pipeline="dylanebert/multi-view-diffusion",
    torch_dtype=torch.float16,
    trust_remote_code=True,
).to("cuda")

# Load input image
image = np.array(Image.open("input.jpg"), dtype=np.float32) / 255.0

# Generate 4 multi-views
images = pipeline("", image, guidance_scale=5, num_inference_steps=30, elevation=0)
# Returns 4 images (top-left, top-right, bottom-left, bottom-right)
```

### Understanding Multi-View Output Layout

The output is a 2×2 grid:
```
┌─────────┬─────────┐
│ View 1  │ View 2  │
│ (0°)    │ (90°)   │
├─────────┼─────────┤
│ View 3  │ View 4  │
│ (180°)  │ (270°)  │
└─────────┴─────────┘
```

To extract individual views:
```python
# Split the 2x2 grid into separate images
w, h = images.size
view_size = w // 2
top_left = images.crop((0, 0, view_size, view_size))
top_right = images.crop((view_size, 0, w, view_size))
bottom_left = images.crop((0, view_size, view_size, h))
bottom_right = images.crop((view_size, view_size, w, h))
```

### Key models on Hub
- `dylanebert/multi-view-diffusion` — mirror of ashawkey/mvdream-sd2.1-diffusers
- `ashawkey/mvdream-sd2.1-diffusers` — original MVDream

## Gaussian Splatting (Unit 3) — LGM Pipeline

### Complete Text-to-Splat Pipeline

Full text-to-splat using LGM (Large Gaussian Model):

```python
# Stage 1: Multi-view diffusion
image_pipeline = DiffusionPipeline.from_pretrained(
    "dylanebert/multi-view-diffusion", custom_pipeline="dylanebert/multi-view-diffusion",
    torch_dtype=torch.float16, trust_remote_code=True,
).to("cuda")

# Stage 2: Gaussian splat generation
splat_pipeline = DiffusionPipeline.from_pretrained(
    "dylanebert/LGM", custom_pipeline="dylanebert/LGM",
    torch_dtype=torch.float16, trust_remote_code=True,
).to("cuda")

# Run pipeline
image = np.array(Image.open("input.jpg"), dtype=np.float32) / 255.0
multi_view_images = image_pipeline(
    "", image, guidance_scale=5, num_inference_steps=30, elevation=0
)
splat = splat_pipeline(multi_view_images)
splat_pipeline.save_ply(splat, "output.ply")
```

### What is a Gaussian Splat?

A `.ply` file containing:
- **Position (x, y, z)** — 3D coordinates of each Gaussian
- **Covariance (scale + rotation)** — shape and orientation
- **Color (RGB)** — view-dependent color via spherical harmonics
- **Opacity (α)** — transparency

### Gaussian Splatting Rendering (Web Viewer)

```python
# Use gradio to render splats in the browser
import gradio as gr

def run(image):
    input_image = image.astype("float32") / 255.0
    images = image_pipeline("", input_image, guidance_scale=5, num_inference_steps=30, elevation=0)
    splat = splat_pipeline(images)
    splat_pipeline.save_ply(splat, "/tmp/output.ply")
    return "/tmp/output.ply"

demo = gr.Interface(
    fn=run,
    inputs="image",
    outputs=gr.Model3D(),
    title="Image-to-3D Gaussian Splatting",
)
demo.launch()
```

### Gaussian Splatting Visualization Code
```python
# Read and inspect a .ply splat file
import trimesh
import numpy as np

# Load PLY
mesh = trimesh.load("output.ply")
print(f"Vertices: {len(mesh.vertices)}")
print(f"Faces: {len(mesh.faces)}")
print(f"Vertex attributes: {list(mesh.visual.vertex_attributes.keys()) if hasattr(mesh.visual, 'vertex_attributes') else 'none'}")

# For actual Gaussian visualization, use the LGM viewer or
# a web-based splat viewer like super-splat
```

## Mesh Pipeline

### 1. Marching Cubes — Extract mesh from voxels/density fields
```python
import trimesh
from skimage.measure import marching_cubes
import numpy as np

# Generate a simple SDF (signed distance function)
x, y, z = np.meshgrid(np.linspace(-1, 1, 64), np.linspace(-1, 1, 64), np.linspace(-1, 1, 64))
sdf = np.sqrt(x**2 + y**2 + z**2) - 0.5  # Sphere SDF

# Marching cubes
verts, faces, _, _ = marching_cubes(sdf, level=0)
mesh = trimesh.Trimesh(vertices=verts, faces=faces)
mesh.export("sphere_mesh.obj")
print(f"Mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
```

### 2. MeshAnything — Convert dense to low-poly meshes
MeshAnything takes dense meshes and produces clean, low-polygon versions suitable for games and rendering.

### 3. Traditional cleanup — Blender, Meshlab for production

### 4. Mesh Optimization
```python
# Simplify a mesh (reduce polygon count)
mesh = trimesh.load("dense_mesh.obj")
simplified = mesh.simplify_quadric_decimation(1000)  # Target 1000 faces
simplified.export("simplified_mesh.obj")
```

## ML-friendly 3D Representations

| Method | Description | Real-time? | Use Case |
|--------|-------------|------------|----------|
| **Gaussian Splatting** | Optimized 3D Gaussians, differentiable rendering | ✅ Yes | Real-time novel view synthesis |
| **Triplanes** | 3-axis feature planes, latest SOTA | ✅ Yes | Efficient 3D feature representation |
| **NeRF** | Neural Radiance Fields, implicit | ⚠️ No (slow) | High-quality novel views |
| **Voxels** | 3D grid of occupancy | ⚠️ No (memory heavy) | Simple 3D representations |
| **Point Clouds** | Unstructured 3D points | ✅ Yes | Raw 3D data from LiDAR/SfM |
| **Signed Distance Fields (SDF)** | Continuous implicit surface | ✅ Yes | Mesh extraction |
| **Triangular Meshes** | Vertices + faces | ✅ Yes | Standard 3D format for rendering |

## Top 3D Models on HF Hub (by downloads)

| Model | Pipeline Tag | Description |
|-------|-------------|-------------|
| `stabilityai/stable-fast-3d` | image-to-3d | Fast 3D from single image (840 ❤️) |
| `stabilityai/stable-point-aware-3d` | image-to-3d | Point-aware 3D generation (352 ❤️) |
| `facebook/sam-3d-objects` | n/a | Meta's SAM for 3D objects (439 ❤️) |
| `facebook/sam-3d-body-dinov3` | n/a | 3D human mesh recovery (249 ❤️) |
| `tencent/TRELLIS-image-large` | image-to-3d | Large-scale image-to-3D generation |

## Top 3D Spaces on HF Hub

1. **multimodalart/qwen-image-multiple-angles-3d-camera** (2623 ❤️) — multi-angle 3D
2. **stabilityai/stable-fast-3d** (1202 ❤️) — fast image-to-3d
3. **stabilityai/stable-point-aware-3d** (468 ❤️) — point-aware 3D
4. **3d-arena/3d-arena** (400 ❤️) — 3D model comparison arena
5. **radames/dpt-depth-estimation-3d-obj** (277 ❤️) — depth to 3D

## Gradio 3D Demo (Complete)

```python
import gradio as gr
from diffusers import DiffusionPipeline
import numpy as np
from PIL import Image

# Initialize pipelines
image_pipeline = DiffusionPipeline.from_pretrained(
    "dylanebert/multi-view-diffusion",
    custom_pipeline="dylanebert/multi-view-diffusion",
    torch_dtype=torch.float16,
    trust_remote_code=True,
).to("cuda")

splat_pipeline = DiffusionPipeline.from_pretrained(
    "dylanebert/LGM",
    custom_pipeline="dylanebert/LGM",
    torch_dtype=torch.float16,
    trust_remote_code=True,
).to("cuda")

def image_to_3d(input_image):
    """Convert a single image to a 3D Gaussian splat."""
    img = np.array(input_image, dtype=np.float32) / 255.0
    views = image_pipeline("", img, guidance_scale=5, num_inference_steps=30)
    splat = splat_pipeline(views)
    splat_pipeline.save_ply(splat, "/tmp/output.ply")
    return "/tmp/output.ply"

# Build interface with preprocessing
def process_and_convert(image):
    if image is None:
        return None
    # Ensure minimum size
    pil_img = Image.fromarray(image)
    if pil_img.width < 128 or pil_img.height < 128:
        pil_img = pil_img.resize((256, 256))
    return image_to_3d(pil_img)

demo = gr.Interface(
    fn=process_and_convert,
    inputs=gr.Image(label="Input Image"),
    outputs=gr.Model3D(label="3D Gaussian Splat"),
    title="Image to 3D Gaussian Splatting",
    description="Upload an image to generate a 3D Gaussian splat model",
)
demo.launch()
```

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `CUDA out of memory` | LGM uses 12GB+ | Reduce resolution, use fp16, enable CPU offload |
| `trust_remote_code=True fails` | Diffusers version too old | Upgrade to diffusers>=0.25.0 |
| `Missing diff-gaussian-rasterization` | CUDA dependency | Install matching wheel for your Python/CUDA version |
| `Inconsistent multi-views` | Bad input image | Use centered object on plain background |
| `PLY file won't render` | Wrong format | Verify splat uses the LGM output format |
| `Gradio Model3D shows nothing` | File path issue | Use absolute paths for .ply files |
| `pytorch3d install fails` | System deps missing | Use conda: `conda install -c fvcore -c iopath -c conda-forge pytorch3d` |

## Pitfalls

- 3D generation is computationally expensive — GPU with ≥16GB VRAM recommended.
- Multi-view diffusion may produce inconsistent views — post-processing helps.
- Gaussian splatting requires multi-view input; doesn't work from a single image alone.
- Diffusers doesn't officially support 3D — all 3D pipelines are `custom_pipeline` with `trust_remote_code=True`.
- Mesh quality from generative methods varies — cleanup often needed.
- `diff-gaussian-rasterization` needs exact Python version wheel — check Space/hardware constraints.
- `stable-fast-3d` is much faster than LGM but produces less detailed output.
- The ML for 3D Course is community-maintained — content may evolve rapidly.
- For production 3D workflows, consider Blender for post-processing.

## Verification

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}, VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

import trimesh
mesh = trimesh.primitives.Sphere()
print(f"Trimesh OK — sphere with {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

# Verify multi-view pipeline loads
from diffusers import DiffusionPipeline
pipe = DiffusionPipeline.from_pretrained(
    "dylanebert/multi-view-diffusion",
    custom_pipeline="dylanebert/multi-view-diffusion",
    trust_remote_code=True,
)
print("Multi-view pipeline loads OK")
```

## References

- HF ML for 3D Course: https://huggingface.co/learn/ml-for-3d-course
- Course GitHub: https://github.com/huggingface/ml-for-3d-course
- Course Notebooks: https://github.com/dylanebert/ml-for-3d-course-notebooks
- Diffusers pipelines: https://huggingface.co/docs/diffusers/main/en/api/pipelines
- 3D Models on Hub: https://huggingface.co/models?pipeline_tag=image-to-3d
- 3D Spaces on Hub: https://huggingface.co/spaces?search=3d
- LGM (Large Gaussian Model): https://huggingface.co/dylanebert/LGM
- Stable Fast 3D: https://huggingface.co/stabilityai/stable-fast-3d
- Gaussian Splatting Paper: https://arxiv.org/abs/2308.04079
