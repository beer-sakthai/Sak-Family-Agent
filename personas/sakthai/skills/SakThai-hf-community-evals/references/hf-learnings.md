# HF Learnings Log — hf-community-evals

## 2026-07-25: Hugging Face Community Evals + EEE (Every Eval Ever) Integration

### Summary
Deep-dive into Hugging Face's decentralized evaluation results system (Community Evals, launched Feb 2026) and its cross-compatibility with Every Eval Ever (EEE, launched Feb 2026) — announced June 30, 2026. Covers the dual system: benchmark datasets with leaderboards, model repos with `.eval_results/` YAML files, community PR submission workflow, and the EEE converter tool that automates cross-posting with verified source badges.

### Key Findings

---

#### 1. Hugging Face Community Evals (Feb 2026)

Hugging Face launched Community Evals as a decentralized system for tracking model evaluation results directly on the Hub. Two sides:

**For Benchmarks:**
- Dataset repos can register as **Benchmarks** (tag: "Benchmark")
- Registration done via `eval.yaml` in the dataset repo root
- Once registered, the dataset page automatically aggregates all reported scores from across the Hub and displays a **leaderboard** of top models
- Official benchmarks: MMLU-Pro, GPQA, HLE, GSM8K (4 initial, expanding)
- Browse: https://huggingface.co/datasets?benchmark=benchmark:official&sort=trending

**For Models:**
- Evaluation scores live in `.eval_results/*.yaml` inside the model repo
- Results automatically appear on the model card
- Results also feed into the matching benchmark leaderboard
- Both model author's results AND community-submitted results are aggregated
- Model authors can close score PRs or hide results on their own repo

**For the Community:**
- Anyone can submit evaluation results for any model via Pull Request
- Results show as "community" immediately, even before the PR is merged
- Scores carry badges: author-submitted, community-submitted, or independently verified
- Full git history of when evals were added and changed
- Results exposed via Hub APIs for aggregation into curated leaderboards

---

#### 2. Evaluation Results YAML Format (`.eval_results/*.yaml`)

Full spec: https://github.com/huggingface/hub-docs/blob/main/eval_results.yaml

**Fields in the spec:**

```yaml
- dataset:
    id: cais/hle                  # Required. Valid dataset id with "Benchmark" tag
    task_id: {task_id}            # Required. Task ID as defined in eval.yaml
    revision: {dataset_revision}  # Optional. Hash of the dataset revision

  value: {metric_value}           # Required. Example: 20.90

  verifyToken: {verify_token}     # Optional. Signature for auditable/reproducible evals
                                  # (e.g., run in HF Job using inspect-ai or lighteval)

  date: "{date}"                  # Optional. ISO-8601 date or datetime (string)

  source:                         # Optional. Attribution for this result
    url: {source_url}             # Required if source block present
    name: {source_name}           # Optional. Name of the source
    user: {username}              # Optional. HF username
    org: {orgname}                # Optional. HF org name

  notes: "{notes}"                # Optional. Setup details (tools, CoT, etc.)
```

**Minimal example:**
```yaml
- dataset:
    id: Idavidrein/gpqa
    task_id: gpqa_diamond
  value: 0.412
```

**Extended example with EEE source link:**
```yaml
- dataset:
    id: TIGER-Lab/MMLU-Pro
    task_id: mmlu_pro
  value: 72.3
  date: "2026-06-15"
  source:
    url: https://huggingface.co/datasets/evaleval/EEE_datastore/blob/main/flat/objects/ab/cd/<uuid>.json
    name: EvalEval
  notes: "5-shot, CoT"
```

---

#### 3. Benchmark Registration (`eval.yaml`)

Located in the dataset repo root. Based on the Inspect AI format.

**Required fields:**
```yaml
# Minimal eval.yaml
benchmark:
  name: MMLU-Pro
  tasks:
    - task_id: mmlu_pro
      dataset:
        path: TIGER-Lab/MMLU-Pro
      metrics:
        - accuracy
```

**Example templates from production:**
- https://huggingface.co/datasets/Idavidrein/gpqa/blob/main/eval.yaml
- https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/blob/main/eval.yaml
- https://huggingface.co/datasets/cais/hle/blob/main/eval.yaml
- https://huggingface.co/datasets/openai/gsm8k/blob/main/eval.yaml

