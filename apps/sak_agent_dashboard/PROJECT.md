# Project: Sak-Agent-Family Dashboard

## Architecture
- Framework: Next.js 14/15 TypeScript App Router
- Styling: Tailwind CSS, Inter & Outfit Google fonts, dark-mode styling (`#090d16` background, glassmorphic cards `bg-slate-900/80`)
- Data Storage & Runtime Access: Read-only access to `~/.sakthai/` (`eval.jsonl`, `audit.log`, `memory.db` SQLite via Node `sqlite3`/`better-sqlite3`, `sessions/*.json`)
- Charts & Visualization: Recharts / Chart.js for responsive performance, token usage, latency trends, and stop reason breakdown
- Test Suite: Vitest / Jest + React Testing Library for API route testing and component unit/integration tests (`npm test`)

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | App Scaffold & Infrastructure | Next.js TS project setup, Tailwind CSS, typography (Inter/Outfit), layout wrapper | M1 | Survey |
| 2 | Data Access Layer & Services | Helper modules (`lib/sakthai.ts`, `lib/db.ts`) to read/parse `eval.jsonl`, `audit.log`, `memory.db`, `sessions/*.json` | M2 | Survey |
| 3 | API Routes | `/api/agents`, `/api/metrics`, `/api/memory`, `/api/sessions` with JSON response payloads & query filters | M2 | Survey |
| 4 | Agent Overview Panel UI | Live status cards for SakThai, SakKing, SakSee, SakSit, SakJules (model, status, skills, latency, runs) | M3 | Survey |
| 5 | Analytics & Interactive Charts UI | Visualizations for benchmark scores, token consumption, latency trends, and stop reason breakdown | M3 | Survey |
| 6 | Session & Memory Explorer UI | Searchable transcripts, modal transcript detail viewer, security audit log inspector, memory.db viewer | M3 | Survey |
| 7 | Automated Test Suite | Comprehensive API unit/integration tests and UI component rendering tests (`npm test` 100% pass) | Testing Track & M4 | Survey |
| 8 | Build Hardening & E2E Acceptance | `npm run build` succeeds with 0 TS/lint errors; full verification by Reviewers, Challengers, Auditor | M4 | Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: App Setup & Infrastructure | Scaffold Next.js TS app, install dependencies, Tailwind setup, Root Layout, dark mode theme | None | DONE (2f901ad7-3ff8-425b-a653-ec2d03b7838b) |
| 2 | M2: Data Layer & API Routes | `lib/` data parsers, SQLite reader, `/api/agents`, `/api/metrics`, `/api/memory`, `/api/sessions` | M1 | DONE (78895c9f-0c72-475d-8ad7-1df011545d3a) |
| 3 | M3: Dashboard UI Components | Agent Overview cards, Recharts visualizations, Session explorer modal, Audit log viewer | M2 | DONE (8fbba1f0-a7e1-4e88-9ad2-1ab00b630184) |
| 4 | M4: Testing, Verification & Build | Vitest/Jest unit/integration test suite (`npm test`), clean compilation (`npm run build`) | M3, Testing Track | IN_PROGRESS (Gate verification: Reviewers, Challengers, Auditor) |

## Interface Contracts
### Data Parsers ↔ API Routes
- `getAgentOverview()` -> `PersonaOverview[]` (SakThai, SakKing, SakSee, SakSit, SakJules)
- `getMetricsSummary()` -> `{ totalRuns, avgLatencyMs, successRate, tokenStats, stopReasons, trends }`
- `getMemoryAndAudit(query, severity)` -> `{ facts: [], observations: [], auditLogs: [] }`
- `getSessionTranscripts(search, limit, offset)` -> `{ sessions: [], total: 761 }`

### API Routes ↔ Frontend UI
- `GET /api/agents` -> `{ success: true, agents: PersonaCard[] }`
- `GET /api/metrics` -> `{ success: true, metrics: MetricsData }`
- `GET /api/memory` -> `{ success: true, memory: MemoryData, auditLogs: AuditLog[] }`
- `GET /api/sessions` -> `{ success: true, sessions: SessionMeta[], total: number }`

## Code Layout
```
sak_agent_dashboard/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── api/
│   │   │   ├── agents/route.ts
│   │   │   ├── metrics/route.ts
│   │   │   ├── memory/route.ts
│   │   │   └── sessions/route.ts
│   ├── components/
│   │   ├── AgentCard.tsx
│   │   ├── AgentOverview.tsx
│   │   ├── AnalyticsCharts.tsx
│   │   ├── SessionExplorer.tsx
│   │   ├── MemoryExplorer.tsx
│   │   └── AuditLogs.tsx
│   ├── lib/
│   │   ├── sakthai.ts
│   │   ├── db.ts
│   │   └── types.ts
│   └── tests/
│       ├── api.test.ts
│       └── components.test.tsx
├── public/
├── package.json
├── tsconfig.json
├── next.config.mjs
└── tailwind.config.ts
```
