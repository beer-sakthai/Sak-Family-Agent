# SGLang-HF Research Log

> Cron run 2026-07-30 — initial research for hf-sglang-integration skill.

## Sources Consulted

| Source | URL | Content |
|--------|-----|---------|
| Official docs | https://docs.sglang.io/ | Full documentation platform (mintlify) |
| GitHub repo | https://github.com/sgl-project/sglang | 31k stars, 15.8k commits, 1299 branches |
| llms.txt index | https://docs.sglang.io/llms.txt | 166 doc pages listed |
| Quickstart | `.md` fetch from `/docs/get-started/quickstart.md` | Install, launch server, send requests (8KB) |
| Model Loading | `.md` fetch from `/docs/advanced_features/model_loading.md` | 14 load formats, weight perf flags, extra config (15KB) |
| Server Arguments | `.md` fetch from `/docs/advanced_features/server_arguments.md` | Full arguments table (293KB) |
| Native API | `.md` fetch from `/docs/basic_usage/native_api.md` | All native endpoints with examples (16KB) |
| Offline Engine | `.md` fetch from `/docs/basic_usage/offline_engine_api.md` | Engine class batch inference (5KB) |
| LoRA Serving | `.md` fetch from `/docs/advanced_features/lora.md` | Multi-LORA args, backends, management (20KB) |
| Quantization | `.md` fetch from `/docs/advanced_features/quantization.md` | FP8/int4/int8/nvfp4 details (39KB) |
| Tool Parser | `.md` fetch from `/docs/advanced_features/tool_parser.md` | Function calling setup (28KB) |
| Supported Models | `.md` fetch from `/docs/supported-models.md` | Model families overview (4KB) |

## Key HF Integration Points Discovered

1. **Model-path accepts any HF repo ID** — not just local paths. Auto-detects format from model index files.
2. **`HF_TOKEN` env var** used natively for gated model access in Docker.
3. **HF cache directory** (`~/.cache/huggingface`) mounted into Docker containers.
4. **Chat template auto-detected** from HF tokenizer; overrideable with `--chat-template` or `--hf-chat-template-name`.
5. **Tokenizer backend** defaults to `huggingface` (the standard HF tokenizers library); optional `fastokens` for speed.
6. **`--download-dir`** controls where HF models are cached — separate from standard HF_HOME if needed.

## Notable Gotchas

- The SGLang docs site lives at `docs.sglang.io` but some internal links redirect to `docs.sglang.ai`. Both work.
- Raw markdown via `.md` URL contains Mintlify JSX that isn't standard markdown — extract from plaintext.
- The `server_arguments.md` page is 293KB — by far the largest page. Fetch with `head -200` or targeted grep.
- `hf-sglang-integration` was chosen because "sglang" was NOT found in any of the 4 `hf-topics-covered.json` files.
- SGLang's load format `layered` is unique — loads layer-by-layer for lower peak memory during quantization. Not found in vLLM or TGI.
- The `fastsafetensors` load format uses a special iterator — distinct from the standard `safetensors` format.
- `remote_instance` lets you pull weights from another SGLang instance over the network (seed pattern) — useful for clusters.
