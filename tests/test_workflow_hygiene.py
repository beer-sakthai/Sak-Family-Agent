"""Repository invariants for ``.github/workflows/`` and the scanners it drives.

Every rule here exists because the repository has already been broken by its
violation at least once, and in each case the break was silent — a workflow
that looked present and configured while doing nothing, or a security control
that disappeared inside a commit whose message described something else.

* **Loadable workflows.** A batch of pasted starter templates was removed on
  2026-08-13; one was named ``foo. yml`` (with a space), which GitHub ignores
  entirely rather than rejecting. A file that is not a real workflow must fail
  here rather than sit in the directory looking like coverage.

* **Top-level ``permissions:``.** This is Scorecard's ``TokenPermissionsID``,
  which the 2026-08-12 sweep spent three rounds closing. Every stock GitHub
  starter template omits it, so it regresses every time one is pasted in — most
  recently ``codeql.yml`` and ``eslint.yml``.

* **SHA-pinned actions.** Scorecard's ``PinnedDependenciesID``, and the reason
  the repository does not use floating tags anywhere. A tag can be moved by
  whoever owns the action; a commit SHA cannot.

* **The ``self-healing-ci.yml`` fork guard.** Commit ``93e306a``
  ("Sentinel: Fix heredoc interpreter execution bypass in workflow executor")
  reverted 446 lines it never mentioned, including the one-line condition that
  stops a fork's pull request from having its commit checked out and executed
  with ``contents: write`` and ``ANTHROPIC_API_KEY`` in scope. That is
  Scorecard's ``DangerousWorkflowID``, it had already been fixed and merged
  once, and nothing failed when it was undone. It fails here now.

* **The CodeQL scope config is wired in.** ``.github/codeql/codeql-config.yml``
  spent its first day inert because nothing referenced it: it was written for
  GitHub's default setup, which reads a config file only via a repository
  property. An advanced workflow reads it through ``config-file:``, and if that
  reference is dropped the file silently stops applying — the same failure mode,
  one layer along.

* **``.bandit`` is an ini file.** It was committed as a pasted fragment of
  GitHub Actions YAML, so bandit logged "Unable to parse config file" and every
  bare invocation ran with no configuration at all.

* **Pull-request workflows serialise per ref.** Until 2026-08-18 not one of the
  eleven push/pull-request workflows declared ``concurrency:``, so every
  force-push left the previous CI, Pylint, CodeQL, Bandit, SonarCloud, ESLint
  and subproject runs to finish against a commit nobody would look at again.
  The repository had accumulated 27,417 workflow runs. Every stock starter
  template omits the block, which is how it stayed missing.

* **Every job declares a timeout.** A job with no ``timeout-minutes`` holds a
  runner for GitHub's six-hour default. Four workflows set one; the other
  sixteen did not.

* **Composite actions are held to the same pinning rule.** Moving the shared
  Python bootstrap into ``.github/actions/setup-uv-python`` moved four
  workflows' ``uses:`` lines out of the directory this file used to scan. An
  unpinned action inside a composite is exactly as unpinned as one in a
  workflow, and it is now referenced by every gating Python job at once —
  ``ci.yml``, ``pylint.yml``, ``dependency-audit.yml`` and both of
  ``subprojects.yml``'s Python jobs — so the blast radius went up, not down,
  while the coverage would have gone to zero.

* **The self-hosted runner stays opt-in.** ``ci.yml`` selects its runner with
  ``vars.CI_RUNNER_LABEL || 'ubuntu-latest'``. A hard-coded ``[self-hosted]``
  does not *fail* when the host is unreachable — the job queues for up to 24
  hours and then expires, so the whole repository stops reporting with nothing
  red to point at. The fallback is what makes turning the runner off a
  settings-page action instead of a pull request, and it is one careless edit
  away from being lost.
"""

from __future__ import annotations

import configparser
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"
CODEQL_CONFIG = REPO_ROOT / ".github" / "codeql" / "codeql-config.yml"
BANDIT_INI = REPO_ROOT / ".bandit"

# A 40-character hex commit SHA — the only `uses:` ref this repository accepts.
_SHA_REF = re.compile(r"^[0-9a-f]{40}$")

# `uses:` on a step, tolerating quotes and a trailing `# v1.2.3` comment.
_USES = re.compile(r"""^\s*-?\s*uses:\s*["']?([^\s"'#]+)""")

# gh-aw agentic workflows are authored as Markdown and compiled to a
# `.lock.yml` beside them. The Markdown source is not itself a workflow, so it
# is checked for having a compiled counterpart rather than for workflow syntax.
_AGENTIC_SOURCE_SUFFIX = ".md"


