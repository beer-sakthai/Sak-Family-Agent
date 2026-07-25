# Cron Watchdog Self-Heal

Auto-detect and re-enable cron jobs that have stopped, become disabled, or
entered a "completed" state when they should still be recurring.

## Tool constraint

The `cronjob` tool (from the `cronjob` toolset) is **not available** in cron
sessions. It only exists in normal CLI/Telegram sessions. To inspect and
modify jobs from a cron session, access the file directly:

- **Jobs file:** `~/profiles/sakthai/cron/jobs.json`
- **Structure:** `{"jobs": [...], "updated_at": "..."}`

## Procedure

1. **List all jobs** — read the file:
   ```
   read_file(path='~/profiles/sakthai/cron/jobs.json')
   ```

2. **Inspect each job's state.** A recurring job (repeat: forever) needs
   healing if:
   - `enabled: false` AND no `paused_reason` is set
   - `state: "completed"` when it should be recurring
   - `last_status` indicates an error (not `"ok"`)

3. **Re-enable** — since `cronjob(action='update')` is unavailable:
   - Read `jobs.json`
   - Set `enabled: true` and `state: "scheduled"` for the affected job
   - Write the full updated JSON back via `write_file`

4. **Check scheduler health** — ticker timestamps at
   `~/profiles/sakthai/cron/ticker_last_success` and
   `~/profiles/sakthai/cron/ticker_heartbeat` should be recent (Unix epoch
   seconds within the last few minutes).

## Handling disabled skills

The `cron-watchdog-self-heal` skill file exists on disk at:
```
~/profiles/sakthai/skills/environment-automation/cron-watchdog-self-heal/SKILL.md
```
but `skill_view()` may return "Skill is disabled" when Hermes' skill index
does not have it registered. Work around this by reading the file directly
with `read_file()`.

**Duplicate paths:** The skill may also exist at
`~/profiles/sakthai/skills/skills/environment-automation/cron-watchdog-self-heal/SKILL.md`
due to a `skills/` subdirectory within `skills/`. The duplicate won't appear
in `skills_list` output — only the index controls visibility.

## Pitfalls

- Do NOT heal intentionally paused jobs (check `paused_reason`).
- Do NOT heal one-shot jobs (repeat: with `times` set, not null).
- If a job keeps failing immediately after heal, report the failure loop
  rather than re-healing.
- Rate-limit reports — only notify on actual changes, not every tick.
- After writing `jobs.json`, verify the format is valid JSON and that the
  `"updated_at"` field is updated.
