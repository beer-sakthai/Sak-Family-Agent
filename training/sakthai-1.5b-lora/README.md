# SakThai 1.5B LoRA Training

One-click Colab notebook for LoRA fine-tuning Qwen2.5-1.5B-Instruct on the SakThai tool-calling dataset.

## Artifacts & Configuration

- **Notebook:** `sakthai_lora_training.ipynb` — Google Colab notebook (22 cells, T4-ready)
- **Base Model:** `Qwen/Qwen2.5-1.5B-Instruct`
- **Dataset:** [sakthai-combined-v5](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v5)
- **Output Adapter:** [sakthai-context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools)
- **Merged Model:** [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged)
- **Hyperparameters:** LoRA rank $r=16$, $\alpha=32$, 4-bit NF4 quantization, 4 epochs, 220 steps, T4 GPU (~$0.26)

## Execution Workflow

1. Open `sakthai_lora_training.ipynb` in Google Colab with a free-tier T4 GPU.
2. Provide your Hugging Face API token with write permissions via Colab Secrets (`HF_TOKEN`).
3. Execute all cells sequentially to train the QLoRA adapter, evaluate tool-calling fidelity, and push adapter weights to Hugging Face Hub.
