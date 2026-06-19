# SakThai fine-tuning on HF Jobs

Scripts for fine-tuning small SakThai models on Hugging Face Jobs (GPU compute),
driven from a machine without a local GPU.

## Files

| File | Purpose |
|---|---|
| `train_persona_lora.py` | PEP 723 uv script. QLoRA SFT of `Qwen/Qwen2.5-0.5B-Instruct` on the persona/doc data (`Nanthasit/hermes-dataset`). Teaches **voice/style only** — not tool-calling. Pushes the adapter to the Hub. |
| `train_toolcalling_lora.py` | PEP 723 uv script. QLoRA SFT of `Qwen/Qwen2.5-1.5B-Instruct` (configurable) on `Nanthasit/sakthai-toolcalling-v1`. Renders each row with the model's own chat template (`apply_chat_template(..., tools=...)`) so it learns **when and how to emit a tool call**. Pushes the adapter to the Hub. |
| `build_toolcalling_dataset.py` | Generates synthetic tool-calling examples for SakThai's 8 `BUILTIN_TOOLS` (+ "no-tool" negatives) in Qwen `messages`+`tools` format. Pure stdlib. |
| `fetch_public_toolcalling.py` | Pulls + reformats a slice of `glaiveai/glaive-function-calling-v2` (via the datasets-server rows API) into the same schema, for general function-calling competence. |

## Run a training job

```bash
# Persona / voice (small, fast):
hf jobs uv run --flavor t4-small --secrets HF_TOKEN --timeout 30m train_persona_lora.py

# Tool-calling behaviour (Qwen2.5-1.5B base, the capable run):
hf jobs uv run --flavor l4x1 --secrets HF_TOKEN --timeout 1h train_toolcalling_lora.py

# Bigger base — set env on the job (3B needs more VRAM; use a24g/a100):
hf jobs uv run --flavor a10g-large --secrets HF_TOKEN --timeout 2h \
  -e BASE_MODEL=Qwen/Qwen2.5-3B-Instruct \
  -e OUTPUT_REPO=Nanthasit/sakthai-toolcalling-3b-lora \
  train_toolcalling_lora.py
```

`--secrets HF_TOKEN` forwards your local token so the job can pull the private
dataset and `push_to_hub`. The token is **never** baked into the image or
committed — it lives only as a job secret. Monitor with
`hf jobs logs -f <id>` / `hf jobs inspect <id>`.

Suggested GPU flavor per base model (QLoRA 4-bit, seq 2048):

| Base model | Flavor | Notes |
|---|---|---|
| Qwen2.5-0.5B | `t4-small` | persona run |
| Qwen2.5-1.5B | `l4x1` | default tool-calling run |
| Qwen2.5-3B | `a10g-large` / `a100-large` | set `BASE_MODEL` + `OUTPUT_REPO` env |

## Build the tool-calling dataset

```bash
python build_toolcalling_dataset.py     # -> sakthai_toolcalling_synthetic.jsonl
python fetch_public_toolcalling.py       # -> glaive_converted.jsonl
# merge + dedup + split, then `hf upload <repo> train.jsonl --repo-type dataset`
```

## Artifacts (on the Hub)

- Model: `Nanthasit/sakthai-persona-0.5b-lora` (QLoRA adapter, Qwen2.5-0.5B base — voice only)
- Model: `Nanthasit/sakthai-toolcalling-1.5b-lora` (QLoRA adapter, Qwen2.5-1.5B base — tool-calling; produced by `train_toolcalling_lora.py`)
- Dataset: `Nanthasit/sakthai-toolcalling-v1` (167 examples: 151 train / 16 test, `messages`+`tools`)

## Notes

- `Nanthasit/sakthai-context-0.5b` is a stale LoRA adapter whose base path points at
  a dead local path; train from the public Qwen base instead.
- Generated `.jsonl` files are intentionally not committed — they live on the Hub.