def _workflow_files() -> list[Path]:
    return sorted(p for p in WORKFLOWS_DIR.iterdir() if p.is_file())


def _yaml_workflows() -> list[Path]:
    return [p for p in _workflow_files() if p.suffix in {".yml", ".yaml"}]


def _authored_workflows() -> list[Path]:
    """The workflows a human edits — the ``.lock.yml`` files are compiler output.

    gh-aw generates its lock files from the Markdown sources, and the shape of
    that output is upstream's decision: it emits a top-level ``concurrency:``
    but sets ``timeout-minutes`` on only one of each workflow's five-to-eight
    generated jobs. Holding generated files to a rule the generator does not
    follow would fail on every recompile, so the two rules below apply to the
    hand-written workflows and say so.
    """
    return [p for p in _yaml_workflows() if not p.name.endswith(".lock.yml")]


def _composite_actions() -> list[Path]:
    """The repository's own composite actions, if it has any.

    ``.github/actions/<name>/action.yml`` is where a local action lives; a
    workflow reaches it as ``uses: ./.github/actions/<name>``, which the
    pinning check skips (correctly — a local action is versioned with the
    repository, so there is no third-party commit to pin). What it must not
    skip is what the action itself pulls in.
    """
    if not ACTIONS_DIR.is_dir():
        return []
    return sorted(p for p in ACTIONS_DIR.glob("*/action.y*ml") if p.suffix in {".yml", ".yaml"})


def _triggers(data: dict) -> set[str]:
    """The event names in a workflow's ``on:``, however it was written.

    ``on:`` accepts a list (``on: [push]``), a mapping (``on:\\n  push:``) or a
    bare string, and PyYAML resolves the unquoted key ``on`` to the boolean
    ``True`` under YAML 1.1 — so the key itself has to be looked up both ways.
    """
    on = data.get("on", data.get(True))
    if isinstance(on, dict):
        return set(on)
    if isinstance(on, list):
        return set(on)
    return {on} if isinstance(on, str) else set()


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path.name}: top level is not a mapping"
    return data


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_every_file_is_a_workflow_or_an_agentic_source(path: Path) -> None:
    """No file in the workflows directory may be inert.

    GitHub loads ``.yml``/``.yaml`` and ignores everything else without
    complaint, so an unloadable file is indistinguishable from a working one
    until someone checks the Actions tab.
    """
    if path.suffix == _AGENTIC_SOURCE_SUFFIX:
        compiled = path.with_suffix(".lock.yml")
        assert compiled.exists(), (
            f"{path.name} is a gh-aw agentic workflow source with no compiled "
            f"{compiled.name} beside it — GitHub will never run it. "
            "Compile it, or move the file out of .github/workflows/."
        )
        return

    assert path.suffix in {".yml", ".yaml"}, (
        f"{path.name} is neither a workflow (.yml/.yaml) nor a gh-aw source "
        "(.md). GitHub silently ignores it."
    )


@pytest.mark.parametrize("path", _yaml_workflows(), ids=lambda p: p.name)
def test_workflow_has_trigger_and_jobs(path: Path) -> None:
    """A workflow needs ``on:`` and ``jobs:`` to do anything at all."""
    data = _load(path)
    # PyYAML resolves an unquoted `on:` key to the boolean True (YAML 1.1).
    assert "on" in data or True in data, f"{path.name}: no top-level `on:` trigger"
    assert data.get("jobs"), f"{path.name}: no `jobs:`"


@pytest.mark.parametrize("path", _yaml_workflows(), ids=lambda p: p.name)
def test_workflow_declares_top_level_permissions(path: Path) -> None:
    """Scorecard ``TokenPermissionsID``: default token scope must be narrowed.

    Without a top-level block the job inherits the repository default, which
    can be write-all. Job-level grants do not substitute — Scorecard reads the
    top level, and so does anyone auditing the file.
    """
    data = _load(path)
    assert "permissions" in data, (
        f"{path.name}: no top-level `permissions:` block. Add "
        "`permissions:\\n  contents: read` and grant anything wider per job."
    )


@pytest.mark.parametrize("path", _yaml_workflows(), ids=lambda p: p.name)
def test_actions_are_pinned_to_a_commit_sha(path: Path) -> None:
    """Scorecard ``PinnedDependenciesID``: no floating tags or branches."""
    unpinned: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = _USES.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue  # a local composite action, versioned with the repository
        if "@" not in ref or not _SHA_REF.match(ref.rsplit("@", 1)[1]):
            unpinned.append(f"{path.name}:{lineno}: {ref}")
    assert not unpinned, "Actions must be pinned to a 40-character commit SHA:\n" + "\n".join(
        unpinned
    )


