---
name: run-sakthai-skills
description: Build, run, smoke-test, and drive sakthai-skills — the root ~/ Node/TS package (Gemini agent loop + skills registry behind an HTTP server). Use when asked to run sakthai-skills, start its server, test the agent loop or a skill, or verify the root TS code works.
---

`sakthai-skills` is the Node/TS package at the workspace root (`~/`): an HTTP
server (`src/index.ts`, endpoints `/health` and `POST /chat`) that runs a
Gemini tool-calling agent loop (`src/agent.ts`) over a pluggable skills
registry (`src/skills/registry.ts`; `calculate` is the one built-in skill).
Drive all of it with `.claude/skills/run-sakthai-skills/driver.mjs` — it
exercises the agent loop **offline with a mocked Gemini client** plus the
server endpoints, so no API key or network is needed.

All paths are relative to `packages/sakthai-skills/`.

## Prerequisites

Node ≥ 24 with npm (verified with v24.18.0 / npm 11.16.0). No system packages.

## Build

```bash
npm install      # only on a clean checkout
npm run build    # tsc → dist/ (entry lands at dist/src/index.js, NOT dist/index.js)
```

## Run (agent path) — the driver

```bash
node .claude/skills/run-sakthai-skills/driver.mjs
```

It prints PASS/FAIL per check and exits non-zero on any failure. Checks:

1. **Direct invocation, offline** — loads `dist/src/agent.js`, injects a mock
   `GoogleGenAI` client, and runs the full tool-call cycle: model emits a
   `functionCall` for `calculate`, the skill executes, the tool response is
   fed back, final text returned. Also verifies an unknown skill name comes
   back as a tool *error*, not a crash.
2. **Server smoke** — spawns `node dist/src/index.js` on port 8199 (override
   with `DRIVER_PORT`), then checks `GET /health` → `{"status":"ok"}`,
   `POST /chat` with no prompt → 400, unknown route → 404, and kills it.
3. **Live `/chat`** — only if `GEMINI_API_KEY` is set; otherwise SKIP.

To test a **new skill** the same way, mirror the driver's mock-client pattern:
`require` the compiled skill module (its `registerSkill` call runs on import),
then call `runAgentLoop(mockAi, ...)` where the mock's first response emits a
`functionCall` naming your skill.

## Run (human path)

```bash
PORT=8123 node dist/src/index.js   # logs "Server is listening on port 8123"
curl http://127.0.0.1:8123/health
```

`POST /chat` with a real prompt needs `GEMINI_API_KEY`; see Gotchas. Ctrl-C to
stop.

## Test

```bash
npm test             # Jest via ts-jest; 4 suites / 12 tests, ~10 s
npm test -- skills   # single file/pattern
```

## Gotchas

- **`/chat` without `GEMINI_API_KEY` silently falls back to Vertex AI ADC**
  (`src/index.ts`) using the hardcoded project `supple-cosine-470306-d4`. On
  this machine that returns a 500 wrapping a 403
  `"Lightning dunning decision is deny"` — the GCP project is billing-blocked.
  The gemini-CLI OAuth creds in `~/.gemini/` do **not** help; the SDK wants an
  API key or ADC. Health/validation endpoints work fine without any creds.
- **Compiled entry is `dist/src/index.js`**, because `tsconfig.json` has
  `rootDir: "./"` and includes `__tests__/`. `node dist/index.js` fails.
- **`runAgentLoop` takes any object with `models.generateContent`** — that's
  the seam the driver uses to test the loop offline. Skills self-register on
  import (`registerSkill` at module top level), so just requiring
  `dist/src/skills/sampleSkill.js` makes `calculate` available.

## Troubleshooting

- `Error: Cannot find module '.../dist/src/agent.js'` → you didn't build.
  Run `npm run build` first.
- Driver reports `FAIL server starts` → port in use; rerun with
  `DRIVER_PORT=8200 node .claude/skills/run-sakthai-skills/driver.mjs`.
- `/chat` returns 500 with a 403 inside → missing/invalid Gemini credentials
  (see Gotchas); export `GEMINI_API_KEY` and restart the server.
