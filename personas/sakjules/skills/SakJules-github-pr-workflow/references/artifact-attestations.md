# GitHub Artifact Attestations (`actions/attest`) Reference

> **Persona Domain:** SakJules · Master of Automation & CI/CD
> **Source Action:** [`actions/attest`](https://github.com/actions/attest)
> **Pinned SHA:** `1e69f48acb82d1966a394da916b4c1698aa569d6` (`v4.2.2`)

---

## 1. Overview & Purpose

`actions/attest` is GitHub's unified, first-party GitHub Action for generating cryptographically signed attestations for workflow artifacts. It replaces and unifies the earlier `actions/attest-build-provenance` and `actions/attest-sbom` actions into a single high-performance engine powered internally by `@actions/attest`.

In the House of Sak automation and DevSecOps ecosystem, this action establishes:
1. **SLSA Build Provenance (Level 3)** — Non-forgeable cryptographic evidence documenting the source repository, commit SHA, workflow file, builder environment, and input materials used to produce distribution artifacts.
2. **Software Bill of Materials (SBOM) Integrity** — Cryptographic binding connecting the built binary packages (`dist/*.whl`, `dist/*.tar.gz`) to their SPDX or CycloneDX dependency manifests.
3. **Keyless Signing via Sigstore** — Uses GitHub's native OpenID Connect (OIDC) identity provider and Sigstore root Certificate Authority (Fulcio) to sign attestations without managing long-lived cryptographic keys or secrets.
4. **Public & Private Transparency** — Records public repository attestations into the public Sigstore Rekor transparency log, and stores private enterprise attestations in GitHub's native attestation store.

---

## 2. Token & Permission Requirements

Generating artifact attestations requires strictly scoped job-level permissions:

| Permission | Scope | Justification |
| :--- | :--- | :--- |
| `id-token` | `write` | Mints a short-lived OIDC JSON Web Token (JWT) from GitHub's token service to request a Sigstore signing certificate. |
| `attestations` | `write` | Uploads the signed in-toto attestation bundle to GitHub's Attestations API (`/repos/{owner}/{repo}/attestations`). |
| `contents` | `read` | Accesses repository source code and built workflow artifacts. |

```yaml
permissions:
  contents: read
  id-token: write
  attestations: write
```

> **Security Note:** In accordance with House of Sak security invariants, permissions must always be declared as explicit mapping dictionaries at the job level. Top-level write permissions and scalar permissions (`read-all` / `write-all`) are strictly forbidden.

---

## 3. Attestation Types & Workflows

### 3.1 SLSA Build Provenance Attestation (Default)
When invoked with `subject-path` (or discovered subjects) and no `sbom-path` or `predicate`, the action automatically produces a SLSA build provenance predicate (`https://slsa.dev/provenance/v1.0`):

```yaml
- name: Attest build provenance
  uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
  with:
    subject-path: 'dist/*'
```

### 3.2 SBOM Attestation
Binds a software bill of materials (SPDX or CycloneDX JSON) to the build artifacts:

```yaml
- name: Attest SBOM
  uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
  with:
    subject-path: 'dist/*'
    sbom-path: 'dist.spdx.json'
```

### 3.3 Custom In-Toto Predicate Attestation
Allows domain-specific security, evaluation, or benchmark claims:

```yaml
- name: Attest custom benchmark verification
  uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
  with:
    subject-path: 'dist/*'
    predicate-type: 'https://sakthai.dev/predicates/eval-v1'
    predicate-path: 'eval-summary.json'
```

### 3.4 Container Image Attestation
Attests OCI container images with registry push:

```yaml
- name: Attest container image
  uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
  with:
    subject-name: 'ghcr.io/beer-sakthai/sakthai-agent'
    subject-digest: '${{ steps.build-push.outputs.digest }}'
    push-to-registry: true
```

---

## 4. Verification Protocol (`gh attestation verify`)

Downstream consumers, deployment gates, and security scanners can verify generated attestations using the official GitHub CLI:

```bash
# Verify Python wheel or source distribution package provenance
gh attestation verify dist/sakthai_agent-*.whl --repo beer-sakthai/Sak-Family-Agent

# Verify SBOM attestation
gh attestation verify dist/sakthai_agent-*.whl \
  --repo beer-sakthai/Sak-Family-Agent \
  --predicate-type https://spdx.dev/Document

# Verify with strict signer workflow constraint
gh attestation verify dist/sakthai_agent-*.whl \
  --repo beer-sakthai/Sak-Family-Agent \
  --cert-identity "https://github.com/beer-sakthai/Sak-Family-Agent/.github/workflows/attest-build-provenance.yml@refs/heads/main"
```

---

## 5. House of Sak Integration Invariants

- **Immutable Pinning:** All workflow references must use `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2`.
- **Harden-Runner Preflight:** Every attestation job must execute `step-security/harden-runner` with audit or block egress policy prior to network token exchange.
- **Dedicated Workflows:**
  - Standard packaging & provenance: `.github/workflows/attest-build-provenance.yml`
  - Reusable attestation engine: `.github/workflows/reusable-artifact-attestation.yml`
