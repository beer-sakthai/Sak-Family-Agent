---
name: SakThai-hf-hub-cli-rebuilt
author: SakThai
license: MIT
description: "This skill covers the rebuilt hf CLI introduced in huggingface_hub v1.22.0+ and the new features shipped in v1.22, v1.23, and v1.24: Sandboxes, faster tree-cached downloads, Space templates, Job naming, CLI extensions, and the Click-based CLI framework."
version: 1.0.0
category: mlops
tags: [huggingface-hub, cli, sandbox, jobs, spaces-templates]
requires: huggingface_hub >= 1.22.0
---

# hf-hub-cli-rebuilt

**Area:** Hugging Face Hub / CLI
**Tags:** `huggingface-hub`, `cli`, `sandbox`, `jobs`, `spaces-templates`, `v1.22`, `v1.23`, `v1.24`

## Purpose

This skill covers the rebuilt `hf` CLI introduced in huggingface_hub v1.22.0+ and the new features shipped in v1.22, v1.23, and v1.24: Sandboxes, faster tree-cached downloads, Space templates, Job naming, CLI extensions, and the Click-based CLI framework.

## When to Use

- User asks about the `hf` CLI, new commands, or CLI changes
- User wants to spin up Sandboxes (`Sandbox.create`, `SandboxPool`)
- User wants to create Spaces from official templates
- User wants to name Jobs or use scheduled Jobs
- User asks about "what's new" in huggingface_hub v1.22–v1.24

## Key References

- **CLI Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/cli
- **CLI Reference:** https://huggingface.co/docs/huggingface_hub/en/package_reference/cli
- **Sandboxes Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/sandbox
- **Jobs Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/jobs
- **Space Templates:** `hf spaces templates` CLI or `list_space_templates()` API
- **Learnings:** `references/hf-learnings.md`

## `hf upload` — Uploading Files (GGUF, safetensors, README)

The `hf upload` command handles both LFS and regular files correctly. **Do NOT use `upload_file()` from the Python API for large files** — it creates empty LFS stubs (134-byte git pointers) without uploading the actual blob.

```bash
# Syntax: hf upload REPO_ID LOCAL_PATH PATH_IN_REPO [--repo-type TYPE] [--commit-message "msg"]
# Positional args, not flags: REPO_ID then LOCAL_PATH then PATH_IN_REPO

# Upload GGUF (LFS)
hf upload Nanthasit/my-model ./model.q4_k_m.gguf model.q4_k_m.gguf --repo-type model

# Upload README.md (regular file)
hf upload Nanthasit/my-model ./new_readme.md README.md --commit-message "docs: enrich card"
```

**Pitfall:** `HfApi.upload_file()` from Python shows 100% progress but silently produces empty files (confirmed on huggingface_hub 1.24.0). Always prefer `hf upload` CLI for files >50MB. The `hf upload` command uses the `hf://` protocol internally and properly handles LFS blob upload to HF's Xet storage backend.

**Pitfall — argument order:** `hf upload REPO_ID LOCAL_PATH REMOTE_PATH` — NOT `--path` or `--local-path` flags. The CLI rejects named `--path`/`--local-path` options with "No such option" error.

**Return value:** Prints `url=https://huggingface.co/<repo>/commit/<sha>` on success.

## Verification — Testing GGUF/LFS Uploads

The HF Hub API `/api/models/<id>` siblings endpoint may show `size=0` and `lfs=False` for files that were actually uploaded correctly. **This is a known display issue, not a file problem.**

### Reliable verification: Range download test

```bash
# Download first 1KB of the file — returns HTTP 206 if LFS blob exists
curl -sL -r 0-1023 -o /dev/null -w "HTTP %{http_code} | %{size_download} bytes" \
  "https://huggingface.co/<user>/<repo>/resolve/main/<filename>"
# Expected: HTTP 206 | 1024 bytes
```

HTTP 206 with content = file is properly stored. HTTP 404 = file doesn't exist or upload failed.

### Full download test
```bash
curl -sL -o /dev/null -w "%{http_code}" \
  "https://huggingface.co/<user>/<repo>/resolve/main/<filename>"
# May return 200 even for LFS files (redirects to CDN)
```

## `hf models list` / `hf datasets list` — Quick Ecosystem Snapshots

These commands list all repos by an author in TSV format, useful for checking download counts across the ecosystem:

```bash
# List all models by author
hf models list --author Nanthasit

# List all datasets
hf datasets list --author Nanthasit
```

**Output format:** Tab-separated columns: `id\tcreated_at\tdownloads\tlibrary_name\tlikes\tpipeline_tag\tprivate\ttags\ttrending_score`

**Pitfall:** The commands only accept `--author` not `--owner`. Error message is "No such option" if wrong flag used.

**Pitfall:** The output is never empty — but `--json` flag is not supported. To get JSON, pipe through `python3 -c "..."` or use the REST API directly:

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1"
```

**Usage for ecosystem maintenance:** Pipe to `grep -v private` to filter only public models, or sort by downloads to find low-traffic promotion targets.

## HF Spaces — Free Tier Constraints

| Space Type | SDK | Cost | Interactive? |
|------------|-----|------|-------------|
| **Static** | `static` (HTML/CSS/JS) | Free ✅ | Read-only showcase |
| **Gradio** | `gradio` | **PRO required** ($9/mo) | Interactive ❌ |
| **Docker** | `docker` | **PRO required** | Custom ❌ |

**Implication for zero-cost projects:** Only static Spaces are free. Interactive demos (Gradio/Docker) require a PRO subscription. For showcasing models without budget, build static HTML Spaces with live download badges and example outputs that fetch data from the HF API.

## Dependencies

- huggingface_hub >= 1.22.0
- For standalone `hf` CLI: `curl -fsSL https://huggingface.co/hf/install | bash`
