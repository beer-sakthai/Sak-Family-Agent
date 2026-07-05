# SakThai 7B LoRA Training

Attempt to train Qwen2.5-7B-Instruct with the tool-calling dataset v5.

**Files:**
- `train.py` — training script (HF Jobs entrypoint)
- `submit_job.py` — submits the job to HF Jobs via `run_uv_job`

**Status:** ⚠️ Work in progress — 5 attempts so far, latest fix: TRL version detection for `tokenizer` vs `processing_class`

**Config:** LoRA r=16, alpha=32, 4-bit NF4, 4 epochs, 300 steps, A10G 24GB (~$1.00/hr)
**Dataset:** [sakthai-combined-v5](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v5)

### Failure log
| # | Root cause | Fix |
|---|-----------|:----|
| 1 | No `~/.cache/huggingface/token` in container | Pass `HF_TOKEN` as secret |
| 2–4 | API/param mismatches | Moved `max_seq_length` to SFTTrainer |
| 5 | `SFTTrainer` kwarg `tokenizer` renamed | Dynamic dispatch for TRL < 0.15 vs ≥ 0.15 |
