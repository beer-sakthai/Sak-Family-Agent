# Sak Family Agent — Master Plan Index

> **Dream → Hope → Care → Joy → Trust → Growth**

This is the master index. Navigate from here. Always update sub-plans in-place;
never duplicate content across files.

---

## 🗂️ Where Things Live

| What you're looking for | Where to find it |
|---|---|
| **Business strategy & monetization plan** | [`product/PLAN.md`](./product/PLAN.md) |
| **Session notes & brainstorms** | [`product/sessions/`](./product/sessions/) |
| **Team identity, Charge & Principles** | [`docs/SOUL.md`](./docs/SOUL.md) |
| **Memory tools & agent guide** | [`docs/SAKTHAI.md`](./docs/SAKTHAI.md) |
| **Beer's profile & core values** | [`docs/USER.md`](./docs/USER.md) |
| **Agent operating rules** | [`docs/OPERATING_CONTRACT.md`](./docs/OPERATING_CONTRACT.md) |
| **Architecture & capabilities** | [`docs/architecture.md`](./docs/architecture.md) · [`docs/capabilities.md`](./docs/capabilities.md) |
| **Python source** | [`sakthai/`](./sakthai/) |
| **Agent personas** | [`personas/`](./personas/) |
| **Skills (69 total)** | [`skills/`](./skills/) — see `skills/README.md` for categories |
| **Helper scripts** | [`scripts/`](./scripts/) |
| **Tests** | [`tests/`](./tests/) |
| **Web dashboard** | [`dashboard/`](./dashboard/) |
| **Assets / images** | [`assets/`](./assets/) |
| **Scratch / orphan files** | [`scratch/`](./scratch/) |

---

## 🚦 Current Status

