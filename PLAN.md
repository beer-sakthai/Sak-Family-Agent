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

## 📋 Sub-Plans

| Plan | Location | Status |
|---|---|---|
| Product & Monetization | [`product/PLAN.md`](./product/PLAN.md) | 🟡 Active — Phase 6 done, extending |
| SakJules — skills organisation | [`personas/sakjules/PLAN.md`](./personas/sakjules/PLAN.md) | ✅ Complete — archived |
| SakTan — daily story & diary | [`personas/saktan/PLAN.md`](./personas/saktan/PLAN.md) | 🟢 Active — daily rhythm |
| Agent Self-Evolution (×6 agents) | `personas/*/agent-self-evolution/PLAN.md` | 🟡 Active — personalised per agent |

## 🔧 Runtime Notes

Runtime and deployment details are tracked in the implementation docs and the
workspace runtime config under `infra/`.

### Source files

- `docs/agent-diagnosis.md` for the standalone run checklist and runtime notes.
- `infra/hermes-agents/` for the live agent profiles, systemd services, and deployment config.
- `product/todo.md` for the product delivery checklist.

---

## 🔑 Working Rules

1. **Plan first.** Update this file or the relevant sub-plan before acting.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **No duplication.** One source of truth per topic — link, don't copy.
4. **Protect Beer first.** No-cost, low-risk solutions always preferred.