**Key fields in `eval.yaml` tasks[]:**

| Field | Required | Description |
|-------|----------|-------------|
| `task_id` | Yes | Unique ID for this leaderboard/task |
| `dataset.path` | Yes | Dataset repo ID |
| `metrics[]` | Yes | Metric names to display |
| `evaluation_framework` | No (but required if `inspect-ai`) | E.g., `inspect-ai` |
| `inspect_ai.solver` | If `inspect-ai` | Solver used |
| `inspect_ai.scorer` | If `inspect-ai` | Scorer used |

---

#### 4. Every Eval Ever (EEE) — The EvalEval Coalition

**Launched**: February 2026
**Project**: https://evalevalai.com/
**GitHub**: https://github.com/evaleval/every_eval_ever

EEE was built as the first cross-institutional effort to standardize how AI evaluation results get reported. It defines:

**One JSON schema** for an evaluation result that records:
- Generation config (temperature, top_p, max_tokens, etc.)
- Harness version and configuration
- Reproducibility notes
- Instance-level data (per-question scores)
- Source attribution
- Evaluation timestamp

**Scale (as of June 2026):**
- ~229,000 evaluation results
- 22,000+ models evaluated
- 2,200+ benchmarks
- Pulled from 31 different reporting formats
- Datastore: https://huggingface.co/datasets/evaleval/EEE_datastore

**Key insight**: Reproducing those runs from scratch would cost "hundreds of thousands of dollars" — EEE preserves the data once someone has paid to generate it.

**Verification system**: 
- Verified checkmark on Eval Cards when submitted through org's official HF account
- Verification info: https://evalcards.evalevalai.com/help/get-verified

---

#### 5. The Integration: EEE ↔ Community Evals (June 30, 2026)

**Announcement**: https://huggingface.co/blog/eee-community-evals

**What changed**: Community Evals and EEE became intercompatible. Cross-posting and interpreting evaluation results between the two systems, linking to open models, leaderboards, and a unified standardized metadata store.

**The Converter Tool**:
- Repository: https://github.com/evaleval/every_eval_ever/tree/main/tools/hf-community-evals
- Source file: `community_evals_converter.py`
- Language: Python (uses `huggingface_hub`, `rich`, `requests`, `pyyaml`)

**How it works**:

1. **Input**: Points at one EEE datastore collection
2. **Download**: Downloads that collection + referenced records
3. **Verify**: Checks object hashes for integrity
4. **Filter**: Finds scores that map to supported benchmarks (4 initial: MMLU-Pro, GPQA, HLE, GSM8K)
5. **Audit**: Reads every `.eval_results` YAML on model's main branch and in open PRs
6. **Compare**: Checks by dataset+task (not filename):
   - Same score exists → `already_present`
   - Different score for same task → `score_conflict`
   - Model repo not on Hub → `missing_hf_model`
   - Everything else → `ready`
7. **Review**: Writes local YAML previews + review file; shows report of ready/needs-attention
8. **Push**: Only opens PRs after user types `OPEN PRS` + commit message

**Mapping from EEE → Community Evals YAML**:
```
source_data.hf_repo        → dataset.id
evaluation_name            → task_id
score_details.score        → value
evaluation_timestamp       → date
datastore object URL       → source.url (backlink to full JSON record)
source_name = "EvalEval"   → source.name
```

**Source badge flow**:
1. EEE record → converter → `.eval_results/*.yaml` with `source.url` linking to EEE JSON
2. On model page, badge shows "Source: EvalEval" with link
3. Clickthrough → full EEE record with generation config, harness version, instance-level data

**Usage**:
```sh
# Process a collection
uv run tools/hf-community-evals/community_evals_converter.py MMLU-Pro

# With custom options
uv run tools/hf-community-evals/community_evals_converter.py \
  --benchmark MMLU-Pro \
  --datastore evaleval/EEE_datastore \
  --force
```

---

#### 6. Verified Score Badges

**Verified vs Community scores:**

| Badge | Meaning | Source |
|-------|---------|--------|
| **Verified** | Submitted through official org HF account, provably reproducible | First-party eval via HF Jobs, Inspect AI, Lighteval |
| **Author** | Submitted by model author | Model author's own reporting |
| **Community** | Submitted by anyone via PR | Third-party eval |
| **Source: EvalEval** | Cross-posted from EEE datastore | EEE converter with backlink |

