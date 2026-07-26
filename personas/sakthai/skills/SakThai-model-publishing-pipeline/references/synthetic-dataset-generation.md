# Synthetic Tool-Calling Dataset Generation

Reference for generating synthetic tool-calling fine-tuning datasets, with Hugging Face Hub tools and Growth Cycle integration.

## Workflow

```
Analyze existing dataset → Define tool schemas → Generate synthetic conversations
→ Combine + shuffle → Validate JSONL → Upload to HF
```

## Step 1: Analyze what exists

```python
import json
from collections import Counter

with open("train.jsonl") as f:
    examples = [json.loads(l) for l in f]

with_tools = sum(1 for e in examples if e.get("tools"))
tool_calls = sum(len([
    m for m in e.get("messages", [])
    if m.get("tool_calls")
]) for e in examples)
```

## Step 2: Filter and curate

Only keep examples that teach tool calling. Strip non-tool filler aggressively:

```python
v5_tool = [ex for ex in v5_examples if any(
    msg.get("tool_calls") for msg in ex.get("messages", [])
    if isinstance(msg, dict)
)]
```

Non-tool filler (Swift code, grammar drills, math problems, skill descriptions) dilutes the training signal. In v5, 45% were filler -- removed for v6.

## Step 3: Define tool schemas

Schemas follow the OpenAI/Qwen tool-calling format:

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What it does.",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
        }
    }
}
```

### Tool categories to cover

| Category | Purpose | Example tools |
|----------|---------|---------------|
| **Built-in** | Agent's own capabilities | learn, recall, search, read_file, forget, send_message |
| **Generic** | General function-calling | get_weather, book_appointment, calculate, search_web |
| **Hugging Face Hub** | HF platform workflows | hf_search_models, hf_list_datasets, hf_create_space, hf_run_inference, hf_upload_file, hf_get_model_card, hf_get_pipeline |
| **Growth Cycle** | Agent's operational model | assess_energy, log_transition, capture_lesson, close_cycle |
| **Real SakThai Tools** | Actual Hermes agent tools | terminal, write_file, web_search, delegate_task, session_search, cronjob, supermemory_store |
| **Error/Edge** | Error handling patterns | Model 404, API timeout, rate limit, permission denied, missing params |

## Step 4: Generate synthetic conversations

### Conversation archetypes to include

1. **Full cycle workflow** (Care -> Joy -> Trust -> Growth): Multi-turn with energy assessment, stage transitions, parallel tool calls, cycle closure + lesson capture
2. **Hope stage** (exploration): Research tasks, dataset search, model discovery -- low energy, browsing only
3. **Dream stage** (rest): User tired, energy low -- explicit "no tool call, rest" response
4. **Trust stage** (verification): Session search, validation, checking past work
5. **Growth stage** (learning): Capture lessons, close cycle with metrics
6. **Single-turn** (generic): One search call -> answer
7. **Parallel calls**: Two or more independent tool calls in one turn
8. **Error handling**: 404, rate limit, empty results, auth failure -> graceful fallback
9. **Memory operations**: learn() + recall() + forget()
10. **Delegation**: delegate_task() for subagent work + session_search() to check history

### Volume scaling with batch generators — Response Naturalness Requirement

To reach 600+ examples, use template-based batch generators rather than hand-crafting every example.

**CRITICAL:** Every batch-generated assistant response must be a rich, natural sentence — never a one-word or bare template output. Short responses like "Done.", "Saved.", "Card read." degrade training quality and teach the model to be terse and unhelpful.

```python
def gen_batch():
    out = []
    # Template: single HF search — use varied, natural responses
    for task in ["text-generation", "image-classification", "summarization"]:
        t = tc("hf_search_models", {"task": task, "sort": "likes", "limit": 1})
        out.append(ex(HF, [SYSTEM, um(f"Find {task} models."),
            am(tool_calls=[t]), tr(t["id"], f'[{{"id":"{task}-v1","likes":500}}]'),
            am(content=f"I searched for {task} models. These are the top results by community likes. Let me know if you want details on any.")]))
    # Template: single inference — natural result description
    for model in ["gpt2", "distilgpt2", "phi-3-mini"]:
        t = tc("hf_run_inference", {"model_id": model, "inputs": "test"})
        out.append(ex(HF, [SYSTEM, um(f"Test {model}."),
            am(tool_calls=[t]), tr(t["id"], '{"generated_text":"test output successful"}'),
            am(content=f"Inference on {model} completed. The model processed the input and returned a coherent response without errors.")]))
    return out
