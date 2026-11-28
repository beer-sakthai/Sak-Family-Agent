# Plan: Sak Agent Dashboard Interactive Runner & Memory Curation Hub

**Date:** 2026-11-28  
**Author:** SakJules · Master of Automation & CI/CD  
**Scope:** `apps/sak_agent_dashboard/` and supporting core dashboard integrations  

---

## 1. Executive Summary & Objective

Transform the Sak Agent Dashboard from a read-heavy analytics interface into an **interactive execution and curation mission control** for the House of Sak.

### Key Capabilities Aligned with User Interview:
1. **Universal Dockable Runner Drawer**: A bottom/side slide-out terminal console accessible across the entire application (Overview, Gateway, Memory, Persona Cards, keyboard shortcut `Ctrl+\`` / `⌘\`, or Command Palette).
2. **Direct Subprocess SSE Streaming**: When the HTTP Gateway daemon (:8080) is offline, the backend API dynamically spawns `sakthai run` child processes with parameter validation, streaming stdout/stderr over Server-Sent Events directly to the UI.
3. **Dry-Run Preflight with 1-Click Execution**: Interactive dry-run toggle allows testing prompt feasibility, tool access, and model resolution without spending tokens, followed by immediate 1-click execution.
4. **Full In-Place Memory Fact Curation**: Extend `MemoryExplorer` to support in-place fact editing, tag curation, private fact redaction badges, and direct local SQLite shard mutations when the Gateway is offline.
5. **Full E2E Verification**: Comprehensive test coverage across Vitest, Next.js build validation, TypeScript typing, and workflow engine verification.

---

## 2. Technical Architecture

### 2.1 API Route: `POST /api/gateway/runner`
- Runtime: `nodejs`
- Body:
  ```json
  {
    "persona": "sakjules",
    "task": "Check CI status and verify contracts",
    "dryRun": true,
    "fast": false,
    "maxIterations": 12,
    "model": null
  }
  ```
- Execution Flow:
  1. Validates persona against known list (`sakthai`, `sakking`, `saksee`, `sakjules`, `saksit`, `saktan`).
  2. If `SAKTHAI_GATEWAY_URL` is responsive, proxies stream.
  3. Otherwise, spawns `uv run sakthai run "<task>" --persona <persona> ...` safely without shell interpolation.
  4. Returns `text/event-stream` emitting structured events:
     - `data: {"type": "stdout", "text": "..."}\n\n`
     - `data: {"type": "stderr", "text": "..."}\n\n`
     - `data: {"type": "exit", "code": 0}\n\n`

### 2.2 Component: `src/components/RunnerDrawer.tsx`
- Slide-out dockable drawer at screen bottom.
- Persona selector with avatar, color accents, and role summary.
- Task prompt input with quick presets per persona.
- Execution controls: Dry-Run switch, Fast-track toggle, Clear, Abort (kills subprocess).
- Real-time ANSI terminal log viewer with autoscroll.

### 2.3 Memory Curation: In-Place Editing & Direct SQLite Fallback
- `POST /api/gateway/memory/edit` updates existing fact value, key, and tags.
- Direct SQLite shard fallback: updates `~/.sakthai/<persona>/memory.db` directly using `better-sqlite3` when Gateway is offline.
- Private fact shield badge for sensitive tags or private categories.

---

## 3. Implementation Phasing

### Phase 1: Direct Subprocess SSE Streaming API (`/api/gateway/runner`)
- Create `src/app/api/gateway/runner/route.ts` with streaming SSE child process execution.
- Implement argument array sanitization and abort controller signal handling.

### Phase 2: Universal Dockable Runner Drawer (`RunnerDrawer.tsx`)
- Implement `RunnerDrawer.tsx` with persona tabs, prompt presets, streaming terminal output, and status badges.
- Wire into `src/app/page.tsx` and keyboard shortcuts (`Ctrl+\``, `⌘\`).

### Phase 3: Direct Memory Curation & In-Place Editing
- Implement `src/app/api/gateway/memory/edit/route.ts` with local SQLite fallback.
- Enhance `MemoryExplorer.tsx` with Edit Fact modal, inline tag chips, and private fact indicators.

### Phase 4: Shell Integration, Warnings Cleanup & Ergonomics
- Add "Run Agent" trigger to `AgentCard.tsx` and `PersonaDrawer.tsx`.
- Remove unused `accentClasses` in `Card.tsx` to ensure 0 lint warnings.
- Integrate runner action into `CommandPalette.tsx`.

### Phase 5: Automated Testing & Verification
- Author Vitest tests: `src/tests/runner-drawer.test.tsx` and `src/tests/memory-curation.test.ts`.
- Run `npm test`, `npm run lint`, `npm run build`, and `npm run test:workflows`.
- Verify full test suite passes.
