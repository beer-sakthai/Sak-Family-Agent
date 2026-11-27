# Spaces App Architecture Patterns, Docker & Hardware Secrets

The Space now exists at `https://huggingface.co/spaces/<namespace>/<name>` but is empty.

### README.md frontmatter

Always required:

```yaml
---
title: ...
emoji: 🚀                # pick something representative
colorFrom: blue          # red|yellow|green|blue|indigo|purple|pink|gray (only these)
colorTo: indigo
sdk: gradio              # gradio | docker | static
sdk_version: 6.15.1      # latest stable unless you have a reason*
app_file: app.py         # gradio only (docker / static use Dockerfile / index.html)
short_description: ...   # ≤ 60 chars (server rejects longer)
python_version: "3.12"   # ZeroGPU officially supports 3.10.13 and 3.12.12
startup_duration_timeout: 30m   # default; bump to 1h for big LLMs / heavy downloads
---
```

\* Default to the current latest stable, and **look up what that is** (`pip index versions gradio`, or the version a freshly-created Space defaults to) — the number above is a placeholder that goes stale, don't reuse it. Only pin older when the latest genuinely doesn't work for this Space: a custom component pins it, or you're adapting an existing demo and don't want to rewrite for 5.x→6.x breaking changes. If you need a 5.x, pick `5.50.0` (latest of the series; still supports custom components).

All frontmatter options: https://huggingface.co/docs/hub/spaces-config-reference

### Minimal ZeroGPU Gradio app

```python
import spaces           # MUST come before torch / diffusers / transformers
import torch
import gradio as gr
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("<repo>", torch_dtype=torch.bfloat16).to("cuda")

@spaces.GPU(duration=60)
def generate(prompt: str):
    """Generate an image from a text prompt."""   # docstring → API / MCP tool description
    return pipe(prompt).images[0]

gr.Interface(fn=generate, inputs=gr.Text(), outputs=gr.Image()).launch(mcp_server=True)
```

Three rules — full treatment in [`references/zerogpu.md`](references/zerogpu.md):

1. **`import spaces` before torch / any CUDA-touching import.** It monkey-patches `torch.cuda.*`; once CUDA is initialized in the main process, it's too late.
2. **Load the model at module scope, `.to("cuda")` eagerly.** ZeroGPU intercepts the call, packs weights to disk, and streams them into VRAM on the first `@spaces.GPU` entry. Lazy loading inside the decorator costs every user.
3. **Decorate the function Gradio binds.** Estimate `duration` to the realistic worst case (smaller = higher queue priority and tighter quota check). For input-dependent runtime, pass a callable.

### Examples, docstrings, and MCP

- **Add `gr.Examples` whenever it makes sense** (the app takes input and representative inputs exist) — prefer the model/repo's own official examples. Keep example rows to the few inputs a user actually varies (prompt, image) and give the handler defaults for the rest (steps, seed, guidance) so a row is `["a prompt"]`, not a wall of knobs. Use `cache_examples=True, cache_mode="lazy"`. See [`references/gradio.md`](references/gradio.md).
- **Give every API-triggered function a docstring and type hints.** Each Gradio event handler is exposed over the API; the docstring + signature are what a caller — and the MCP tool schema — sees.
- **Launch with `demo.launch(mcp_server=True)`** (Gradio 5+) so the Space doubles as an MCP server: each API function becomes an MCP tool described by its docstring and hints.

### requirements.txt

Short version:

- **Do NOT list**: `gradio`, `spaces`, `huggingface_hub` (preinstalled and platform-managed; pinning them causes resolution failures or silently breaks the ZeroGPU runtime).
- **Do list if you use them**: `torchvision`, `torchaudio` (not preinstalled), plus everything else (`diffusers`, `transformers`, `accelerate`, `sentencepiece`, …).
- ZeroGPU only accepts torch `2.8.0`, `2.9.1`, `2.10.0`, `2.11.0`. Default to leaving torch unpinned (the runtime preinstalls the latest). Only pin when a dep forces it.
- For prebuilt CUDA-extension wheels (`flash_attn`, `xformers`, `pytorch3d`, `nvdiffrast`, `diff_gaussian_rasterization`, `torchmcubes`): use the prebuilt Blackwell wheels at `https://huggingface.co/datasets/multimodalart/zerogpu-blackwell-wheels/tree/main/wheels`. Full mapping + caveats in [`references/requirements.md`](references/requirements.md).

### Per-SDK depth

- **Gradio patterns** (themes, `gr.Examples`, streaming, custom HTML components, `gr.Server`): [`references/gradio.md`](references/gradio.md).
- **Docker**: https://huggingface.co/docs/hub/spaces-sdks-docker. Examples: `hf spaces list --filter docker`.
- **Static**: https://huggingface.co/docs/hub/spaces-sdks-static. For built SPAs, set `app_build_command: npm run build` and `app_file: dist/index.html` in frontmatter.
- **ZeroGPU specifics** (decorator semantics, sizing, AoTI, generators, concurrency, pickle / `gr.State` across the worker boundary): [`references/zerogpu.md`](references/zerogpu.md) — read this whenever the Space targets ZeroGPU.


