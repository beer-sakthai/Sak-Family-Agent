# Cron Job Health Check

Check all Hermes cron jobs and re-enable any that are down.

## Trigger

Run this whenever the user asks for a cron job check, or as a periodic maintenance task.

## Procedure

### 1. Find the right cron directory

The cron directory is profile-specific. Two possible locations exist:

| Profile root style | Cron path |
|---|---|
| `~/profiles/<name>/` (non-standard, as in this sakthai setup) | `~/profiles/<name>/cron/` |
| `~/.hermes/profiles/<name>/` (Hermes default) | `~/.hermes/profiles/<name>/cron/` |

**Pitfall:** This sakthai profile stores cron at `~/profiles/sakthai/cron/`, NOT at `~/.hermes/profiles/sakthai/cron/`. Checking the wrong directory yields a false negative — no jobs found when jobs may actually exist.

### 2. List jobs via `hermes cron list`

If the `hermes` CLI is available, use:
```bash
hermes cron list              # active jobs only
hermes cron list --all        # include disabled jobs
```

The CLI is authoritative — it reads the profile's `state.db`.

### 3. If `hermes` CLI is unavailable

Fall back to filesystem inspection of the cron directory.

```bash
ls -la ~/profiles/<name>/cron/
```

Each job is stored as a JSON file (`{uuid}.json`). Individual job files contain:
- `schedule`: cron expression or duration string
- `enabled`: boolean
- `state`: current run state
- `prompt`: job instruction
- `delivery`: delivery config (platform/channel)
- `skills`: optional skill list to preload
- `last_run_at`: ISO timestamp
- `model` / `provider`: optional overrides

The `output/` subdirectory holds per-run logs.

### 4. Heal disabled or completed jobs

Check each job file for `"enabled": false` or `"state": "completed"`.

**With CLI:**
```bash
hermes cron resume <job-id>
```

**Without CLI (manual patch):**
Edit the job JSON file, set `"enabled": true` and reset `"state"` to `"idle"` (or delete the state field).

### 5. Report

Only report when you actually healed something — one line per healed job.
If all jobs are healthy, respond `[SILENT]` to suppress delivery.

## Verification

After healing, confirm by running `hermes cron list` or checking that `enabled: true` persists in the job file.

## Pitfalls

- **Wrong profile path:** This sakthai profile stores cron at `~/profiles/sakthai/cron/`, not the default `~/.hermes/profiles/sakthai/cron/`. Always consult `environment-automation` skill for correct paths.
- **`hermes` CLI missing in sandbox:** The `hermes` binary may not be on `$PATH` in remote sandboxes. Fall back to filesystem inspection.
- **State vs enabled:** A job can be `enabled: true` but `state: completed` — it won't run again until state is reset. Check both fields.
- **Cron output dir:** Per-run logs accumulate in `<cron-dir>/output/`. Clean up periodically.