| Area | Status |
|---|---|
| Repository hygiene — persona SOULs | ✅ All 6 personas done (2026-07-02) |
| Business strategy — market analysis | ✅ Done (2026-07-02) |
| MVP definition | ✅ Done (2026-07-02) — ServiceQuoteBot |
| Monetization strategy | ✅ Done (2026-07-02) — Setup + Subscription |
| MVP execution — ServiceQuoteBot build | ✅ Done (2026-07-02) |
| Model Evaluation — Task validation via lm-evaluation-harness | ✅ Done (2026-07-06) |
| Documentation — Revamp README with banner and detailed status | ✅ Done (2026-07-06) |
| Repository hygiene — per-agent skill name prefixes; SakFin role folded into SakTan's `SOUL.md` (no standalone SakFin persona) | ✅ Done (2026-07-06) |
| Restructure — copy sakthai package + agent-self-evolution into each persona; remove root packages/ and sakthai/ | ✅ Done (2026-07-06) |
| Build/CI repointing — canonical package at personas/sakthai/sakthai; pyproject, workflows, Dockerfile, path fixes | ✅ Done (2026-07-06) |
| Restructure — move servicequotebot scaffold from personas/ to services/ | ✅ Done (2026-07-06) |
| **Plans audit & refresh** — standardized markers, cross-links, archived completed sub-plans | ✅ Done (2026-07-07) |
| **Test Coverage Improvement** — 100% coverage on all previously untested modules, sync and eval Edge Cases | ✅ Done (2026-07-08) |
| **Security hardening + free-local model policy** — memory metadata redaction, static-serving path canonicalisation, all agents default to local `sakthai`, handles standardized (PR #344) | ✅ Done (2026-07-10) |
| **Test Coverage round 2** — dashboard data tests + injectable store, guardrail deny-path branches, MCP guardrail paths, auth expiry, store aggregates, small CLI/web/config gaps, guardrails added to mutation scope; coverage 95.4% → 98.3%, floor raised to 95 | ✅ Done (2026-07-10) |
| **README rewrite** — corrected origin story (fabricated "cleaners found me" detail removed at Beer's request), status bars + emoji, refreshed project facts | ✅ Done (2026-07-10) |
| **Repo security audit round 2** — gitleaks CI gate added (`secret-scan.yml`), pip-audit dependency audit added, `@latest` action pinned, dead Dependabot npm target fixed, HF_TOKEN moved to env block, SECURITY.md/CLAUDE.md corrected; report at `docs/security_audit_2026-07-11.md` | ✅ Done (2026-07-11) |
| **Caveman skill injection in prompt_builder** — replaced the placeholder in `render_skills_prompt_block` with real caveman skill loading (mirrors `agent/loop.py`), simplified directive kept as fallback | ✅ Done (2026-07-11) |
| **Test Coverage round 3** — guardrails wrapper/find bypass branches (88% → 99%, zero missed statements), agent-loop failure seams, `memory pull` CLI, tool overrides, telegram session/main paths, provider detection edges, win32 CLI stream reconfigure; coverage 97.6% → 99.2%, floor raised to 97, CLAUDE.md floor claim corrected | ✅ Done (2026-07-12) |
| **SOUL consistency + repo hygiene** — fix six-persona SOUL drift (sibling lists in SakThai/SakKing, SakSee model line → local `sakthai` per PR #344 policy, finance lane → SakTan/SakFin, SakKing phantom tools + web-lane split vs SakSee, SakJules/SakSee craft passes), refresh `personas/README.md` skill counts from disk, add `tests/test_soul_consistency.py` CI guard, untrack `coverage.xml`/`sakking-dashboard.tar.gz`, remove throwaway `LABELER_TEST.md` | ✅ Done (2026-07-13) |
| **Security audit round 3** — git-URL transport validation (`giturl.py`, applied in memory sync + extensions install), `extensions remove` containment check, HTTP sync timeout, Telegram `/workflow` empty-allowlist bypass, bot handlers moved off the event loop, tool-override load failures logged | ✅ Done (2026-07-13) |
| **Skill-path fix + dry-run skill preflight** — added `personas/shared/skills/` to `default_skill_roots()` so `Sak-auto-cycle-loop` resolves; `--dry-run` now validates `--with-skills` names (fails on misses, reports resolved), live path warns instead of silently dropping; +6 tests, verified end-to-end | ✅ Done (2026-07-13) |
| **Sentinel relative-path hardening (PR #378/#381)** — `_is_sensitive_path` blocks relative paths to sensitive data (`.ssh/`, `.aws/`, shell histories, key basenames) via `_SENSITIVE_BASENAMES`/`_SENSITIVE_DIRS`/`_SENSITIVE_KEY_STEMS`, case-insensitively and across separator values, backup-suffixed keys, globs, and interpreter one-liners; superset of the concurrently-merged #379; synced across all six personas; prevention: `tests/test_persona_guardrails_parity.py` fails CI on persona guardrail drift + regression tests in `tests/test_sentinel_ssh_leak.py` | ✅ Done (2026-07-14) |
| **Relative system-root blocking (re-land of PR #380)** — `_is_sensitive_path` now treats relative paths whose first component names a critical root (`etc/passwd`, `var/log/…`) as sensitive, with a single-component `tmp` exception; `.config`/`.npm` added to `_SENSITIVE_DIRS`, `credentials` to `_SENSITIVE_BASENAMES`; landed as a delta on top of the stronger #381 hardening instead of merging the conflicting/regressive #380 branch; synced across all six personas; regression tests in `tests/test_guardrails_relative_roots.py` | ✅ Done (2026-07-14) |
| **Branch consolidation — all 8 open PRs merged to main** — dependabot #386 (mypy 2.3.0) + #387 (actions group); Sentinel #384 (shell-config basenames + critical roots in `_SENSITIVE_NAME_RE`), #385 (ssh/ssh-add/ssh-keygen/ssh-copy-id in scan lists + `tests/test_sentinel_ssh_tools.py`), #388 (`cp` check widened from kubectl-only to docker/podman/kubectl), #389 (docker/podman/kubectl/chroot/nsenter added to destructive + exfiltration scan lists), #391 (`,` added as `_is_sensitive_path` delimiter + `tests/test_guardrails_sentinel_bypasses.py` case), #392 (protections already subsumed by the consolidated version; merged for history, journal entry kept). Conflicting hunks resolved by keeping the stronger consolidated implementation (chroot NEWROOT check, conservative nsenter flag list, no internal-command censoring); guardrails synced across all six personas; closed branches #378/#380 skipped as previously superseded by #381/#382 | ✅ Done (2026-07-16) |
| **Security Audit & High-Priority Fixes Plan** — comprehensive audit completed (audit report: 120+ pages, A+ grade); two high-priority fixes identified: (1) Rotate Stripe + Twilio credentials in git history (5 min, Beer), (2) Add web API bearer token auth (4-6 hrs, Claude Code); full plan at `security/SECURITY_FIXES_PLAN.md` with phases, tests, rollout, and rollback. Additional: Upgraded vulnerable pinned dependency `cryptography` from v49.0.0 to v50.0.0 (CVE-PYSEC-2026-3552). | ✅ Done (2026-08-09) |
| **Native per-persona capabilities (no Hermes dependency)** — persona-aware skill discovery (fixes `SKILLS_DIR` hardcoded to SakThai in `config.py`), auto-wired per-persona `mcp.json` + model/provider defaults for `run`/`chat --persona`, Telegram gateway `SAKTHAI_PERSONA` support, removal of the dead `sakthai-telegram-native@.service` template, `CLAUDE.md` canonical-package claim corrected; full test suite + mypy + ruff green | ✅ Done (2026-08-02) |
| **HF Ecosystem Improvement** — 5-phase plan written: broken/skeleton repo fixes, card/metadata consistency (19/16/7 counts), functional upgrades, cleanup, automation + health monitoring (cron confirmed dead); plan at `docs/hf-cards-improvement-plan.md` | [/] In progress — awaiting approval to start Phase 1 |
| **Hermes profile scaffold repair (×6 agents)** — merge `6992353b` had silently deleted `infra/hermes-agents/{default,profiles/*}` and reverted `diagnose_personas.py`/`export_agent_repo.py`'s default-profile check back to the pre-`debd90de` sakking-keyed logic; restored 11 files from `debd90de`, fixed both regressed checks back to sakthai-keyed. `scripts/diagnose_personas.py` now passes 6/6 hermes-profile-scaffold checks (run with `.venv/bin/python3`, not system `python3` — the MCP-load subcheck needs the venv's `sakthai` import) | [/] In progress — uncommitted, awaiting Beer's go-ahead to commit |
| **Branch consolidation round 2 — repo reduced to `main` only** — 10 stale branches / 7 open PRs collapsed into one merge. Merged: #555 (MS Graph credentials added to the redaction sets across all persona `config.py`/`guardrails.py` + `sakthai-chat-cli`). Re-landed as a clean delta: #547's `make` guardrail (recipe scanning, `-C`/`-f` resolution, include-cycle guard) — its own branch had reverted `executor.py` hardening and deleted tracked `.workflow_runs/` fixtures during a bad merge, so only the guardrail hunks were taken. Consolidated: the unique protections from the five duplicate `_validate_filepath` rewrites (#552/#553/#554/#556/#557) folded onto main's #558 implementation — backslash-normalized traversal check, `opt` root, `.docker`/`.kube`/`.gnupg`/`.gcloud`/`.azure` dirs, `.env-`/`.env_`/`memory.db-` prefixes, private-key stem matching. Dropped without merging: two GraphClient branches that would have regressed #549's custom-scheme check back to a `startswith("http")` test, one SSRF branch already subsumed by #558, and a branch downgrading every GitHub Action from v7 to v4 | ✅ Done (2026-08-08) |
| **CLAUDE.md refresh — reconciled with the repo on disk** — re-audited every claim against the tree: persona package layout (three personas now carry partial real `sakthai/` dirs shadowing a `sakthai~origin_main` symlink, not five clean symlinks), the undocumented `agent/` modules (`guardrails`, `guardrails_hardened`, `security_hardening`, `context_filter`, `context_manager`, `prompt_builder`, `chat`, `eval`) and top-level `giturl`/`hf`/`sakking_skills`/`lead/`/`learn/ingest`, the real CLI surface (`chat`, `web setup|regen-token`, `extensions install` not `add`, `sessions clean` not `export`, `eval summary`, full `memory` subcommand list), 15 GitHub workflows (was 9), the mypy `sakthai.telegram.*` strict exemption, the closed web-server static-auth gap, and the full env-var set. Figures re-verified locally: 1,978 tests over 95 files green, 96.56% branch coverage, mypy strict clean over 69 files, ruff clean | ✅ Done (2026-08-08) |
| **README refresh — metrics reconciled with the repo** — replaced stale/unverifiable figures with locally verified ones (1,978 tests over 95 files, 96.56% branch coverage against the real `fail_under = 96`, mypy strict clean over 69 files, bandit 0 findings); corrected the package tree (14 tools not 10, added `security_hardening`/`guardrails_hardened`/`context_filter`/`context_manager`/`prompt_builder`/`chat` and the `cycle`/`web`/`dashboard`/`telegram`/`extensions`/`learn`/`lead` subpackages); persona skill counts recounted from `SKILL.md` files (823, was 843) with each persona's configured default model; provider table rewritten around how providers are actually selected (default model `claude-opus-4-8`); CI section rebuilt from the 15 real workflows, splitting per-push from scheduled; dropped the unverifiable security perf/benchmark tables in favour of the 8 named defense classes and measured hardening-test coverage; fixed `sakthai run` usage (takes a TASK argument) and the license section (all rights reserved) | ✅ Done (2026-08-08) |
| **Test coverage audit (analysis only)** — full suite re-measured on 3.11 (2,004 passed / 2 skipped / 6 deselected, 101 files, 96.018% branch coverage against `fail_under = 96`); eight ranked findings written up in [`docs/test-coverage-audit-2026-08-26.md`](./docs/test-coverage-audit-2026-08-26.md). Headline gaps: `telegram/bot.py` at 38% and hidden by a coverage `omit` with its authorization branch untested; `guardrails_hardened.py` + `security_hardening.py` (371 stmts) imported by nothing but their own test; `guardrails.py` section-6 container rules unreachable because `_check_destructive_tokens` denies first; web-auth tests cover acceptance only; the `SAKTHAI_*` deployment env readers at 0%; `team/engine.py` parallel failure paths untested; 13.5k lines of `personas/shared/sakthai/` (SakJules, SakTan) unmeasured. No production code changed | ✅ Done (2026-08-26) |

| **Bandit remediation across the non-package trees** — triage of the Bandit backlog on the code-scanning dashboard, rebuilt onto current `main`. **`B615` ×23 (unpinned Hugging Face downloads), split by who owns the repo:** four upstream `Qwen/*` base models pinned to immutable commit SHAs resolved from the Hub API and verified to exist, with `BASE_MODEL_REVISION` falling back to `None` when `BASE_MODEL` is overridden so a pin can never outlive the model it names; own-namespace `Nanthasit/*` adapters and datasets given `# nosec B615` with the reason, since an eval/export script exists to exercise whatever was last pushed and a pin would freeze the training loop against its own output. Bandit's acceptance of a *variable* `revision=` was probed before editing — which is why the own-namespace calls did **not** get a variable resolving to `None`, a move that would silence the rule while changing nothing. **`B108` ×11** replaced hardcoded `/tmp` with `tempfile.mkdtemp()` (mode 0700) / `gettempdir()`, the actual win being a private per-run directory instead of a predictable name in a world-writable one. **`B110`/`B112`** narrowed rather than suppressed: four bare `except:` in `scripts/workbench/` were swallowing `KeyboardInterrupt`/`SystemExit` alongside the JSON error they meant to catch; both `agent-self-evolution/.../skill_module.py` copies narrowed identically and `diff`-verified. **`B105`/`B310`** suppressed with rationale at the call site — token *paths* read as passwords, and literal loopback / fixed-host URLs. Verified with bandit 1.9.4: the scoped scan and a bare `bandit -r .` agree exactly. `SECURITY-INSIGHTS.yml` added (OpenSSF Security Insights v2.0.0, validated against the upstream CUE schema), populated only from facts the repository can prove and deliberately omitting the `release` block, since no official distribution point exists for the package itself | [x] 2026-08-26 |
## 📋 Sub-Plans

| Plan | Location | Status |
|---|---|---|
| Product & Monetization | [`product/PLAN.md`](./product/PLAN.md) | 🟡 Active — Phase 6 done, extending |
| Security Fixes (2026-07 Audit) | [`security/SECURITY_FIXES_PLAN.md`](./security/SECURITY_FIXES_PLAN.md) | 🔴 HIGH — Credential rotation + Web API auth |
| SakJules — skills organisation | [`personas/sakjules/PLAN.md`](./personas/sakjules/PLAN.md) | ✅ Complete — archived |
| SakTan — daily story & diary | `personas/saktan/PLAN.md` | ⚪ Archived — persona deleted per Beer directive |
| Agent Self-Evolution (×6 agents) | `personas/*/agent-self-evolution/PLAN.md` | 🟡 Active — personalised per agent |
| **Repo Hygiene Round 2** | [SCRATCH_ORGANISATION_PLAN](#scratch-organisation-plan) | 🟡 Active — root cleanup |
| **HF Ecosystem Improvement (19 models · 16 datasets · 7 Spaces)** | [`docs/hf-cards-improvement-plan.md`](./docs/hf-cards-improvement-plan.md) | 🟡 Active — Phase 1 (broken repos) next |

## 🔧 Runtime Notes

Runtime and deployment details are tracked in the implementation docs and the
workspace runtime config under `infra/`.

### Source files

- `docs/agent-diagnosis.md` for the standalone run checklist and runtime notes.
- `infra/hermes-agents/` for the live agent profiles, systemd services, and deployment config.
- `product/TODO.md` for the product delivery checklist.

---

## 🔑 Working Rules

1. **Plan first.** Update this file or the relevant sub-plan before acting.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **No duplication.** One source of truth per topic — link, don't copy.
4. **Protect Beer first.** No-cost, low-risk solutions always preferred.

---

## 🧹 SCRATCH_ORGANISATION_PLAN.MD

**Owner:** SakKing (spotter) → SakJules (executor)
**Status:** [x] 2026-08-08 — executed. Superseded in scope by
[`docs/repo-audit-2026-08-08.md`](./docs/repo-audit-2026-08-08.md), which covered
these root files plus generated-state bloat and the `.gitignore` shadowing bug.
**Priority:** Medium

### Problem
Root directory of `Sak-Family-Agent/` has accumulated scratch files that belong in subdirectories:

**5 Python scripts at root** (should be in `scripts/`):
- `_check_models.py` — HF model checker
- `_check_spaces.py` — HF spaces checker
- `_parse_datasets.py` — dataset parser
- `_parse_models.py` — model parser
- `_parse_spaces.py` — spaces parser

**5 JSON data files at root** (should be in `data/`):
- `ci_runs.json` (76 KB) — GitHub Actions run data
- `hf-topics-covered.json` (17 KB) — HF topic coverage data
- `hf_dataset.json` (0 bytes) — empty placeholder
- `hf_ds_size.json` (0 bytes) — empty placeholder
- `hf_embed_check.json` (0 bytes) — empty placeholder

### Steps for SakJules
1. Move 5 Python scripts to `scripts/`
2. Move 2 non-empty JSON files to `data/`
3. Remove 3 empty placeholder JSON files
4. Update any references in scripts that import these files

### Verification
1. `ls *.py *.json` at root → nothing ✅
2. `ls scripts/hf/_*.py` → 5 files ✅ (landed in `scripts/hf/`, not `scripts/`)
3. `ls data/*.json` → `hf-topics-covered.json` ✅ (`ci_runs.json` was deleted, not
   moved: it is a regenerable API-response cache the consuming skill reads from
   `/opt/data/`, never the repo copy)
4. Empty placeholders removed ✅
