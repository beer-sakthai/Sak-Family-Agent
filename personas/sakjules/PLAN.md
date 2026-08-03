# PLAN.md — SakJules 🔧
> *DevSecOps, GitHub Actions & Asynchronous Model Training Plan*
> *Status: Active Execution Phase*

---

## 1. 🎯 Mega Model Training Plan (`Nanthasit/*` Suite)

SakJules manages the training, benchmark evaluation, and deployment of the custom **`Nanthasit/*`** open-weights model suite on Hugging Face Jobs:

| Model ID | Primary Purpose | Training Compute | Target Benchmark |
|:---|:---|:---|:---|
| **`Nanthasit/sakthai-triage-1.5b`** | Sub-100ms ultra-fast task triage & deputy routing | HF Jobs (`t4-small`) | >85% Accuracy |
| **`Nanthasit/sakthai-context-7b-tools-v3`** | SakJules tool-calling, Pytest repair & PR synthesis | HF Jobs (`a100-large`) | >80% Benchmark v3 |
| **`Nanthasit/sakthai-vision-7b-v2`** | SakSee Playwright screenshot vision & coordinate prediction | HF Jobs (`a100-large`) | >75% MiniWoB++ |
| **`Nanthasit/sakthai-embedding-multilingual`** | Custom cross-lingual RAG embedding model | Native Sentence-Transformers | 100% RAG Retrieval |

---

## 2. 📋 6-Stage Sak-Family Growth Cycle Roadmap

```
1. 🌙 Dream    ➔ Synthesize 25,000 task routing & code dataset (.opencode/scripts/run-benchmark-v3.py)
2. 🌅 Hope     ➔ Configure standalone PEP 723 scripts (SakThai-Training/ & openenv-rl-training/)
3. 🏗️ Care     ➔ Run GPU fine-tuning on Hugging Face Jobs (hf jobs run)
4. 🎉 Joy      ➔ Run .opencode/scripts/run-eval.py to verify >75% benchmark accuracy
5. 🔎 Trust    ➔ Audit code security (bandit, ruff, credential scans)
6. 🌱 Growth   ➔ Export GGUF to local Ollama & update model cards (.opencode/scripts/update-model-cards.py)
```

---

## 3. 🛠️ SakJules Workspace Requirements Matrix

- **Active Model Matrix ([`opencode.json`](file:///home/beern/opencode.json))**:
  - `model`: `huggingface/deepseek-ai/DeepSeek-V4-Flash`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Connected MCP Tools**:
  - `julesServer` MCP (`✓ Connected`)
  - `colab-mcp` (`✓ Connected`)
  - `supermemory` (`http://localhost:6767` — `✓ Connected`)
- **Zero-Cost Policy**: $0.00 USD financial spend enforced via local Ollama & local Supermemory ONNX embeddings.

---

*Last Updated: August 2026 · SakJules Automation Master Plan*