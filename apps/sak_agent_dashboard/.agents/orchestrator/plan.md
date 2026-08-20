# Implementation Plan — Sak-Agent-Family Dashboard

## Phase 0: Survey & Scope Mapping
- Spawn 3 parallel Explorers to investigate current codebase `/home/beern/teamwork_projects/sak_agent_dashboard`, runtime data structures in `~/.sakthai/` (`eval.jsonl`, `audit.log`, `memory.db`), and existing dependencies/tooling.
- Synthesize survey findings into `PROJECT.md` § Feature Inventory, Architecture, Interface Contracts, and Milestones.

## Phase 1: Milestone Setup & Dual-Track Execution
- E2E Testing Track: Design test suite structure and test cases for API routes and UI components (`TEST_INFRA.md`).
- Implementation Milestones:
  - Milestone 1: Data Access Layer & Helper Libraries (parse `eval.jsonl`, `audit.log`, SQLite `memory.db`).
  - Milestone 2: Next.js API Routes (`/api/agents`, `/api/metrics`, `/api/memory`).
  - Milestone 3: Dashboard UI Components & Styling (Inter/Outfit typography, Dark Mode theme, status cards for SakThai, SakKing, SakSee, SakSit, SakJules, charts, transcripts).
  - Milestone 4: Integration, E2E Test Pass (`npm test` 100%), and Build Hardening (`npm run build` 0 errors).

## Phase 2: Verification & Delivery
- Reviewer, Challenger, and Forensic Auditor verification per milestone.
- Notify Sentinel upon completion.
