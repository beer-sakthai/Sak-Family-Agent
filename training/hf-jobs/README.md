# SakThai fine-tuning on HF Jobs

Scripts for fine-tuning small SakThai models on Hugging Face Jobs (GPU compute),
driven from a machine without a local GPU.

## Files

| File | Purpose |
|---|---|
| `train_persona_lora.py` | PEP 723 uv script. QLoRA SFT of `Qwen/Qwen2.5-0.5B-Instruct` on the persona/doc data (`Nanthasit/hermes-dataset`). Pushes the adapter to the Hub. Runs as-is on HF Jobs. |
| `build_toolcalling_dataset.py` | Generates synthetic tool-calling examples for SakThai's 8 `BUILTIN_TOOLS` (+ "no-tool" negatives) in Qwen `messages`+`tools` format. Pure stdlib. |
| `fetch_public_toolcalling.py` | Pulls + reformats a slice of `glaiveai/glaive-function-calling-v2` (via the datasets-server rows API) into the same schema, for general function-calling competence. |

## Run a training job

```bash
hf jobs uv run --flavor t4-small --secrets HF_TOKEN --timeout 30m train_persona_lora.py
```

`--secrets HF_TOKEN` forwards your local token so the job can `push_to_hub`.
Monitor with `hf jobs logs -f <id>` / `hf jobs inspect <id>`.

## Build the tool-calling dataset

```bash
python build_toolcalling_dataset.py     # -> sakthai_toolcalling_synthetic.jsonl
python fetch_public_toolcalling.py       # -> glaive_converted.jsonl
# merge + dedup + split, then `hf upload <repo> train.jsonl --repo-type dataset`
```

## Artifacts (on the Hub)

- Model: `Nanthasit/sakthai-persona-0.5b-lora` (QLoRA adapter, Qwen2.5-0.5B base)
- Dataset: `Nanthasit/sakthai-toolcalling-v1` (167 examples, `messages`+`tools`)

## Notes

- `Nanthasit/sakthai-context-0.5b` is a stale LoRA adapter whose base path points at
  a dead local path; train from the public Qwen base instead.
- Generated `.jsonl` files are intentionally not committed — they live on the Hub.
