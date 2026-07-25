# Full Evaluation Pipeline

Combine speed, BFCL tool-calling, and coding benchmarks into one unified report. Run locally on CPU GGUF models after conversion.

## Signal
Use this when you need to evaluate a GGUF model's real-world performance beyond just BFCL. The full eval covers three dimensions: speed (tok/s), tool-calling accuracy (BFCL), and coding ability (for code-specific models).

## Pipeline

### 1. Speed Benchmark

```bash
LLAMA="/path/to/llama-cli"
MODEL="/path/to/model.gguf"

# One-shot: time inference
time LD_LIBRARY_PATH="$LIB" "$LLAMA" -m "$MODEL" -no-cnv \
  -p "<|im_start|>user\nWrite a short poem about AI<|im_end|>\n<|im_start|>assistant\n" \
  -n 64 -t 2 --temp 0.1 --no-display-prompt

# Count output tokens (rough: wc -w / elapsed seconds)
```

Expected speeds (2-core CPU):
| Model | Tok/s |
|-------|:-----:|
| 0.5B Q4_K_M | ~13 |
| 1.5B Q4_K_M | ~3 |
| Coder 1.5B | ~7 |

### 2. BFCL Tool-Calling (5 tests)

Tools schema (include 4 basic tools):
- `get_weather(location)`
- `search_web(query)`  
- `calculate(expression)`
- `get_time(timezone)`

System prompt with `<tools>` XML tags per ChatML format. Run 5 tests:

| Test | Prompt | Expected |
|------|--------|----------|
| `get_weather` | "Weather in Tokyo?" | `<tool_call>{"name":"get_weather","arguments":{"location":"Tokyo"}}</tool_call>` |
| `search_web` | "Search for AI news" | `<tool_call>{"name":"search_web","arguments":{"query":"AI news"}}</tool_call>` |
| `calculate` | "Calculate 25*4+10" | `<tool_call>{"name":"calculate","arguments":{"expression":"25*4+10"}}</tool_call>` |
| `get_time` | "Time in London?" | `<tool_call>{"name":"get_time","arguments":{"timezone":"London"}}</tool_call>` |
| `irrelevance` | "Who painted Mona Lisa?" | Direct answer, NO tool call |

### 3. Coding Benchmark (5 tests, Coder model only)

| Test | Prompt | Expected indicator |
|------|--------|-------------------|
| Function writing | "Write Python merge two sorted lists" | `def merge_` |
| Debugging | "Fix: def avg(a,b): return a+b/2" | `(a+b)/2` |
| Code explanation | "Explain async/await" | `coroutine`/`async`/`await` |
| Refactoring | "Refactor: if x==1: True else False" | `return x==1` |
| Algorithm | "Find primes up to 100" | `sieve`/`is_prime` |

### 4. Combined Report Format

Save results to `eval/benchmark-full.json`:

```json
{
  "date": "2026-07-25",
  "engine": "llama.cpp (CPU, 2 threads)",
  "benchmarks": {
    "speed_ram": [
      {"model": "0.5B Q4_K_M", "size": "380 MB", "speed": "~13 tok/s"},
      {"model": "1.5B Q4_K_M", "size": "941 MB", "speed": "~3 tok/s"}
    ],
    "coding_coder": {
      "function_writing": "pass",
      "debugging": "pass",
      "score": "5/5"
    },
    "bfcl_tool_calling": {
      "0.5B": {"get_weather": "pass", "search_web": "pass", "score": "3/5"},
      "1.5B": {"get_weather": "pass", "calculate": "pass", "score": "4/5"}
    }
  }
}
```

Push to HF model repos:
```python
api.upload_file(path_or_fileobj='eval_results.json', path_in_repo='eval/benchmark-full.json',
    repo_id='Nanthasit/model-name', repo_type='model')
```
