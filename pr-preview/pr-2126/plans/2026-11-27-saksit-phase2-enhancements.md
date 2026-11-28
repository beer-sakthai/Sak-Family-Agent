# SakSit Phase 2 Architecture & Capability Enhancements Implementation Plan

> **Date**: 2026-11-27<br>
> **Persona**: SakSit (`@saksit_agent_bot`)<br>
> **Orchestrator**: SakJules · Master of Automation & CI/CD<br>
> **Methodology**: `superpowers-unified` (TDD, Micro-Tasks, Strict Verification)<br>
> **Status**: In-Progress

---

## 1. Overview & Objective

Building directly upon the foundational Phase 1 upgrade (PR #2096), this Phase 2 enhancement elevates **SakSit** (`personas/saksit/`) into a fully autonomous, production-grade social operations hub for the House of Sak.

### Key Pillars:
1. **Live Hugging Face Hub Metadata Hydration**: Direct `httpx` integration with `https://huggingface.co/api/` and 1-hour TTL local caching in `~/.sakthai/cache/stager/hub_metadata/`, automatically hydrating `{{DOWNLOADS}}`, `{{LIKES}}`, and commit SHAs into copy templates with offline fallback.
2. **Thai/English Bilingual Tone & GEO Evaluator**: Extending `evaluate_editorial_quality()` with Thai Unicode detection (`\u0e00-\u0e7f`), rewarding natural Thai technical phrasing and zero-cost framing, while penalizing awkward machine translations.
3. **Automated Social Asset Bundler**: Compiling staged copy (`post.md`), multimodal presets (`prompts.json`), and metadata (`metadata.json`) into structured bundle folders under `personas/saksit/reports/bundles/<slug>/` alongside an auto-generated `package.zip`.
4. **Gated Dual-Channel Webhook Dispatcher**: Providing controlled outbound broadcasting to Telegram channels and Discord webhooks, strictly gated by HMAC approval tokens from Beer's 1-tap digest with full `--dry-run` preflight support.
5. **Cross-Persona Parity & Quality Gates**: 100% byte-for-byte package parity across all 6 personas, test coverage floor $\ge 96.0\%$, strict Mypy, Ruff, and Bandit compliance.

---

## 2. Test-Driven Development (TDD) Phase Breakdown

### [x] Phase 1: Live Hugging Face Hub Metadata Hydration
- [x] RED: Write unit tests in `tests/test_saksit_live_hub_hydration.py` testing successful API hydration, 1-hour TTL cache retrieval, missing repo fallback, and offline network error handling.
- [x] GREEN: Implement `fetch_live_hub_metadata()` and `hydrate_with_live_hub()` in `sakthai.agent.stager`.
- [x] REFACTOR: Verify 100% test coverage and copy to all 6 personas.

### [x] Phase 2: Thai/English Bilingual Tone & GEO Evaluator
- [x] RED: Write unit tests in `tests/test_saksit_bilingual_eval.py` testing authentic Thai technical copy, machine-translation penalties, and bilingual consistency scoring.
- [x] GREEN: Update `evaluate_editorial_quality()` in `sakthai.agent.editorial_eval` with Thai evaluation rules.
- [x] REFACTOR: Verify 100% test coverage and copy to all 6 personas.

### [x] Phase 3: Automated Social Asset Bundler
- [x] RED: Write unit tests in `tests/test_saksit_social_bundler.py` testing bundle directory generation, `post.md`, `prompts.json`, `metadata.json`, and valid `package.zip` archive creation.
- [x] GREEN: Implement `create_social_asset_bundle()` in `sakthai.agent.bundler`.
- [x] REFACTOR: Verify 100% test coverage and copy to all 6 personas.

### [x] Phase 4: Gated Dual-Channel Webhook Dispatcher
- [x] RED: Write unit tests in `tests/test_saksit_webhook_dispatcher.py` testing HMAC token validation, `--dry-run` payload logging, Telegram channel broadcast, and Discord webhook dispatching.
- [x] GREEN: Implement `dispatch_social_post()` in `sakthai.telegram.dispatcher`.
- [x] REFACTOR: Verify 100% test coverage and copy to all 6 personas.

### [x] Phase 5: Documentation, Working Files & Final Quality Verification
- [x] Update `personas/saksit/BACKPACK.md`, `SOUL.md`, and `HANDOFF.md`.
- [x] Update `docs/capabilities.md` and root `PLAN.md`.
- [x] Verify test suite with coverage $\ge 96.0\%$, `make lint`, `mypy`, and `bandit`.
- [x] Commit, push branch `feat/saksit-phase2-enhancements`, and open Pull Request for Beer's review.
