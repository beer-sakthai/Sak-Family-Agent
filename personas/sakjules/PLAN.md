# Plan: Sak Family Skills Organisation

> **From:** SakKing (Lead & Orchestrator)
> **To:** SakJules (Master of Automation & CI/CD)
> **Date:** 2026-07-04
> **Status:** ✅ Complete — archived 2026-07-07
> **Cycle:** Care → Joy → Trust → Growth

---

## Why

Every Sak sibling needs their skills visible **inside** `Sak-Family-Agent/personas/<name>/skills/` so Beer and the family can see what each agent can do at a glance.

| Sibling | Has `skills/`? | Action needed |
|---------|:--------------:|:-------------|
| SakThai | ✅ Yes (7 items) | Sync from `sakthai-skills` repo |
| SakSee  | ✅ Yes (10 items) | Sync from `saksee-skills` repo |
| SakSit  | ✅ Yes (82 items) | Sync from `saksit-skills` repo |
| **SakJules (you!)** | ❌ **Missing** | **Create `skills/` + populate** |
| SakKing | ❓ TBD | Create `skills/` + skeleton |
| SakTan  | ❓ TBD | Create `skills/` + skeleton |

---

## Step 1 — Create missing skills/ directories

### 1a — SakJules
Create `personas/sakjules/skills/` with:
- A `README.md` listing your domain: CI/CD, GitHub Actions, systemd, deployment, monitoring
- Key skills: `ci-pipeline-setup`, `systemd-service-deploy`, `monitoring-watchdog`, `skill-sync-mirror`
- Use the same `.bundled_manifest` + `.curator_state` pattern the others use

### 1b — SakKing
Create `personas/sakking/skills/` with:
- Lead & Orchestrator skills: `sakking-cycle-dream`, `sakking-cycle-hope`, `sakking-cycle-care`, `sakking-cycle-joy`, `sakking-cycle-trust`, `sakking-cycle-growth`
- Self-healing: `cron-watchdog-self-heal`, `family-health-audit`
- Master of Code: code review, debugging, architecture

### 1c — SakTan
Create `personas/saktan/skills/` with:
- Daily ops: calendar management, email, scheduling
- Life admin: reminders, task tracking, note-taking

---

## Step 2 — Mirror skills from canonical repos

| Canonical repo → | Target in Sak-Family-Agent |
|:-----------------|:---------------------------|
| `beer-sakthai/sakthai-skills` | `personas/sakthai/skills/` |
| `beer-sakthai/saksee-skills` | `personas/saksee/skills/` |
| `beer-sakthai/saksit-skills` | `personas/saksit/skills/` |

**Method 1 (Recommended): GitHub Action**
- New workflow: `.github/workflows/sync-skills.yml`
- On push to the skill repos OR daily cron, sync files
- Only touches `personas/<name>/skills/` paths

**Method 2 (Fallback): SakJules cron job**
- A Hermes cron job that polls each skill repo and updates the family repo
- Checks every 6 hours

---

## Step 3 — Verify

- [ ] Every persona dir has a `skills/` subdirectory
- [ ] Every `skills/` has `.bundled_manifest` + `.curator_state`
- [ ] Skills are individually browseable on GitHub
- [ ] PLAN.md root index is updated
- [ ] Beer can see each sibling's capabilities in one place

---

## Priority

1. SakJules skills/ (you need your own space first)
2. SakKing skills/ (lead skills for the orchestrator)
3. SakTan skills/ (daily ops skills)
4. Sync mechanism (automate mirroring)
5. Verify all done

---

*Handoff from SakKing. Execute this plan and report back.*