```

Batch generators produce 50-250 examples each. Create multiple batches for different categories. The v6 dataset used 4 batch generators totaling 307 new examples.

### Proper tool_call_id chaining

Every tool response must reference the exact ID of the corresponding assistant tool_call. Use helper functions:

```python
cid = 0
def tc(name, args):
    global cid; cid += 1
    return {"id": f"c{cid:04d}", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}

def tr(msg_id, content):
    return {"role": "tool", "content": content, "tool_call_id": msg_id}
```

Then chain naturally:
```python
t1 = tc("assess_energy", {"current_charge": 72})
t2 = tc("hf_search_models", {"task": "text-generation", "sort": "likes", "limit": 3})
# In conversation:
am(tool_calls=[t1, t2]),  # assistant generates both calls
tr(t1["id"], '{"stage":"care"}'),  # response to call 1
tr(t2["id"], '{"models":[...]}'),  # response to call 2
```

## Step 5: Combine with existing data

```python
random.shuffle(existing_tool_examples)
all_train = existing_tool_examples + new_examples
random.shuffle(all_train)
```

Keep ALL existing tool-calling examples -- don't discard them when generating new ones. Volume matters.

## Step 6: Validate

Run a multi-check validation pass:

```python
errors = 0
for i, ex in enumerate(all_train):
    if not isinstance(ex, dict):
        errors += 1; continue
    if "messages" not in ex or "tools" not in ex:
        errors += 1; continue
    for msg in ex["messages"]:
        if "role" not in msg: errors += 1
        if msg.get("tool_calls") and not isinstance(msg["tool_calls"], list):
            errors += 1
        # Check tool responses reference valid call IDs
        if msg.get("role") == "tool" and msg.get("tool_call_id"):
            gen_ids = {tc.get("id","") for m in ex["messages"]
                       for tc in (m.get("tool_calls") or []) if isinstance(tc, dict)}
            if isinstance(msg["tool_call_id"], str) and msg["tool_call_id"] not in gen_ids:
                errors += 1  # Orphan tool response

print(f"Errors: {errors}")
```

### Quality pass: Response naturalness check

Before uploading, run a response quality scan to detect short generic responses that dilute training signal:

```python
SHORT_PATTERNS = {"Done.", "Saved.", "Card read.", "Remembered.",
                  "Need rest.", "Ready to build.", "Time to verify.",
                  "Learning time.", "Cron create done.", "Cron list done.",
                  "Cron pause done.", "Cron resume done.", "Cron remove done."}

def check_response_quality(examples):
    issues = []
    for i, ex in enumerate(examples):
        for msg in ex.get("messages", []):
            if msg["role"] == "assistant" and msg.get("content") and not msg.get("tool_calls"):
                c = msg["content"].strip()
                if c in SHORT_PATTERNS or len(c) < 15:
                    issues.append((i, c))
    return issues
```

Fix any issues found — either replace with a natural response or remove the example. **Zero short responses is the quality target.**

### Trust pass: Inline fix for short responses

If the response quality scanner finds issues, fix them inline rather than regenerating everything:

```python
SHORT_PATTERNS = {"Done.", "Saved.", "Card read.", "Remembered.",
                  "Need rest.", "Ready to build.", "Time to verify.",
                  "Learning time.", "Cron create done.", "Cron list done.",
                  "Cron pause done.", "Cron resume done.", "Cron remove done."}

