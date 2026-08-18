# Dashboard Expansion Plan

Checklist mapping each requested external repo to concrete additions inside
`apps/sak_agent_dashboard/`. Follows the established pattern: one `lib/`
data module, one `app/api/*` route, one `components/*Panel.tsx`, one test
file, one wire-up in `app/page.tsx`.

## Source repos surveyed

| # | Repo | Verdict | Where it lands |
|---|------|---------|----------------|
| 1 | [open-telemetry/opentelemetry.io](https://github.com/open-telemetry/opentelemetry.io) | Docs site source. Ship a concept + integration tab, not source files. | New tab: **Observability** |
| 2 | [google/adk-python](https://github.com/google/adk-python) | Code-first agent framework; distinct from Genkit/Antigravity. | New tab: **Google ADK** |
| 3 | [GoogleCloudPlatform/training-data-analyst](https://github.com/GoogleCloudPlatform/training-data-analyst) | 8.6k-star training catalog. Ship curated resource cards. | New tab: **Learning** |
| 4 | [github/spec-kit](https://github.com/github/spec-kit) | Upstream of the `.specify/` install already documented. | **Enhance** existing SpecKit tab (upstream section) |
| 5 | [microsoft/Agents-M365Copilot / python package](https://github.com/microsoft/Agents-M365Copilot/tree/main/python/packages/microsoft_agents_m365copilot) | Delegated-OAuth SDK, contrasts with existing app-only teams-copilot-mcp. | New tab: **M365 Copilot** |

Result: **4 new tabs + 1 enhancement**. No raw source files are copied out
of the upstream repos into this repo — each addition mirrors the upstream
surface (commands, primitives, install lines, directory maps) with links
back so the dashboard stays self-contained and license-clean.

---

## 1. Observability (OpenTelemetry) — new tab

- [x] `src/lib/otel.ts` — data module with core concepts, signals, exporters, Python install lines, LLM-related semantic conventions, and a sakthai integration snippet showing how to add OTel to the agent loop / eval log.
- [x] `src/app/api/otel/route.ts` — GET returning the snapshot.
- [x] `src/components/OtelPanel.tsx` — overview + signal cards (traces/metrics/logs) + exporter grid + install + semconv table + integration snippet.
- [x] `src/tests/otel.test.tsx` — data + route + component tests.
- [x] Types added to `src/lib/types.ts`.
- [x] Tab wired in `src/app/page.tsx`.

## 2. Google ADK — new tab

- [x] `src/lib/googleAdk.ts` — data module: package info (`google-adk`), CLI (`adk run` / `adk web`), primitives (`Agent`, `LlmAgent`, `SequentialAgent`, `ParallelAgent`, `Runner`, tool + MCP integration), quickstart, comparison row appended to the Antigravity comparison map.
- [x] `src/app/api/google-adk/route.ts` — GET route.
- [x] `src/components/GoogleAdkPanel.tsx` — overview + install + primitives + workflow types + CLI card.
- [x] `src/tests/google_adk.test.tsx` — tests.
- [x] Types added to `src/lib/types.ts`.
- [x] Tab wired in `src/app/page.tsx`.

## 3. GCP Learning (training-data-analyst) — new tab

- [x] `src/lib/gcpLearning.ts` — curated set of directories from the upstream repo with a one-line summary per directory (courses/, quests/, self-paced-labs/, bootcamps/, blogs/, datalab/, doc/), plus a filter category (agents / ML / data / notebooks).
- [x] `src/app/api/gcp-learning/route.ts` — GET route.
- [x] `src/components/GcpLearningPanel.tsx` — repo card + filterable resource grid with deep links.
- [x] `src/tests/gcp_learning.test.tsx` — tests.
- [x] Types added to `src/lib/types.ts`.
- [x] Tab wired in `src/app/page.tsx`.

## 4. SpecKit — enhance existing tab

- [x] Extend `src/lib/speckit.ts` snapshot with an `upstream` block: repo URL, license (MIT), `uv tool install specify-cli` install, the upstream command roster (constitution / specify / clarify / plan / tasks / taskstoissues / analyze / checklist / implement / converge), and a note that the `.specify/` layout in this repo mirrors the upstream template pipeline.
- [x] Extend `SpecKitPanel` to render an "Upstream" section with the CLI install snippet, the full upstream command list, and a link out to the source repo.
- [x] Extend `src/tests/speckit.test.tsx` to assert the upstream section is populated and rendered.

## 5. M365 Copilot Agents — new tab

- [x] `src/lib/m365Copilot.ts` — data module: package (`microsoft-agents-m365copilot`), install, key classes (`AgentsM365CopilotServiceClient`, `RetrievalPostRequestBody`, `RetrievalDataSource`), delegated-OAuth (`DeviceCodeCredential`) flow, and a contrast card vs. teams-copilot-mcp (app-only + stdio MCP).
- [x] `src/app/api/m365-copilot/route.ts` — GET route.
- [x] `src/components/M365CopilotPanel.tsx` — overview + install + primitives with copyable Python snippets + delegated-auth flow diagram (text) + contrast card.
- [x] `src/tests/m365_copilot.test.tsx` — tests.
- [x] Types added to `src/lib/types.ts`.
- [x] Tab wired in `src/app/page.tsx`.

---

## Cross-cutting

- [x] Strict TypeScript typecheck across all changed files (isolated env, since the dashboard's own npm install is blocked by pre-existing lockfile corruption).
- [x] Commit as **one PR-ready change** on `claude/sak-agent-dashboard-ffnoks`.
- [x] Push to origin.

## Deliberately not doing

- **Not copying source files** from upstream repos into this repo. Each addition is a *dashboard view* of the upstream (concepts, commands, install lines, links). This keeps license and update-tracking clean and avoids duplicating docs that live upstream.
- **Not scraping training-data-analyst notebook contents** — 8.6k-star repo, 8k+ commits, way too large. The Learning tab links to specific top-level dirs and calls out the ones actually relevant to agent development.
- **Not adding another SpecKit tab** — enhancing the existing one is the right move; the upstream and the local install describe the same tool at two layers.
