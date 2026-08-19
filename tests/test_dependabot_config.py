"""Repository invariants for ``.github/dependabot.yml``.

Nothing validated this file until 2026-08-19, and it shows. Every rule below
exists because the config had already been broken by its violation, silently,
for as long as anyone had been reading it as coverage.

* **Directories that exist.** ``npm`` was configured at ``/`` where there is no
  ``package.json``. Dependabot reports "no manifest found" on its own dashboard
  and nowhere else; from the repository it is indistinguishable from an
  ecosystem that simply has nothing to update.

* **Ecosystems that match the manifest.** The root is a uv project — ``uv.lock``
  and ``[dependency-groups]`` — and was declared ``pip``. ``pip`` does not model
  dependency groups, which is the same blind spot ``uv export --all-extras``
  has and the reason ``sqlitedict`` stayed hidden from ``pip-audit``. See
  ``docs/dependabot-sweep-2026-08-18.md``.

* **No symlinked directories, and no globs that could reach one.**
  ``personas/{sakjules,sakking,saksee,saksit,saktan}/agent-self-evolution`` are
  committed as mode-120000 symlinks into ``personas/shared/``. Dependabot's file
  fetchers select entries of Contents-API type ``"file"``; a symlinked directory
  yields a job that permanently finds no manifest. A ``/personas/*/…`` glob
  therefore manufactures five dead entries that read as coverage — and
  ``/personas/*/skills/*`` matches 826 directories.

* **A bounded pull-request budget.** The previous config allowed 95 simultaneous
  open version-update pull requests (3 entries at 10, 13 at the default 5).
  Every pull request into ``main`` needs an approving review from a non-author
  (``docs/CONTRIBUTING.md``), so an unbounded bump queue does not just make
  noise — it consumes the only review capacity the repository has. A flood
  should fail here, not be discovered on the pull requests tab.

* **Coverage completeness.** Seven real manifests had no entry at all, including
  the three ``agent-self-evolution`` projects where the 2026-08-18 sweep found
  live ``pytest`` and ``dspy`` advisories. A manifest that no entry covers still
  raises *alerts* (those come from the dependency graph) but can never receive a
  version-update pull request, so it looks watched and is not. Anything left out
  must be listed in ``UNCOVERED_BY_DESIGN`` with a reason.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".github" / "dependabot.yml"

# Mirrored verbatim from dependabot-core, docker/lib/dependabot/docker/
# file_fetcher.rb. It is unanchored and case-insensitive, matched against the
# bare filename, which is why `Dockerfile.sandbox` at the repository root is
# discovered by `directory: "/"` even though it is not named `Dockerfile`.
# If that regex ever changes upstream, this constant is the single place to fix.
DOCKER_REGEXP = re.compile(r"dockerfile|containerfile", re.IGNORECASE)

# What each ecosystem needs to see in a directory for the entry to do anything.
#
# `uv` deliberately requires BOTH files. dependabot-core says "uv.lock is not a
# standalone required file - it requires pyproject.toml", and a bare
# pyproject.toml is a `pip` project. Requiring both is what stops a lock-less
# Poetry tree (apps/sak_agent_dashboard/microsoft_agents_m365copilot) or a
# lock-less PEP 621 tree (the agent-self-evolution copies) from being
# mislabelled `uv`.
ECOSYSTEM_ALL_OF: dict[str, tuple[str, ...]] = {
    "uv": ("pyproject.toml", "uv.lock"),
}

ECOSYSTEM_ANY_GLOB: dict[str, tuple[str, ...]] = {
    "pip": (
        "*requirements*.txt",
        "*requirements*.in",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
    ),
    "npm": ("package.json",),
}

# The github-actions ecosystem's path is fixed by the ecosystem, not by the
# `directory` value: it always means .github/workflows/.
FIXED_ROOT_ECOSYSTEMS = frozenset({"github-actions"})

# Characters that make a path a glob rather than a literal. `directories`
# supports `*` and `**`; this repository must not use them (see the module
# docstring on symlinks and on /personas/*/skills/* matching 826 directories).
GLOB_CHARS = ("*", "?", "[")

# Total simultaneous open *version-update* pull requests this repository is
# willing to carry. Security-update pull requests are not subject to
# open-pull-requests-limit and do not count toward it, so this is a floor on the
# real number, never a ceiling.
MAX_OPEN_PR_BUDGET = 20

# Directories holding a manifest that is deliberately NOT covered by an entry.
# Each needs a reason, and the reason must be about why an entry would be wrong
# — not about it being inconvenient to add.
UNCOVERED_BY_DESIGN: dict[str, str] = {
    # pip-compile `.in` inputs paired with a hash-pinned `.lock` output.
    # Dependabot regenerates a `.txt` beside the `.in`, never a `.lock`, and
    # bandit.yml installs from the `.lock` with --require-hashes. A bump to the
    # `.in` alone changes nothing while looking like it did. Cover these the day
    # scripts/gen_hash_lock.py runs on Dependabot branches.
    ".github": "bandit-requirements.in has a hash-pinned .lock Dependabot cannot regenerate",
    "infra/sakthai-training-space": "deepspeed-trl/ml-stack .in files have hash-pinned .lock siblings",
    "personas/sakking/skills/SakKing-comfyui/scripts": "comfy-cli-requirements.in has a .lock sibling",
    "personas/saksee/skills/SakSee-comfyui/scripts": "comfy-cli-requirements.in has a .lock sibling",
    "sakthai-chat-cli/personas/sakthai/skills/creative/comfyui/scripts": (
        "comfy-cli-requirements.in has a .lock sibling"
    ),
    # setup.py files that are not packaging manifests: they declare
    # REQUIRED_PACKAGES = [...] and shell out to pip, with no setup() call.
    # Dependabot would accept the directory and extract zero dependencies.
    "personas/sakjules/skills/SakJules-google-workspace/scripts": "setup.py is an OAuth CLI, not packaging",
    "personas/sakking/skills/SakKing-google-workspace/scripts": "setup.py is an OAuth CLI, not packaging",
    "personas/saksee/skills/SakSee-google-workspace/scripts": "setup.py is an OAuth CLI, not packaging",
    "sakthai-chat-cli/personas/sakthai/skills/productivity/SakThai-google-workspace/scripts": (
        "setup.py is an OAuth CLI, not packaging"
    ),
}

# Trees that are not ours to update, or not real source.
SKIP_DIR_NAMES = frozenset(
    {".git", "node_modules", ".venv", "venv", "build", "dist", ".mypy_cache", ".pytest_cache"}
)

# Filenames that make a directory a candidate for Dependabot coverage. Kept
# deliberately narrower than ECOSYSTEM_ANY_GLOB: this drives the completeness
# sweep, so it should flag real projects, not every stray text file.
COVERAGE_MANIFESTS = ("pyproject.toml", "package.json", "setup.py")
COVERAGE_MANIFEST_GLOBS = ("*requirements*.txt", "*requirements*.in")


def _load() -> dict:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "dependabot.yml top level is not a mapping"
    return data


def _entries() -> list[dict]:
    return list(_load()["updates"])


def _entry_id(entry: dict) -> str:
    dirs = entry.get("directories") or [entry.get("directory")]
    return f"{entry.get('package-ecosystem')}[{len(dirs)}]"


def _declared_dirs(entry: dict) -> list[str]:
    if "directories" in entry:
        return list(entry["directories"])
    return [entry["directory"]]


def _resolve(declared: str) -> Path:
    """Map a config path (always absolute-looking, rooted at the repo) to disk."""
    return REPO_ROOT / declared.lstrip("/")


def _all_declared() -> list[tuple[str, str]]:
    """Every ``(ecosystem, declared_directory)`` pair in the config."""
    return [(e["package-ecosystem"], d) for e in _entries() for d in _declared_dirs(e)]


ENTRIES = _entries()


def test_config_is_version_2_with_updates() -> None:
    data = _load()
    assert data["version"] == 2, "dependabot.yml must declare `version: 2`"
    assert isinstance(data.get("updates"), list) and data["updates"], "no `updates:` entries"


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_entry_declares_exactly_one_directory_key(entry: dict) -> None:
    """``directory`` and ``directories`` are alternatives, never both."""
    has_singular = "directory" in entry
    has_plural = "directories" in entry
    assert has_singular != has_plural, (
        f"{_entry_id(entry)}: declare exactly one of `directory:` or `directories:`, "
        f"got directory={has_singular} directories={has_plural}"
    )


@pytest.mark.parametrize("ecosystem,declared", _all_declared(), ids=lambda v: str(v))
def test_declared_paths_are_literal(ecosystem: str, declared: str) -> None:
    """No globs. See the module docstring — every natural one here is a trap."""
    found = [c for c in GLOB_CHARS if c in declared]
    assert not found, (
        f"{ecosystem} {declared!r} contains glob character(s) {found}. "
        "`directories` supports globs but this repository must not use them: "
        "/personas/*/skills/* matches 826 directories, and "
        "/personas/*/agent-self-evolution matches five symlinks into "
        "personas/shared/, which Dependabot cannot follow."
    )


@pytest.mark.parametrize("ecosystem,declared", _all_declared(), ids=lambda v: str(v))
def test_declared_directory_exists_and_is_not_a_symlink(ecosystem: str, declared: str) -> None:
    path = _resolve(declared)
    assert path.is_dir(), (
        f"{ecosystem} {declared!r} is not a directory in this repository. "
        "Dependabot reports this only on its own dashboard; from here a dead "
        "entry is indistinguishable from an ecosystem with nothing to update."
    )
    assert not path.is_symlink(), (
        f"{ecosystem} {declared!r} is a symlink. Dependabot's file fetchers "
        "select Contents-API entries of type 'file', so a symlinked directory "
        "yields a job that permanently finds no manifest."
    )


@pytest.mark.parametrize("ecosystem,declared", _all_declared(), ids=lambda v: str(v))
def test_declared_directory_holds_a_matching_manifest(ecosystem: str, declared: str) -> None:
    """The manifest that makes the entry meaningful is actually present."""
    path = _resolve(declared)

    if ecosystem in FIXED_ROOT_ECOSYSTEMS:
        workflows = REPO_ROOT / ".github" / "workflows"
        assert any(workflows.glob("*.yml")) or any(workflows.glob("*.yaml")), (
            "github-actions is configured but .github/workflows/ has no workflow files"
        )
        return

    if ecosystem == "docker":
        # Mirror the fetcher: a flat, non-recursive listing of the configured
        # directory, matched by name against the unanchored DOCKER_REGEXP.
        matches = [p.name for p in path.iterdir() if p.is_file() and DOCKER_REGEXP.search(p.name)]
        assert matches, (
            f"docker {declared!r} holds no file matching {DOCKER_REGEXP.pattern!r} "
            "in a flat listing. Dependabot's docker fetcher is non-recursive, so "
            "renaming (for example) Dockerfile.sandbox to something without "
            "'dockerfile' in it silently ends coverage for this directory."
        )
        return

    if ecosystem in ECOSYSTEM_ALL_OF:
        required = ECOSYSTEM_ALL_OF[ecosystem]
        missing = [name for name in required if not (path / name).is_file()]
        assert not missing, (
            f"{ecosystem} {declared!r} is missing {missing}. The `uv` ecosystem "
            "needs both pyproject.toml and uv.lock; a lock-less pyproject.toml "
            "is a `pip` project (Poetry or plain PEP 621), and declaring it "
            "`uv` misrepresents what Dependabot will resolve."
        )
        return

    globs = ECOSYSTEM_ANY_GLOB[ecosystem]
    assert any(next(path.glob(g), None) for g in globs), (
        f"{ecosystem} {declared!r} holds none of {list(globs)}"
    )


def test_no_duplicate_ecosystem_directory_pairs() -> None:
    pairs = _all_declared()
    seen: set[tuple[str, str]] = set()
    duplicates = [p for p in pairs if p in seen or seen.add(p)]  # type: ignore[func-returns-value]
    assert not duplicates, f"duplicate (ecosystem, directory) pairs: {sorted(set(duplicates))}"


def test_no_directory_is_claimed_by_both_uv_and_pip() -> None:
    """Two Python ecosystems on one directory means two competing pull requests."""
    uv_dirs = {d for eco, d in _all_declared() if eco == "uv"}
    pip_dirs = {d for eco, d in _all_declared() if eco == "pip"}
    overlap = uv_dirs & pip_dirs
    assert not overlap, (
        f"{sorted(overlap)} is declared under both `uv` and `pip`. Both would "
        "resolve the same pyproject.toml and open competing pull requests for "
        "every bump."
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_entry_declares_schedule_labels_limit_and_groups(entry: dict) -> None:
    name = _entry_id(entry)

    interval = (entry.get("schedule") or {}).get("interval")
    assert interval in {"daily", "weekly", "monthly"}, f"{name}: bad schedule.interval {interval!r}"

    labels = entry.get("labels") or []
    assert "dependencies" in labels, (
        f"{name}: labels must include 'dependencies'. Note Dependabot creates "
        "that label itself but SILENTLY DROPS any label that does not already "
        "exist — see docs/dependabot-setup.md for the `gh label create` lines."
    )

    limit = entry.get("open-pull-requests-limit")
    assert isinstance(limit, int), f"{name}: open-pull-requests-limit must be an integer"

    assert (entry.get("commit-message") or {}).get("prefix"), f"{name}: no commit-message.prefix"
    assert entry.get("groups"), (
        f"{name}: no `groups:`. Ungrouped daily updates open one pull request "
        "per dependency, and each one costs a non-author human review."
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_entry_does_not_set_target_branch(entry: dict) -> None:
    """``target-branch`` scopes an entry to version updates only.

    ``main`` is already the default branch, so naming it changes no routing —
    but it does stop the entry's labels, commit prefix and groups from applying
    to *security* pull requests, which are the ones that matter most. All cost,
    no benefit.
    """
    assert "target-branch" not in entry, (
        f"{_entry_id(entry)}: remove `target-branch`. It is redundant (main is "
        "the default branch) and it scopes this entry to version updates, "
        "dropping these labels and groups from security pull requests."
    )


def test_open_pull_request_budget_is_bounded() -> None:
    total = sum(e["open-pull-requests-limit"] for e in ENTRIES)
    assert total <= MAX_OPEN_PR_BUDGET, (
        f"Configured budget is {total} simultaneous open version-update pull "
        f"requests, over the {MAX_OPEN_PR_BUDGET} this repository carries. The "
        "pre-2026-08-19 config allowed 95, and every one of them needs an "
        "approving review from a non-author (docs/CONTRIBUTING.md). Lower a "
        "limit or collapse directories into a group instead of raising this."
    )


def _iter_manifest_dirs() -> set[str]:
    """Every repo-relative directory holding a manifest Dependabot could parse.

    Directories reached through a symlink are skipped: Dependabot cannot follow
    one, so covering it would be meaningless.
    """
    found: set[str] = set()
    stack = [REPO_ROOT]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        has_manifest = False
        for child in children:
            if child.is_symlink():
                continue
            if child.is_dir():
                if child.name not in SKIP_DIR_NAMES:
                    stack.append(child)
                continue
            if child.name in COVERAGE_MANIFESTS:
                has_manifest = True
        if not has_manifest:
            has_manifest = any(next(current.glob(g), None) for g in COVERAGE_MANIFEST_GLOBS)
        if has_manifest:
            found.add(current.relative_to(REPO_ROOT).as_posix())
    return found


def test_every_manifest_is_covered_or_declared_uncovered() -> None:
    """The rule that would have caught all seven missing entries.

    A manifest with no entry still produces Dependabot *alerts* — those come
    from the dependency graph, which scans the whole repository — but can never
    receive a version-update pull request. That is the worst state to be in:
    it looks watched, and it is not.
    """
    configured = {_resolve(d).relative_to(REPO_ROOT).as_posix() for _, d in _all_declared()}
    uncovered = _iter_manifest_dirs() - configured - set(UNCOVERED_BY_DESIGN)

    assert not uncovered, (
        "These directories hold a dependency manifest that no dependabot.yml "
        f"entry covers: {sorted(uncovered)}\n"
        "Add an entry for each, or add it to UNCOVERED_BY_DESIGN in this file "
        "with a reason explaining why an entry would be wrong rather than "
        "merely inconvenient."
    )


def test_uncovered_by_design_entries_are_still_real() -> None:
    """A stale exemption is a lie about the shape of the repository."""
    manifest_dirs = _iter_manifest_dirs()
    stale = sorted(d for d in UNCOVERED_BY_DESIGN if d not in manifest_dirs)
    assert not stale, (
        f"UNCOVERED_BY_DESIGN lists {stale}, which no longer hold a manifest. "
        "Remove the entries so the exemption list keeps describing the repository."
    )