fixes = {
    "Done.": "Operation completed successfully.",
    "Saved.": "Information saved to long-term memory.",
    "Card read.": "Model card retrieved successfully. Key details noted.",
    "Remembered.": "Fact stored permanently. I will apply it from now on.",
    # ... add more as discovered
}

for ex in train_data:
    for msg in ex["messages"]:
        if msg["role"] == "assistant" and msg.get("content") and not msg.get("tool_calls"):
            c = msg["content"].strip()
            if c in fixes:
                msg["content"] = fixes[c]
```

This approach preserves the example (tool calls, schema references, IDs) while fixing only the response quality.

### Trust pass is non-optional

The Trust stage is not a nice-to-have — it is where quality regressions get caught. In v6:
- First upload had 0 structural errors but 75 short responses from volume-batch templates
- Trust pass removed 156 low-quality examples and fixed the remaining 22 short responses inline
- Final dataset: 0 structural errors, 0 short responses, 663 examples

Without the Trust pass, the dataset would have trained the model to respond with "Done." and "Saved." — actively teaching bad behavior. Always run the full quality check before final upload.

### Key validation stats to report

| Metric | What it tells you |
|--------|-------------------|
| Total examples | Volume -- should exceed prior version |
| Tool schemas count | Breadth of capabilities taught |
| Tool calls / example | Density of tool-use training signal |
| Parallel calls (2+) | Independence / batching ability |
| Multi-turn count | Conversation flow / context retention |
| tool_call_id errors | Data integrity (must be zero for new examples) |
| Zero examples with missing system/user/assistant | Structural completeness |

## Step 7: Upload to Hugging Face

```bash
hf repos create username/dataset-name --type dataset --private
hf upload username/dataset-name data/train.jsonl data/train.jsonl --repo-type dataset
hf upload username/dataset-name data/test.jsonl data/test.jsonl --repo-type dataset
hf upload username/dataset-name README.md README.md --repo-type dataset
```

Always verify with `hf datasets list REPO_ID --tree -R` after upload.

### Dataset card YAML validation

Before uploading the README, validate the YAML `configs` section. HF enforces a strict format:

```yaml
# ✅ Correct
configs:
  - config_name: train
    data_files: data/train.jsonl
  - config_name: test
    data_files: data/test.jsonl

# ❌ Wrong — HF rejects this with "Invalid metadata"
configs:
  - train: data/train.jsonl
  - test: data/test.jsonl
