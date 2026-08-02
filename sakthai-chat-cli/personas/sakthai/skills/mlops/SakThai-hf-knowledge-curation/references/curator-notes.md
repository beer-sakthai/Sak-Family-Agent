# Curator Notes

## 2026-06-21: Overlap between hf-fine-grained-tokens and hf-gated-repos

`hf-fine-grained-tokens` lives in `~/.hermes/profiles/hermesagent/skills/mlops/hf-fine-grained-tokens/SKILL.md`.
It overlaps with the newly created `hf-fine-grained-tokens` (gated repos) on access control.

**Boundary:**
- `hf-fine-grained-tokens` = token creation / org policies / RBAC / service accounts
- `hf-gated-repos` = per-repo gating configuration and user access-request lifecycle

**Action needed:** Add a "Related Skills" cross-reference section to `hf-fine-grained-tokens/SKILL.md`.
Cross-profile write required from `sakthai` profile using `write_file`/`patch` with `cross_profile=true`.

## 2026-06-21: Patched sections in this skill

- Added `mcp_huggingface_hf_doc_search` as mid-fallback when `mcp_huggingface_hf_doc_fetch` times out.
- Added directory existence verification (`find` / `terminal ls`) before cross-profile writes.

## 2026-06-22: New skill hf-sentence-transformers in hermesagent profile

`hf-sentence-transformers` was created at `~/.hermes/profiles/hermesagent/skills/mlops/hf-sentence-transformers/SKILL.md`.
It covers SentenceTransformer, CrossEncoder, SparseEncoder, Inference API feature-extraction usage, TEI serving, and MTEB benchmarking.

**Potential overlaps with existing hermesagent skills:**
- `hf-inference-client` — may also cover generic feature-extraction; boundary is that sentence-transformers skill is domain-specific (embeddings, reranking, MTEB, model family selection).
- `hf-tei` — covers generic TEI deployment; sentence-transformers skill adds model-selection guidance and domain-specific examples.
- `hf-inference-endpoints` — general endpoint hosting; sentence-transformers skill focuses on embedding-specific configuration.

**Action needed:** Add "Related Skills" cross-reference sections to `hf-sentence-transformers/SKILL.md` pointing to `hf-tei`, `hf-inference-client`, and `hf-inference-endpoints` in the hermesagent profile. Cross-profile write required using `write_file`/`patch` with `cross_profile=true`.
