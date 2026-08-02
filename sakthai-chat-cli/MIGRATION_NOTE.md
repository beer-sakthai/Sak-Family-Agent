# Migration note

This directory is the folded-in copy of the standalone `sakthai-chat-cli`
repo (github.com/beer-sakthai/sakthai-chat-cli), migrated in on 2026-08-01.

It is kept as a **self-contained tree**, not merged into the canonical
`personas/sakthai/sakthai` package, because the two copies had genuinely
diverged in both directions since the original export:

- This copy (`sakthai-chat-cli/sakthai/`) has a full-screen Textual TUI
  redesign of `sakthai chat` that the canonical package does not have.
- The canonical package (`personas/sakthai/sakthai/`) has a `huggingface`
  provider, output-wrapping/guardrails hardening, and a web dashboard
  subpackage that this copy does not have.

Auto-merging these would silently drop one side's features. Reconciling
them (deciding which improvements move where, or whether to re-establish
`scripts/export_agent_repo.py` as an ongoing sync mechanism) is left as a
deliberate follow-up, not attempted as part of this migration.

Also stale as of the migration: this copy's docs/config still list six
personas including the retired `saktan` — Sak-Family-Agent's current roster
is five (see `docs/SOUL.md` at the repo root).
