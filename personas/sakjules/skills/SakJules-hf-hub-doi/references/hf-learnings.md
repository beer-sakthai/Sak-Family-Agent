# HF Learnings Log — hf-hub-doi

## 2026-07-25: hf-hub-doi-deep-dive-v2 — DataCite Metadata Schema, DOIs Programmatic Querying & Patterns

### Summary
Deep dive into the DataCite integration layer of Hugging Face DOIs. Researched the DataCite REST API, kernel-4 XML metadata schema, element mapping between HF repos and DataCite metadata, programmatic patterns for DOI discovery, citation generation via content negotiation, and limitations of the current HF DOI implementation.

### Key Findings

**HF DOI Architecture:**
- DOI prefix: `10.57967/hf/` + numeric ID (e.g. `10.57967/hf/8345`)
- Managed entirely through DataCite — HF's own API exposes NO DOI field
- Publisher is always `"Hugging Face"` in DataCite metadata
- Version field = git commit SHA at generation time
- Two states: `findable` (current/active) and `registered` (previous version, deprecated)

**DataCite Metadata Mapping:**
- `creators[]` → user's public name (customizable), `nameType="Personal"`, NO affiliations sent
- `titles[].title` → repo name only (not full path)
- `resourceType.resourceTypeGeneral` → `Dataset` or `Model`
- `version` → abbreviated git SHA
- `url` → HF repo page, `contentUrl` → revision tree URL

**Elements HF Does NOT Send:**
- No `descriptions`/abstract — repos with rich model cards lose that context
- No `subjects`/keywords
- No `rightsList`/license info
- No `relatedIdentifiers` (no links to papers, code, datasets)
- No `affiliation` on creators
- No `fundingReferences`

**DataCite REST API:**
- Base: `https://api.datacite.org/dois`
- Query by prefix: `?query=10.57967/hf`
- Get single DOI: `/dois/{doi_with_%2F}`
- Supports content negotiation for citation formats (BibTeX, RIS, CSL, XML)
- Python-queryable with standard `requests` library
- No authentication required for read-only queries

**Key Limitation:**
The Hugging Face Hub's own REST API (`/api/models/{id}`, `/api/datasets/{id}`) does not include a `doi` field. The only way to programmatically determine if a repo has a DOI is to query DataCite's API and match by URL or repo name.

### Impact & Use Cases
- Authors can verify their DOIs are findable via DataCite
- Citation generation can be automated using DataCite content negotiation
- Repo DOI status can be checked programmatically (with name-matching caveats)
- The minimal DataCite metadata means HF DOIs lack context (description, license) that other DOI providers include

### Skill Updated
`hf-hub-doi/` — version bumped to 2.0.0 with the deep-dive on DataCite schema, programmatic patterns, and citation generation.

### Sources
- HF Docs: https://huggingface.co/docs/hub/en/doi (raw: https://raw.githubusercontent.com/huggingface/hub-docs/main/docs/hub/doi.md)
- DataCite API: https://api.datacite.org/dois (with live queries of actual HF DOIs)
- DataCite Kernel 4 Schema: https://schema.datacite.org/meta/kernel-4.5/
- HF Blog: https://huggingface.co/blog/introducing-doi
