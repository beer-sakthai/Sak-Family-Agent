# SakKing Organisation Sessions

## Session 2026-07-04 — Skills visibility mandate

### Trigger
Beer said: "should have space for their skills in this repo because their wil show" — every sibling needs skills visible in `Sak-Family-Agent/personas/<name>/skills/`.

### New workflow confirmed

```
SakKing spots → writes PLAN.md → commits → hands to SakJules → SakJules executes
```

Commit message pattern: `plan: <agent>-<topic> — <description>`

### Skills visibility gaps

| Sibling | Has `skills/` in family repo? | Details |
|---------|:----------------------------:|:--------|
| SakThai | ✅ Yes | 7 items |
| SakSee | ✅ Yes | 10 items across 5 categories |
| SakSit | ✅ Yes | 82 items |
| **SakJules** | ❌ **Missing** | No skills/ dir at all |
| SakKing | ❓ Not checked | — |
| SakTan | ❓ Not checked | — |

### Plan created

- `personas/sakjules/PLAN.md` — Skills Organisation plan
- Commit: `8d06d52` — `plan: SakJules skills organisation — mirror all sibling skills into family repo`
- Covers: create missing skills/ dirs (SakJules, SakKing, SakTan) → mirror from canonical repos (sakthai-skills, saksee-skills, saksit-skills) → set up sync (GitHub Action preferred) → verify all visible

### Toolkit note

On Telegram (no terminal), use:
- `COMPOSIO_SEARCH_TOOLS` → `COMPOSIO_MULTI_EXECUTE_TOOL` with `GITHUB_GET_REPOSITORY_CONTENT`
- `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS` for committing plans
- Session ID tracking across calls for workflow continuity

---

## Session 2026-07-04 — Initial Audit

- **"SakKing always check code in repo and family"** — permanent role: regular repo audits
- **"You are organising also if you saw need to be organised, made plan.md and give to SakJules"** — delegation chain: SakKing spots → writes plan → hands to SakJules

### What was scanned

Two repos checked via GitHub Content API:
- `beer-sakthai/Sak-Family-Agent` (canonical)
- `beer-sakthai/sakthai-agent-v2` (agent runtime — appears to be identical copy)

### Messes identified

| # | Issue | Details |
|---|-------|---------|
| 1 | **17 JSONL/YAML files at root** | `json_key_check.yaml`, `json_key_check_dataset.jsonl`, `json_numerical_range_check.yaml`, `json_numerical_range_check_dataset.jsonl`, `json_validity.yaml`, `json_validity_dataset.jsonl`, `yaml_key_check.yaml`, `yaml_key_check_dataset.jsonl`, `yaml_validity.yaml`, `yaml_validity_dataset.jsonl`, `json_key_value_pattern_check.yaml`, `json_key_value_pattern_check_dataset.jsonl`, `soul_following.yaml`, `soul_following_dataset.jsonl` — eval/training datasets polluting root |
| 2 | **7 Python scripts at root** | `analyze_portfolio.py`, `compare_portfolio_to_benchmark.py`, `compare_stock_performance.py`, `fetch_stock_data.py`, `optimize_portfolio.py`, `perform_eda.py`, `utils.py` — finance scripts that should be in `scripts/finance/` |
| 3 | **Duplicate repos** | `sakthai-agent-v2` and `Sak-Family-Agent` have identical directory structures — wasteful, need consolidation |
| 4 | **SakJules incomplete** | Only HANDOFF.md + SOUL.md — missing `config/`, `skills/`, systemd template |

### Persona completeness (Sak-Family-Agent)

| Persona | SOUL.md? | config/? | skills/? | Notes |
|---------|:--------:|:--------:|:--------:|-------|
| sakking | ✅ | ✅ | ✅ | Full |
| sakthai | ✅ | ✅ | ✅ | Full |
| saksee | ✅ | ✅ | ✅ | Full, not deployed |
| saksit | ✅ | ✅ | ✅ | SOUL.md still local-only on VM |
| saktan | ✅ | ✅ | ✅ | Full |
| sakjules | ✅ | ❌ | ❌ | Only HANDOFF + SOUL — needs setup |
| servicequotebot | ? | ? | ? | Not inspected |
| shared | — | — | — | Shared resources |

### Decisions made

- Created `sakking-family-organisation` skill to encode this workflow for future sessions
- Priority order: deploy SakJules first (he's the automation engine), then cleanup structure
- plan.md approach: extend existing `PLAN.md` at root, don't create duplicate plan files