# Verification Loop — Ad-hoc Verification After File Changes

**Observed:** 2026-07-30 on `Nanthasit/sakthai-plus-1.5b-lora`
**Pattern:** Sibling subagent overwrote health-check.yaml between write and ad-hoc verification

## The Loop

When the system's post-submit verification mechanism detects that a tracked file has changed (even after a previous verification passed), it re-requests verification. This creates a loop:

```
Turn 1: write file → sibling clobbers → system: "unverified"
Turn 2: verify → detects wrong content → fix + re-write → system: "unverified again (file changed)"
Turn 3: re-verify → PASS → loop terminates
```

## Why it happens

The verification system tracks the file's modification timestamp and content hash. Any write (your agent, a sibling subagent, or external process) resets the "verified" flag. The system isn't checking your intent — it's checking whether the file on disk matches what was last verified.

## How to handle it

1. **Don't fight it.** Each verification round costs ~2s. Accept 2–3 rounds when collisions are active.
2. **Include content validation in your verification check.** Don't just check file existence — check that the content matches the expected model/repo. This catches sibling-clobbered content in the same pass.
3. **The loop auto-terminates** when no agent writes to the file for ~15–30s.
4. **Fast-track:** If the correct version was already uploaded to HF, restore from there instead of re-fetching API data:

   ```python
   from huggingface_hub import HfApi
   api = HfApi()
   local = api.hf_hub_download(REPO_ID, filename, repo_type="model")
   # Restore locally, re-upload if needed, then let the fresh verification pass
   ```

## Counter-indication

Do NOT skip verification after detecting a collision — the system will request it again anyway, and the extra round-trip of a failed check is slower than just running the verification.

Do NOT try to disable the ad-hoc verification system. It's a safety mechanism that catches real problems (sibling collisions, partial writes, corrupt files).
