# Model Card Enrichment Patterns

Practical patterns for enriching Hugging Face model cards beyond the basics — benchmarks, multi-language code examples, badges, and YAML tag strategies.

## Fetching Current README

Before enriching, get the current card. Two approaches:

### Reliable (curl)
```bash
curl -s https://huggingface.co/{owner}/{repo}/raw/main/README.md
```
Works without auth, no billing issues. Always available.

### Avoid: web_extract / Firecrawl on HF raw URLs
```python
# ❌ This may fail with 402 Billing Error:
from hermes_tools import web_extract
web_extract(urls=["https://huggingface.co/{owner}/{repo}/raw/main/README.md"])
```
Hermes' `web_extract` (Firecrawl) can return HTTP 402 `Insufficient available balance` errors on `huggingface.co/raw/` URLs. This is a Firecrawl billing issue, not an HF auth issue — the content itself is public. **Always use curl for HF raw content.** The Firecrawl billing failure is transient and depends on the org's subscription balance, not the target site.

### Python API
```python
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id="owner/repo", filename="README.md")
with open(path) as f:
    content = f.read()
```

## Badge Patterns

### Downloads — Daily
```markdown
<img src="https://img.shields.io/huggingface/dd/{owner}/{repo}" alt="Daily Downloads"/>
```

### Downloads — Total (dynamic from API)
```markdown
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A//huggingface.co/api/models/{owner}/{repo}&query=%24.downloads&label=total%20downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
```
URL-encode the API path: `https%3A//huggingface.co/api/models/{owner}/{repo}`, query `%24.downloads` (decoded: `$.downloads`).

### Downloads — Total (shields.io dynamic)
A second badge variant using shields.io's Hugging Face endpoint directly — may render faster than the dynamic-JSON variant:

```markdown
![Downloads](https://img.shields.io/huggingface/models/{owner}/{repo}?style=flat-square&label=Downloads)
```

This uses shields.io's native `huggingface/models` transformer which fetches the model's download count directly. The `?label=Downloads` overrides the default label text; without it the label shows "models" (legacy behavior). Adding `&logo=huggingface` inserts the HF logo icon.

### Downloads — Total (huggingface/dt, simplest)
The simplest total downloads badge — no JSON path, no URL encoding:

```markdown
<img src="https://img.shields.io/huggingface/dt/{owner}/{repo}" alt="Total Downloads"/>
```

This uses shields.io's `huggingface/dt` endpoint (daily-total namespace) which takes the raw repo ID. The badge auto-updates. **Preferred over dynamic-JSON** because:
- No URL-encoding needed (no `%24.query` complexity)
- No billing / API key dependency — shields.io caches HF API data server-side
- Renders faster than dynamic JSON (shields.io native endpoint vs. fetch+eval)
- Works for models AND datasets (dynamic JSON requires different API paths per repo type)

### License Badge
A static badge showing the model's license — helps users quickly identify permissive licenses:

```markdown
![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)
```
Format: `https://img.shields.io/badge/{label}-{message}-{color}`. Replace spaces and special chars with URL encoding (`%20` for space, `%2F` for `/`).

### Model Info Badge
Highlights the model size or distinctive technique at a glance:

```markdown
![Model](https://img.shields.io/badge/model-1.5B%20params-purple?style=flat-square)
![Tech](https://img.shields.io/badge/rsLoRA-All%207%20modules-purple?style=flat-square)
```

### Badge Row Layout
Group compact badges on one line below the title for a clean header:

```markdown
![Downloads](https://img.shields.io/huggingface/models/{owner}/{repo}?style=flat-square&label=Downloads)
![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)
![Model](https://img.shields.io/badge/model-1.5B%20params-purple?style=flat-square)
```

### Custom Tech Badge
For highlighting a specific technique (rsLoRA, QLoRA, etc.):
```markdown
<img src="https://img.shields.io/badge/rsLoRA-All%207%20modules-purple" alt="rsLoRA"/>
```
Format: `{label}-{message}-{color}` with spaces encoded as `%20`.

## YAML Tag Strategies

Beyond the obvious tags, add specificity for discoverability:

```yaml
tags:
  # Base model family (generic → specific)
  - qwen2.5
  - qwen2.5-coder
  - Qwen2.5-Coder-1.5B-Instruct

  # Training method
  - rsLoRA     # lowercase for HF norm
  - rsLoRA     # also as-is for badge rendering
  - QLoRA

  # Languages the model generates
  - python
  - javascript

  # Project brand
  - sakthai
  - house-of-sak
  - family
```

