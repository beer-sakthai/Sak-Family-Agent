# Dependency vulnerability audit — 2026-08-18

GitHub reported **35 Dependabot alerts** on `main` (11 high, 16 moderate, 8 low)
in the push output. This is the measurement behind that number, what was fixed,
and what deliberately was not.

**Caveat on the count:** the Dependabot dashboard is not readable from the
session that produced this document, so the 35 could not be reconciled
alert-by-alert. Everything below was derived independently by auditing every
dependency manifest in the repository against OSV (the same advisory corpus
Dependabot draws from). Treat the package-level findings as authoritative and
the mapping to "35" as approximate.

---

## Method, and why `pip-audit` was not enough

`.github/workflows/dependency-audit.yml` runs `pip-audit` over `uv.lock`, and it
reports clean. That is a narrower check than Dependabot performs, in two ways:

1. **Coverage.** `pip-audit` was run against the root `uv.lock` only. The repo
   has 12 other dependency manifests.
2. **Corpus.** `pip-audit`'s default source did not report `sqlitedict`, which
   OSV/the GitHub Advisory Database does. A clean `pip-audit` run is therefore
   not evidence of a clean Dependabot dashboard.

Two manifests additionally **cannot** be audited by `pip-audit` at all: the
training-space locks pin `torch==2.5.1+cu124`, and that local-version wheel does
not exist on PyPI, so `pip-audit`'s dry-run install fails outright. Those were
audited by querying OSV directly with the base version.

Everything was re-checked with `npm audit` / `pnpm audit` for the Node
subprojects and a direct OSV batch query for every pinned Python distribution.

## What was scanned

| Manifest | Result |
|---|---|
| `uv.lock` (root) | `sqlitedict` only |
| `apps/sak_agent_dashboard` (pnpm) | clean |
| `infra/pw-poc` (npm) | clean |
| `personas/saksee/skills/SakSee-stitch::react-{components,native}` (npm) | clean |
| `services/teams-copilot-mcp/uv.lock` | clean |
| `sakthai-chat-cli/uv.lock` | clean |
| `personas/*/telegram/requirements.txt`, skill `requirements.txt` files | clean |
| `infra/sakthai-training-space/ml-stack-requirements.lock` | `torch`, `transformers` |
| `infra/sakthai-training-space/deepspeed-trl-requirements.lock` | `torch`, `transformers`, `sentencepiece` |
| `personas/{saksee,sakking}/skills/*-comfyui/…lock`, `sakthai-chat-cli/…/comfyui/…lock` | `comfy-cli` |

## Fixed

All three live in `infra/sakthai-training-space/`, pinned in the `.in` files and
resolved into hash-locked `.lock` files. The `.in` pins were bumped and both
locks regenerated with the command documented in that directory's `Dockerfile`,
then `ml-stack.constraints` was regenerated from the new ml-stack lock.

| Package | Before | After | Advisories |
|---|---|---|---|
| `torch` | 2.5.1+cu124 | **2.6.0+cu124** | 9 → 8 — clears **GHSA-53q9-r3pm-6pq6 (CRITICAL)**, `torch.load` RCE under `weights_only=True` |
| `transformers` | 4.47.1 | **4.53.0** | 17 → 3 — clears 3 HIGH, 10 MODERATE, 1 LOW |
| `sentencepiece` | 0.2.0 | **0.2.1** | 1 → 0 — clears GHSA-38vq-g6vr-w8wf (HIGH), heap overflow |

`torchvision` (0.20.1 → 0.21.0) and `torchaudio` (2.5.1 → 2.6.0) were bumped in
lockstep; they are not independently vulnerable but must match torch's minor.

Verification: every one of the 11 `torch-2.6.0+cu124` wheel hashes on
`download.pytorch.org/whl/cu124` is recorded in the regenerated lock, including
the `cp311-linux_x86_64` wheel the Dockerfile actually installs; the
`transformers==4.53.0` and `sentencepiece==0.2.1` hashes were checked against
PyPI's published digests, per the instruction in the lock header.

## Not fixed, and why

### `torch` — 8 residual (3 moderate, 5 low). Blocked by the CUDA index.

The Dockerfile installs from `download.pytorch.org/whl/cu124`. **cu124 builds
stop at torch 2.6.0** — 2.7 onward ship cu126/cu128 only. 2.6.0 is therefore the
highest version reachable without also migrating the image's CUDA version, which
is a hardware/driver decision, not a dependency bump. The residual 8 are memory
-corruption and local-DoS issues reachable only from adversarial tensor input,
not from the training path. Clearing them means moving to cu126+ and torch 2.9+.

