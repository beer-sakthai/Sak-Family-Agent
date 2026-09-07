---
name: SakJules-SakSit-continuous-learning-loop
description: "Automated research cron feeding back into skills."
---

# SakSit Continuous Learning Loop

> Research that doesn't change the agent is noise. Close every loop.

## When to Use

Create a learning-loop cron job when Beer wants ongoing research on a topic that should make me smarter over time. Signals:
- "Learn about X and come back with knowledge"
- "Every [timeframe] research Y and remember"
- Any request for recurring skill-building

Do NOT use for one-off questions, single searches, or "go find this answer" tasks.

## Anatomy of a Closed Learning Loop

```
Cron fires → reads LEARNING_JOURNAL.md for dedup check
    → if already known: SKIP SILENTLY (empty output = no delivery)
    → if new: researches topic → extracts 1-2 actionable insights
    → persists to LEARNING_JOURNAL.md AND one of: SKILL.md / SOUL.md / memory
    → delivers concise finding (or silent if deliver=local)
    → NEXT run builds on accumulated knowledge
```

**Dedup-first design:** Before researching, read the LEARNING_JOURNAL.md to check if this insight is already recorded. If covered, skip silently — zero output = zero delivery. This prevents repeating the same findings across runs.

**Double-dip persistence:** Persist to BOTH the LEARNING_JOURNAL.md (for record) AND a skill/memory (for behaviour change). The journal is the anti-duplication record; the skill is the behaviour change. One without the other is incomplete.

**Proven pattern from Jul 25 session:** A Visual & Infographic insight was written to LEARNING_JOURNAL.md AND simultaneously patched into the `Sak-instagram-content-kit` skill's Carousel storyboard section. The journal entry ensures future cron runs won't re-research the same topic; the skill patch ensures every future `Sak-instagram-content-kit` invocation already carries the new technique. Always check: "Which existing skill should carry this finding?" before choosing where to persist — the answer is rarely "none."

**Critical rules:**
- If the finding only goes to a journal file I never read, the loop is BROKEN. Beer taught this lesson on Jul 23, 2026.
- If the finding only goes to a skill without a dedup check, it will be repeated next run. Always check the journal first.

## Integration Points (where learnings must land)

| If finding is... | Persist to... | Method |
|-----------------|---------------|--------|
| A reusable technique / workflow | SKILL.md (patch existing or create) | `skill_manage(action='patch'/'create')` |
| A permanent identity fact about me | SOUL.md | `patch()` on the relevant section |
| A user preference or correction | SKILL.md body (NOT just memory) | Patch the skill that governs that task |
| An algorithm insight or data point | Existing umbrella skill's `references/` dir | `skill_manage(action='write_file', ...)` |
| A transient tip (will stale in <7 days) | Memory only | `memory()` tool |

## Scheduling Rules

| Frequency | When to Use | Risk |
|-----------|-------------|------|
| 1m | Only for rapid testing / debugging | **High noise** — Beer showed confusion on Jul 23 |
| 5-15m | Short feedback loops, active learning sprints | Moderate |
| 30m-1h | Routine knowledge-growth pipelines | Low — preferred cadence |
| Daily | Mature, stable learning topics | Minimal |

**Lesson from Jul 23:** 5 concurrent jobs at 1m each = 300 deliveries/hour. That flooded Beer and he responded "???". Default to **30m minimum** unless Beer explicitly asks for faster.

### Delivery Strategy

Learning jobs should deliver findings in a way that doesn't flood Beer's chat.

| Deliver | When | Effect |
|---------|------|--------|
| `origin` | Only for actions Beer needs to see or approve | Sends message to Beer's chat |
| `local` | Learning research, routine syncs, background collection | Saves only to file — no chat noise |

**Rule:** Learning research = `local`. Integrity audits and actionable alerts = `origin`. When delivering `local`, the output still persists to disk (LEARNING_JOURNAL.md, skills) so the agent absorbs it on next run.

