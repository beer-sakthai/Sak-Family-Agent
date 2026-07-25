# HF Learnings — hf-hub-doi (Deep Dive)

## 2026-07-25: Deep Dive — DataCite Integration, API Internals & Metadata Schema

### Summary
Deep-dive update covering the DataCite metadata schema (Kernel-4), DOI tag format in the Hub API, versioning mechanics, programmatic detection, DataCite resolve API, scope limitations, and comparison with Zenodo/OSF.

### 1. DOI Format & Prefix
- **All HF DOIs** use DataCite prefix `10.57967` (HF's allocated prefix)
- Suffix format: `hf/{number}` — e.g., `10.57967/hf/0039` (GPT-2), `10.57967/hf/1096` (test dataset)
- The numbering appears sequential; early models like GPT-2 have low numbers (0039)
- **Full DOI examples**: `10.57967/hf/0039`, `10.57967/hf/1096`, `10.57967/hf/4329`

### 2. Repository Storage Format
- DOIs are stored as **tags** in the repo metadata — **not** in cardData
- Tag format: `doi:10.57967/hf/0039` (literal string with `doi:` prefix)
- Discoverable via Hub API:
  - `GET /api/models?tags=doi:10.57967&full=true` — finds models with DOIs
  - `GET /api/datasets?tags=doi:10.57967&full=true` — finds datasets with DOIs
- The `cardData` dictionary does **not** contain a `doi` field
- The README.md is **not** auto-modified — citations are rendered by the Hub UI from the DOI tag

### 3. DataCite Metadata Schema (Kernel-4) — What HF Registers

HF transmits **minimal** metadata to DataCite. Based on live DataCite API inspection of `10.57967/hf/1096` and `10.57967/hf/0039`:

| Field | Value | Notes |
|-------|-------|-------|
| `identifier` | `10.57967/HF/1096` | DataCite internal (case-insensitive) |
| `creators[].creatorName` | HF user's full name (e.g. "Ahmed Elnaggar") or "HF Canonical Model Maintainers" | Customizable by user before generation |
| `creators[].nameType` | `Personal` or `Organizational` | Depending on whether user customised |
| `titles[].title` | Repository name (e.g. "gpt2") | The repo slug, no description |
| `publisher` | `Hugging Face` | Always |
| `publicationYear` | Year of DOI generation (e.g. 2022 for GPT-2) | Not the model creation year |
| `resourceType.resourceTypeGeneral` | `Model` for models, `Dataset` for datasets | Maps to DataCite resource types |
| `version` | Git commit SHA (e.g. `b31c615`, `909a290`) | Not semver — raw SHA |
| `url` | `https://huggingface.co/{repo_type}/{repo_name}` | Permanent link |
| `contentUrl` | `https://huggingface.co/{repo_type}/{repo_name}/tree/{sha}` | Version-pinned tree URL |

**Not registered (missing from DataCite records):**
- ❌ `descriptions` — README content/abstract NOT included
- ❌ `subjects` — tags/keywords NOT transferred
- ❌ `rightsList` — license info NOT transferred
- ❌ `fundingReferences` — no funding metadata
- ❌ `relatedIdentifiers` — no links to papers, code, or other versions
- ❌ `contributors` — only creators, no contributors
- ❌ `affiliation` — creator affiliations not included
- ❌ `dates` — no specific date metadata

This is a **minimalist** registration — sufficient for discoverability but lacks rich metadata that DataCite supports.

### 4. DataCite API — Public Resolution
Anyone can resolve HF DOIs via the DataCite REST API:
```
GET https://api.datacite.org/dois/10.57967%2Fhf%2F1096
```
Returns JSON with full attributes (creators, titles, type, version, URL, citation/view counts, state).

State is `findable` and `isActive: true` for active DOIs.

### 5. Versioning Mechanics
- New commit pushed → new Head revision
- User clicks "Generate new DOI" in Settings
- New DOI is minted pointing to the new commit SHA
- **Old DOI is not deleted** — it's deprecated/historical in DataCite
- Old repos remain accessible at their specific commit tree
- Users can cite any specific version by its DOI

This is a **sequential versioning** model — no semantic version tags, just SHA-linked DOIs.

### 6. Protection & Locking Implementation
When a repo has a DOI tag:
- `delete_repo()` is blocked server-side
- `move_repo()` (rename) is blocked
- Visibility changes (private ↔ public) are blocked
- The Hub shows "locked by DOI" message on these actions
- Exception: filing a support request to `website@huggingface.co`

The lock is tied to the presence of the `doi:` tag, not the DataCite registration itself.

### 7. Known Models & Datasets with DOIs
From Hub API inspection (non-exhaustive):
- `openai-community/gpt2` → `doi:10.57967/hf/0039`
- `agemagician/doi-dataset-test` → `doi:10.57967/hf/1096`
- `Bingsu/adetailer` → `doi:10.57967/hf/3633`
- `hexgrad/Kokoro-82M` → `doi:10.57967/hf/4329`

### 8. huggingface_hub Python Library
- **No `create_doi()` or similar method** exists in `HfApi`
- **No `get_doi()` method** — though you can detect DOI by checking `repo_info().tags` for `doi:` prefix
- Generation is **exclusively UI-based** due to required DataCite consent flow (interactive)
- The `hf` CLI has no DOI commands

### 9. Scope & Limitations
| Aspect | Detail |
|--------|--------|
| Supported repo types | Models and datasets only |
| Not supported | Spaces, Collections, Discussions |
| Cost | Free |
| Consent | User's full name transmitted to DataCite |
| Author customisation | Optional — can add crediting list before generation |
| Deletion | Only via support request |
| API access | Read-only via DataCite API; no write API |

### 10. Comparison with Other DOI Services

| Aspect | HF Hub DOI | Zenodo | OSF | Figshare |
|--------|-----------|--------|-----|---------|
| Cost | Free | Free (50GB) | Free | Free (20GB) |
| Metadata richness | Minimal | Moderate (descriptions, grants, etc.) | Full | Full |
| Versioning | SHA-based sequential | Semantic versioning | Versioned | Versioned |
| Lock-in | HF platform | Zenodo (long-term) | OSF | Figshare |
| API | Read-only (DataCite) | Full CRUD | Full REST | Full REST |
| Automation | None (UI-only) | GitHub Actions upload | Zapier/integrations | API upload |

### Sources
- HF Docs: https://huggingface.co/docs/hub/en/doi
- HF Blog: https://huggingface.co/blog/introducing-doi
- DataCite API (live): https://api.datacite.org/dois/10.57967%2Fhf%2F1096
- DataCite API (live): https://api.datacite.org/dois/10.57967%2Fhf%2F0039
- Hub API: `GET /api/models/openai-community/gpt2` + tags inspection
- DataCite Schema: https://schema.datacite.org/meta/kernel-4/
- DataCite Metadata: https://datacite.org
