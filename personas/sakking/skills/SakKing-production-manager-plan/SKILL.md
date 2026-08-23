---
name: SakSit-production-manager-plan
description: Plan, analyze, and report production with cost and metrics.
...
---

# Production Manager Plan

A structured framework for production management planning — covering planning, improvement analysis, cost tracking, timeframe management, outcome measurement, reporting, performance KPIs, and usage metrics. Designed for content production pipelines, AI agent operations, and SaaS delivery contexts. Tool-agnostic: adapts to whatever data sources are available (Google Sheets, Drive files, API endpoints, local logs).

## When to Use

- "Create a production plan for [project]"
- "Analyze production costs and timelines"
- "Report on production performance and metrics"
- "Track usage metrics for [service/product]"
- "Build a production improvement roadmap"
- "Audit production outcomes and flag issues"

## Prerequisites

- Access to relevant data sources: Google Drive/Sheets (via Composio), local files, or API endpoints
- `terminal` tool for running analysis scripts
- `execute_code` for complex multi-step data processing
- `memory` or `supermemory` for persisting recurring metrics thresholds

## How to Run

Invoke via `execute_code` with a structured pipeline. The procedure below is the canonical flow — pick the relevant phases for your scope.

## Procedure

### Phase 1: Gather & Baseline

1. **Collect data sources.** Use `search_files` for local logs, `GOOGLEDRIVE_FIND_FILE` for Drive, `GOOGLESHEETS_GET_VALUES` for Sheets, or `web_extract` for dashboard URLs.
2. **Inventory what you have.** Key fields to extract:
   - Production items (posts, deployments, agent runs, builds)
   - Timestamps (created, completed, duration)
   - Cost data (compute, labor, tooling)
   - Output/outcome metrics (views, conversions, uptime, throughput)
3. **Establish baselines:** mean, median, p90 for each metric over last 30 days.

### Phase 2: Analysis

1. **Cost analysis:** break down by category (compute, storage, API calls, human time). Flag items exceeding 2× standard deviation from mean.
2. **Timeframe analysis:**
   - Planned vs actual duration per item
   - Bottleneck detection: which stages consistently overrun?
   - Dependency chains: what blocks what?
3. **Performance metrics:**
   - Throughput (items/time unit)
   - Quality (error rate, rework rate, failure rate)
   - SLA adherence (% delivered on time)
4. **Usage metrics:**
   - Adoption rate (new users/consumers per period)
   - Utilization (actual vs capacity)
   - Engagement (depth, frequency, retention)

### Phase 3: Improvement Plan

1. **Identify top-3 improvement levers** by impact/cost ratio.
2. **Define measurable targets** for each metric (e.g., "reduce cost per unit by 15% in 60 days").
3. **Build a timeframe:**
   - Quick wins (≤7 days)
   - Medium-term (30 days)
   - Strategic (90 days)
4. **Document trade-offs:** cost vs speed vs quality.

### Phase 4: Outcome & Report

1. **Outcome assessment:** compare actual results to targets. Color-code:
   - ✅ On track (within 10% of target)
   - ⚠️ At risk (10–30% off)
   - ❌ Off track (>30% off)
2. **Generate a structured report** with:
   - Executive summary (3–5 bullet points)
   - Metrics dashboard table
   - Cost summary
   - Timeline Gantt overview (text-based)
   - Improvement roadmap
3. **Save the report** to a file (`.md` or `.csv`) via `write_file` for future reference.

### Phase 5: Continuous Loop

1. Save recurring metric thresholds to `memory` so future runs can flag anomalies without re-baselining.
2. If the same production pipeline is analyzed repeatedly, save as a `cronjob` (e.g., weekly production report). See `references/cron-watchdog-report-pattern.md` for the watchdog script template and registration steps.
3. After 3+ runs, update this skill with pipeline-specific data sources and thresholds.

## Production Metrics Table Template

| Metric | Current | Target | Prior Period | Trend | Status |
|--------|---------|--------|-------------|-------|--------|
| Cost/Unit | $X | $Y | $Z | ↑↓→ | ✅/⚠️/❌ |
| Throughput | X/d | Y/d | Z/d | ↑↓→ | ✅/⚠️/❌ |
| Error Rate | X% | Y% | Z% | ↑↓→ | ✅/⚠️/❌ |
| SLA % | X% | Y% | Z% | ↑↓→ | ✅/⚠️/❌ |
| Utilization | X% | Y% | Z% | ↑↓→ | ✅/⚠️/❌ |
| Adoption | X | Y | Z | ↑↓→ | ✅/⚠️/❌ |

## Cost Breakdown Table

| Category | This Period | Last Period | Change | % of Total |
|----------|-------------|-------------|--------|-----------|
| Compute | $X | $Y | $Δ | X% |
| Storage | $X | $Y | $Δ | X% |
| API/Tools | $X | $Y | $Δ | X% |
| Labor | $X | $Y | $Δ | X% |
| **Total** | **$X** | **$Y** | **$Δ** | **100%** |

## Related Skills

- `saksit-social-media-posting-workflows` — Execution companion. Use this skill to PLAN and ANALYZE content production; use the posting workflows skill to EXECUTE (post to IG/LI/FB/YT). The two form a plan→do→review loop.
- `sakthai-cycle-growth` — Fold analysis findings back into skills and memory after each run.

## Pitfalls

- Don't report raw numbers without context — always compare to baseline or target.
- Don't skip the "improve" phase — a plan without improvement actions is just an audit.
- Cost data may be incomplete (hidden compute, shared resources). Flag assumptions clearly.
- Timeframes slip. Always include confidence levels (high/medium/low) for each estimate.
- Usage metrics without denominators (e.g., "100 new users" vs "100/1000 = 10% adoption") are misleading.
- If gathering from multiple sources, deduplicate by item ID or timestamp before analysis.

## Verification

Run this check after completing a plan: confirm the output file exists and contains all 5 phases (gather, analyze, improve, outcome, report) with at least one populated table.
