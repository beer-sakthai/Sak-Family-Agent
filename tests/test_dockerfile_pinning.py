"""Repository invariants for supply-chain pinning outside ``.github/workflows/``.

The workflow-side pinning rules live in ``test_workflow_hygiene.py``; this file
covers the *other* surfaces Scorecard's ``PinnedDependenciesID`` scans — the
Dockerfiles and the self-hosted runner installer.

Every rule here exists because the repository had already tripped the check at
least once:

* **The root image installs from the lockfile.** ``Dockerfile`` and
  ``Dockerfile.sandbox`` used ``pip install -e "."``, which resolves fresh from
  the version ranges in ``pyproject.toml`` on every build — the ``uv.lock``
  committed beside it never participated. Scorecard read that as an unpinned
  install, and a future ``pyproject.toml`` range could resolve to a package
  that was never reviewed. Both images now ``COPY`` a digest-pinned ``uv``
  binary and run ``uv sync --frozen``, which installs exactly what the lockfile
  records and fails on drift.

* **The uv binary is pinned by digest.** ``COPY --from=ghcr.io/astral-sh/uv``
  carries the multi-arch image-index digest, not a mutable tag. A tag can be
  republished; the digest is content-addressed. The dashboard and training
  images already pinned their base images the same way (``@sha256:…``).

* **The runner tarball is verified or the install aborts.** The previous
  ``install-runner.sh`` checked the digest only when ``RUNNER_SHA256`` was set;
  unset, it downloaded, extracted and ran an unverified tarball while printing
  a warning. Verification has to be a gate, not a courtesy. The digest is now
  pinned per architecture for the default runner version, and a mismatch (or an
  overridden version without a matching digest) fails the install.

* **The training image's toolchain upgrades are hash-locked.** The last unpinned
  ``pip install`` in the repository was ``python -m pip install --upgrade pip
  setuptools wheel`` in ``infra/sakthai-training-space/Dockerfile``, which
  installed whatever those tools were that morning. All three are now pinned by
  exact version and SHA-256, like the two ``--require-hashes`` lock files
  further down in the same image.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

DOCKERFILES = [
    REPO_ROOT / "Dockerfile",
    REPO_ROOT / "Dockerfile.sandbox",
]

# A full-length SHA-256 — the only digest this repository accepts.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

_UV_IMAGE_REF = re.compile(
    r"ghcr\.io/astral-sh/uv:[^@\s]+@sha256:([0-9a-f]{64})"
)

_PIP_INSTALL = re.compile(r"(?<!uv )(?:python\s+-m\s+)?pip\s+install")


def _logical_lines(text: str) -> list[str]:
    """Join backslash-continued Dockerfile ``RUN`` lines into logical lines.

    A hash pin on a continuation line (``\\`` + newline) belongs to the same
    install command as the ``pip install`` that introduced it; judging the
    physical lines separately would flag a correctly pinned command.
    """
    logical: list[str] = []
    for physical in text.splitlines():
        if logical and logical[-1].rstrip().endswith("\\"):
            logical[-1] = logical[-1].rstrip()[:-1] + " " + physical.strip()
        else:
            logical.append(physical)
    return logical


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _container_images(path: Path) -> set[str]:
    """The image digests this Dockerfile pins, whatever the ``FROM`` syntax."""
    return set(re.findall(r"@sha256:([0-9a-f]{64})", _text(path)))


def test_uv_binary_is_pinned_by_digest() -> None:
    """The ``uv`` image used to install the project must carry a full digest.

    ``COPY --from=ghcr.io/astral-sh/uv:0.12.5@sha256:…`` without the digest
    would re-pull a mutable tag at build time; with a digest, the exact image
    is content-addressed. A bare tag is exactly the pattern Scorecard's
    ``PinnedDependenciesID`` flags.
    """
    for path in DOCKERFILES:
        matches = _UV_IMAGE_REF.findall(_text(path))
        assert matches, f"{path.name}: the pinned uv image COPY is missing"
        for digest in matches:
            assert _SHA256.fullmatch(digest), (
                f"{path.name}: uv image digest is not a full SHA-256 ({digest!r})"
            )


def test_agent_images_install_from_the_lockfile() -> None:
    """Both agent images must ``uv sync --frozen`` and never bare-``pip install``.

    ``uv sync --frozen`` installs exactly what ``uv.lock`` records and refuses
    to run when the lockfile drifts from ``pyproject.toml``. A ``pip install``
    without ``--require-hashes`` resolves version ranges freshly and is what
    the unpinned-install alert is about.
    """
    for path in DOCKERFILES:
        text = _text(path)
        assert "uv sync --frozen" in text, (
            f"{path.name}: the install step must be `uv sync --frozen` so the "
            "image builds from uv.lock, not from pyproject ranges."
        )
        for line in _logical_lines(text):
            if _PIP_INSTALL.search(line) and "--require-hashes" not in line:
                pytest.fail(
                    f"{path.name}: unpinned `pip install` at: {line.strip()!r} "
                    "— install from the lockfile instead."
                )


def test_agent_images_export_the_venv_on_path() -> None:
    """``uv sync`` installs into ``.venv``; the entrypoint must resolve it.

    The entrypoints are bare binaries (``python -m sakthai.telegram.bot`` and
    ``sakthai``), so ``PATH`` must lead with ``/app/.venv/bin`` or the images
    would run the base image's Python with none of the locked dependencies.
    """
    for path in DOCKERFILES:
        text = _text(path)
        assert 'PATH="/app/.venv/bin:${PATH}"' in text, (
            f"{path.name}: uv sync installs to /app/.venv, so PATH must lead "
            "with /app/.venv/bin for the entrypoint to resolve it."
        )
        assert "uv.lock" in text, (
            f"{path.name}: the lockfile must be copied into the image — "
            "`uv sync --frozen` cannot install without it."
        )


def test_training_image_toolchain_upgrades_are_hash_locked() -> None:
    """The last bare ``pip install`` in the repository must stay locked.

    ``pip``, ``setuptools`` and ``wheel`` are pinned by exact version with a
    ``--hash`` each, so a compromised or republished release cannot be pulled
    by the ``--upgrade``. A new unpinned ``pip install`` anywhere in the image
    fails this test.
    """
    path = REPO_ROOT / "infra" / "sakthai-training-space" / "Dockerfile"
    text = _text(path)

    hashes = re.findall(r"--hash=sha256:([0-9a-f]{64})", text)
    assert len(hashes) >= 3, (
        "the training image must hash-pin pip, setuptools and wheel; found "
        f"{len(hashes)} hash pins."
    )

    for line in _logical_lines(text):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if _PIP_INSTALL.search(line) and "--require-hashes" not in line and "--hash" not in line:
            pytest.fail(
                f"{path.name}: unpinned `pip install` at: {stripped!r} "
                "— pin the tools by version and hash."
            )


def test_runner_installer_verifies_the_tarball_or_fails() -> None:
    """``install-runner.sh`` must gate on the digest, not warn past it.

    The runner tarball is verified against a per-architecture pinned digest
    before extraction; a mismatch must abort the install. A return to the
    warning-only path (``::warning::`` + print the digest) fails here.
    """
    path = REPO_ROOT / "infra" / "self-hosted-runner" / "install-runner.sh"
    text = _text(path)

    assert "sha256sum -c -" in text, (
        "install-runner.sh must verify the tarball with `sha256sum -c -`."
    )
    assert "RUNNER_SHA256:-af5c33fa94f3cc33b8e97937939136a6b04197e6dadfcfb3b6e33ae1bf41e79a" in text, (
        "install-runner.sh lost the pinned x64 digest for the default runner "
        "version."
    )
    assert "RUNNER_SHA256:-9cb43527912086c7c8fb4119cb06409fcbcbd6f93a2d8507f30b07c495620f5c" in text, (
        "install-runner.sh lost the pinned arm64 digest for the default runner "
        "version."
    )
    assert "was NOT verified" not in text and "::warning::" not in text.split("config.sh")[0], (
        "install-runner.sh must not degrade digest verification to a warning "
        "— an unverified tarball must abort the install."
    )
    assert "failed checksum verification" in text, (
        "install-runner.sh must fail loudly on digest mismatch."
    )
