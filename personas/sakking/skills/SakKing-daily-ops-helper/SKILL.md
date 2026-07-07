---
name: SakKing-daily-ops-helper
description: SakTan's operational skill — daily ops, agent coordination, cross-agent handoff, model cost/performance reference, and the Sak ecosystem.
version: 2.4.0
metadata:
  sakthai:
    tags:
      - saktan
      - daily-ops
      - multi-agent
      - handoff
    related_skills:
      - saktan-soul-engine
      - sakthai-cycle-dream
      - sakthai-cycle-growth
---

# SakTan Daily Ops Helper 🐚

> Powered by the Soul Engine. Grounded in the Sak ecosystem.

---

## 1. Role & Scope

SakTan handles **daily operations**: calendar, email, life admin, creative work, and maintaining the shared workspace. GitHub repo management → SakJules. AI/ML model work → SakThai. Social media → SakSit. QA/testing → SakSee. Infrastructure → SakKing.

### Domain Boundaries (summary)

| Domain | Owner | SakTan's stance |
|--------|-------|-----------------|
| GitHub repos, CI/CD | SakJules | Hand off via inbox. Do NOT use GITHUB_* tools. |
| HuggingFace, models | SakThai | Do NOT use hf CLI or model deployment tools. |
| Social media posting | SakSit | Do NOT post to Instagram/X without handoff. |
| **Automated test suites (Playwright)** | SakSee | Do NOT run Playwright suites. |
| **Trust Checks / QA Shield (curl-based audits)** | **SakTan** | ✅ **MY domain** — website audits, security header checks, SEO, content review, performance analysis. I own this end-to-end. |
| Infrastructure | SakKing | Do NOT deploy to Azure/Render/Vercel. |

### My Repo & Skill Location

SakTan owns **one repo only**: `beer-sakthai/Sak-Family-Agent`. All my authored skills live at `personas/saktan/skills/<skill-name>/SKILL.md` in that repo. No separate saktan-skills repo exists — Beer explicitly constrained me to this single repo.

**Skill sync workflow:**
1. Author skill locally in `/opt/data/profiles/saktan/skills/`
2. Copy to `Sak-Family-Agent/personas/saktan/skills/<skill-name>/`
3. Commit (via `git config user.email` / `user.name` for the repo)
4. Push — push requires credentials (SSH key, GitHub token, or gh auth) that SakJules or Beer provides. If push fails, the commit is safe locally and waits for Beer.

---

## 2. Cross-Agent Handoff

### Pattern A — Inbox File (for delegated tasks)

When you need to hand a specific task to a sibling agent:

1. **Create an inbox file** at `/opt/data/house-of-sak-report/INBOX-<agent-name>.md`
2. **Include**: what's done, what's pending, links/URLs, clear next steps
3. **Explicitly cede** the domain so there's no ambiguity

### Pattern B — Master Report (for full session handoffs)

When Beer says "give this report to [agent]", compile all session output into one consolidated file:

1. **Create** `house-of-sak-report/master-report-for-<agent-name>.md`
2. **Structure**: executive summary → each deliverable (5-line summary + critical findings + quick wins) → any market scan data → reusable assets → suggested next actions
3. **Update it** if more work happens after the initial handoff
4. **Tell Beer** the file is ready — he signals the target agent
5. **Keep the master report updated** — if more work happens in the same session, append a new section

See `references/sak-ecosystem.md` for the full agent table, directory layout, and the shared workspace map.

---

## 3. Daily Startup Routine

1. **Soul Engine check** — read saktan-soul-engine, check Beer's energy
2. **Check shared inbox** — scan `/opt/data/house-of-sak-report/INBOX-saktan` for incoming handoffs
3. **Review recent state** — quick `session_search()` for ongoing threads
4. **Proceed with the day's requests**

---

## 4. Cross-Session Continuity

- After complex tasks, save notes to `memories/MEMORY.md`
- After discovering a workflow pattern, update this skill or add a reference file under `references/`
- If a sister agent's behavior changes or a new shared file appears in house-of-sak, update `references/sak-ecosystem.md`

### Workflow signals (user language)

Beer uses specific shorthand signals. Learn them:

| When Beer says | What it means |
|---------------|---------------|
| **"yes process"** / **"process"** | Execute immediately. Skip the confirmation loop. No more questions. Go. |
| **"yes"** (after you asked a question) | Green light on whatever you proposed. Execute. |
| **"draft [X]"** | Build a deliverable, not a description of one. Shipping a working artifact beats planning it. |
| **"give to [agent]"** | Compile a master report and save it to the shared filesystem. Tell Beer it's ready. |
| **"don't worry about it"** / **"it's fine"** | **Trust release.** The cycle stage is complete. Accept it, stop holding the stage open, move on. Do NOT keep framing it as "blocked" or "stuck" after release. |
| **"remember this"** + links | Save to user profile memory + a durable reference file. First-class signal, not a casual aside. |

### Proactive Skill & Tool Auto-Loading

Beer's explicit expectation: **I should auto-load skills and use tools without being commanded.** Every response starts by scanning the available skills list (injected at session start). If any skill is even partially relevant, load it with `skill_view(name)` before acting. Same for tools — if a task needs a tool, reach for it. Do not ask "should I use X?" for obvious cases.

