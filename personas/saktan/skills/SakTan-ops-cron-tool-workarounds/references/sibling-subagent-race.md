# Sibling Subagent Race on Shared Output Paths

**Context:** In cron mode, multiple sibling subagents can write to the same file path simultaneously. Each agent reads the file, modifies it, and writes back — but without coordination, the last writer wins and all other agents' work is lost.

## Symptoms

- You write content (e.g., a health check YAML), but `read_file` later shows different content from a different model
- Verification scripts fail because expected keys are missing — the file now has another agent's content
- File size changes between your read and write operations
- System warning: `"was modified by sibling subagent '<id>' at <time> — after this agent's last read at <time>"`

## Root Cause

Multiple cron jobs targeting different models all write their output to the same shared file path (e.g., `.eval_results/health-check.yaml`). They run concurrently with no locking, no coordination, and no awareness of each other's writes.

This differs from the partial-read overwrite trap (covered in SKILL.md) — the sibling race happens even when every agent reads the full file before writing. It's a pure concurrent-writer conflict.

## Fix Strategies

### Strategy A — Unique filenames (preferred)

Use model-specific or task-specific paths so siblings never collide:

```
.eval_results/health-check-<model-shortname>.yaml
```

Good examples:
- `.eval_results/health-check-lora-adapter.yaml`
- `.eval_results/health-check-vision-7b.yaml`
- `.eval_results/health-check-context-1.5b.yaml`

Bad (generic): `.eval_results/health-check.yaml` — every sibling writes here.

### Strategy B — Verify against remote artifact

When you MUST use a shared path (e.g., system hard-codes the filename):

1. **Upload first** — `upload_file()` / `hf upload` is atomic at the API level. Your content reaches HF correctly even when the local file is being overwritten.

2. **Verify against remote** — fetch the raw URL and confirm YOUR markers:
   ```bash
   curl -s "https://huggingface.co/<user>/<repo>/raw/main/.eval_results/health-check.yaml" | grep -c "your-unique-marker"
   ```
   If the marker is present, the upload succeeded regardless of local file state.

3. **Ignore the local file** — it's unreliable. The remote HF artifact is the source of truth.

4. **"No files modified" is not an error** — If `upload_file()` returns `"No files have been modified since last commit. Skipping to prevent empty commit."` but gives you a commit URL, the content was already correct. No action needed; the commit URL points to the current HEAD.

### Strategy C — Atomic inline write+upload (high-frequency race)

When siblings overwrite the local file within *seconds* of every write — even Strategy B fails because the local file is unusable as a source:

1. **Skip the local file entirely.** Construct your YAML/JSON content as an inline Python string — no write_file, no local file at all.

2. **Upload in-memory bytes in one `uv run python3` command:**

   ```python
   uv run python3 -c "
   from huggingface_hub import HfApi
   import os

   yaml_content = '''# Health check report for owner/model
   model:
     id: owner/model
     metrics:
       downloads: 0
       likes: 0
   '''

   api = HfApi()
   api.upload_file(
       path_or_fileobj=yaml_content.encode(),  # in-memory bytes — no local file
       path_in_repo='.eval_results/health-check.yaml',
       repo_id='owner/model',
       token=os.environ['HF_TOKEN'],
       commit_message='health-check: nightly cron'
   )
   print('Uploaded from inline, no local file involved')
   "
   ```

3. **Verify against remote** — same as Strategy B step 2: `curl -s <raw-url> | head -3` confirming your model ID.

**Key difference from Strategy B:** Strategy B writes to a local file first, then uploads. Strategy C constructs content entirely in memory — the race on local disk is irrelevant because there's no local file to race on.

**Pitfall — bare `python3` lacks `huggingface_hub`:** Always use `uv run python3` (not plain `python3`) for `HfApi` operations. The system Python does not have the huggingface_hub package installed; only the uv-managed environment does. Verified 2026-07-30: `python3 -c "from huggingface_hub import HfApi"` raised `ModuleNotFoundError`.

### Detecting the race in tool output

After every `write_file` call, scan the tool response for this warning pattern:

```
_warning: "... was modified by sibling subagent '<id>' at <time> — after this agent's last read at <time>"
```

If present, another agent wrote to the same path between your last read and your write. Your write may have overwritten their content (or vice versa). After uploading, re-read the remote artifact to confirm YOUR content is correct.

## In Practice — Real Incident (2026-07-30)

During the 2026-07-30 cron health eval cycle:

1. **SakThai** wrote a health check for `Nanthasit/sakthai-plus-1.5b-lora` (LoRA adapter) → uploaded to HF ✅
2. A sibling agent overwrote the local `.eval_results/health-check.yaml` with context-models health check
3. **SakThai** re-wrote the LoRA check → uploaded again (HF reported "No files modified" — already correct)
4. Another sibling overwrote with TTS model check
5. **SakThai** re-wrote again → verified against remote → LoRA check was correct on HF the whole time

**Lesson:** The remote HF artifact never had the race — only the local file did. Always verify against the remote when siblings are active.

## Related

- Main SKILL.md § "Write-file overwrite trap" — covers the partial-read → overwrite variant (different root cause)
- `references/security-scanner-blocked-patterns.md` — covers cron-mode tool restrictions (separate issue)
