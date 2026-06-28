# Official ZeroGPU Docs Excerpt (2026-06-21)

Source: https://huggingface.co/docs/hub/en/spaces-zerogpu
Extracted via: curl + local HTML parsing (web_search/extract failed due to Firecrawl billing limit).

## Raw excerpts from official docs

"ZeroGPU is a shared infrastructure that optimizes GPU usage for AI models and demos on Hugging Face Spaces. It dynamically allocates and releases NVIDIA RTX Pro 6000 Blackwell GPUs as needed, offering: Free GPU Access..."

"ZeroGPU Spaces are available to use for free to all users. PRO users get x8 more daily usage quota, highest priority in GPU queues, and can go beyond their daily quota using pre-paid credits..."

"Personal accounts: Subscribe to PRO to access ZeroGPU in the hardware options when creating a new Gradio SDK Space. Organizations: Subscribe to a Team or Enterprise plan to enable ZeroGPU Spaces for all organization members."

"Currently, ZeroGPU Spaces are exclusively compatible with the Gradio SDK."

"Model loading: Even though a real GPU is only available inside @spaces.GPU functions, models must be placed on cuda at the root module level."

"ZeroGPU does not support torch.compile, but you can use PyTorch ahead-of-time compilation (requires torch 2.8+)"

"Included daily quota resets exactly 24 hours after your first GPU usage."

"PRO, Team, and Enterprise users can continue using ZeroGPU Spaces beyond their included daily quota by consuming pre-paid credits at the rate of $1 per 10 minutes of GPU time."

## Extraction methodology

When `web_search` or `web_extract` hit a Firecrawl billing error, fallback to:
1. `curl -sL URL -o /tmp/page.html`
2. Parse `/tmp/page.html` with Python regex to strip tags and locate content sections.
3. Verify HTTP status with `curl -o /dev/null -w "%{http_code}"` before parsing.

This allows reading HF docs directly without relying on Firecrawl credits.