def test_self_healing_ci_refuses_untrusted_forks() -> None:
    """Scorecard ``DangerousWorkflowID`` — the guard a bot silently reverted.

    ``self-healing-ci.yml`` triggers on ``workflow_run``, which runs in the base
    repository's context: the job holds ``contents: write``,
    ``pull-requests: write`` and ``ANTHROPIC_API_KEY``, and it checks out
    ``workflow_run.head_sha`` and executes it (``uv sync`` alone runs build
    hooks from the checked-out tree).

    The ``branches: [main]`` trigger filter does **not** make that safe: it
    matches the head branch *name*, so a pull request opened from a fork's own
    ``main`` produces a run whose ``head_branch`` is ``main`` and whose
    ``head_sha`` is the contributor's commit.
    """
    workflow = WORKFLOWS_DIR / "self-healing-ci.yml"
    condition = str(_load(workflow)["jobs"]["heal"]["if"])
    normalised = " ".join(condition.split())
    assert (
        "github.event.workflow_run.head_repository.full_name == github.repository" in normalised
    ), (
        "self-healing-ci.yml lost its fork guard. The `heal` job must require "
        "`github.event.workflow_run.head_repository.full_name == "
        "github.repository`, or a fork PR's commit is checked out and executed "
        "with write credentials and the Anthropic key in scope."
    )


def test_codeql_workflow_uses_the_scope_config() -> None:
    """The scope config only applies while a workflow points at it."""
    assert CODEQL_CONFIG.exists(), f"{CODEQL_CONFIG} is missing"

    workflow = WORKFLOWS_DIR / "codeql.yml"
    assert workflow.exists(), (
        "codeql.yml is missing. CodeQL runs here as an advanced setup; without "
        "this workflow nothing analyses the repository."
    )

    steps = _load(workflow)["jobs"]["analyze"]["steps"]
    init = [s for s in steps if "codeql-action/init" in str(s.get("uses", ""))]
    assert init, "codeql.yml has no `codeql-action/init` step"

    config_ref = str(init[0].get("with", {}).get("config-file", ""))
    assert config_ref.endswith(".github/codeql/codeql-config.yml"), (
        "codeql.yml must pass `config-file: ./.github/codeql/codeql-config.yml` "
        "to codeql-action/init. Without it the paths-ignore scope is inert and "
        "CodeQL re-reports the vendored trees the repository does not author."
    )


def test_codeql_scope_config_is_valid() -> None:
    """``paths-ignore`` must parse, and must still cover the vendored trees."""
    data = yaml.safe_load(CODEQL_CONFIG.read_text(encoding="utf-8"))
    ignored = set(data["paths-ignore"])
    for required in ("library", "sakthai-chat-cli", "tests"):
        assert required in ignored, f"codeql-config.yml no longer ignores {required!r}"


def test_bandit_ini_is_parseable_configuration() -> None:
    """``.bandit`` was once a pasted Actions YAML fragment, not a config.

    Bandit discovers this file by walking the scan target and reads
    command-line defaults from it. When it cannot parse it, it logs a warning
    and continues with *no* configuration — so a bare ``bandit -r .`` scanned
    every vendored tree and reported thousands of findings that the project's
    own settings exclude.
    """
    parser = configparser.ConfigParser()
    parser.read(BANDIT_INI, encoding="utf-8")
    assert parser.has_section("bandit"), (
        ".bandit has no [bandit] section — bandit cannot parse it and will run unconfigured."
    )
    skips = {s.strip() for s in parser.get("bandit", "skips").split(",")}
    assert "B101" in skips, ".bandit must skip B101; pytest is built on assert"
    assert parser.get("bandit", "exclude").strip(), ".bandit declares no exclusions"


def test_bandit_ini_exclusions_are_anchored() -> None:
    """Bandit matches exclusions by plain substring, so ``./`` is load-bearing.

    ``bandit/core/manager.py`` decides exclusion with
    ``any(x in path for x in excluded_path_strings)``. A bare ``build`` entry
    therefore also excludes ``training/hf-jobs/build_toolcalling_dataset.py`` —
    measured: 13 real findings in that one file disappeared before the entries
    were anchored.
    """
    parser = configparser.ConfigParser()
    parser.read(BANDIT_INI, encoding="utf-8")
    entries = [e.strip() for e in parser.get("bandit", "exclude").split(",") if e.strip()]
    unanchored = [e for e in entries if not e.startswith("./")]
    assert not unanchored, (
        "Every .bandit exclusion must start with './' so it can only match at "
        f"the repository root. Unanchored: {unanchored}"
    )


