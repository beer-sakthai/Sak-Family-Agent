---
name: SakThai-hf-unlimited-ocr
description: "Complete reference on Baidu Unlimited-OCR \u2014 the 3.3B long-horizon OCR VLM with\
  \ Reference Sliding Window Attention (R-SWA) that transcribes dozens of document\
  \ pages in a single 32K forward pass. Covers architecture, R-SWA mechanics, deployment\
  \ (transformers/vLLM/SGLang), and usage patterns."
---

# Baidu Unlimited-OCR (2026-06)

End-to-end OCR model from Baidu that pushes **DeepSeek-OCR** one step further — "the era of one-shot long-horizon parsing." Transcribes dozens of pages of documents in a single forward pass at standard 32K max length. **MIT license**, 3.3B params, BF16, multilingual. arXiv:2606.23050 "Unlimited OCR Works". HF: `baidu/Unlimited-OCR` (2.6M+ downloads, ~3.6K likes within 6 weeks of release). GitHub: baidu/Unlimited-OCR.

## Why it matters / why it trends

- Standard end-to-end OCR (e.g., DeepSeek-OCR) degrades on long documents: KV cache grows with output length → memory + latency climb. Unlimited-OCR keeps a **constant KV cache** throughout decoding, mimicking human "parsing working memory."
- Builds directly on DeepSeek-OCR: same high-compression vision encoder ("DeepEncoder") + a DeepSeek-V2-style MoE decoder, with every attention layer swapped for R-SWA.
- Massive ecosystem adoption: vLLM official Docker images, SGLang recipe, ms-swift training support, ModelScope mirror, Baidu Cloud API, akhaliq demo Space.

## Architecture (verified from config.json + repo files)

- **Vision encoder** (`deepencoder.py`): "deeplip_b_l" — CLIP-L-14-224 branch (24 layers, width 1024, patch 14) + SAM-ViT-B branch, image_size 1024, candidate_resolutions [[1024,1024]], tile_tag "2D".
- **Projector**: linear MLP, 2048 → 1280 (n_embed).
- **Decoder** (`modeling_deepseekv2.py` / `modeling_unlimitedocr.py`): DeepSeek-V2-style MoE — hidden_size 1280, 12 layers, 64 routed experts + 2 shared, 6 experts/tok, MoE intermediate 896, first_k_dense_replace 1, vocab 129280, max_position_embeddings 32768, BF16.
- **R-SWA** (`sliding_window_size: 128` in language_config): Reference Sliding Window Attention replaces ALL attention in decoder. Attention cost is bounded and KV cache stays constant regardless of output length. General-purpose parsing attention — authors say applicable beyond OCR (ASR, translation).
- Single safetensors file (~6.6 GB BF16), custom code (`trust_remote_code=True`), `UnlimitedOCRForCausalLM`.

## Inference quickstart

### Transformers (trust_remote_code)
```python
from transformers import AutoModel, AutoTokenizer
tok = AutoTokenizer.from_pretrained('baidu/Unlimited-OCR', trust_remote_code=True)
model = AutoModel.from_pretrained('baidu/Unlimited-OCR', trust_remote_code=True,
                                  use_safetensors=True, torch_dtype=torch.bfloat16).eval().cuda()
# gundam mode (single image, crop): base_size=1024, image_size=640, crop_mode=True
# base mode (single or multi image): base_size=1024, image_size=1024, crop_mode=False
model.infer(tok, prompt='<image>document parsing.', image_file='img.jpg',
            output_path='out', base_size=1024, image_size=640, crop_mode=True,
            max_length=32768, no_repeat_ngram_size=35, ngram_window=128)
model.infer_multi(tok, prompt='<image>Multi page parsing.', image_files=[...],
                  output_path='out', image_size=1024, max_length=32768,
                  no_repeat_ngram_size=35, ngram_window=1024)
```
- PDFs: convert pages to images with PyMuPDF at 300 dpi, then `infer_multi`.
- Key sampling knobs: `no_repeat_ngram_size=35` + `ngram_window` (128 gundam / 1024 base). The n-gram repetition suppression is handled by a custom logit processor (DeepseekOCRNoRepeatNGramLogitProcessor) — important, copy this pattern when serving.
- OmniDocBench eval needs post-processing: strip `<|det|>type [bbox]<|/det|>` markers (image category dropped, text grouped into blocks with `\n\n`).

### vLLM
- Official images: `vllm/vllm-openai:unlimited-ocr` (CUDA 13.0) or `...:unlimited-ocr-cu129` (Hopper). Recipe: https://recipes.vllm.ai/baidu/Unlimited-OCR

### SGLang
- Local wheel + `kernels==0.11.7` + pymupdf. Launch with `--attention-backend fa3 --page-size 1 --context-length 32768 --enable-custom-logit-processor --disable-overlap-schedule`. Send base64 images to OpenAI-compatible `/v1/chat/completions` with `images_config={"image_mode": "gundam"|"base"}` and the custom logit processor.

## Pitfalls

- **trust_remote_code required** — custom modeling files (modeling_unlimitedocr.py etc.).
- Pinned dep set in README: torch 2.10.0, transformers 4.57.1, PyMuPDF 1.27.2.2.
- Two image modes are NOT interchangeable: `gundam` (crop, 640) is single-image only; `base` (1024, no crop) required for multi-page/PDF.
- Zero-cost note: full repo is ~6.6GB BF16 — on constrained hardware use the HF Inference Providers (baidu/Unlimited-OCR available) or consider quantization; no official GGUF as of tracking date.
- Do not run `infer`/`infer_multi` without `no_repeat_ngram_size` — repetition collapses long outputs.
