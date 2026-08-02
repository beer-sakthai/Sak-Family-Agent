# Pipeline Integration Section

**Purpose:** Shows how a model fits into the SakThai ecosystem — its upstream (base model, training data), downstream (merged artifacts, agent runtime), and sibling relationships. Turns an isolated model card into a node in a family network.

## When to Add

Every model card in a family ecosystem should have a Pipeline Integration section. Add one when:

- The model is one processing step in a chain (e.g., LoRA adapter → merge → GGUF → agent)
- The card only shows "how to use this" but not "why this exists and what it connects to"
- A visitor landing on the card can't tell it's part of a larger family without scrolling to the bottom table

Cards that benefit most: **LoRA adapters, tool-calling fine-tunes, specialized sub-models** (vision, TTS, embedding). These are often found via search — the Pipeline Integration section is their only link back to the family.

## Standard Structure

### 1. ASCII Pipeline Diagram

Shows the chain from base model to agent runtime. Use monospace formatting:

```markdown
```
Base Model (Qwen2.5-7B-Instruct)
    ↓ PEFT LoRA fine-tune
sakthai-context-7b-tools  ← You are here
    ↓ merge_and_unload()
sakthai-context-7b-merged  (the merged GGUF, ready for llama.cpp)
    ↓ shared memory (~/.sakthai)
SakThai Agent (@sakthai_agent_bot) — Main Lead
SakKing Agent (@sakking_agent_bot) — Runner
```
```

Variations:

- **For merged GGUF cards** (no adapter step): show `Base → GGUF → Agent`
- **For standalone models** (no fine-tune, no merge): show `Model → Inference → Integration`
- **For datasets**: show `Raw Data → Pipeline → Downstream Models`

### 2. Relationship Descriptions

After the diagram, explain each link with bold headers:

```markdown
**Upstream:** [brief description of what feeds into this model]
**Downstream:** [brief description of what this model produces or enables]
**Sibling:** [related models at the same level in the pipeline]
**Ecosystem role:** [one-line summary of this model's purpose in the family]
```

Example from `sakthai-context-7b-tools`:

```markdown
**Upstream:** The adapter is trained on [sakthai-combined-v6](...) (2,003 tool-calling examples) using QLoRA on Qwen2.5-7B-Instruct.

**Downstream:** The merged version ([context-7b-merged](...)) can be loaded directly in llama.cpp with the `<tool>` prompt format for agentic use.

**Sibling adapters:** [1.5B-Tools](...) provides the same tool-calling capability in a smaller 427 MB package.

**Ecosystem role:** Powers the Sak-Family-Agent tool-calling stack — the structured `<tool>` XML format used here is what every agent in the family reads and writes.
```

### 3. (Optional) Companion Spaces

If the model has a Space demo, link it:

```markdown
**Try it:** [TTS Playground Space](...) — hear this model's voice output in your browser.
```

## Where in the Card

Insert the Pipeline Integration section **after the Training/Technical Details section and before the Merged Versions/Comparison section**. This puts the ecosystem context right after the "what it is" details and before the "what to use instead" table.

Position map for a typical LoRA adapter card:

```
YAML frontmatter
Family header + badges
Title + Description
Usage (how to load/run)
Tool Format (input/output spec)
Training (hyperparams, dataset)
🔹 Pipeline Integration ← HERE (after training, before comparisons)
Merged Versions (sibling links)
SakThai Model Family table
Footer + Collection link
```

## Checklist

After writing a Pipeline Integration section, verify:

- [ ] ASCII diagram renders correctly (check for extra spaces, alignment)
- [ ] Every linked repo exists (no 404s) — use HEAD requests to verify
- [ ] Upstream chain is accurate (base model → this artifact → downstream)
- [ ] Sibling references match (not listing itself as sibling)
- [ ] Download counts NOT used inside the section — they go stale. Use descriptive text or dynamic badges
- [ ] Card size grew (measure before/after)

## Real-World Examples

### LoRA Adapter (sakthai-context-7b-tools)
- **Before (4,615 chars):** Usage + Training + Merged Versions + Family table — no pipeline context
- **After (6,106 chars):** Added Pipeline Integration with ASCII diagram + 4 relationship descriptions
- **Diff:** The card now shows the full chain from base model to agent runtime, not just adapter usage

### Future: Merged GGUF
Planned structure for 7b-merged, 7b-128k, 1.5b-merged:
```markdown
## Pipeline Integration

```
Base Model (Qwen2.5-7B-Instruct)
    ↓ LoRA training → merge → GGUF quantization
sakthai-context-7b-merged  ← You are here
    ↓ loaded by llama.cpp / Ollama
SakThai Agent — Main Lead
```

**Upstream:** Fine-tuned from [sakthai-context-7b-tools](...) via `merge_and_unload()`, then quantized with llama.cpp to GGUF format for CPU/edge deployment.

**Downstream:** Loaded directly by the SakThai and SakKing agents via llama.cpp. The [`<tool>` prompt format](...) enables structured function calling.

**Sibling merges:** [1.5B-merged](...) for lighter deployments, [0.5B-merged](...) for edge devices.
```

## Relationship to Other Skills

This reference complements:
- `hf-ecosystem-cron-maintenance.md` — the cron workflow that picks which card to improve
- `narrative-consistency-audit.md` — marker #7 checks for Pipeline Integration existence; this doc provides the content standard
- `hf-hub-repocard-system` SKILL.md — the technical upload/commit methods to deploy the section
