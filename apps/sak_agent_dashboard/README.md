# House of Sak Agent Dashboard & Unified Workflow Engine

Next.js 16+ telemetry dashboard and embedded durable workflow engine for **House of Sak** (`Sak-Family-Agent`).

---

## 🌟 Overview

The dashboard provides visual telemetry, system health status, memory inspection, and workflow orchestration for the six Sak Family personas. It sits above the core Python package (`personas/sakthai/`) and operates in four primary modes:
1. **Live API Mode**: Connects over HTTP to `web/server.py` using a bearer token (configured via `sakthai web setup`).
2. **Runtime Gateway Console**: Live SSE streaming chat playground connected to the OpenAI-compatible Runtime Gateway (`sakthai.gateway`), supporting persona switching across all 6 agents (Gemini 4 Neon flagship default), duplex WebSocket audio streaming (`/v1/chat/ws`), and memory drawer inspection.
3. **Live Multi-Agent Pipeline Visualizer (`/pipelines`)**: Interactive SVG DAG canvas connected to Gateway SSE streaming (`/v1/team/pipelines/stream` via Next.js `/api/gateway/team/stream`), displaying dynamic step progression, pulsing active nodes, and live token streaming terminal.
4. **Memory Shard Studio (`/memory`)**: Deep inspection of sharded SQLite databases across all 6 personas (`/v1/memory/shards`), semantic kind filtering (`/v1/memory/facts`), and interactive dry-run prompt injection simulator (`/v1/memory/preview`) with DataLossGuardrail protection.

Embedded directly within the dashboard application is the **Unified Workflow Engine** (`workflow_engine/`), providing durable DAG execution, step retries, state persistence, and verification tooling. Dependencies are kept secure via daily Dependabot automated updates (`interval: "daily"`).

---

## 🛠️ Tech Stack

- **Framework**: Next.js 16+ (App Router, React 19, TypeScript)
- **Styling**: Tailwind CSS v4, Lucide React icons
- **Visualizations**: Recharts data visualizations & interactive SVG DAG canvas
- **Real-Time Streaming**: Server-Sent Events (SSE) and duplex WebSockets
- **Local Persistence**: `better-sqlite3` and sharded SQLite per persona (`~/.sakthai/<persona>/memory.db`)
- **Embedded Workflow Engine**: Python 3.11+ durable workflow execution engine (`workflow_engine/`)
- **Testing**: Vitest (24 test suites), React Testing Library, Fast-Check property testing, and workflow verification (`verify.py`)

---

## 🚀 Getting Started

### Prerequisites
- Node.js **>= 22.0.0**
- npm **>= 10.9.0**
- Python **>= 3.11** (for the embedded workflow engine and core API)

### Installation

```bash
cd apps/sak_agent_dashboard
npm ci
```

### Running the Dashboard

```bash
# Start Next.js development server on http://localhost:3000
npm run dev

# Or start Python API (:3001) and Dashboard (:3000) concurrently from repo root:
make dashboard-dev
```

### Building & Production

```bash
npm run build
npm run start
```

---

## 🧪 Testing & Verification

```bash
# Run Next.js and React unit tests (Vitest — 24 test suites)
npm test

# Run embedded workflow engine verification
npm run test:workflows

# Run complete full-stack verification suite
npm run test:all

# Run ESLint & TypeScript build checks
npm run lint
npm run build
```

---

## 📂 Subsystem Structure

```text
apps/sak_agent_dashboard/
├── src/
│   ├── app/                   Next.js App Router pages (overview, personas, memory, pipelines, system)
│   │   └── api/gateway/       Gateway proxies (/team/stream, /memory/shards, /memory/facts, /memory/preview)
│   ├── components/            Reusable UI components (TeamPipelineVisualizer, MemoryExplorer, charts)
│   └── lib/                   Data sources, contracts, and API client resolvers
├── public/                    Static assets and persona avatar SVGs
├── workflow_engine/           Embedded durable agent workflow engine
│   ├── agent_workflow/        DAG parser, task runner, and state persistence
│   ├── tests/                 Python workflow engine unit and integration tests
│   ├── verify.py              Durable workflow benchmark and verification runner
│   └── README.md              Detailed workflow engine documentation
├── DEPLOYMENT.md              Production deployment and Vercel hosting guide
├── TESTING.md                 Testing guidelines and coverage requirements
└── package.json               App dependencies and execution scripts
```
