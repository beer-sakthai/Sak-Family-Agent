# SakThai 1.5B LoRA Training

One-click Colab notebook for LoRA fine-tuning Qwen2.5-1.5B-Instruct on the SakThai tool-calling dataset.

**Files:**
- `sakthai_lora_training.ipynb` — Google Colab notebook (22 cells, T4-ready)
- **Dataset:** [sakthai-combined-v5](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v5)
- **Output adapter:** [sakthai-context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools)
- **Merged model:** [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged)

**Config:** LoRA r=16, alpha=32, 4-bit NF4, 4 epochs, 220 steps, T4 GPU (~$0.26)