The `verifyToken` field in the YAML spec enables cryptographic verification:
- Generated by running eval in HF Job with inspect-ai or lighteval
- Proves the evaluation was run in a tamper-proof environment
- Still optional — most community scores won't have it

---

#### 7. Comparison: Community Evals vs. Open LLM Leaderboard

| Aspect | Community Evals | Open LLM Leaderboard |
|--------|----------------|---------------------|
| **Launch** | Feb 2026 | 2023 (multiple versions) |
| **Model** | Decentralized — any model repo can host results | Centralized — curated list of models |
| **Submission** | PR-driven, anyone can contribute | Submit via form, curated team reviews |
| **Benchmarks** | Dataset-defined via eval.yaml (4 official, expanding) | Fixed set of benchmarks per version |
| **Results location** | `.eval_results/*.yaml` in model repo | Leaderboard dataset |
| **Verification** | Optional verifyToken, source badges | Standardized evaluation harness |
| **EEE integration** | Direct — converter tool cross-posts | Separate (EEE pulls from leaderboard) |
| **Use case** | Surface any eval result transparently | Gold-standard reproducible comparison |

---

#### 8. Key Takeaways for SakThai Agents

- Community Evals is the **decentralized eval layer** — any model can carry scores, any user can contribute
- EEE is the **structured data layer** — canonical JSON schema, large datastore (229K results)
- The integration means: **submit once, appear in both places** with source attribution
- For Beer's models (11 models on Nanthasit account), we could:
  - Add `.eval_results/` YAML with benchmark scores
  - Submit scores via PR to our own model repos
  - Source from EEE datastore if runs have been recorded there
  - Use the converter tool to cross-post from EEE collections
- Zero-cost: PR submission to model repos is free, no API calls needed
- The `hf` CLI / `huggingface_hub` Python API can manage these files programmatically

**How to add eval results to a model repo manually:**
```python
from huggingface_hub import HfApi
api = HfApi()

# Create eval result YAML content
yaml_content = """
- dataset:
    id: TIGER-Lab/MMLU-Pro
    task_id: mmlu_pro
  value: 68.5
  date: "2026-07-20"
  source:
    url: https://github.com/my-org/eval-logs
    name: My Eval Run
"""

api.upload_file(
    path_or_fileobj=yaml_content.encode(),
    path_in_repo=".eval_results/mmlu-pro.yaml",
    repo_id="Nanthasit/my-model",
    repo_type="model",
)
```

---

#### 9. Architecture Diagram (Conceptual)

```
                    ┌──────────────────────┐
                    │   EEE Datastore       │
                    │  (evaleval/EEE_datastore) │
                    │  229K results         │
                    │  22K models           │
                    │  2.2K benchmarks      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   EEE→HF Converter   │
                    │  (community_evals_    │
                    │   converter.py)      │
                    └──────────┬───────────┘
                               │ downloads, audits,
                               │ maps fields, opens PRs
                    ┌──────────▼───────────┐
                    │   Model Repo          │
                    │  .eval_results/*.yaml │
                    │  ┌─────────────────┐  │
                    │  │ dataset.id      │  │
                    │  │ task_id         │  │──→ Benchmark Dataset Page
                    │  │ value           │  │    (aggregated leaderboard)
                    │  │ source.url ─────┼──┤──→ Back to EEE JSON record
                    │  │ source.name     │  │
                    │  └─────────────────┘  │
                    └──────────────────────┘
```

### Practical Tips (from SakThai v7 eval uploads, 2026-07-29)

#### Multiple results per file

The YAML spec uses a **list** format (`- dataset:` repeated items), so multiple results can go in one file. This is cleaner than one file per result:

```yaml
# ✅ GOOD — one file, four results
- dataset:
    id: llamastack/bfcl_v3
    task_id: simple
  value: 0.80
  source:
    url: https://github.com/beer-sakthai/Sak-Family-Agent
    name: SakThai Internal Benchmark
    user: Nanthasit
  notes: "4/5 simple tool calls"

- dataset:
    id: llamastack/bfcl_v3
    task_id: multiple
  value: 1.0
  source:
    url: https://...
    name: SakThai Internal Benchmark
    user: Nanthasit
  notes: "5/5 multiple calls"
```

