# HF API Research — curl Fallbacks

When Composio web_search / EXA_SEARCH tools are unavailable (Enhanced Controls, rate limits, etc.), use direct `curl` to HF REST APIs and GitHub for research. These patterns also avoid tirith pipe-to-interpreter security blocks by saving to files first.

## HF Models API (search + sort)

```bash
curl -s "https://huggingface.co/api/models?search=<term>&sort=downloads&direction=-1&limit=20" -o /tmp/hf_models.json
# Then read with read_file tool — never pipe to python3
read_file(path="/tmp/hf_models.json")
```

**Useful params:**
- `search=<term>` — keyword search
- `sort=downloads|likes|trending|created` — sort order
- `direction=-1|1` — descending/ascending
- `limit=N` — results per page (max 100)
- `pipeline_tag=image-to-3d` — filter by pipeline type
- `library_name=diffusers` — filter by library

## HF Spaces API (search + sort)

```bash
curl -s "https://huggingface.co/api/spaces?search=<term>&sort=likes&direction=-1&limit=10" -o /tmp/hf_spaces.json
read_file(path="/tmp/hf_spaces.json")
```

**Response fields:** `id`, `likes`, `sdk` (gradio/docker/static), `tags`

## HF Course/Docs Content (via GitHub raw)

The official HF courses are open-source on GitHub. Use raw URLs for fast, HTML-free content:

```bash
# Course unit content
curl -sL "https://raw.githubusercontent.com/huggingface/ml-for-3d-course/main/units/en/unit<N>/<filename>.mdx" -o /tmp/course_unit.md

# Diffusers pipeline docs
curl -sL "https://raw.githubusercontent.com/huggingface/diffusers/main/docs/source/en/api/pipelines/<name>.md" -o /tmp/pipeline.md

# To list files in a directory (discover filenames)
curl -s "https://api.github.com/repos/huggingface/<repo>/contents/<path>" -o /tmp/gh_contents.json
```

## Common HF Course Repos

| Course | GitHub Repo | Units Path |
|--------|-------------|------------|
| ML for 3D | `huggingface/ml-for-3d-course` | `units/en/unit<N>/` |
| Diffusion | `huggingface/diffusion-course` | — |
| Audio | `huggingface/audio-course` | — |
| LLMs | `huggingface/llm-course` | — |
| Agents | `huggingface/agents-course` | — |
| Smol | `huggingface/smol-course` | — |
| Deep RL | `huggingface/deep-rl-course` | — |

## Tirith Security — Pipe Avoidance

The tirith security layer blocks `curl | python3` patterns. **Never pipe HTTP output to an interpreter.** Instead:

```bash
# ❌ Blocked: curl | python3
# ✅ Works: save to temp file, read separately
curl -s "https://api.url.com/endpoint" -o /tmp/research_data.json
# Then use read_file or process(action='log') to access the data
```

This applies to any `curl | python3`, `curl | jq`, or `curl | sh` pattern.

## Common HF API Endpoints Quick Reference

| Endpoint | Purpose |
|----------|---------|
| `huggingface.co/api/models?search=X` | Search models |
| `huggingface.co/api/models/{id}` | Single model info + cardData |
| `huggingface.co/api/spaces?search=X` | Search Spaces |
| `huggingface.co/api/trending` | Trending models |
| `huggingface.co/{id}/raw/main/README.md` | Raw model card text |
| `api.github.com/repos/huggingface/{repo}/contents/{path}` | GitHub directory listing |
| `raw.githubusercontent.com/huggingface/{repo}/main/{path}` | GitHub raw file |
