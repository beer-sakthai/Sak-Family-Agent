# SakSit Full-Spectrum Upgrade Implementation Plan

> **Date**: 2026-11-26<br>
> **Persona**: SakSit (`@saksit_agent_bot`)<br>
> **Orchestrator**: SakJules · Master of Automation & CI/CD<br>
> **Methodology**: `superpowers-unified` (TDD, Micro-Tasks, Strict Verification)<br>
> **Status**: Complete (2026-11-26) — 100% Verified

---

## Overview

A comprehensive upgrade of **SakSit** (`personas/saksit/`) across role boundaries, approval pipelines, skill deduplication, multimodal media presets, upstream resilience, evaluator rubrics, and security guardrails.

---

## Phase 1: Skill Portfolio Pruning & Cross-Persona Parity Alignment

### Task 1.1: Prune Redundant Skills in `personas/saksit/skills/`
- **Goal**: Retire 3 duplicate skills (`SakSit-instagram-content-kit`, `SakSit-audiocraft`, `SakSit-b2b-saas-interactive-content-2026`) and migrate `SakSit-css-content-visibility` to `personas/saksee/skills/`.
- **Target Files**:
  - Remove: `personas/saksit/skills/SakSit-instagram-content-kit/`
  - Remove: `personas/saksit/skills/SakSit-audiocraft/`
  - Remove: `personas/saksit/skills/SakSit-b2b-saas-interactive-content-2026/`
  - Move: `personas/saksit/skills/SakSit-css-content-visibility/` $\rightarrow$ `personas/saksee/skills/SakSee-css-content-visibility/`
- **Verification**: `test ! -d personas/saksit/skills/SakSit-instagram-content-kit && test -d personas/saksee/skills/SakSee-css-content-visibility`

### Task 1.2: Update Persona Inventory & Documentation
- **Goal**: Align skill count (45 $\rightarrow$ 41 overlay skills for SakSit, 106 $\rightarrow$ 107 for SakSee) in `BACKPACK.md`, `AGENTS.md`, `MEMORY.md`, and `HANDOFF.md`.
- **Target Files**:
  - `personas/saksit/BACKPACK.md`
  - `personas/saksit/AGENTS.md`
  - `personas/saksit/MEMORY.md`
  - `personas/saksit/HANDOFF.md`
  - `personas/saksee/BACKPACK.md`
  - `personas/saksee/AGENTS.md`
- **Verification**: `git grep -n "45 Overlay Skills" personas/saksit/` returns 0 hits; verifies 41 overlay skills.

### Task 1.3: Update Structural Parity Tests & Regression Suites
- **Goal**: Update expected skill counts and assertions in `tests/test_persona_structure_parity.py` and `tests/test_persona_package_parity.py`.
- **Target Files**:
  - `tests/test_persona_structure_parity.py`
  - `tests/test_persona_package_parity.py`
- **Verification**: `uv run pytest tests/test_persona_structure_parity.py tests/test_persona_package_parity.py -q`

---

## Phase 2: Security & Path Leak Linter Integration

### Task 2.1: Write Failing Test for Public Secret & Path Leak Linter (RED)
- **Goal**: Define unit tests asserting that staged drafts containing local paths (`/home/...`), IP addresses, or secret key patterns trigger a security rejection.
- **Target Files**: `tests/test_content_leak_guardrail.py`
- **Verification**: `uv run pytest tests/test_content_leak_guardrail.py -q` (Must fail with expected error)

### Task 2.2: Implement Content Leak Linter & Sanitizer (GREEN)
- **Goal**: Add `scan_draft_for_leaks()` and `sanitize_external_quotes()` to `personas/sakthai/agent/guardrails.py` (and sync across personas).
- **Target Files**:
  - `personas/sakthai/agent/guardrails.py`
  - Sync to `personas/*/agent/guardrails.py`
- **Verification**: `uv run pytest tests/test_content_leak_guardrail.py tests/test_persona_guardrails_parity.py -q`

---

## Phase 3: Asynchronous Staging & Offline Cache Resilience

