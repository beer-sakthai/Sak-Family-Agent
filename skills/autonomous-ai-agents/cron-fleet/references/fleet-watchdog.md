# Fleet Watchdog — Cron Cross-Profile Notes

## What this session discovered

Running `cron-fleet` across the default + sakthai + hermesagent + saksit
profiles on a single machine revealed two durable gotchas.

### 1. `--all` is required to see disabled / completed jobs

`hermes cron list` hides any job that is not currently `[active]`.
To audit the full fleet you **must** pass `--all`.

### 2. JSON state ≠ CLI display name

The CLI labels a disabled job `[completed]`, but the underlying JSON
carries `"enabled": false` and `"state": "completed"`. A job can be
disabled yet show `last_status: "ok"` because it ran successfully before
being paused — this is the safe auto-resume candidate.

### 3. Profile boundary

Each profile has an isolated `$HERMES_HOME/cron/jobs.json` and an
independent scheduler process. A disabled job in `default` does not
appear in `sakthai`. Fleet audits need to check every profile explicitly.

## Reproducing the watchdog

```bash
for p in default sakthai hermesagent saksit; do
  export HERMES_HOME="$HOME/.hermes"
  [[ $p != default ]] && HERMES_HOME="$HOME/.hermes/profiles/$p"
  echo "=== $p ==="
  hermes cron list --all
done
```

## When to re-enable

Safe resume mask:

```bash
hermes cron resume <id>
```

Only when **both** hold:
- `enabled: false` (job is currently off)
- `last_status = "ok"` (last run was healthy)

Chronic error jobs (`last_status: "error"` or non-null `last_delivery_error`)
must be reported and left disabled for human triage.