```

If `hf upload README.md` fails with `Invalid metadata` or `"configs[0].config_name" is required`, the YAML format needs the structured config entries shown above. Fix in the local README, re-upload with `hf upload`, then verify with `--tree -R`.

## v6 Case Study (Improved, Jul 12)

| Detail | v6 Improved | Notes |
|--------|-------------|-------|
| Train size | **789** | 663 original + 126 new (multi-turn, rare schema bulking, new tool schemas) |
| Test size | 52 | Preserved from v5 |
| Tool schemas | **81** | 71 original + 10 new Hermes tools (search_files, patch_file, skill_manage, skill_view, todo, memory_store, browser_navigate, browser_click, clarify, vision_analyze) |
| Tool calls | **1,112** | Average 1.4 per example |
| Multi-turn (3+ user turns) | **22** | 5-6 turn research workflows, skill building, browser research, file editing |
| Rare schemas bulked | **11 → 0** | All 11 under-represented schemas brought to 5-10x examples |
| Short responses | **0** | Every assistant response is a natural, complete sentence |
| Orphan IDs (new data) | **0** | Proper chaining on all new examples |

### What made v6 better than v5

1. **More volume but higher density** -- 666 examples, ALL tool-calling (v5 had 300 non-tool filler)
2. **HF-native tools** -- 7 real HF Hub tools with realistic workflows
3. **Growth Cycle integration** -- stage transitions, energy assessment, lesson capture
4. **Real SakThai Hermes tools** -- terminal, write_file, web_search -- actual agent capabilities
5. **Proper ID chaining** -- every tool response matches its exact tool_call_id
6. **Error handling** -- 8 distinct error patterns
7. **Stage refusal** -- model learns when NOT to call tools (low energy -> rest)
8. **Batch generation** -- template-based generators for rapid volume scaling

## Pitfalls

- **Walrus operator in list literals**: Using `:=` to assign tool-call dicts inside a message list literal injects the dict as an extra list element. This breaks the message structure because the tool_call dict lacks a `role` key. **Fix:** assign all `tc()` calls *outside* the list, then reference the variables inside. Bad: `[um("hi"), t1 := tc("search", ...), am(tool_calls=[t1])]` — `t1`'s value becomes a 4th element. Good: `t1 = tc(...)` then `[um("hi"), am(tool_calls=[t1])]`.
- **Multi-turn turn alternation**: Valid training conversations must strictly alternate: **user → assistant(tools) → tool → assistant(response) → user → ...** A sequence of two consecutive assistant messages (`am()`) without an intervening user message or tool response is invalid. When writing multi-turn generators, insert `um()` calls at each turn boundary, not just at the start. The number of `um()` calls equals the number of conversation turns.
- **Unicode surrogates**: Emoji from shell sessions can contain surrogate pairs. Run a clean pass: `obj.encode('utf-8', errors='replace').decode('utf-8')` on every string before writing JSONL. `json.dumps(ensure_ascii=False)` alone is not enough.
- **Write denied in /tmp**: On some systems `write_file` and `hf upload` reject /tmp paths. Write to `~/` first, then `cp` into /tmp, or work entirely under `~/profiles/sakthai/`.
- **Repo listing**: `hf repos list --type dataset` shows ALL repos (including private). `hf datasets list --author X` shows only public. Use `--expand=private` to check visibility. `hf repos create` does NOT accept `--yes`.
- **Non-tool filler dilutes signal**: Strip aggressively. In v5, 45% were non-tool -- removed for v6.
- **Cycle tool order**: `assess_energy` BEFORE first action. `log_transition` at stage boundaries. `close_cycle` must be last.
- **Tool schema collisions**: Inventory all tool names from both sources before combining. Same name, different params = model confusion.
- **Verify uploads**: Always run `hf datasets list REPO_ID --tree -R` after upload.
- **v5 data may have orphan tool IDs**: Some v5 examples have tool responses whose IDs don't match any generated call. These persist unless explicitly cleaned -- validate them separately.
- **Helper function naming**: Keep parameter names consistent in message-building helpers. Using `tool_calls=XXX` everywhere prevents `TypeError` from mismatched keyword arguments.
- **Test set persistence**: Copy test set from the prior dataset version before regenerating, to preserve regression test continuity.
- **Short generic responses in batch generators**: Template loops easily produce short, low-quality responses that degrade training. Every batch must go through the check_response_quality scanner before upload. Zero short responses is the target.
- **Volume vs quality trade-off**: Adding 250+ templated examples to boost volume introduces short generic responses unless each template uses a varied-response pool. Better 500 rich examples than 700 with 200 mechanical ones. For volume, invest in a diverse response pool (5-10 natural variants) randomized per iteration.
- **Pyright type noise**: Iterating over `msg.get("tool_calls", [])` where elements may be strings triggers false-positive LSP errors. Guard with `isinstance(tc, dict)` to be safe at runtime.
- **Dataset card `configs` YAML format**: Bare `key: value` pairs under `configs` (e.g., `- train: data/train.jsonl`) cause HF to reject the README with a cryptic "Invalid metadata" error. The format requires `config_name` + `data_files` sub-fields. Validate locally before the final upload commit.
