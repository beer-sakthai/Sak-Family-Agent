# Dataset Enrichment Workflow

Analyze an existing tool-calling dataset to identify gaps, then generate targeted new examples to fill them.

## When to Use

- You have a training dataset and want to make the next model better without starting from scratch
- The model shows weaknesses in specific areas (multi-turn, refusal, cycle-awareness, non-tool direct answers)

## Workflow

```
Analyze current stats → Identify under-represented categories
→ Build scenario-based generators → Validate every example
→ Merge + upload to HF
```

### 1. Analyze Current Dataset

```python
import json
from huggingface_hub import hf_hub_download
path = hf_hub_download("Nanthasit/sakthai-combined-v6", "data/train.jsonl", repo_type="dataset")
data = [json.loads(l) for l in open(path) if l.strip()]
total = len(data)
tool_examples = sum(1 for d in data if any(
    any(tc.get('function',{}).get('name','') != '' for tc in m.get('tool_calls',[]))
    for m in d.get('messages',[]) if isinstance(m, dict)))
multi_turn = sum(1 for d in data if sum(1 for m in d.get('messages',[]) if m.get('role')=='user') > 1)
has_energy = sum(1 for d in data if any(
    tc.get('function',{}).get('name') == 'assess_energy'
    for m in d.get('messages',[]) if isinstance(m, dict)
    for tc in m.get('tool_calls',[]) if isinstance(tc, dict)))
```

### 2. Identify Gaps

Compare against targets:

| Gap | Target | Why |
|-----|--------|-----|
| Low multi-turn | >15% | Model needs follow-up conversation flow |
| Low energy-awareness | >10% | Core SakThai feature — assess before acting |
| Low non-tool ratio | >11% | Must know when NOT to call a tool |

### 3. Build Scenario-Based Generators

Use a class-based generator with scenario templates, not hand-crafted examples. Structure:

#### Generator architecture

```python
class ExampleGenerator:
    def __init__(self):
        self.examples = []

    # Helper: build tool call dict with unique call_id
    def _tc(self, name, args, cid=None):
        return {
            "id": cid or f"call_{uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}
        }

    # Helper: build tool response with matching call_id
    def _tr(self, cid, content):
        return {"role": "tool", "tool_call_id": cid, "content": content}

    # Helper: build tool definition array from schema subset
    def _tools(self, names, schemas):
        return [{"type": "function", "function": schemas[n]} for n in names
                if n in schemas]
```

#### Multi-turn patterns (target: 100 examples)

| Pattern | Description | Turns | Tools |
|---------|-------------|-------|-------|
| `simple_followup` | Tool call → answer → user follows up → direct or different tool | 2 | Same domain (weather→need umbrella?, stock→news) |
| `research_chain` | Search → dig deeper → summarize findings | 3-4 | web_search chained |
| `multi_step` | User starts multi-step workflow, says "next" between each | 2-5 | Random selection per step |
| `tool_switch` | User asks unrelated things in sequence | 2-4 | Different tool each turn |
| `direct_then_tool` | First answer is a direct knowledge response, then user asks tool-worthy Q | 2-3 | mixed |
| `refine` | User asks → results → "narrow it down" → refined search → summarize | 2-3 | Same tool refined |
| `hf_workflow` | HF-specific: search models → get card → run inference → create space | 2-4 | hf_* tools only |

#### Energy-aware patterns (target: 80 examples)

| Template | Charge | Behavior |
|----------|--------|----------|
| `low_energy_refuse` | 5-18% (Dream) | assess_energy → refuse complex work, rest mode |
| `assess_then_execute` | 50-85% (Care) | assess → proceed with normal task |
| `high_energy_creative` | 80-98% (Joy/Trust/Growth) | assess → do creative work (generate, quote, color) |
| `full_cycle` | 45-75% | assess → log_transition → execute → close_cycle → capture_lesson |
| `hope_explore` | 25-45% (Hope) | assess → light research only, no heavy tasks |

**Critical energy stage mapping:**

```
Dream  (0-19%)  — rest only, refuse tool-heavy tasks
Hope   (20-49%) — light exploration, research
Care   (50-79%) — building, coding, productive work
Joy    (80-100%) — creative, complex problem-solving
Trust  (80-100%) — verification, review, deployment
Growth (80-100%) — learning, experimentation
```