### `transformers` — 3 residual (2 high, 1 moderate). Needs a major version.

No 4.x release clears them: 4.53.0, 4.54.1 and 4.56.2 all sit at the same 3.
Only **5.x** does. The stack pins `trl[deepspeed]==0.15.2`, which declares
`transformers>=4.46.0` with no upper bound — so transformers 5.5.0 *resolves*
(99 packages vs 88), but that is loose metadata, not a compatibility guarantee:
trl 0.15.2 predates transformers 5.0 and subclasses the 4.x `Trainer` API.

The three are arbitrary-code-execution on loading an **untrusted** model
(GHSA-29pf-2h5f-8g72, GHSA-fgcw-684q-jj6r, GHSA-69w3-r845-3855). This stack
trains from the project's own configs, so the exploit path requires deliberately
pointing it at a hostile checkpoint.

Going to 5.x is a live option but should bump `trl`/`peft` together and be
validated by an actual training run — which the audit could not perform (no GPU,
no training execution). Left as an owner decision rather than a silent
major-version bump of a pinned reproducible training stack.

### `sqlitedict==2.1.0` (root `uv.lock`) — HIGH, no fix exists.

GHSA-g4r7-86gm-pgqc, insecure deserialization. **No fixed version has ever been
published** — the package is unmaintained. It is a transitive dependency of
`lm-eval`, which is in the `evals` dependency group, installed only by the weekly
`run-evals.yml` workflow, and `lm-eval==0.4.12` is already the latest release, so
there is no upgrade that drops it. Not imported by any first-party code.
Exploitation needs an attacker-controlled cache database on disk.

### `comfy-cli==1.16.0` (3 comfyui skill locks) — HIGH, **advisory is mis-scoped.**

GHSA-562r-8445-54r2 declares affected ranges `[0, 3.39.2)` and `[4.0.0, 4.0.5)`
for the PyPI package `comfy-cli`. But comfy-cli has **no 3.x or 4.x releases** —
its latest is 1.16.0, which is what is already pinned. Those version numbers
belong to **ComfyUI-Manager**, a different project, mapped onto the wrong PyPI
package in the advisory. Because `[0, 3.39.2)` swallows 1.16.0, every scanner
flags it, and there is no version to upgrade to. Nothing to do here but wait for
the advisory to be corrected upstream.

---

## Postscript: this fix was reverted the same day

PR #860 — two commits, both titled **"🔒 fix(security): replace hardcoded example
API key strings in SakKing-comfyui"** — reverted every pin above (`torch`,
`torchvision`, `torchaudio`, `transformers`, `sentencepiece`), both `.lock`
files and `ml-stack.constraints`, and deleted this document along with
`docs/ci-regression-2026-08-18.md`. The CRITICAL `torch.load` RCE was back on
`main`, under a commit message about API-key strings. Nothing failed.

That is the fifth commit in one day whose diff bears no relation to its message.

**New guard:** `tests/test_persona_guardrails_parity.py::TestVulnerableDependencyPinsStayFixed`
asserts a *minimum safe version* for each of the five packages, read straight
from the `.in` files. Raising a pin always passes; only dropping below a version
with a known advisory fails. Verified by replaying the exact revert — all five
subtests fail on the reverted pins and pass on the fixed ones.

It lives in the parity module rather than beside the training config on purpose:
that file has survived every revert so far, whereas a feature's own tests tend
to go out with the feature. It is also, as noted above, the *only* automated
floor on these files — `dependency-audit.yml` reads the root `uv.lock` and
cannot audit these at all.

---

## Preventing recurrence

- `dependency-audit.yml` runs `pip-audit` over the root `uv.lock` only. It did
  not see any of the findings above — not the training stack (wrong manifest,
  and unauditable by pip-audit anyway) and not `sqlitedict` (narrower corpus).
  Widening it to the other manifests, or scanning against OSV, would close that
  gap; not done here to keep this change to the vulnerabilities themselves.
- When bumping a pinned version in `infra/sakthai-training-space/*.in`,
  regenerate **both** the `.lock` and `ml-stack.constraints`. The documented
  `grep`-based command for the constraints file drops its hand-written header —
  re-add it.
- Check that an advisory's "fixed" version actually exists on PyPI before
  bumping to it. The comfy-cli finding above would otherwise have produced a pin
  to a release that does not exist.