### Task 3.1: Write Unit Test for Template Staging & Cache Fallback (RED)
- **Goal**: Assert that SakSit can stage content with `{{PLACEHOLDER}}` tags when SakThai or SakSee is unready, and hydrates from local cache without stalling.
- **Target Files**: `tests/test_saksit_template_staging.py`
- **Verification**: `uv run pytest tests/test_saksit_template_staging.py -q` (Fails RED)

### Task 3.2: Implement Template Stager & Local Hub Cache Handler (GREEN)
- **Goal**: Implement template stager supporting `{{VARIABLE}}` slot replacement and graceful fallback tags (`[PENDING VERIFICATION]`).
- **Target Files**:
  - `personas/saksit/agent/stager.py`
  - `personas/sakthai/agent/stager.py`
- **Verification**: `uv run pytest tests/test_saksit_template_staging.py -q`

---

## Phase 4: Multimodal Social Dimension Presets

### Task 4.1: Write Test for Social Media Dimension Presets (RED)
- **Goal**: Test helper mapping preset names (`ig-reel`, `ig-carousel`, `x-card`, `linkedin-banner`) to exact aspect ratios, dimensions, and tool arguments.
- **Target Files**: `tests/test_media_dimension_presets.py`
- **Verification**: `uv run pytest tests/test_media_dimension_presets.py -q` (Fails RED)

### Task 4.2: Implement Media Preset Helper (GREEN)
- **Goal**: Create `media_presets.py` providing validated dimensions, aspect ratios, and prompt wrappers for FLUX.1/LTX-Video.
- **Target Files**:
  - `personas/saksit/agent_platform/media_presets.py`
  - `personas/sakthai/agent_platform/media_presets.py`
- **Verification**: `uv run pytest tests/test_media_dimension_presets.py -q`

---

## Phase 5: Multi-Pass Editorial & GEO Evaluator Loop

### Task 5.1: Write Test for 3-Part Editorial & AI Citation Evaluator (RED)
- **Goal**: Test evaluation rubric scoring (Beer's Authentic Voice, Technical Precision, GEO / AI Citation Readiness) returning 0-100 score.
- **Target Files**: `tests/test_saksit_editorial_eval.py`
- **Verification**: `uv run pytest tests/test_saksit_editorial_eval.py -q` (Fails RED)

### Task 5.2: Implement 3-Part Editorial Evaluator (GREEN)
- **Goal**: Implement editorial rubric scoring functions in evaluation pipeline.
- **Target Files**:
  - `personas/sakthai/agent/editorial_eval.py`
  - `personas/saksit/agent/editorial_eval.py`
- **Verification**: `uv run pytest tests/test_saksit_editorial_eval.py -q`

---

## Phase 6: Hybrid Joy Approval Pipeline & Staging Integration

### Task 6.1: Write Test for Telegram 1-Tap Digest & Staged Markdown Writer (RED)
- **Goal**: Test generation of Telegram inline callback payloads and markdown report generation in `reports/staged/`.
- **Target Files**: `tests/test_saksit_approval_pipeline.py`
- **Verification**: `uv run pytest tests/test_saksit_approval_pipeline.py -q` (Fails RED)

### Task 6.2: Implement Approval Pipeline & Staging Writer (GREEN)
- **Goal**: Implement Telegram digest formatter with callback actions and staged report generator.
- **Target Files**:
  - `personas/saksit/telegram/digest.py`
  - `personas/sakthai/telegram/digest.py`
  - Directory: `personas/saksit/reports/staged/`
- **Verification**: `uv run pytest tests/test_saksit_approval_pipeline.py -q`

---

## Phase 7: Full Suite Verification & Quality Gates

### Task 7.1: Cross-Persona Parity & Diagnostic Audit
- **Command**: `uv run sakthai eval audit --persona saksit && uv run sakthai eval personas --persona saksit`
- **Acceptance**: 100% Grade A+ on all 6 pillars.

### Task 7.2: Full Test Suite, Lint & Security Scans
- **Command**: `make test && make lint && uv run bandit -c pyproject.toml -r personas/sakthai`
- **Acceptance**: All tests pass, 0 linter errors, 0 security vulnerabilities.
