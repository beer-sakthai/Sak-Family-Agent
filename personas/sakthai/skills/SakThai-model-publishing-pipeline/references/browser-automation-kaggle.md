# Browser Automation for Kaggle (via agent-browser / Playwright)

When CLI push keeps failing with papermill errors, or when the Kaggle API doesn't support the action needed, use **browser automation** to drive Kaggle's web UI.

## Prerequisites

- Chrome installed: `npx agent-browser install` (or `agent-browser install --with-deps` for shared libs)
- Location: `/opt/data/.agent-browser/browsers/chrome-*`

## When to use

1. **Kaggle CLI push keeps failing** with papermill `No kernel name found` errors (even with workaround A — native format pull-then-push)
2. **Kaggle API / Composio tools lack push/run capability** (Composio has LIST, PULL, STATUS but no PUSH)
3. **The user explicitly said "I will never run anything"** — manual URL import is not acceptable

## Steps

### 1. Install Chrome (one-time)
```bash
npx agent-browser install
# If shared library errors:
npx agent-browser install --with-deps
```

### 2. Navigate to Kaggle
```python
browser_navigate("https://www.kaggle.com/account/login?phase=emailSignIn")
```

### 3. Auth approach
Kaggle's web UI requires Google/GitHub/email OAuth login. The browser automation approach works when:
- Session cookies are cached (already logged in)
- Or using the API token approach via CLI instead

**Known limitation:** If Kaggle requires OAuth web login, browser automation may not be able to authenticate without credentials. In that case, fall back to CLI push with KAGGLE_API_TOKEN env var (see `kaggle-training-watchdog.md`).

## Alternative: Python API bypass (when browser auth blocks)

If browser auth is blocked, use the Kaggle Python API directly (not CLI) to push a kernel with minimal metadata:

```python
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
# api.kernels_push() requires a folder path, not inline dict
```

But this has the same papermill issue as CLI. The most reliable approach remains:
1. Pull native kernel: `kaggle kernels pull <slug> -p <dir> -m`
2. Replace cells (not metadata)
3. Push with `KAGGLE_API_TOKEN` (not `KAGGLE_KEY`)

## Pitfalls

- **Chrome not found**: Run `agent-browser install` before navigating
- **OAuth wall**: Kaggle web login cannot be bypassed programmatically without credentials
- **Session timeout**: Browser sessions reset between Hermes turns — navigation state is not preserved