@pytest.mark.parametrize("path", _composite_actions(), ids=lambda p: p.parent.name)
def test_composite_actions_pin_what_they_use(path: Path) -> None:
    """Scorecard ``PinnedDependenciesID``, one directory along.

    Extracting the shared Python bootstrap into ``.github/actions/`` moved four
    workflows' ``uses:`` lines out of ``.github/workflows/``, which is the only
    place :func:`test_actions_are_pinned_to_a_commit_sha` looks. The action is
    referenced by every gating Python job in the repository, so an unpinned
    ``uses:`` inside it reaches further than an unpinned one in any single
    workflow — and nothing would have said so.
    """
    unpinned: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = _USES.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue
        if "@" not in ref or not _SHA_REF.match(ref.rsplit("@", 1)[1]):
            unpinned.append(f"{path.parent.name}/{path.name}:{lineno}: {ref}")
    assert not unpinned, (
        "A composite action must pin its own dependencies to a commit SHA:\n" + "\n".join(unpinned)
    )


@pytest.mark.parametrize("path", _composite_actions(), ids=lambda p: p.parent.name)
def test_composite_actions_are_well_formed(path: Path) -> None:
    """A composite action needs ``runs:`` to be an action at all.

    A file that parses as YAML but declares no ``runs:`` block is not ignored
    the way a misnamed workflow is — every workflow referencing it fails at
    once, with ``Can't find 'action.yml'``-shaped errors that point at the
    caller rather than at the file that is actually wrong.
    """
    data = _load(path)
    assert data.get("runs", {}).get("using") == "composite", (
        f"{path.parent.name}/{path.name}: not a composite action "
        "(`runs.using` must be `composite`)."
    )
    assert data.get("name"), f"{path.parent.name}/{path.name}: no `name:`"
    assert data.get("description"), (
        f"{path.parent.name}/{path.name}: no `description:` — required by "
        "GitHub, and the action fails to load without it."
    )


def test_ci_keeps_its_hosted_runner_fallback() -> None:
    """The self-hosted runner must stay opt-in, and reversible from a settings page.

    ``runs-on: ${{ vars.CI_RUNNER_LABEL || 'ubuntu-latest' }}`` means: use the
    self-hosted host when the repository variable names one, otherwise use a
    GitHub-hosted runner. Deleting the variable reverts CI to hosted runners on
    the very next run.

    Hard-coding ``runs-on: [self-hosted]`` instead is not a symmetric choice,
    because an unavailable runner does not produce a failure. A job dispatched
    to a label with nothing online **queues** — for up to 24 hours, then
    expires. Every pull request in the repository would stop reporting, with
    nothing red anywhere to explain why. Restoring service would then need a
    pull request, which needs CI, which is queued.

    See ``infra/self-hosted-runner/README.md``.
    """
    runs_on = str(_load(WORKFLOWS_DIR / "ci.yml")["jobs"]["test"]["runs-on"])
    normalised = " ".join(runs_on.split())
    assert "vars.CI_RUNNER_LABEL" in normalised, (
        "ci.yml's `test` job no longer selects its runner from the "
        "`CI_RUNNER_LABEL` repository variable."
    )
    assert "ubuntu-latest" in normalised, (
        "ci.yml's `test` job lost its GitHub-hosted fallback. Without it, an "
        "unreachable self-hosted runner does not fail CI — it queues every job "
        "for 24 hours and then expires them, silently."
    )


def test_cache_cleanup_never_runs_a_fork_pull_request() -> None:
    """``cache-cleanup.yml`` holds ``actions: write`` on a ``pull_request`` event.

    That combination is only safe because the job checks out nothing and the
    fork guard keeps it from running at all on a fork's pull request — where
    the token is read-only regardless of the declared permissions, so the
    delete would 403 and fail a run nobody can fix.
    """
    job = _load(WORKFLOWS_DIR / "cache-cleanup.yml")["jobs"]["purge"]

    condition = " ".join(str(job["if"]).split())
    assert "github.event.pull_request.head.repo.full_name == github.repository" in condition, (
        "cache-cleanup.yml's `purge` job lost its fork guard."
    )

    uses = [str(step.get("uses", "")) for step in job["steps"]]
    assert not any("actions/checkout" in u for u in uses), (
        "cache-cleanup.yml must not check out the repository. It runs on "
        "`pull_request` with `actions: write`; fetching the pull request's code "
        "into that job is Scorecard's `DangerousWorkflowID`."
    )
