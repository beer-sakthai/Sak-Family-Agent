## 2026-08-02T15:45:45Z
You are assigned to implement Milestone 2 (M2: Data Layer & API Routes) for the Sak-Agent-Family Dashboard project.
Working directory: /home/beern/teamwork_projects/sak_agent_dashboard/.agents/teamwork_preview_worker_m2
Project root: /home/beern/teamwork_projects/sak_agent_dashboard

Please read the following documents first:
- /home/beern/teamwork_projects/sak_agent_dashboard/ORIGINAL_REQUEST.md
- /home/beern/teamwork_projects/sak_agent_dashboard/PROJECT.md
- /home/beern/teamwork_projects/sak_agent_dashboard/TEST_INFRA.md

Your tasks for Milestone 2:
1. Initialize `.agents/teamwork_preview_worker_m2/DISPATCH.md`, `BRIEFING.md`, and `progress.md`.
2. Implement data layer helper modules in `src/lib/`:
   - `src/lib/types.ts`: Define TypeScript interfaces for AgentPersona, MetricsData, MemoryData, AuditLog, SessionTranscript, SessionMessage, and API response envelopes.
   - `src/lib/sakthai.ts`: Implement parsers for `~/.sakthai/eval.jsonl`, `~/.sakthai/audit.log`, and `~/.sakthai/sessions/*.json`. Provide robust try-catch handling, divide-by-zero protection, empty file fallbacks, and realistic sample data generation when demo mode is active (`demo=true`).
   - `src/lib/db.ts`: Implement SQLite parser for `~/.sakthai/memory.db` using `better-sqlite3`. Query facts and observations tables. Gracefully handle missing database file or table schema variations, returning fallback sample memory records when appropriate or in demo mode.
3. Implement Next.js App Router API endpoints in `src/app/api/`:
   - `src/app/api/agents/route.ts`: `GET /api/agents` (supports `?demo=true`). Serves live status cards for SakThai, SakKing, SakSee, SakSit, SakJules with pulse badges, latency metrics, and benchmark scores.
   - `src/app/api/metrics/route.ts`: `GET /api/metrics` (supports `?demo=true`). Serves aggregated benchmark performance stats, token consumption, latency trends, and stop reason breakdown.
   - `src/app/api/memory/route.ts`: `GET /api/memory` (supports `?demo=true`, `?query=...`, `?severity=...`). Serves SQLite memory facts, observations, and security audit logs with severity filtering.
   - `src/app/api/sessions/route.ts`: `GET /api/sessions` (supports `?demo=true`, `?search=...`, `?limit=...`, `?offset=...`, `?id=...`). Serves searchable session transcripts with pagination, search filtering, and single-session detail fetching.
4. Verify execution:
   - Run `npm test` to ensure all API route contract tests in `src/tests/api.test.ts` and integration tests in `src/tests/integration.test.ts` pass with 100% exit code 0.
   - Run `npm run build` to verify 0 TypeScript compilation or lint errors.
5. Write `handoff.md` in your working directory and notify the parent orchestrator via send_message.