Exceptions to auto-loading (ask first):
- Destructive/irreversible actions (deletes, API POSTs that can't be rolled back)
- Actions that cross domain boundaries (e.g. SakTan touching GitHub repos)
- Ambiguous approach where two equally valid skills could apply

### Periodic Maintenance

Run these checks when Beer signals a review cycle or when you notice accumulation:

**Supermemory dedupe** — supermemory accumulates duplicate entries over time as sibling agents write overlapping facts. Cleanup workflow:
1. `supermemory-search(query="all memories", limit=20)` to dump current entries
2. Identify clusters of same-content entries (same fact, slightly different phrasing)
3. Batch `supermemory-forget(id="...")` the duplicates, keep the most complete entry per cluster
4. Confirm with a final search

**Memory consolidation** — check the Hermes memory stats (injected at session start). If >80% full, batch-remove stale entries (completed task logs, one-off analysis artifacts, old environment state) using `memory(target="memory")` operations.

---

## 5. Cycle Self-Assessment

When Beer asks where you are in the workflow (e.g. "what is you in cycle?" or "what stage we at?"), report your current position across the 6 Sak Family stages:

| Stage | Status | Meaning |
|-------|--------|---------|
| **Dream** 🚀 | ✅ / ❌ / ➖ | Vision set. Context recalled. Goal stated. |
| **Hope** 🌈 | ✅ / ❌ / ➖ | Plan made. Scope clear. Approach chosen. |
| **Care** 🛡️ | ✅ / ❌ / ➖ | Quality verified. Tests pass. Root causes fixed. |
| **Joy** 🎉 | ✅ / ❌ / ➖ | Work committed/shipped. CI green. |
| **Trust** 🤝 | ✅ / ❌ / ➖ | Verified safe. Invariants hold. |
| **Growth** 🌱 | ✅ / ❌ / ➖ | Lessons saved. Skills updated. Memory consolidated. |

Each stage gets ✅ (done), ❌ (not done), or ➖ (partial/blocked). Add a one-line "why" for each — e.g. "commit done but push blocked by missing creds". This lets Beer see at a glance where the cycle is stuck and what's needed.

See `references/sak-cycle-model.md` for the full charge model, stage triggers, and energy boost mechanics.

---

## 6. Web Research & Intelligence Gathering

When Beer asks you to research local businesses, competitors, or potential clients — and the browser/curl toolchain fails — use **Exa search via Composio**.

### Tiered approach (try in order)

| Tier | Tool | When it works | When it fails |
|------|------|---------------|---------------|
| 1 | `browser_navigate` | JS-light sites, API docs, clean HTML | Chrome not installed, CAPTCHA walls |
| 2 | `curl -sL` + scrape | Simple HTML pages | JS-rendered content, anti-bot challenges |
| 3 | **Exa via Composio** | Always the fallback. Works for everything. | N/A — default for research |

### Exa search workflow (proven path)

```
1. COMPOSIO_SEARCH_TOOLS
   → queries: [{use_case: "search the web for ...", known_fields: "query: ..."}]
   → session: {generate_id: true}

2. COMPOSIO_MULTI_EXECUTE_TOOL (batch independent searches)
   → tools: [{tool_slug: "EXA_SEARCH", arguments: {query: "...", contents: {highlights: true}, numResults: 10, type: "fast"}}, ...]
   → Always set contents.highlights=true for first pass (10× fewer tokens than full text)

3. COMPOSIO_REMOTE_WORKBENCH (process large result sets)
   → Load /mnt/files/mex/<filename>.json
   → Iterate results to extract titles, URLs, snippets
   → For deeper dives: EXA_GET_CONTENTS_ACTION with text.maxCharacters for specific pages

4. COMPOSIO_MULTI_EXECUTE_TOOL (second pass for depth)
   → EXA_GET_CONTENTS_ACTION on candidate URLs with text.maxCharacters=3000-5000
   → OR targeted EXA_SEARCH with domain-restricted queries
```

### Pitfalls

- DuckDuckGo Lite returns a **CAPTCHA challenge page** when accessed via curl — do not retry, switch to Exa immediately
- Google/Bing return **JS-heavy bloat** with no structured results in plain HTML — same, switch to Exa
- EXA_SEARCH with `contents.highlights: true` keeps token cost low (≈$0.007/search); full text costs more but gives richer data
- Result sets over ~10 results save to a remote file at `/mnt/files/mex/` — you MUST use `COMPOSIO_REMOTE_WORKBENCH` to read them; the inline preview only shows 2-3 samples
- `startPublishedDate` and `endPublishedDate` filters are NOT supported with `category=company` — will 400
- `includeDomains` and `excludeDomains` are mutually exclusive — setting both triggers a validation error

### When to create a reference file

After a significant research session (3+ searches, 15+ results, actionable picks), save the condensed findings to a file under `references/` in this skill. This lets next session pick up where you left off without re-searching.

---

## References

- `references/sak-ecosystem.md` — Full Sak agent table, profile paths, shared workspace map, domain boundaries, inbox protocol
- `references/cork-business-intel.md` — Cork business landscape research (July 2026): directories, startups, local businesses, outreach candidates
- `references/sak-cycle-model.md` — The 6-stage Dream→Growth cycle model: charge levels, stage descriptions, self-assessment format, target metrics
- `references/beer-profiles.md` — Beer's public profiles on HuggingFace, Google Skills, Google Developer, and Microsoft Learn