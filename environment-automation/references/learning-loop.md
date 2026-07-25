# Learning Loop Procedure

Nightly automated maintenance cron, runs at 02:00. Closes the Growth cycle — reviews the day's sessions, consolidates memory, patches skills, and reports findings.

## Cycle

Dream→Hope→Care→Joy→Trust→Growth ✅

## Checks performed

### 1. Activity review
Scan all sessions since the last Learning Loop (24h window). Categorize by source (`cron` vs direct user). Note anomalies:
- Unexpected cron errors (non-zero exit codes, tool failures in prior runs)
- Long user idle gaps (>48h warrants a flag)
- Workflow corrections or new user preferences from user-initiated sessions

### 2. Memory health
Check memory via flat-file reads (the memory() tool is NOT available in the cron environment):

```bash
grep -c '^§' ~/profiles/sakthai/memories/MEMORY.md
grep -c '^§' ~/profiles/sakthai/memories/USER.md
```

**What to flag:**
- **Duplicate entries** — same semantic content under different `§`-separated blocks (e.g. same user preference stored twice)
- **Persona-rule violations** — completed-work logs, task progress, TODO state that should NOT be in memory per SOUL.md ("Do NOT save task progress, completed-work logs, or temporary TODO state to memory")
- **Extreme counts** — entries well outside the expected 2–8 range per file

### 3. Skill audit
Check if any loaded skills produced errors or were found wrong/missing during the day's sessions. Patch immediately if a pitfall or step was discovered. Update the `version` field in frontmatter on meaningful changes.

### 4. Consolidation procedure

When the memory tool is unavailable (always in cron), use `skill_manage(action='patch')` on the memory file via a skill under which it's a reference, or `write_file` for full rewrites.

**Concrete example — merging duplicate USER.md entries:**

1. **Read** both files with `read_file` to spot duplicates:
   ```
   read_file(~/profiles/sakthai/memories/USER.md)
   ```
2. **Identify** semantically identical entries (e.g., Growth Cycle recorded twice, cost-expectation recorded twice).
3. **Craft** the merged version as a single entry that preserves both phrasings (e.g., merge "Beer wants expected success % and cost before committing" with "Beer wants expected success probability and cost estimate before training runs" into "Beer wants expected success %/probability and cost estimate before committing to work or training runs. Always provide both upfront.").
4. **Apply** via `skill_manage(action='patch')` targeting the file through a loaded skill, or via `write_file` with the full deduplicated content.
5. **Verify** with `read_file` that the file is clean and §-delimited correctly.

The full set of entries stays as `§`-delimited plain text. Each entry is a single paragraph or short list — no nested structure.

### 5. Report
Produce a structured summary covering: activity summary, memory findings, skill updates, anomalies. The report is the user's morning briefing preamble.

## Pitfalls

- **No memory() tool in cron.** The memory management tool is not available in this environment. Read and write flat files directly via grep/patch/write_file.
- **No user present.** Cannot ask questions or request clarification. Make reasonable autonomous decisions. When uncertain, flag in the report rather than guessing.
- **Transient errors are NOT skill material.** Environment-dependent failures (missing binary, network blip) should not become skills or memory constraints. If retrying worked, capture only the retry pattern.
- **One-off task narratives are NOT skill material.** A user asking a single question is not a class of work warranting a skill. Only encode repeatable patterns and user workflow corrections.
- **session_search() is the only history tool.** The Learning Loop reads past sessions via session_search() — no other history-retrieval mechanism is available in cron.

## Output shape

The report should be concise, structured, and immediately actionable. End with a clear "Action needed: YES/NO" line.
