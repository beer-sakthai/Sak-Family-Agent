# Hunyuan3D-2 Deep Dive — 2026-07-23

**Space:** tencent/Hunyuan3D-2 (3338 likes)
**By:** Tencent Hunyuan3D Team
**SDK:** Gradio 4.44.0 · **Hardware:** ZeroGPU (zero-a10g)
**License:** TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
**Models:** tencent/Hunyuan3D-2
**Links:** [Space](https://huggingface.co/spaces/tencent/Hunyuan3D-2) · [GitHub](https://github.com/Tencent/Hunyuan3D-2) · [Report](https://github.com/Tencent/Hunyuan3D-2/blob/main/assets/report/Tencent_Hunyuan3D_2_0.pdf)

## Architecture

Two-stage text/image-to-3D generation pipeline:

1. **Hunyuan3D-DiT** — flow-based diffusion transformer for shape generation. Takes an image (or text→image via HunyuanDiT) and produces a bare mesh via marching cubes at configurable octree resolution (up to 512).
2. **Hunyuan3D-Paint** — texture synthesis model that takes the bare mesh + input image and generates a high-resolution vibrant texture map. Can also texture hand-crafted meshes independently.

Also supports Multi-View (MV) mode with up to 4 reference views (front/back/left/right).

## Notable Patterns for Space Analysis

### Multi-Duration ZeroGPU

This Space uses **two different `@spaces.GPU` durations** for different sub-tasks:

| Decorator | Duration | Purpose |
|-----------|----------|---------|
| `@spaces.GPU(duration=40)` | 40s | Shape-only generation (bare mesh) |
| `@spaces.GPU(duration=90)` | 90s | Full textured generation (shape + paint) |

The duration values directly reveal the per-stage compute cost — texture synthesis takes ~2x the compute of shape generation.

### Explicit ZeroGPU Lifecycle

The Space bypasses implicit ZeroGPU lifecycle management and calls `zero.startup()` explicitly at the end of `__main__`:
```python
from spaces import zero
zero.startup()
```
This pattern is seen in large multi-stage Spaces and should be checked for when analyzing ZeroGPU usage patterns.

### Compiled CUDA Extension

The Space compiles a custom CUDA rasterizer at startup:
```python
os.system("cd /home/user/app/hy3dgen/texgen/differentiable_renderer/ && bash compile_mesh_painter.sh")
subprocess.run(shlex.split("pip install custom_rasterizer-0.1-cp310-cp310-linux_x86_64.whl"), check=True)
```
This means it ships a pre-built `.whl` and a compile script. The presence of `.whl` files in siblings signals custom GPU kernels.

### Large Gradio App

`gradio_app.py` is ~9000+ lines. Reading it required 3 chunked fetches (0-4000, 4000-8000, 8000-end) to get the full picture including the Gradio UI layout, all event handlers, and the `__main__` setup section.

### File Serving Pattern

Uses FastAPI + gr.mount_gradio_app to serve static files alongside the Gradio interface:
```python
app = FastAPI()
static_dir = Path(SAVE_DIR).absolute()
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
app = gr.mount_gradio_app(app, demo, path="/")
```
3D previews are served as `<iframe>` embedding HTML files with `<model-viewer>` tags referencing GLB files in the static directory.

## Key Comparisons

- Outperforms both open-source and closed-source alternatives on CMMD (3.193↓), FID-CLIP (49.165↓), FID (282.429↓), and CLIP-score (0.809↑).
- One of the highest-liked ZeroGPU 3D generation Spaces on HF (3338 likes).
