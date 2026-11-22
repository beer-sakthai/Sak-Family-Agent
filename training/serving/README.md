# Serving the SakThai model

Once `train_toolcalling_lora.py` has produced the adapter
(`Nanthasit/sakthai-toolcalling-1.5b-lora`), these scripts let the **SakThai
agent actually run on it**. Five paths, same model:

| Script / Runtime | Path | Cost | What it does |
|---|---|---|---|
| `eval_toolcalling.py` | verify | free (local) / cheap (HF Job) | Loads base + adapter and runs tool-calling probe prompts. Confirms the fine-tune learned the tool-call format before you wire it up. |
| `export_ollama.py` | **local (Ollama)** | free | Merges the adapter, writes an Ollama `Modelfile`, and prints the GGUF-conversion + `ollama create` steps. Then `sakthai run --provider ollama --model sakthai ...`. |
| `sakthai gateway` | **local / networked API** | free | Multi-threaded OpenAI-compatible Gateway (`/v1/chat/completions`) with streaming SSE, voice audio (`/v1/chat/ws`), and DataLossGuardrail security. |
| `vLLM` | **local / self-hosted GPU** | free (local GPU) | High-throughput OpenAI-compatible server with PagedAttention and batched inference. Point `OPENAI_API_BASE` at `http://localhost:8000/v1`. |
| `deploy_hf_endpoint.py` | **cloud** | billable (dry-run by default) | Provisions a TGI Inference Endpoint exposing an OpenAI-compatible `/v1` API. Point `OPENAI_API_BASE` at it and `sakthai run --provider openai ...`. |

All paths reuse the **single** tool/system definitions from
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

## 3. High-throughput serving via vLLM (GPU)

For production or benchmark workloads on a GPU-enabled workstation or server:

```bash
uv run python -m vllm.entrypoints.openai.api_server \
  --model Nanthasit/sakthai-context-1.5b-merged \
  --port 8000 \
  --chat-template-content-format openai
```

Then point the SakThai CLI at the local vLLM endpoint:

```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="none"
sakthai run --provider openai --model Nanthasit/sakthai-context-1.5b-merged "Check system status"
```

## 4. Cloud via HF Inference Endpoint (billable)

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

## 5. Local / Networked Runtime Gateway

Serve all 6 personas over an OpenAI-compatible REST API and WebSocket audio endpoint:

```bash
# Start Gateway on port 8080:
uv run sakthai gateway serve --port 8080

# Query from any OpenAI SDK or HTTP client:
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $SAKTHAI_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "sakthai", "messages": [{"role": "user", "content": "Analyze system health"}]}'
```

## Security

- Tokens are read from env / job secrets only — **never** committed or baked into
  an image.
- `deploy_hf_endpoint.py` **dry-runs by default**; provisioning a billable
  endpoint requires an explicit `--create`.
- The endpoint type is `protected` (auth required), not public.
- Merged weights / GGUF artifacts are build outputs — keep them out of git
  (they live on the Hub or on disk).
