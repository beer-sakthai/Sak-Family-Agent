# Enabling Dependabot on this repository

`.github/dependabot.yml` configures the **version-update queue** and nothing
else. Three things it cannot switch on live in repository settings, and until
they are on, most of what this repository does about vulnerable dependencies
does not happen:

| Setting | What it does | Can `dependabot.yml` enable it? |
|---|---|---|
| **Dependency graph** | Parses every manifest in the repository into a dependency list. Everything else is built on it. | No |
| **Dependabot alerts** | Matches that list against the GitHub Advisory Database and files alerts. | No |
| **Dependabot security updates** | Opens pull requests that fix those alerts. | No |
| Dependabot version updates | Routine bumps on a schedule. | **Yes — that is what the file is** |

The distinction matters more here than it looks. Alerts come from the dependency
graph, which scans the **whole repository**. Version-update pull requests only
reach directories listed in `dependabot.yml`. A manifest that alerts but has no
entry will keep alerting and can never self-heal — which is precisely what
happened to the six gradio advisories in
[`dependabot-sweep-2026-08-18.md`](dependabot-sweep-2026-08-18.md).

## The click path (one time)

**Settings → Advanced Security** (older UI: *Code security and analysis*):

1. **Dependency graph** → *Enable*. On a public repository this is always on and
   the control is absent; that is expected, not a missing step.
2. **Dependabot alerts** → *Enable*.
3. **Dependabot security updates** → *Enable*. This is greyed out until alerts
   are on — enable them in that order.
4. Optional: **Dependabot on Actions runners**, which makes update jobs run on
   your runners instead of GitHub's hosted Dependabot infrastructure. Not
   required by anything in this repository.

## The scripted alternative

```bash
# Report what is currently on — read-only
GITHUB_TOKEN=<pat> bash scripts/enable_dependabot.sh

# Actually enable alerts + security updates
GITHUB_TOKEN=<pat> bash scripts/enable_dependabot.sh --apply
```

It is a dry run unless `--apply` is passed, mirroring
`scripts/code_scanning_analyses.py`. The token needs administration rights:
classic PAT with `repo`, or a fine-grained token with **Administration: write**.

## Create the labels first

**Dependabot silently drops labels that do not exist.** It creates
`dependencies` on its own; the rest must exist beforehand or the pull requests
arrive carrying only that one, with no error anywhere:

```bash
gh label create python         -c 3572A5 -d "Python dependencies"
gh label create javascript     -c F1E05A -d "JavaScript/Node dependencies"
gh label create docker         -c 384D54 -d "Container base images"
gh label create github_actions -c 2088FF -d "GitHub Actions versions"
gh label create security       -c D93F0B -d "Security advisories"
```

## The advisory report needs its own token

`.github/workflows/innersource-advisories.yml` reads
`GET /repos/{owner}/{repo}/dependabot/alerts` daily. **The Actions
`GITHUB_TOKEN` cannot call that endpoint.** Granting the job
`security-events: read` does not help: the Actions GitHub App does not carry the
"Dependabot alerts" permission at all, so the call returns
`403 Resource not accessible by integration`.

This is the one place Dependabot alerts differ from code scanning.
`.github/workflows/code-scanning-cleanup.yml` genuinely does read its alerts on
the stock token with a per-job `security-events: write`. Do not generalise from
it — that assumption produces a workflow that looks configured and 403s every
night while reporting zero alerts.

Add a PAT as the **`DEPENDABOT_ALERTS_TOKEN`** repository secret:

- classic — the `security_events` scope (or `repo` if the repository is private)
- fine-grained — the **Dependabot alerts: read** repository permission

The workflow fails loudly when the secret is absent rather than publishing an
empty report, and `scripts/dependabot_advisories.py` prints the same remedy on a
403. An advisory report that silently says "all clear" is worse than no report.

## Verifying it worked

```bash
# Settings are on
GITHUB_TOKEN=<pat> bash scripts/enable_dependabot.sh

# The alert list is readable, and is not silently empty
GITHUB_TOKEN=<pat> python scripts/dependabot_advisories.py list

# The config is well-formed and every directory resolves
uv run pytest tests/test_dependabot_config.py -q
```

On GitHub: the **Insights → Dependency graph → Dependabot** tab should list all
five ecosystems (`uv`, `pip`, `npm`, `docker`, `github-actions`) each with a
recent "last checked", and no "dependabot.yml is invalid" banner. The first
scheduled run of `innersource-advisories.yml` should open the standing issue
rather than fail on the token check.

## Related

- [`configuring-multi-ecosystem-updates.md`](configuring-multi-ecosystem-updates.md) — why the config is shaped the way it is
- [`../.github/INNERSOURCE.md`](../.github/INNERSOURCE.md) — who acts on an advisory, and how fast
- [`dependabot-sweep-2026-08-18.md`](dependabot-sweep-2026-08-18.md) — the sweep that motivated all of this
