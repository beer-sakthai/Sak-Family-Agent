# Kaggle Platform Caching — Notebook Content Doesn't Update

## Problem

You push v2, v3, v4, v5 of the same Kaggle kernel, but EVERY version produces the EXACT same error referencing old code you already changed. You keep debugging the notebook content when the real problem is Kaggle's content cache.

## Root Cause

Kaggle caches the **first-ever notebook content** uploaded for a given kernel slug. Subsequent `kaggle kernels push` calls upload new `kernel-metadata.json` but may NOT propagate the notebook `.ipynb` content changes. The kernel runs the ORIGINAL notebook every time.

## Diagnostic

Compare the error traceback in the kernel output with your local notebook content:

- Error shows old code (`kaggle_secrets.UserSecretsClient().get_secret()`) but your local notebook uses new code (`os.environ.get("HF_TOKEN")`) → **caching confirmed**
- Error references code lines you already deleted/rewrote → **caching confirmed**
- Error shows papermill "No kernel name found" but you added kernelspec to your local notebook → check if the PUSHED notebook actually has kernelspec. Pull it back with `kaggle kernels pull` to verify. If the pulled code IS correct but still errors, the notebook format may be missing Kaggle-native metadata markers — use Fix B (pull existing → replace cells) to get the exact format Kaggle expects.

## Fixes

### Fix A: New slug (recommended)
Create a completely NEW kernel with a different slug. Fresh kernels always get the latest content. The old slug is poisoned.

```bash
# kernel-metadata.json
{
  "id": "username/sakthai-v7-fresh",  # ← new slug
  "title": "SakThai v7 Fresh",        # ← new title
  ...
}
```

### Fix B: Pull → replace → push
```bash
kaggle kernels pull username/old-slug -p /tmp/kernel -m
# Replace CELL CONTENT ONLY in /tmp/kernel/notebook.ipynb
# Keep Kaggle's notebook metadata EXACTLY as-is
kaggle kernels push
```

### Fix C: Manual URL import (bypasses caching entirely)
Import the notebook by URL on kaggle.com — creates a fresh kernel from the URL content. Cache doesn't apply because it's a new kernel.

## Prevention

- **Never push multiple versions of the same slug.** If the first run fails, don't push v2 — create a fresh slug.
- Test notebook content locally before pushing (verify auth cells, pip installs, file paths).
- Keep a `kernel-metadata.json` template with `env_vars` for secrets (avoids Kaggle Secrets dependency).
- The `KAGGLE_API_TOKEN` env var (not `KAGGLE_KEY`) is the modern auth method for CLI v2.2.3+.
