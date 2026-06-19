# Serving the SakThai model

Once `train_toolcalling_lora.py` has produced the adapter
(`Nanthasit/sakthai-toolcalling-1.5b-lora`), these scripts let the **SakThai
agent actually run on it**. Three paths, same model:

| Script | Path | Cost | What it does |
|---|---|---|---|
| `eval_toolcalling.py` | verify | free (local) / cheap (HF Job) | Loads base + adapter and runs tool-calling probe prompts. Confirms the fine-tune learned the tool-call format before you wire it up. |
| `export_ollama.py` | **local** | free | Merges the adapter, writes an Ollama `Modelfile`, and prints the GGUF-conversion + `ollama create` steps. Then `sakthai run --provider ollama --model sakthai ...`. |
| `deploy_hf_endpoint.py` | **cloud** | billable (dry-run by default) | Provisions a TGI Inference Endpoint exposing an OpenAI-compatible `/v1` API. Point `OPENAI_API_BASE` at it and `sakthai run --provider openai ...`. |

All three reuse the **single** tool/system definitions from
`../hf-jobs/build_toolcalling_dataset.py`, so serving matches training exactly.

## 1. Verify the adapter

```bash
uv run training/serving/eval_toolcalling.py
# or on HF Jobs (no local GPU):
hf jobs uv run --flavor t4-small --secrets HF_TOKEN training/serving/eval_toolcalling.py
```

You should see tool calls emitted for action prompts and plain answers for the
"no-tool" probes.

## 2. Local via Ollama (recommended, free)

```bash
uv run training/serving/export_ollama.py --out ./sakthai-merged
# then follow the printed llama.cpp + ollama steps, finally:
sakthai run --provider ollama --model sakthai "Remember I use uv, never pip"
```

Needs [`llama.cpp`](https://github.com/ggerganov/llama.cpp) (for
`convert_hf_to_gguf.py`) and [Ollama](https://ollama.com) installed. The agent's
OpenAI/Ollama provider already targets `127.0.0.1:11434`.

## 3. Cloud via HF Inference Endpoint (billable)

```bash
# Merge + upload a serving repo first (TGI serves a full model, not a bare adapter):
uv run training/serving/export_ollama.py --out ./sakthai-merged
hf upload Nanthasit/sakthai-toolcalling-1.5b-merged ./sakthai-merged

# Dry-run the deploy plan (no cost):
uv run training/serving/deploy_hf_endpoint.py --repo Nanthasit/sakthai-toolcalling-1.5b-merged
# Provision for real (BILLABLE):
HF_TOKEN=... uv run training/serving/deploy_hf_endpoint.py \
    --repo Nanthasit/sakthai-toolcalling-1.5b-merged --create

export OPENAI_API_BASE="https://<endpoint>.endpoints.huggingface.cloud/v1"
export OPENAI_API_KEY="$HF_TOKEN"
sakthai run --provider openai --model tgi "Remember I prefer dark mode"
```

## Security

- Tokens are read from env / job secrets only — **never** committed or baked into
  an image.
- `deploy_hf_endpoint.py` **dry-runs by default**; provisioning a billable
  endpoint requires an explicit `--create`.
- The endpoint type is `protected` (auth required), not public.
- Merged weights / GGUF artifacts are build outputs — keep them out of git
  (they live on the Hub or on disk).
