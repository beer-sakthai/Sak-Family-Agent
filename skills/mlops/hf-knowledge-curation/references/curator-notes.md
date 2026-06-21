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