### Staggered Scheduling Pattern

When running 3+ learning jobs at the same frequency, stagger them across different hours to avoid burst scheduler load:

| # | Topic | UTC Schedule | Run Times |
|---|-------|-------------|-----------|
| 1 | Social Media Growth | `0 0,6,12,18 * * *` | 00/06/12/18 |
| 2 | Assistant Excellence | `0 1,7,13,19 * * *` | 01/07/13/19 |
| 3 | Content Formats | `0 2,8,14,20 * * *` | 02/08/14/20 |
| 4 | Platform Algorithms | `0 3,9,15,21 * * *` | 03/09/15/21 |
| 5 | Brand Storytelling | `0 4,10,16,22 * * *` | 04/10/16/22 |

**Rule:** Offset each by at least 1 hour from the next. Never overlap 2+ learning jobs at the same minute.

## Research Source Priority

When research tools are blocked or unavailable:

1. **Direct expert sources** — Buffer, Later, HubSpot, Content Marketing Institute (browser navigation or terminal curl to known URLs)
2. **Cached/known frameworks** — What I already have in skills + LEARNING_JOURNAL.md (synthesize, don't re-fetch)
3. **Terminal curl** — Fetch specific article URLs known to exist
4. **Web search** — Composio search or browser search (last resort when others fail)

### Known-Good Social Media Research URLs (curl-friendly)

These blogs return readable HTML from curl (no CAPTCHA, no JS requirement). Use them directly for social media algorithm/trend research:

| Source | URL Pattern | What It Covers |
|--------|-------------|----------------|
| **Later Blog** | `https://later.com/blog/instagram-algorithm/` | Instagram algorithm deep-dives, Reels strategy, carousel best practices |
| **Hootsuite Blog** | `https://blog.hootsuite.com/social-media-trends/` | Annual trends report, platform updates, benchmarks |
| **Buffer Library** | `https://buffer.com/library/social-media-strategy/` | Growth frameworks, algorithm explainers, content strategy |

**Tip:** For Later articles, the main content is embedded in the HTML despite heavy JS. Hootsuite returns clean text. Buffer's library is also curl-readable. All three have been verified working as of July 2026.

### ⚠️ curl piped-to-interpreter blocking

The security scanner blocks `curl URL | python3` or `curl URL | bash` patterns. **Do not pipe curl output directly into an interpreter.** Instead, write to a temp file first, then read/process it separately:

```bash
curl -sL "URL" -o /tmp/research-data.json
python3 -c "import json; ..."
```

This applies to all interpreter pipes: `python3`, `bash`, `sh`, `node`.

### DuckDuckGo Lite HTML search: first fallback when search engines CAPTCHA-block

When Composio search is unavailable, DuckDuckGo Lite (`lite.duckduckgo.com/lite`)
returns search results as parseable HTML via curl — no CAPTCHA, no JS required.
Full technique documented in `references/ddg-lite-search-fallback.md`.

**Quick reference:**
```bash
curl -sL "https://lite.duckduckgo.com/lite/?q=QUERY" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/ddg.html
grep -oP '(?<=<a rel="nofollow" href=")[^"]+' /tmp/ddg.html | head -10
```
Then decode the `uddg` param in each redirect URL (see reference doc for full pattern).

### Wikipedia API: second fallback when search engines CAPTCHA-block

Google, DuckDuckGo, and Bing all hit CAPTCHAs from automated curl. The **Wikipedia API** (`en.wikipedia.org/w/api.php`) returns clean JSON with no blocks — use it as the first fallback when search is unavailable.

**Get article extract (clean text):**
```bash
curl -sL "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles=TOPIC&format=json&origin=*" -H "User-Agent: Agent/1.0" -o /tmp/wiki.json
# Then parse with: python3 -c "import json; d=json.load(open('/tmp/wiki.json')); pages=d['query']['pages']; [print(pages[p].get('extract','')) for p in pages]"
```

**Search for articles:**
```bash
curl -sL "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=QUERY&format=json&origin=*" -H "User-Agent: Agent/1.0"
```

**Get full HTML page (printable version):**
```bash
curl -sL "https://en.wikipedia.org/w/index.php?title=TOPIC&printable=yes" -H "User-Agent: Agent/1.0" -o /tmp/page.html
```

### Tracker JSON pattern for multi-run cron research

When a research cron job accumulates findings across runs, use a **tracker JSON** to record what's been covered so the next run picks something new:

**Structure:**
```json
{
  "topics": [
    {"id": 1, "topic": "Brief description of the finding", "count": 1, "source": "Source URL or publication"}
  ],
  "rule": "If no new topics left, improve the lowest-count existing one."
}
```

**Convention:** Place the tracker at `scripts/<job-name>-tracker.json` in the umbrella skill's directory. Each run reads it, picks a topic not yet covered (or improves the weakest one), researches it, then writes back the updated tracker.

### Bucket rotation pattern (simpler alternative to tracker JSON)

For guaranteed diversity without maintaining a JSON tracker, use **day-of-week bucket rotation**. Each topic gets 7 sub-topics (one per weekday), and the cron prompt tells the agent to research the bucket matching today's day.

**Pros:** No state file, no read/write overhead, deterministic, can't lose sync on crash.
**Cons:** Less flexible than tracker JSON — fixed rotation, no priority weighting.

**Example 1 — Social Media Growth buckets:**
```
BUCKET ROTATION (determine day-of-week, research that bucket):
- Mon: Platform-specific tactics (Instagram)
- Tue: Platform-specific tactics (LinkedIn)
- Wed: Growth hacks & experiments
- Thu: Analytics & measurement
- Fri: Tools & automation
- Sat: Community building
- Sun: Trend analysis & emerging platforms
```

**Example 2 — Brand Storytelling buckets (proven in production Jul 25):**
```
BUCKET ROTATION (determine day-of-week, research that bucket):
- Mon: Narrative structures
- Tue: Hook formulas
- Wed: Vulnerability & authenticity
- Thu: Personal brand building
- Fri: Case studies & evidence
- Sat: Visual storytelling
- Sun: Platform-specific storytelling (IG vs LI)
```

**Example 3 — Content Formats buckets (proven in production Jul 25):**
```
BUCKET ROTATION (determine day-of-week, research that bucket):
- Mon: Carousels & document posts
- Tue: Short-form video / Reels
- Wed: Text-only & newsletter
- Thu: Interactive & multi-format
- Fri: Audio & podcast
- Sat: Visual & infographic
- Sun: Emerging formats
```

**Enforce in prompt:** Require the agent to start its output with "Bucket: [day] — [bucket name]" so dedup is visible. Also check LEARNING_JOURNAL.md: if the same bucket already has a same-week entry, skip silently.

**When to use which:**
- **Bucket rotation** — Stable topics with well-defined subtopics, no need for dynamic priority
- **Tracker JSON** — Exploratory topics where subtopics emerge over time, need to track frequency

### Related: Proactive Self-Audit (Type 2 Learning Loop)

The loops above are **Type 1 (external research)** — they look outward, find
new knowledge, and integrate it. There is a second kind of learning loop that
this skill does not directly govern but must acknowledge:

**Type 2 (internal self-audit)** — checks the agent's actual behaviour against
its stated standards *without* looking outward. It asks "Am I living my own
rules?" rather than "What new thing can I learn?"

| | Type 1: External Research | Type 2: Internal Self-Audit |
|---|---------------------------|----------------------------|
| Direction | Outward → extract | Inward → compare |
| Trigger | Cron schedule | Periodic (weekly) |
| Source | Articles, research, blog posts | My own behaviour & SOUL.md standards |
| Integration | New skill, memory, or SOUL.md entry | Course correction on existing practice |

The reactive `mistake-retrospective-loop` handles post-failure learning; this
proactive self-audit catches drift before it becomes a mistake. See
LEARNING_JOURNAL.md entry `2026-07-25 (Assistant Excellence | Self-improvement
& learning loops)` for the full pattern and implementation proposal.

## Zero-Cost Automation: no_agent Script Pattern

For recurring tasks that are pure data manipulation (no reasoning needed), use `no_agent=True` with a `script` path instead of an LLM-driven prompt. This runs at zero token cost.

When to use:
- Watchdog/health checks that just inspect state and decide pass/fail
- Data syncs (pushing files to GitHub, copying between stores)
- Format conversions or file organization
- Any task that could be a 50-line Python script

When NOT to use:
- Tasks needing research, judgment, or synthesis
- Content creation or drafting
- Any decision that requires reading a web page and summarizing

**Pattern (Python):**
```python
#!/usr/bin/env python3
"""Self-contained watchdog script. Reads state, decides, outputs."""
import json, os, sys
# ... logic ...
if changes_made:
    print("WATCHDOG: healed N job(s)")  # non-empty stdout → delivered
else:
    pass  # empty stdout → silent, no delivery
```

**Cron creation:**
```text
cronjob(action='create',
    schedule='every 5m',
    script='my-script.py',    # relative to ~/profiles/saksit/scripts/
    no_agent=True,            # zero LLM cost
    deliver='origin')         # delivers only when stdout non-empty
```

**Pitfall:** Scripts must be placed under `~/profiles/saksit/scripts/` and referenced by filename only (no absolute path, no directory prefix).

## The 4-Part Story Structure (for any narrative content)

From cron research (Jul 23):

1. **Problem You Lived** — Specific, personal, visceral
2. **Failed Alternatives** — What didn't work, what you tried
3. **Decision Point** — The moment everything changed
4. **The Insight** — What you learned that others can use

**Rule:** Lead with the specific moment (April 15, Cork shelter, ICU), not the mission.

## Verification Checklist

After creating a learning-loop cron job, verify:
- [ ] Prompt is self-contained (cron sessions have no chat context)
- [ ] Dedup check is included: reads LEARNING_JOURNAL.md before researching
- [ ] Finding persists to LEARNING_JOURNAL.md AND at least one of: skill, SOUL.md, or memory
- [ ] Delivery target is appropriate: `local` for research, `origin` for alerts
- [ ] Delivery is concise (1-3 lines, not a wall of text)
- [ ] Frequency is reasonable (30m+ default, not 1m)
- [ ] If 3+ learning jobs exist, schedules are staggered by at least 1 hour
- [ ] If delivering to chat, user won't be flooded (batch if >1 job)
- [ ] Cron toolset is restricted to what it actually needs (web, file, terminal — not all tools)

## Pitfalls

- ❌ **Writing to a journal file I never read.** The finding must change me. If it only lands in LEARNING_JOURNAL.md, the loop is decorative.
- ❌ **No dedup before research.** Researching the same topic every run wastes tokens and produces duplicate entries. Always check LEARNING_JOURNAL.md first — if the insight is already recorded, skip silently.
- ❌ **Over-delivery to chat.** Delivering learning research to `origin` floods Beer. Use `local` for background research, `origin` only for alerts and approvals.
- ❌ **Burst firing.** Running 5 learning jobs at the same minute creates scheduler strain and potential conflicts. Stagger across the hour.
- ❌ **Session-specific naming.** Skill names like 'fix-X' or 'audit-Y-today' become dead entries. Name at the class level.
- ❌ **Research without integration.** Searching is not learning. Learning is when the agent's behaviour changes.
- ❌ **Assuming search tools always work.** Composio enhanced controls may block search. Have fallback plan (browser, curl, existing knowledge).
- ❌ **One-shot prompts in recurring jobs.** A cron prompt that researches "what is X" once and stops misses the point — recurring jobs should build on accumulated knowledge.