**Why dual naming:** Some tags need lowercase form for HF Hub indexing (`rslor`), while the same term in a badge renders better with correct casing (`rsLoRA`). Both are fine in the YAML array — the Hub normalizes display but indexes both forms.

## Benchmark Comparison Tables

When fine-tuning from a known base model, show a comparison table with honest status markers:

```markdown
| Benchmark | Base Model | Fine-Tune (this model) |
|-----------|:----------:|:----------------------:|
| HumanEval (pass@1) | **74.4%** | *pending* ⏳ |
| MBPP (pass@1) | **71.2%** | *pending* ⏳ |
```

**Patterns:**
- Source base model scores from the base model's own card (or the [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard))
- Mark fine-tune scores as `*pending* ⏳` when not yet evaluated — honest and shows intent
- Add a footnote with evaluation caveats: engine used, format mismatch risks, multi-trial methodology

## Multi-Language Code Examples

For code-generation models, show examples in multiple languages to demonstrate versatility:

### Python (functional, data-focused)
```markdown
### Python — [Task description]

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("owner/repo", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("owner/repo")

messages = [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "Write a Python function that [task]"}
]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=512, temperature=0.2)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```
```

Then show the **expected output** — realistic code the model would generate:

```python
def fetch_model_downloads(model_ids: list[str], delay: float = 0.5) -> dict[str, int]:
    ...
```

### JavaScript (API/server-side)
```markdown
### JavaScript — [Task description]

```javascript
const express = require("express");

// Function the model would generate
function authMiddleware(apiKey) {
  return (req, res, next) => {
    ...
  };
}
```
```

### TypeScript (typed async patterns)
```markdown
### TypeScript — Generic debounce with typings

\`\`\`typescript
// Type-safe debounce for any callback
function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
\`\`\`
```

TypeScript examples show generics, async patterns, and type-safe utility functions — distinct from JS (which focuses on API/server middleware).

### Go (error handling, stdlib)
```markdown
### Go — URL validator with net/url

\`\`\`go
package validator

import (
	"net/url"
	"strings"
)

// IsValidURL checks if a string is a well-formed absolute URL.
func IsValidURL(rawURL string) bool {
	if len(rawURL) > 2048 || len(rawURL) < 5 {
		return false
	}
	parsed, err := url.ParseRequestURI(rawURL)
	if err != nil {
		return false
	}
	return parsed.Scheme != "" && parsed.Host != ""
}
\`\`\`
```

Go examples highlight stdlib usage, error handling patterns, and idiomatic Go conventions. Avoid third-party deps so the example runs anywhere.

### Rust (iterators, ownership)
```markdown
### Rust — Fibonacci sequence iterator

\`\`\`rust
/// A custom iterator that generates fibonacci numbers
struct Fibonacci {
    a: u64,
    b: u64,
    remaining: u32,
}

impl Fibonacci {
    fn new(n: u32) -> Self {
        Self { a: 0, b: 1, remaining: n }
    }
}

impl Iterator for Fibonacci {
    type Item = u64;
    fn next(&mut self) -> Option<Self::Item> {
        if self.remaining == 0 { return None; }
        let current = self.a;
        self.a = self.b;
        self.b = current + self.b;
        self.remaining -= 1;
        Some(current)
    }
}

fn main() {
    let fibs: Vec<u64> = Fibonacci::new(10).collect();
    println!("First 10 fibonacci: {:?}", fibs);
    // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
}
\`\`\`
```

Rust examples focus on iterators, ownership/borrowing patterns, and zero-cost abstractions.

### YAML Widget Examples for Each Language

Code-gen model cards should add widget entries in the YAML frontmatter for EVERY language shown in the body. This enables the inference playground to demo each language:

```yaml
widget:
- text: "Write a Python function to merge two sorted lists"
  output:
    text: 'def merge_sorted_lists(a, b):\n    result = []\n    ...'
- text: "Write a Go function to check if a string is a valid URL"
  output:
    text: 'func isValidURL(rawURL string) bool {\n    ...'
- text: "Create a Rust function to compute fibonacci numbers"
  output:
    text: 'fn fibonacci(n: u32) -> Vec<u64> {\n    ...'
```