#### Non-tool direct answer patterns (target: 40 examples)

Knowledge Q&A covering:
- **General knowledge**: capitals, science, history, definitions
- **HF-specific**: what is the Hub, Transformers library, Inference API, model cards, Spaces
- **SakThai-specific**: energy stages, what is SakThai-Agent, how the cycle works

Structured as single or double Q&A in sequence, no tools field (or empty `"tools": []`).

### 4. Validate Every Example

```python
def validate(ex):
    msgs = ex.get("messages", [])
    if not msgs or msgs[0].get("role") != "system":
        return False, "missing system as first message"
    # tool_call_id chain integrity
    gen_ids = {tc["id"] for m in msgs for tc in (m.get("tool_calls") or [])
               if isinstance(tc, dict)}
    for m in msgs:
        if m.get("role") == "tool":
            cid = m.get("tool_call_id", "")
            if cid and cid not in gen_ids:
                return False, f"orphan tool_call_id {cid}"
        elif m["role"] == "assistant" and "tool_calls" in m:
            for tc in m["tool_calls"]:
                try:
                    json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    return False, f"invalid JSON args in {tc['function']['name']}"
    return True, "ok"
```

### 5. Merge & Upload

```python
from huggingface_hub import HfApi
api = HfApi()

# Merge
with open("original_train.jsonl") as f:
    original = [json.loads(l) for l in f]
with open("new_examples.jsonl") as f:
    new_examples = [json.loads(l) for l in f]
merged = original + new_examples

# Write combined
with open("train.jsonl", "w") as f:
    for ex in merged:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

# Upload
api.upload_file(
    path_or_fileobj="train.jsonl",
    path_in_repo="data/train.jsonl",
    repo_id="Nanthasit/sakthai-combined-v6",
    repo_type="dataset",
    commit_message="Enrich: +220 examples (100 multi-turn, 80 energy, 40 non-tool)"
)
```

Always verify upload with `api.get_paths_info(...)` or check the commit list.

### 6. Report Final Stats

Print before/after comparison for each target category:

```python
print(f"Before: {len(original)} → After: {len(merged)}")
print(f"  Multi-turn:     {before_multi} → {after_multi}")
print(f"  Energy-aware:   {before_energy} → {after_energy}")
print(f"  Non-tool:       {before_notool} → {after_notool}")
```

## v6 Reference Profile (current)

Updated after enrichment session (July 2026):

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Total** | 908 | **1,128** | +220 |
| **Tool-calling** | 821 (90.4%) | 1,001 (88.7%) | +180 |
| **Multi-turn** | 69 (7.6%) | **179 (15.9%)** | **+110** ✓ |
| **Energy-aware** (assess_energy called) | 41 (4.5%) | **121 (10.7%)** | **+80** ✓ |
| **Non-tool direct answer** | 87 (9.6%) | **127 (11.2%)** | **+40** ✓ |
| **Unique tools** | 81 | 81 | (steady) |

Previous v5: 710 examples with 300 non-tool filler (45%).

## Pitfalls

- **Tool schema availability**: Before generating, extract all tool schemas from the existing dataset. The generator needs them to build valid `tools` arrays. Save as `tool_schemas.json`.
- **Call_id uniqueness**: Use unique IDs per *generation run*, not per conversation. Global counter or random hex string. Duplicate IDs cause validation failures.
- **Multi-turn alternation**: Messages must strictly alternate `user → assistant → tool → assistant → user → ...`. Two consecutive `assistant` or two consecutive `user` messages breaks ChatML. Every user turn boundary needs a `um()`.
- **Response naturalness**: Template-generated responses like "Done." or "Got it." degrade training. Use pools of 3-5 varied natural sentence variants randomized per iteration. Zero short responses is the target.
- **Energy charge consistency**: The charge value passed to `assess_energy` should be consistent with the stage the model claims to be in. Dream <20, Hope 20-49, Care 50-79, Joy/Trust/Growth 80-100.
- **Tool definitions per example**: Only include tools that are actually used in that example. Including every tool inflates token count. Filter to the subset each conversation needs.
- **Non-tool examples may omit `tools`**: If `"tools"` is present for non-tool examples, use `"tools": []`. Omitting the field entirely is also valid — either is fine as long as it's consistent.
- **Verify the upload**: After uploading, confirm the commit appears in the repo's commit history with the correct message and file size.
