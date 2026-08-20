# Automated Learning Loop Patterns

> Updated Jul 24, 2026 — reflecting the 14→8 cron overhaul.
> Previous version (Jul 23) had `deliver: origin` + no dedup — that flooded Beer's chat. This replaces it.

## Core Loop Structure

A complete learning loop has 5 components:
1. **Learner** — web research or model analysis (one insight per run)
2. **Dedup** — reads LEARNING_JOURNAL.md before writing, skips if already covered
3. **Skill output** — findings saved as SKILL.md so the agent absorbs them
4. **GitHub sync** — daily push to `beer-sakthai/saksit-skills` for persistence
5. **Garda audit** — weekly integrity check (SOUL.md, crons, skills, GitHub)

## Cron Job Design Rules (Jul 24 Standard)

| Parameter | Correct Value | Why |
|-----------|--------------|-----|
| repeat | 999999 (large number) | Jobs must persist, not vanish after first run |
| deliver | **local** for learning/research jobs | Origin floods Beer's chat. Only production_weekly and garda-audit deliver to chat. |
| enabled_toolsets | Include "web", "file", "terminal", "memory", "skills" | Research needs web; skill creation needs "skills" |
| schedule | **Staggered by 1+ hours** | Never fire two learning jobs at the same time |

## Staggered Schedule Pattern (5 Learning Jobs)

The 5 learning jobs run every 6h, offset by 1h each so they never overlap:

| Job | UTC Hours |
|-----|-----------|
| Social Media Growth | 00:00, 06:00, 12:00, 18:00 |
| Assistant Excellence | 01:00, 07:00, 13:00, 19:00 |
| Content Formats | 02:00, 08:00, 14:00, 20:00 |
| Platform Algorithms | 03:00, 09:00, 15:00, 21:00 |
| Brand Storytelling | 04:00, 10:00, 16:00, 22:00 |

## Dedup Pattern

Every learning job reads LEARNING_JOURNAL.md first. If the insight is already recorded under the relevant category, it skips silently — no output, no noise.

Only genuinely new findings get appended with timestamp + category header.

## Deliver-to-Chat Rules

Only 2 jobs should ever deliver to Beer's chat:

| Job | When | Why |
|-----|------|-----|
| `production_weekly` | Sunday 12:00 UTC | Production metrics Beer needs to see |
| `garda-audit-weekly` | Monday 08:00 UTC | Integrity report with ✅/❌ per check |

Everything else → `deliver: local` → file only. Beer never sees learning research output.

## Guardian Cadence

**Garda audit** (weekly, Monday 08:00):
1. SOUL.md exists and is non-empty
2. All sibling agent SOUL.md files exist
3. All active cron jobs running as expected
4. LEARNING_JOURNAL.md updated in last 7 days
5. Skill count hasn't dropped significantly
6. GitHub repo has recent commits (< 7 days)

## GitHub Backup

**Daily sync at 05:00 UTC** → pushes to `beer-sakthai/saksit-skills`:
- All SKILL.md files from every skill directory
- LEARNING_JOURNAL.md
- Cron config export as JSON
- Only changed files pushed (SHA comparison)
- Uses GitHub PAT from /opt/data/.git-credentials

## Pitfalls

- `repeat: "once"` means the job vanishes after first run — always use a large number or "forever"
- **Do NOT deliver learning/research jobs to chat** — Beer called this out explicitly (Jul 24). Deliver to local.
- **Do NOT schedule learning jobs at the same time** — stagger by at least 1 hour
- **Dedup is required** — without it, every run produces a message even if nothing new was found
- Files the agent never reads are not learning — save as skills AND reference in SOUL.md
- Watchdog jobs are not needed — well-designed learning jobs with `repeat: 999999` and `deliver: local` run silently forever
- GitHub sync should compare content before pushing — don't create noisy commits for unchanged files