**Best practices:**
- Use **different domains** for each language (Python: data processing/CLI scripts; JS: Express middleware/web APIs; Go: stdlib networking; Rust: iterators/zero-cost)
- Include the full inference code at the top so users can run it immediately
- Add temperature guidance: **0.2** for code generation, **0.7** for creative/tool-calling
- Show tool-calling format (XML tags, JSON, etc.) if the model supports it
- **Widget YAML rule:** `output.text` must be a single-quoted string with `\n` for newlines — unquoted values break on em-dashes, backticks, or Unicode

## GGUF / llama.cpp Usage Section

For code-generation models, add a llama.cpp section showing how to run the GGUF locally. This is often the PRIMARY way users interact with small code models (1.5B and below run well on CPU):

```markdown
### 🦙 llama.cpp / GGUF

This model is compatible with llama.cpp via GGUF. Download the GGUF file
from the [Hugging Face repo](https://huggingface.co/{owner}/{repo}/tree/main) and run:

```bash
# Chat mode (interactive)
./llama-cli -m {model-name}-Q4_K_M.gguf \
  --chat-template qwen \
  --temp 0.2 \
  -p "Write a Python function to reverse a linked list"

# One-shot generation (stateless)
./llama-cli -m {model-name}-Q4_K_M.gguf \
  --temp 0.2 \
  -n 512 \
  -p "Write a Rust function to compute SHA-256"
```
```

**Best practices:**
- Specify `--chat-template qwen` for Qwen-based models, `--chat-template chatml` for ChatML-trained models
- Always set `--temp 0.2` for deterministic code output
- Show two modes: interactive chat AND one-shot generation
- Add a GGUF badge to the badge row: `<img src="https://img.shields.io/badge/GGUF-llama.cpp-ff69b4" alt="GGUF"/>`
- If the card has no GGUF section, users assume the model only works via the Inference API or transformers — adding it doubles the practical user base

## Inference YAML Block

Configure the inference playground widget on the HF model page with sensible defaults:

```yaml
inference:
  parameters:
    temperature: 0.2
    top_p: 0.95
    max_new_tokens: 2048
  widget:
    - text: "Write a Python function to merge two sorted lists"
      output:
        text: 'def merge_sorted_lists(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] < b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result'
```

**Key rules:**
- `parameters` block sets the playground sliders — temperature, max_new_tokens, top_p, top_k are common
- `widget` is an array; each entry must have `text` (prompt) and `output.text` (expected output)
- `output.text` must be SINGLE-QUOTED with `\n` for newlines — double-quoted or unquoted values break on special chars
- One widget entry minimum; two to three is typical (one per language or task type)

## Tech Spec Table

For fine-tunes/merges, compare against the predecessor:

```markdown
| Leap | v1 (previous) | v2 (this model) |
|------|:-----------:|:--------------:|
| LoRA method | Standard LoRA | **rsLoRA** |
| Target modules | 4 (q, k, v, o) | **All 7** (+ gate, up, down) |
| Training data | v7 only (2,003) | **v7 + v8** (2,962 — published as `sakthai-combined-v10`) |
```

## Uploading the Updated Card

### Preferred: Python HfApi (cron-safe)
```python
from huggingface_hub import HfApi
import os

# Read token from HF cache (works when $HF_TOKEN not set)
token = open(os.path.expanduser("~/.cache/huggingface/token")).read().strip()

api = HfApi(token=token)
url = api.upload_file(
    path_or_fileobj="path/to/updated-README.md",
    path_in_repo="README.md",
    repo_id="owner/repo",
    commit_message="docs: update model card with benchmarks, code examples, badges"
)
print("Commit:", url)
```

### Alternative: curl (fragile — prefer Python)
```bash
# ⚠️ POST/PUT /api/repos/{repo}/content does NOT work
# Use `hf upload` or Python HfApi instead
```

## Verification Checklist

After uploading, verify the card was correctly updated:

- [ ] Raw README fetch works: `curl -s https://huggingface.co/{owner}/{repo}/raw/main/README.md | head -5`
- [ ] All badges render (check raw URL for badge markdown)
- [ ] YAML frontmatter is valid (check with `python3 -c "import yaml; ..."`)
- [ ] Benchmark table is intact
- [ ] Code examples have correct syntax highlighting markers
- [ ] Family cross-links are correct
- [ ] License and base_model unchanged (unless intended)
