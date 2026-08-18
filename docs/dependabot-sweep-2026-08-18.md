# Dependabot sweep — 2026-08-18

GitHub reported **35 open Dependabot alerts** on `main` (11 high, 16 moderate,
8 low). This note records what was fixed, what cannot be fixed by a version
bump, and — importantly — how much of the alert list is *accounted for* versus
still unexplained.

## Why the usual audits said "clean"

Running `pip-audit` over `uv.lock` and `npm`/`pnpm audit` over the lockfiles
reports **zero** vulnerabilities. That is not a contradiction; it is two blind
spots:

1. **`uv export --all-extras` does not include dependency *groups*.** The
   `evals`, `lint`, and `fuzz` groups are `[dependency-groups]`, not
   `[project.optional-dependencies]`, so they never reached `pip-audit`. This
   is what hid `sqlitedict` (below). `dependency-audit.yml` has the same gap.
2. **Lockfile audits only see manifests that *have* a lockfile.** Dependabot
   also parses manifests that do not, and for those it resolves each `>=`
   constraint to its **lower bound**. `gradio>=6.0` is therefore evaluated as
   gradio 6.0.0 — which is behind six published advisories — even though a real
   install would get 6.24.0 and be fine.

Blind spot 2 is the bulk of the alert list. When auditing this repo, scan the
unlocked manifests at their declared lower bounds, not just the lockfiles.

## Fixed

Both fixes raise a floor past every advisory affecting the old floor. Neither
changes what a real install resolves to today.

| Manifest | Change | Closes |
|---|---|---|
| `personas/sakthai/skills/SakThai-hf-gradio/templates/space-requirements.txt` | `gradio>=6.0,<7.0` → `>=6.15.1,<7.0` | 6 advisories |
| `sakthai-chat-cli/…/SakThai-hf-gradio/templates/space-requirements.txt` | same | 6 advisories |
| `personas/sakthai/agent-self-evolution/pyproject.toml` | `pytest>=7.0` → `>=9.1.1` | 1 advisory |
| `personas/shared/agent-self-evolution/pyproject.toml` | same | 1 advisory |
| `sakthai-chat-cli/personas/sakthai/agent-self-evolution/pyproject.toml` | same | 1 advisory |

The gradio floor is 6.15.1 because that is the highest fixed-in version across
the six: GHSA-jmh7-g254-2cq9 (SSRF via `proxy_url`, high), GHSA-7hp7-4p35-3cx2
(cookie injection, high), GHSA-39mp-8hj3-5c49 (Windows path traversal, high),
GHSA-pfjf-5gxr-995x (OAuth open redirect), GHSA-h3h8-3v2v-rg7m and
GHSA-6655-8ph2-63j3 (low). The pytest floor is 9.1.1 — GHSA-6w46-j5rx-g56g
(`tmpdir` handling) is fixed in 9.0.3, and 9.1.1 is what the root
`pyproject.toml` already pins, so the two now agree.

The three `agent-self-evolution` copies are all of them: the other five
personas symlink to `personas/shared/agent-self-evolution`.

## No upstream fix — needs a dismissal decision, not a bump

| Package | Advisory | Where | Why it cannot be bumped |
|---|---|---|---|
| `sqlitedict` 2.1.0 | GHSA-g4r7-86gm-pgqc (high) — insecure deserialization | root `uv.lock`, transitive via `lm-eval` | 2.1.0 **is** the latest release (Dec 2022). The advisory has no fixed version. |
| `dspy` | GHSA-vvw2-h478-xwr3 (moderate) — does not properly restrict file reads | the 3 `agent-self-evolution` manifests | Advisory covers all versions including the current 3.3.0. No fixed version. |

Suggested handling, for whoever dismisses these:

- **sqlitedict** — reachable only from the `evals` dependency group, which only
  `run-evals.yml` installs (weekly, `uv sync --group evals`). It is never
  installed by `ci.yml`, and nothing in `sakthai` imports it. The deserialization
  sink is not fed by untrusted input in that job. Reasonable dismissal:
  *"no fix available; dev/eval-only path."*
- **dspy** — `agent-self-evolution` is a subproject with its own workflow; the
  file-read weakness matters only if it is pointed at untrusted prompts.

## Accounting — this sweep does not explain all 35

Fixed 15 alert-equivalents, identified 4 more as unfixable: **19 of 35**. The
remaining ~16 are not yet attributed. The most likely reason is that Dependabot
resolves the *full transitive tree* of an unlocked manifest at its lower bounds,
while the scan behind this note only resolved each manifest's **direct**
declarations. `dspy>=3.0.0` and `optuna>=3.0` pull large trees whose lower-bound
resolutions were never queried.

Closing that gap properly needs the actual alert list from
`/security/dependabot`, which is not readable without a token carrying
`security_events`. Do not assume this note is exhaustive.
