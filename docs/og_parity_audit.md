# OG → v2 information-parity audit

Goal: ensure nothing of value in the locked OG `SakThai-Agent` blueprint is lost
in the v2 rewrite. For each item we **re-derive** (never copy verbatim), or
**consciously decline** with a recorded reason. v2 is intentionally curated, so
the default for low-signal v1 artifacts is *decline*.

Status legend: ✅ done · 📋 decision recorded (re-derivation is follow-on work) ·
⛔ declined (with reason).

---

## 12.1 — Identity & governance docs

| Item | Decision | Notes |
|------|----------|-------|
| `SAKTHAI.md` | ✅ re-derived | v2-accurate agent identity; tool set updated (adds `send_telegram_message`, `run_agent_loop`); describes all three runtimes sharing `~/.sakthai/memory.db`. |
| `CONTRIBUTING.md` | ✅ already present, v2-accurate | Documents `uv`, the lint→format→mypy→bandit→pytest bar, and the personal-project/MIT posture. No change needed. |
| `SECURITY.md` | ✅ already present, v2-accurate | Tool sandbox, credential chain, SQL safety, MCP stdio, CI security gates. No change needed. |
| `CODE_OF_CONDUCT.md` | ✅ re-derived | Contributor Covenant 2.1 adaptation. **Corrected from OG**: OG claimed a "proprietary view-only license" and a CLA; v2 is MIT, so participation wording was rewritten to match `LICENSE`. |
| `CHANGELOG.md` | ✅ generated from v2 history | Keep-a-Changelog format built from v2's own phase log and git history. OG's 993-line v1 changelog was **not** copied. |
| `WORKSPACE.md` | ⛔ declined | OG's `WORKSPACE.md` is a *workspace-root* `CLAUDE.md` describing Hermes integration, a root Playwright suite, and `colab_training/` LoRA scripts — none of which exist in v2. v2's workspace context already lives in the repo `CLAUDE.md` + `README.md`, and the multi-repo home layout is covered by `~/CLAUDE.md`. A standalone `WORKSPACE.md` would duplicate or contradict those. |
| `DASHBOARD_IMPROVEMENTS.md` | 📋 folded (see below) | 426-line v1 Streamlit proposal by a third-party agent. Most "weaknesses" it lists are already addressed in v2 (Phase 8: session analytics, token-by-model, export/import) or deferred to v3. Declined as a standalone doc; the few still-open ideas are captured under [Dashboard backlog](#dashboard-backlog). |

### Dashboard backlog
Still-open, genuinely-v2-relevant ideas distilled from OG `DASHBOARD_IMPROVEMENTS.md`
(everything else there is done or v3-scoped):
- Mobile/responsive breakpoints for the Streamlit layout.
- Inline fact editing/deletion from the Memory tab (currently read-only there;
  mutation is CLI/MCP-only via `forget`).
- Real-time refresh instead of a fixed cache TTL.

These are deferred enhancements, not committed work.

---

## 12.2 — Doc / data info files

| Item | Decision | Notes |
|------|----------|-------|
| `docs/devtools_ai_capabilities.md` | ⛔ declined | A 445-byte generic note on browser DevTools diagnostics (Styling/Network/Performance domains). No browser-DevTools workflow exists in v2 (a Python memory agent); nothing to anchor it to. |
| `data/hf_dataset_readme.md` | ⛔ declined | An OG Hugging Face *dataset card* for `Nanthasit/hermes-dataset`. v2 ships no dataset — `data/` carries only `README.md` + `sample-memory.jsonl` (the memory-snapshot format). Re-derive only if/when v2 publishes a dataset. |

---

## 12.3 — Sakthai-own skills backfill (OG 111 vs v2 17)

v2 already ships 17 curated `sakthai-*` skills (cycle×6, coding×7, memory-admin,
personal, understand-caveman, understand-claude-code-workflows). Triage of the
OG-only skills, grouped by prefix:

| OG group (count) | Decision | Rationale |
|------------------|----------|-----------|
| `sakthai-memory` (11) | 📋 re-derive keepers | v2 has only `sakthai-memory-admin`. Memory is core; pick the 2–3 highest-signal (e.g. retention/consolidation guidance) and re-derive; drop near-duplicates. |
| `sakthai-llm` (9) | 📋 re-derive a subset | Overlaps the existing `sakthai-coding-llm-prompting`. Re-derive only ideas not already covered (e.g. eval/judging), fold the rest. |
| `sakthai-agent` (9) | 📋 re-derive a subset | Agent-loop/tool-use guidance partly covered by `coding-mcp-tools`. Keep the distinctly-agentic ones. |
| `sakthai-learning` (8) | 📋 evaluate | Maps to the project's "growth" identity; re-derive 1–2 that aren't cycle duplicates. |
| `sakthai-dashboard` (6) | ⛔ mostly decline | v1 Streamlit-specific; superseded by the v2 dashboard. Keep none unless a vendor-neutral idea survives. |
| `sakthai-automation` (5) | 📋 evaluate | Re-derive if they describe real v2 automation surfaces; otherwise drop. |
| ops/observability singletons (`telemetry`, `tracing`, `logging`, `observability`, `incident`, `alerts`, `audit`, `accountability`, `guardrails`, `safety`, `security`, `privacy`, `auth`, `ci`, `devops`, `infra`, `containers`, `releases`, `sessions`, `acceptance`, `core`, `soul`, `plugins`, `research`, `members`, `user`×2, `skill`×2) | ⛔ mostly decline | ~30 one-off skills. Most are aspirational ops content for infrastructure v2 doesn't have. Re-derive only `soul`/`core` if they carry identity not already in `SOUL.md`. |
| GCP/data skills (~18: `gcp-*`, `bigquery`, `dataform`, `dbt`, `dataflow`, `composer`, `gcloud-auth`, `discovering-gcp-data-assets`, …) + `media/` | ⛔ out of scope | v2 has no BigQuery/Spanner/Dataflow surface and is local-first with no cloud agent. |
| misc (`notebook-guidance`, `ml-best-practices`, `managing-python-dependencies`, `data-autocleaning`, `building-data-apps`) | ⛔ decline | Generic, not SakThai-specific; `uv` dependency guidance already lives in `sakthai-coding-uv`. |

**Correction after inspecting `library/`:** v2 had already re-derived most of the
high-value keepers into `library/` (memory: recall/search/consolidate; agent:
planning/sessions/tools; llm: prompting/providers; learning: feedback/patterns),
so the real gap was small — not ~6–10.

**Backfill done (2026-06-17):** three genuinely-missing keepers re-derived fresh
(no verbatim copy), matching v2's terse library format and validated with
`parse_skill`:

| New skill | Fills gap | OG inspiration (intent only) |
|-----------|-----------|------------------------------|
| `library/memory/sakthai-memory-store` | how to *write* memory (fact vs observation, kind/key, reuse keys) — recall/search existed but not store | `sakthai-memory-store/management` |
| `library/agent/sakthai-agent-reasoning` | tool-use/reasoning discipline in the loop | `sakthai-agent-reasoning` |
| `library/learning/sakthai-learning-curation` | consolidate/dedupe/forget as a habit | `sakthai-learning-curation` |

Remaining OG memory/agent/learning skills (embeddings, graph, index, supermemory,
finetune, serving, inference, benchmark, …) declined as v1-specific or off-mission.

---

## 12.4 — Library corpus triage (OG 357 files / 23 categories vs v2 12)

v2 library categories: agent, automation, coding, devops, learning, llm, memory,
observability, research, safety, security. Per-category decision:

| OG category (files) | In v2? | Decision |
|---------------------|--------|----------|
| creative (236) | no | ⛔ decline — bulk of OG's file count; off-mission for a memory agent. |
| productivity (68) | no | 📋 cherry-pick — a handful may map to `automation`; triage individually. |
| research (63) | yes | 📋 re-derive keepers into existing `research/`. |
| mlops (38) | no | ⛔ decline — no ML training/serving surface in v2. |
| software-development (17) | partial (`coding`) | 📋 fold keepers into `coding/`. |
| github (16) | no | 📋 cherry-pick into `devops/` if vendor-neutral. |
| acquire-codebase-knowledge (11) | no | 📋 evaluate — could fold into `coding/`. |
| red-teaming (9) | no | 📋 cherry-pick into `security/`. |
| security (8) | yes | 📋 re-derive keepers into `security/`. |
| web (8) | no | ⛔ decline — no web surface. |
| devops (7) | yes | 📋 re-derive keepers into `devops/`. |
| autonomous-ai-agents (7) | no | 📋 fold into `agent/`. |
| media (7) | no | ⛔ decline. |
| apple, email, dogfood, social-media, smart-home, note-taking, data-science, yuanbao, composio (≤6 each) | no | ⛔ decline — niche/off-mission. |
| sakthai (1) | n/a | 📋 keep — project-identity skill, re-derive. |

**Net:** decline the large off-mission categories (creative, mlops, web, media,
apple, email, social, smart-home, note-taking, etc.); cherry-pick from research,
security, devops, software-development, github, red-teaming, autonomous-ai-agents,
productivity into the matching v2 categories. CAUTION: every kept skill must be
re-derived (no verbatim copy) and must not conflict with v2's curated grouping;
record a one-line rationale per kept/dropped file at re-derivation time.

---

## 12.5 — Code / feature module gaps

| OG module | Decision | Rationale |
|-----------|----------|-----------|
| `cli/memory.py` `consolidate-sessions` (LLM session mining) | ✅ re-derived | The one genuine in-scope CLI gap: OG mines local session logs into durable facts; v2 already wrote `~/.sakthai/sessions/*.json` but never mined them. Re-derived fresh against v2's `run_agent`/`learn`/`config.sessions_dir`, idempotent via a `consolidated_sessions.json` state file. Tests in `tests/test_cli_consolidate_sessions.py`. |
| `hf.py` (Hugging Face hub) | 📋 roadmap, low priority | Only valuable if v2 ships a dataset/model (see 12.2). Defer until there's a concrete HF artifact. |
| `sandbox.py` (Docker sandbox for `run --sandbox`) | 📋 roadmap, candidate | Genuine security value — a real sandbox for `run_command`. Re-derive as a v2 feature when the agent loop's exec story is hardened. Highest-value of the code gaps. |
| `gemini_plugin.py` + `cli/gemini.py` (Gemini CLI plugin) | 📋 evaluate | v2 already discovers `~/.gemini/extensions`; assess whether a dedicated plugin adds beyond that before re-deriving. |
| `deployment/terraform/` IaC · `app/` ADK bundle | ⛔ decline | Google ADK / Vertex AI cloud deployment is not part of v2 (local-first). Explicitly out of scope. |
| `web/` immersive static gallery | ⛔ decline | v2 has no static web deploy; the Streamlit dashboard covers visualization. |
| `eval/` harness + datasets | 📋 roadmap | A hermetic eval harness would be valuable; re-derive fresh rather than porting v1's. |
| `colab_training/` + `scripts/finetune_sakthai.py` (LoRA) · `data/hermes-dataset` | ⛔ decline | Fine-tuning pipeline is out of v2 scope (v2 is a memory/agent layer, not a training project). |
| artifacts/junk (reports, logs, pngs, `scratch/`, benchmarks) | ⛔ never port | Explicitly excluded per the roadmap. |

---

## Summary

- **Re-derived now (✅):** `SAKTHAI.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`
  (plus `CONTRIBUTING.md`/`SECURITY.md` confirmed already v2-accurate);
  eight skill keepers — `library/memory/sakthai-memory-store`,
  `library/agent/sakthai-agent-reasoning`,
  `library/learning/sakthai-learning-curation`,
  `library/coding/sakthai-coding-codebase-knowledge`,
  `library/devops/sakthai-devops-github-workflows`,
  `library/coding/sakthai-coding-debugging`,
  `library/coding/sakthai-coding-tdd`,
  `library/security/sakthai-security-red-teaming`.
- **Declined with reason (⛔):** `WORKSPACE.md`, `docs/devtools_ai_capabilities.md`,
  `data/hf_dataset_readme.md`, the large off-mission skill/library categories,
  the LoRA/training pipeline, and the static web gallery.
- **Recorded as scoped follow-on (📋):** the code-module roadmap
  (`sandbox.py` and an `eval/` harness as the strongest candidates).

The remaining 📋 items are decisions, not yet code: re-deriving the candidate modules is follow-on work for future phases.