❌ Don't put each result in its own file — it wastes commits and clutters the `.eval_results/` directory.

#### Always add `source.user` for attribution

The `source.user` field makes the result badge show with your username. Without it, the source block shows an unnamed source. All SakThai models were fixed on 2026-07-29 to include `user: Nanthasit`.

#### Registered benchmarks vs any dataset

The `dataset.id` should point to a dataset with the **Benchmark** tag for results to appear on benchmark leaderboards. For non-Benchmark datasets, results still appear on the model page but won't feed into aggregated leaderboards. BFCL (`llamastack/bfcl_v3`) is not a registered benchmark as of 2026-07-29, but results with this dataset ID still show on model pages.

#### Clean up old individual files when consolidating

If you previously uploaded individual result files (e.g. `bfcl-simple.yaml`, `bfcl-multiple.yaml`) and later consolidate into a single file (e.g. `bfcl.yaml`), delete the old files to avoid duplicate display:

```python
from huggingface_hub import HfApi
api = HfApi(token=HF_TOKEN)
for f in ['bfcl-simple.yaml', 'bfcl-multiple.yaml']:
    api.delete_file(
        path_in_repo=f'.eval_results/{f}',
        repo_id='Nanthasit/my-model',
        repo_type='model'
    )
```

Use `HfApi.delete_file()` (not the REST API, which rejects DELETE). The old files still appear on the model's file tree and in API responses if not cleaned.

### References
- https://huggingface.co/blog/eee-community-evals (June 30, 2026)
- https://huggingface.co/blog/community-evals (Feb 2026)
- https://huggingface.co/docs/hub/en/eval-results
- https://github.com/huggingface/hub-docs/blob/main/eval_results.yaml
- https://github.com/evaleval/every_eval_ever (EEE repo)
- https://github.com/evaleval/every_eval_ever/tree/main/tools/hf-community-evals
- https://huggingface.co/datasets/evaleval/EEE_datastore
- https://evalevalai.com/
- https://evalcards.evalevalai.com/help/get-verified
- https://huggingface.co/datasets?benchmark=benchmark:official&sort=trending

---

## 2026-07-29: Transformers v5.14.0 Ecosystem Update

### Summary
Transformers v5.14.0 (Jul 15) and v5.14.1 (Jul 16) released with major new architectures and performance improvements. Key findings for SakThai ecosystem tracking.

### Key Findings

#### 1. Inkling — Thinking Machines Lab (975B total / 41B active MoE)
- General-purpose multimodal model: text + image + audio → text
- MoE architecture: 975B total params, only 41B active per forward pass
- Designed for agentic/tool-use systems, coding, RAG, and conversational AI
- Open weights release for research and fine-tuning
- Context: This is a frontier-scale model on the Hub — relevant for ecosystem awareness but too large (975B) for our zero-cost infra

#### 2. MTP (Multi-Token Prediction) for Assisted Decoding
- Docs added for assisted decoding using Multi-Token Prediction
- Speculative decoding technique: predicts multiple future tokens in one forward pass
- Can significantly speed up text generation throughput

#### 3. TIPSv2 — Vision-Language Contrastive Encoder
- New model family: Text-Image Pre-training with Spatial awareness
- Contrastive vision-language encoder (enhanced CLIP-style)
- Includes TIPSv2 DPT variant for depth estimation
- Source: Bingyi Cao et al. "TIPSv2: Advancing Vision-Language Pretraining with Enhanced Patch-Text Alignment"

#### 4. Kernel & Performance Improvements
- SDPA prefill now uses FlashAttention kernel with StaticCache → **up to 260% faster** for large input sizes
- DeepGEMM Triton fallback made more robust when CUDA_HOME is unset
- Compressed tensors in FP8 format support added

#### 5. Breaking Changes
- GPTNeoX: `embed_out` remapped to `lm_head` (weight naming change)
- GPTBigCode: `_supports_attention_backend = True` enabled for vLLM compatibility

### Action Items for SakThai Ecosystem
- No immediate infra changes needed (our models are 0.5B–7B, Inkling is 975B)
- Good to track MTP as future speculative decoding option for our GGUF inference
- TIPSv2 is relevant reference for our vision-7b model's model card context
- The SDPA+StaticCache performance gain (260%) is worth noting in our inference documentation
