# Innersource advisory policy

This repository is consumed internally. `personas/shared/sakthai/` is executed
by SakJules and SakTan through symlinks, `personas/shared/agent-self-evolution/`
backs five of the six personas, and `scripts/export_agent_repo.py` materializes
standalone per-persona repositories from this tree. A vulnerable dependency here
is not contained here.

This document says who watches for that, how it is published, how fast it gets
handled, and what to do when there is nothing to bump.

## How advisories reach you

You do not need Security-tab access.

[`innersource-advisories.yml`](workflows/innersource-advisories.yml) runs daily
and rewrites a single standing issue titled **"Innersource dependency advisory
report"**, labelled `security`. It is the whole current list, not a diff: an
advisory that disappears from it has been fixed or dismissed. Each row carries
the package, ecosystem, GHSA, **the fixed version or `none`**, and the manifest
path.

Run it yourself with a token carrying `security_events`:

```bash
GITHUB_TOKEN=<pat> python scripts/dependabot_advisories.py list
GITHUB_TOKEN=<pat> python scripts/dependabot_advisories.py report
```

`GITHUB_TOKEN` from Actions **cannot** read Dependabot alerts — see
[`docs/dependabot-setup.md`](../docs/dependabot-setup.md). The script fails with
that explanation rather than printing an empty list, because an advisory report
that silently says "all clear" is worse than no report.

## Ownership

Every path resolves to `@beer-sakthai` today (see [`CODEOWNERS`](CODEOWNERS)).
The split below exists to mark intent and to stay correct if reviewers are ever
divided — it is not a claim that six people are on call.

| Surface | Manifests | Reviewer |
|---|---|---|
| Core package + CLI | `/pyproject.toml`, `/uv.lock` | @beer-sakthai |
| Shared persona runtime | `personas/shared/sakthai/telegram/`, `personas/shared/agent-self-evolution/` | @beer-sakthai |
| Persona skill overlays | `personas/*/skills/**` manifests | @beer-sakthai |
| Services | `services/teams-copilot-mcp/` | @beer-sakthai |
| Frontend | `apps/sak_agent_dashboard/` | @beer-sakthai |
| Infrastructure images | `Dockerfile.sandbox`, `infra/sakthai-training-space/` | @beer-sakthai |
| Chat CLI | `sakthai-chat-cli/**` | @beer-sakthai |

## Response times

Measured from the advisory appearing in the report, not from disclosure.

| Severity | Triage by | Resolve or accept by |
|---|---|---|
| Critical | 1 working day | 3 working days |
| High | 2 working days | 7 working days |
| Moderate | 5 working days | 30 days |
| Low | next review pass | best effort |

"Resolve" means merged, not proposed. Dependabot's own pull request still needs
an approving review from a non-author ([`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md)),
and that review is the control — do not automate it away to hit a number here.

## When there is no fix

A row with **`none`** in the "Fixed in" column cannot be bumped. Bumping is not
the only valid outcome; accepting the risk *in writing* is. What is not
acceptable is the advisory sitting in the report untouched, re-read and
re-ignored every morning until it stops being read at all.

Record the decision by dismissing the alert in the Security tab with a reason,
and add the rationale to `KNOWN_UNFIXABLE` in
[`scripts/dependabot_advisories.py`](../scripts/dependabot_advisories.py) so the
report explains itself to the next reader.

Two are already accepted, from
[`docs/dependabot-sweep-2026-08-18.md`](../docs/dependabot-sweep-2026-08-18.md):

- **`sqlitedict` 2.1.0** — GHSA-g4r7-86gm-pgqc (high, insecure deserialization).
  2.1.0 is the latest release (Dec 2022) and the advisory names no fixed
  version. Transitive via `lm-eval` in the `evals` dependency group, which only
  `run-evals.yml` installs; nothing in `sakthai` imports it, and the
  deserialization sink is not fed by untrusted input in that job.
- **`dspy`** — GHSA-vvw2-h478-xwr3 (moderate, unrestricted file reads). Covers
  all versions including current. Reachable only from `agent-self-evolution`,
  and only when that subproject is pointed at untrusted prompts.

Both are also `--ignore-vuln`'d in
[`dependency-audit.yml`](workflows/dependency-audit.yml). Drop the exemptions the
day a fixed release ships.

## Reporting a vulnerable shared dependency

If you consume something from this repository and find a vulnerable dependency
the report does not list:

1. **Do not open a public issue** if the vulnerability is in this repository's
   own code rather than a third-party package — follow
   [`SECURITY.md`](../SECURITY.md) instead.
2. For a third-party package, comment on the standing advisory issue with the
   package, the version you resolved, the manifest path, and the GHSA.
3. If the manifest is missing from the report entirely, that is the more
   important finding — see below.

## Why something might be missing

**Alerts and updates are different surfaces, and this is the gap that bites.**

Dependabot *alerts* come from the dependency graph, which scans the whole
repository. Dependabot *version-update pull requests* only ever reach
directories listed in [`dependabot.yml`](dependabot.yml). A manifest that alerts
but has no entry will keep alerting and can never self-heal — which is exactly
what happened to the six gradio advisories in the 2026-08-18 sweep: they came
from `SakThai-hf-gradio/templates/space-requirements.txt`, no entry covered it,
and they had to be fixed by hand.

`tests/test_dependabot_config.py` now fails CI when a manifest has no entry,
unless it is listed in `UNCOVERED_BY_DESIGN` with a reason. Three families are
deliberately uncovered:

- **`*-requirements.in` paired with a hash-pinned `.lock`.** Dependabot
  regenerates a `.txt` beside the `.in`, never a `.lock`, and `bandit.yml`
  installs from the `.lock` with `--require-hashes`. A bump to the `.in` alone
  changes nothing while looking like it did. **These need manual attention** —
  regenerate with `scripts/gen_hash_lock.py`.
- **`*-google-workspace/scripts/setup.py`** — OAuth CLI scripts with no
  `setup()` call. Dependabot would extract zero dependencies.
- **`apps/agent_workflow_framework`** — has a CI job but no manifest at all. Its
  dependencies are undeclared; that is a real bug, not an exemption.

If you find a manifest that is neither covered nor listed there, the fix is an
entry in `dependabot.yml`, not a note here.