## 6. Iterate on the Space, not locally

Try to build a release candidate from the user quest locally and push it — then use the live URL as your test loop. The Space environment is the only one that matters; do not try to test locally. `python3 -m py_compile app.py` is the maximum local check worth doing before pushing.

Push files with `hf upload <namespace>/<name> . --repo-type space`. **`--repo-type space` is required** — `hf upload` defaults to a *model* repo and will otherwise upload to (and silently create) a model repo of the same name. Add `--exclude "**/__pycache__/**"` so local bytecode caches aren't committed into the Space.

Once pushed, pick the cheapest update mechanism for each change — hot-reload for pure Python edits, `hf upload` for code-only files hot-reload can't touch, full rebuild only when `requirements.txt` / `Dockerfile` / README frontmatter actually changed. Full ladder + footguns (hot-reload poisoning factory reboot, runtime.sha lag, etc.) in [`references/debugging.md`](references/debugging.md).

## 7. Verify

Don't trust `RUNNING` alone — the app can be running but broken. Four steps, in order:

**A. Alive?** Stage + hardware:
```bash
hf spaces info <ns>/<name> --expand runtime
```

**B. Logs clean post-boot?** Read the run log to confirm startup finished without warnings or silent fallbacks:
```bash
hf spaces logs <ns>/<name> --tail 200
```
Look for model-load completion, no import warnings, no "falling back to CPU" / dtype downgrade messages, no `RUNNING` masking a half-broken app.

**C. API actually responds.** With logs still tailing in another terminal (`hf spaces logs <ns>/<name> --follow`), call the endpoint:
```python
from gradio_client import Client, handle_file
import os
c = Client("<ns>/<name>", token=os.environ["HF_TOKEN"], httpx_kwargs={"timeout": 600})
print(c.view_api())                    # discover endpoints — don't guess
result = c.predict(..., api_name="/generate")
```

**D. Sniff output AND logs.** HTTP 200 ≠ correct output. Check both:
```python
head = open(result, "rb").read(16)
# glTF / \x89PNG / RIFF…WEBP / RIFF…WAVE / [4:8]==b"ftyp" → png/jpg/webp/wav/mp4
```
And look at the run log emitted during the call — silent fallbacks (model snapping to a different size, missing optional dep, dtype downgrade) only show up there.

Full smoke-test patterns (streaming endpoints, OAuth-gated Spaces, `gr.Server` custom routes): [`references/debugging.md`](references/debugging.md).

## 8. Permanent storage (buckets)

Spaces are stateless — `/data` is wiped on restart. If the Space needs to persist user uploads, generations, logs, or interact with a long-lived store, mount a **bucket**:

```bash
hf buckets create <ns>/<bucket-name>                                          # --private optional
hf spaces volumes set <ns>/<space> -v hf://buckets/<ns>/<bucket-name>:/data   # read-write at /data
```

Buckets are paid storage; check `canPay` and confirm with the user. Full patterns (read-fast / write-durable, public bucket URLs, model-cache anti-pattern): [`references/buckets.md`](references/buckets.md).

## 9. When things break

Order of operations:

1. Read the logs: `hf spaces logs <id> --build --follow` (build error) or `hf spaces logs <id> --follow` (runtime error). Find the **first** error, not the last.
2. Grep [`references/known-errors.md`](references/known-errors.md) for the error string. Check if this is a known issue before trying your own fix — most common ZeroGPU / Gradio / dependency errors have a 1–2 line fix there.
3. Iterate using the cheapest rung from [`references/debugging.md`](references/debugging.md). The vast majority of issues resolve with log-reading + smoke-test loops; interactive dev mode + SSH is a heavy-hammer last resort.

If you solve an error that wasn't in the known-errors list, suggest the user PR it back to this skill so future runs benefit.

---

## Reference index

| When to read | File |
|---|---|
| **How ZeroGPU works** + correct patterns (decorator, sizing, pickle, generators, real-time, AoTI) | [`references/zerogpu.md`](references/zerogpu.md) |
| **Iterate + debug**: logs, rung ladder, smoke testing (and dev mode + SSH as a last resort) | [`references/debugging.md`](references/debugging.md) |
| **Error-string lookup** — the single place for all error symptoms (Spaces, ZeroGPU, Gradio, deps) | [`references/known-errors.md`](references/known-errors.md) |
| Pinning deps, picking wheels, torch-family alignment | [`references/requirements.md`](references/requirements.md) |
| `gr.Examples` (add when it makes sense), themes, custom HTML components, `gr.Server`, MCP server (`mcp_server=True`) | [`references/gradio.md`](references/gradio.md) |
| Persistent storage, public bucket URLs | [`references/buckets.md`](references/buckets.md) |
| Community grant requests (non-PRO needing ZeroGPU) | [`references/grants.md`](references/grants.md) |
| Provider proxy (zero-VRAM big LLM via Cerebras / Fireworks / Together / etc.) | [`references/inference-providers.md`](references/inference-providers.md) |
| **3D Spaces: generation, CUDA extensions, output formats, and model recipes (incl. gaussian splatting)** | [`references/3d-generation.md`](references/3d-generation.md) |
