# Mintlify Documentation Research Pattern

> Technique discovered 2026-07-30 during SGLang research cron run. Useful for any session needing to study mintlify-hosted documentation (common in HF ecosystem: vLLM, Gradio, SGLang, smolagents, etc.).

## How Mintlify Docs Work

Mintlify (mintlify.com) is a documentation platform used by many open-source AI projects. It serves both:
- **Dynamic HTML** (JS-rendered, requires browser)
- **Raw markdown** (served at `*.md` URLs)

## The `llms.txt` Index

Every mintlify doc site has a `llms.txt` at its root that lists **every page** in the documentation:

```
https://docs.example.com/llms.txt
```

This file contains all pages with their titles and paths. It's the single best starting point for understanding the full scope of a project's docs.

```bash
curl -sL "https://docs.example.com/llms.txt" | grep "docs/"
```

## Fetching Raw Markdown

Append `.md` to any doc page path to get the raw markdown source:

```bash
# Instead of browser_navigate (slow, ~5-10s):
# https://docs.example.com/docs/advanced_features/model_loading

# Use curl with .md suffix (fast, ~0.5s):
curl -sL "https://docs.example.com/docs/advanced_features/model_loading.md" > /tmp/page.md
```

### Caveats

- The `.md` path returns markdown with Mintlify-specific JSX tags (`<Note>`, `<Card>`, `<Tab>`, `{props.foo}`) — not clean GitHub-flavored markdown. Extract info from the plain-text parts.
- The first 3 lines are always a documentation index banner — skip them:
  ```
  > ## Documentation Index
  > Fetch the complete documentation index at: https://docs.sglang.io/llms.txt
  > Use this file to discover all available pages before exploring further.
  ```
- Use `tail -n +4` to strip the banner, or ignore it visually.

## Full Research Workflow

### Phase 1: Discover scope
```bash
# 1. Get the full doc index
curl -sL "https://docs.project.com/llms.txt" > /tmp/llms.txt

# 2. Find all "docs/" pages (structured docs, not cookbooks)
grep "docs/" /tmp/llms.txt | sort

# 3. Identify key pages by title/description
grep "model_loading\|server_arguments\|quickstart\|quantization" /tmp/llms.txt
```

### Phase 2: Fetch key pages in parallel
```bash
# Fetch multiple pages simultaneously
curl -sL "https://docs.project.com/docs/get-started/quickstart.md" > /tmp/quickstart.md &
curl -sL "https://docs.project.com/docs/advanced_features/model_loading.md" > /tmp/model_loading.md &
curl -sL "https://docs.project.com/docs/advanced_features/server_arguments.md" > /tmp/server_args.md &
wait

# Check sizes to confirm content was received
wc -c /tmp/quickstart.md /tmp/model_loading.md /tmp/server_args.md
```

### Phase 3: Extract actionable knowledge
```bash
# Get installation commands
grep -A 5 "pip install\|uv pip\|docker run" /tmp/quickstart.md | head -30

# Get key server args
grep "| \`--" /tmp/server_args.md | head -20

# Get model loading formats
grep -A 2 "^| \`" /tmp/model_loading.md | head -40
```

### Phase 4: Create skill
Pipe research findings into a structured SKILL.md with:
- Overview + HF integration points
- Installation section
- Key API/syntax tables
- Advanced features
- Troubleshooting
- See Also with official doc links

Include a `references/research-log.md` in the new skill's directory recording what pages were fetched, what was found useful, and any gotchas encountered.

## Why This Beats Browser Navigation

| Approach | Time | Reliability |
|----------|------|-------------|
| `browser_navigate` + scroll + snapshot | ~8-15s per page | Medium — may hit JS-rendering limits or snapshot truncation |
| `curl` + `.md` suffix | ~0.5s per page | High — raw markdown is always text |
| `llms.txt` index | ~0.3s | High — single file, all pages listed |

## Examples of Mintlify Projects

- SGLang: https://docs.sglang.io/
- vLLM: https://docs.vllm.ai/ (uses Sphinx but similar patterns apply)
- Gradio: https://www.gradio.app/docs
- smolagents: https://huggingface.co/docs/smolagents (HF docs, different platform)
- OpenRouter: https://openrouter.ai/docs
