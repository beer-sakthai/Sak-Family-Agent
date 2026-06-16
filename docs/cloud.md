# Cloud runtime (Google ADK / Vertex AI) — roadmap stub

The `sakthai.cloud` package is a **skeleton** for deploying SakThai's memory
agent to Google Cloud via [Google ADK](https://google.github.io/adk-docs/) and
Vertex AI. It is intentionally *not* a wired-up deployment: it lets you describe
a cloud agent, check whether the host is deploy-ready, and scaffold a manifest —
without pulling the heavy Google dependencies into local use or CI.

This corresponds to roadmap item **Phase 10.4** (basic cloud runtime stubs). The
original `SakThai-Agent` shipped a full `app/` ADK bundle; v2 re-derives only the
skeleton, so the cloud stack stays optional and the core package stays light.

## Design

- **No import-time Google dependency.** Importing `sakthai.cloud` never imports
  `google-adk`. `runtime.adk_installed()` probes for it with
  `importlib.util.find_spec`, and `build_adk_agent()` imports it lazily, raising
  `CloudRuntimeError` with an install hint when the `cloud` extra is absent.
- **The memory store is still the seam.** `cloud/tools.py` exposes
  `learn_fact` / `recall_memory` / `search_memory` / `forget_fact` as plain typed
  functions (the shape ADK wants), each going through `MemoryStore`.
- **Config lives in `config.py`.** Project, region, Vertex toggle, and staging
  bucket are read from the standard Google env vars via helpers in `config.py`.

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project id | — |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Route through Vertex AI when truthy | unset (off) |
| `GOOGLE_CLOUD_STAGING_BUCKET` | `gs://` bucket for staging | — |

## Install

```bash
pip install -e ".[cloud]"   # google-adk, google-cloud-aiplatform, google-cloud-logging
```

## CLI

```bash
sakthai cloud status                 # readiness report (no network)
sakthai cloud manifest               # print the deployment manifest (YAML)
sakthai cloud scaffold [DIR]         # write manifest.yaml into DIR (default: ./cloud-deploy)
sakthai cloud build                  # build the ADK agent (requires the cloud extra)
```

`sakthai cloud status` reports three signals — the `cloud` extra installed, a
project configured, and a Google credential resolvable (Vertex, or a Gemini
token/key) — and is only "ready" when all three hold.

## What's deliberately out of scope (for now)

- Actual `agents-cli` / Vertex deployment execution.
- Telemetry / Cloud Logging wiring.
- A synced cloud package bundle (v2 has no `app/` tree by design).

These remain on the roadmap; the stub gives a stable surface to build them on.
