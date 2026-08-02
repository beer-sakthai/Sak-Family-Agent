# TRL Research Notes — Session Context

## Source material
- TRL index: https://huggingface.co/docs/trl/main/en/index
- TRL installation: https://huggingface.co/docs/trl/main/en/installation
- Xet protocol index: https://huggingface.co/docs/xet/main/en/index (tangential, explored during TRL research)

## Extracted TRL taxonomy (as of 2026-06-21)

### Online methods
- `GRPOTrainer` ⚡️ (vLLM + Harbor/OpenEnv support)
- `RLOOTrainer` ⚡️
- `OnlineDPOTrainer` 🧪 ⚡️
- `NashMDTrainer` 🧪 ⚡️
- `PPOTrainer` 🧪
- `XPOTrainer` 🧪 ⚡️

### Reward modeling
- `RewardTrainer`
- `PRMTrainer` 🧪

### Offline methods
- `SFTTrainer`
- `DPOTrainer`
- `BCOTrainer` 🧪
- `CPOTrainer` 🧪
- `KTOTrainer` 🧪
- `ORPOTrainer` 🧪

### Knowledge distillation
- `GKDTrainer` 🧪
- `MiniLLMTrainer` 🧪

## Key blog posts referenced
- TRL v1 (2026-03-27)
- OpenEnv (2025-10-23)
- VLM alignment in TRL (2025-08-07)
- Co-located vLLM in TRL (2025-06-03)
- Liger GRPO meets TRL (2025-05-25)
- Open-R1 (2025-01-28)

## Quick install commands
```bash
# Stable (e.g. v1.6.0)
pip install trl

# Source (main branch, latest features)
git clone https://github.com/huggingface/trl.git
cd trl
pip install -e .
# Dev install
pip install -e ".[dev]"
```

## Research fallback pattern
When `web_search` fails with billing errors (Firecrawl 402 / `BILLING_ERROR`) and `browser_navigate` times out, direct `curl` against the public docs site is a reliable fallback for retrieving static HTML content. Append `| sed -n '1,NNNp'` to inspect head or use `browser_console` JS extraction for cleaned main-content text.
