# Scorecard: accepted risks

Four OpenSSF Scorecard findings stay open on purpose or are triaged as accepted risk. Code-Review and
Branch-Protection measure whether a second person reviews changes, and this
repository has one maintainer. CII-Best-Practices needs an OpenSSF Best
Practices badge, and the passing level needs an open-source licence. SAST
evaluates recent commits on main where automated SAST suites (CodeQL, SonarCloud,
Bandit) run on every push and PR. This page records why they are accepted, what
gates a merge instead, and what would let them close.

All four are dismissed as **Won't fix** on the Security tab with the
comments below, so a new finding is not lost among them. The
`code-scanning-cleanup.yml` workflow dismisses them (see
[Dismissal comments](#dismissal-comments)); the Security tab works too.
Revisit them when the conditions under [When to revisit](#when-to-revisit)
are met.

## Code-Review (alert #15460)

**What Scorecard measures.** It looks at the most recent changesets on
`main`. A changeset counts as reviewed when someone *other than its PR
author* approved the PR or merged it. Changesets authored by bots, such as
Dependabot, are skipped rather than counted. The score at the time of
writing: 0 of 6 human changesets reviewed.

**Why it can't pass here.** Every human-authored PR is opened and merged from
the maintainer's account, and GitHub does not let an author approve their
own PR. No configuration fixes that. Only a second reviewer does.

## Branch-Protection (alert #15379)

**What is enforced on `main`**, as read from the legacy branch-protection API and
the active `main` ruleset (verified 2026-11-15):

- branch deletion and force pushes are blocked;
- changes go through a pull request, and one approving review is required;
- the approval must come from a code owner and must cover the latest push;
- approvals are dismissed when new commits are pushed, and all review threads
  must be resolved before merge;
- commits must be signed, and `main` must maintain linear history;
- required status checks, with the branch kept up to date with `main`:
- the full protected-check set recorded in the branch-protection API, including
  both Python test/build legs, gitleaks, Bandit, OSSAR, CodeQL, repository
  skill validation, quality/security gates, and labeler;
- secret-scanning push protection;
- automatic merging remains available, but only after every required check and
  review rule passes. No bypass actor is configured for the `main` ruleset.

These controls intentionally trade unattended merges for provenance and review
integrity. A pull request opened by the sole code owner cannot self-approve;
automatic merging therefore requires a second eligible reviewer.

## CII-Best-Practices (alert #15462)

**What Scorecard measures.** Whether the project holds an OpenSSF Best
Practices badge from bestpractices.dev. The default policy of
`ossf/scorecard-action` raises an alert below the passing level. Project
[14039](https://www.bestpractices.dev/en/projects/14039) is in progress at
19%, which scores 2 of 10; passing scores 5.

**Why it can't pass here.** Passing needs every MUST criterion met, and three
are not:

- `floss_license`: `LICENSE` reserves all rights, a deliberate change from
  MIT recorded in `CHANGELOG.md`;
- `test`: the test suite must be released as FLOSS too;
- `version_unique`: there are no tagged releases.

Answering the rest of the questionnaire raises the percentage but not the
score, which stays at 2 until every MUST is met. The answers are drafted in
[`cii-best-practices-answers.md`](cii-best-practices-answers.md).

## SAST (alert #15465)

**What Scorecard measures.** It checks whether static application security testing
(SAST) tools (such as CodeQL, SonarCloud, or Bandit) run on all recent commits (~30)
on `main`. A project receives 10/10 if all 30 commits ran SAST.

**Why it scored 9/10.** Scorecard detected 27 out of 30 commits ran a SAST tool,
yielding score 9. Because Scorecard flags any score below 10 with a warning,
Code Scanning raised medium-severity alert #15465. CodeQL, SonarCloud, and Bandit
all execute on every push and pull request to `main`. As historical commits roll out
of the 30-commit evaluation window, the score remains protected by automated CI.

## What gates a merge instead

Every pull request runs the checks below. The required checks listed under
Branch-Protection block a merge; the rest report on the pull request and on
the Security tab.

- `ci.yml` on Python 3.11 and 3.12: ruff (lint and format), strict mypy,
  bandit, and pytest with a 96% branch-coverage floor;
- CodeQL, Bandit (SARIF) and Trivy (OSSAR);
- `dependency-review.yml`, which blocks high-severity advisories;
- gitleaks;
- zizmor over every workflow;
- pip-audit (`dependency-audit.yml`) whenever `pyproject.toml` or `uv.lock`
  changes;
- for changes under `apps/`, the dashboard's lint, type check, tests
  (including `fast-check` fuzzing of the URL parser) and production build.

See [`SECURITY.md`](SECURITY.md) and
[`security-hardening.md`](security-hardening.md) for the controls behind
these checks.

## When to revisit

**Code-Review and Branch-Protection**, when another maintainer joins:

1. Add them to `.github/CODEOWNERS`.
2. Confirm that the new owner can approve a representative pull request and
   that automatic merging proceeds only after the required checks and review
   controls are green.
3. Reopen both alerts on the Security tab. Code-Review then climbs as reviewed
   PRs replace the unreviewed ones in Scorecard's window.

**CII-Best-Practices**, if the project is relicensed under an OSI-approved
licence and starts tagging releases: enter the drafted answers, switching the
three blockers to Met, and reopen the alert. It closes once the badge reaches
passing.

## Dismissal comments

GitHub limits a dismissal comment to 280 characters; each of these fits.
To dismiss one, run **Code scanning cleanup** from the Actions tab with
`dismiss_alert` set to its number, `dismiss_comment` to its comment below,
and `apply` ticked (leave `apply` unticked for a dry run). The workflow's
`GITHUB_TOKEN` has the `security-events: write` permission this needs.

**Code-Review (#15460):**

> Accepted risk: one maintainer, and GitHub won't let an author approve their
> own PR. Every PR instead runs tests, strict mypy, CodeQL, Bandit, Trivy,
> gitleaks, dependency review and zizmor. Revisit when a second maintainer
> joins; see docs/scorecard-accepted-risks.md.

**Branch-Protection (#15379):**

> Accepted risk: main blocks deletion and force pushes, and requires PRs with
> resolved threads and up-to-date status checks. The next tier needs a
> required approval, which one maintainer can't give. Revisit with a second
> maintainer; see docs/scorecard-accepted-risks.md.

**CII-Best-Practices (#15462):**

> Accepted risk: the project is deliberately proprietary, and a passing badge
> needs a FLOSS licence (floss_license, test) and tagged releases
> (version_unique). Answers are drafted in docs/cii-best-practices-answers.md.
> Revisit if relicensed; see docs/scorecard-accepted-risks.md.

**SAST (#15465):**

> Accepted risk: SAST (CodeQL, SonarCloud, Bandit) runs on every push and PR to
> main; score 9 reflects historical window in Scorecard. See
> docs/scorecard-accepted-risks.md.

