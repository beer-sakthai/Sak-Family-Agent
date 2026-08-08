---
name: SakSee-web-deploy-risk-guide
description: "Safely deploy, verify, and recover static websites."
---

# Web Deploy Risk Guide

Deploying a static site through GitHub + Vercel looks simple, but a single bad commit can render the site blank without an error page. This skill covers the full loop: pre-flight checks, safe commits via Composio, post-deploy verification, and fast recovery when content is corrupted.

## When to Use

- Before pushing HTML/CSS/JS changes to a live site.
- After a Vercel deploy looks wrong, blank, or compressed-garbled.
- When committing through Composio MCP tools instead of local git.
- After replacing placeholder content in automated commits.

## Prerequisites

- Active Composio connection to GitHub (`github` toolkit status ACTIVE).
- Vercel project linked to the target GitHub repo.
- Local copy of the site files with the intended changes applied.
- `MCP_COMPOSIO_API_KEY` available in the environment.

## How to Run

1. Stage the intended changes locally and run the verification script via `terminal`.
2. Commit through the Composio MCP endpoint using `execute_code` to avoid literal placeholder strings.
3. Verify the live site via `curl`, `browser_navigate`, and the verification script.
4. If the site is blank or corrupted, force-overwrite the bad files with the same MCP workflow.

## Quick Reference

| Check | Command / Tool |
|-------|----------------|
| GitHub raw HTML | `curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/index.html \| head -10` |
| Vercel headers | `curl -sI https://<site>.vercel.app/` |
| Full response body | `execute_code` with `requests.get(...).content[:200]` |
| DOM title | `browser_console` expression: `document.title` |
| Safe MCP commit | `execute_code` calling `https://connect.composio.dev/mcp` with JSON-RPC |

## Procedure

1. **Validate local files before committing**
   - Use `read_file` on `index.html` to confirm it starts with `<!DOCTYPE html>`.
   - Check that binary assets (PNG, SVG) are real files, not placeholder strings.

2. **Run the pre-deploy verification script**
   - Invoke via `terminal`:
     ```bash
     python3 scripts/verify-deploy.py \
       --owner beer-sakthai \
       --repo house-of-sak \
       --url https://house-of-sak.vercel.app/ \
       --local index.html
     ```
   - The script exits non-zero if the local file is not valid HTML.

3. **Commit safely via Composio MCP**
   - Do NOT paste file content directly into `mcp_composio_COMPOSIO_MULTI_EXECUTE_TOOL` arguments — that path is prone to placeholder-string accidents.
   - Use `execute_code` to read local files into variables and POST to `https://connect.composio.dev/mcp`:
     ```python
     import requests, json, uuid, base64
     API_KEY = "<MCP_COMPOSIO_API_KEY>"
     url = "https://connect.composio.dev/mcp"
     session_id = str(uuid.uuid4())
     headers = {
         "x-consumer-api-key": API_KEY,
         "Content-Type": "application/json",
         "Mcp-Session-Id": session_id,
         "Accept": "application/json, text/event-stream"
     }
     requests.post(url, headers=headers, json={
         "jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "hermes", "version": "1.0"}}
     }, timeout=10)
     # ... build multi_execute payload with real file contents ...
     ```
   - Use `GITHUB_COMMIT_MULTIPLE_FILES` inside `COMPOSIO_MULTI_EXECUTE_TOOL`.

4. **Verify the deployed site**
   - Check GitHub raw content first:
     ```bash
     curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/index.html | head -5
     ```
   - Then check Vercel response:
     ```bash
     curl -sI https://<site>.vercel.app/
     ```
   - Finally use `browser_navigate` to https://<site>.vercel.app/ and `browser_console` to inspect `document.title` and `document.body.innerHTML`.

5. **Recover from a bad commit**
   - If GitHub raw content shows a diff stat, placeholder, or binary garbage, repeat step 3 with `force: true` and the correct file contents.
   - Do not rely on local `git push` unless you have a valid GitHub token or SSH key; the Composio connection is the safer credential path.

## Pitfalls

- **Brotli compression in browser tool.** Vercel may serve `Content-Encoding: br`. The browser snapshot can look garbled even when the page is fine — trust `curl`/raw GitHub over the snapshot text in that case.
- **Placeholder literal strings.** Passing `PLACEHOLDER_INDEX_HTML` as the `content` argument of a Composio tool will write that literal string into the repo. Always load content from files in code.
- **No error on blank page.** A bad `index.html` still returns HTTP 200 because Vercel serves it as HTML. You must inspect the body, not just the status.
- **Stale CDN cache.** `Age: 0` and `X-Vercel-Cache: MISS` mean fresh. If you see `HIT`, wait or add a cache-busting query parameter.
- **Composio v2 API is deprecated.** Direct `backend.composio.dev/api/v2/actions/execute` returns 410. Use the MCP JSON-RPC endpoint instead.

## Verification

Run the verification script after every deploy and confirm the output ends with:

```
PASS: deployed content matches local content
```

If it prints `FAIL`, re-run the safe-commit procedure in step 3 before declaring the deploy complete.
