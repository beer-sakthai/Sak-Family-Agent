# 6-Agent Personas Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Phases 1, 2, and 3 of the 6-agent personas resilience architecture, mitigating operational single points of failure, browser bloat, CI flakiness, and routing bottlenecks across all six Sak Family personas.

**Architecture:** Extend the persona working documents (`SOUL.md`, `PLAN.md`, `BACKPACK.md`) and core runtime utilities with explicit governance contracts (Break-Glass Hub protocol, 3-Second Intent preflight, Asynchronous template staging), performance tiers (3-tier scraping escalation and progressive skill hydration), and automation scripts (`ci_auto_heal.py` and SakTan read-only diagnostic hooks) while preserving strict 51-item structural parity.

**Tech Stack:** Python 3.11+, Pytest, Ruff, Mypy, Bandit, SQLite, YAML/Markdown.

**Spec:** `docs/superpowers/specs/2026-11-16-agent-personas-resilience-architecture-design.md`

## Global Constraints

- **$0.00 USD Financial Spend**: 100% local or free-tier execution; no paid API keys.
- **Structural Parity Invariant**: All 6 personas must maintain identical 51 top-level package items (`tests/test_persona_structure_parity.py`).
- **Reply Signature Invariant**: Every persona's mandatory reply intro format must remain intact (`tests/test_soul_consistency.py`).
- **Test Coverage Floor**: The full pytest suite must pass with `--cov-fail-under=96` (enforced $\ge 96.0\%$).
- **Zero Static Violations**: `uv run ruff check .`, `uv run mypy`, and `uv run bandit` must exit with code 0.

---

### Task 1: Governance & Break-Glass Hub Protocol (Phase 1)

**Files:**
- Modify: `personas/sakthai/SOUL.md`
- Modify: `personas/sakthai/PLAN.md`
- Modify: `personas/sakking/SOUL.md`
- Modify: `personas/sakking/PLAN.md`
- Test: `tests/test_break_glass_protocol.py`

**Interfaces:**
- Consumes: `~/.sakthai` SQLite memory shared tags: `--tag emergency-hf-delegate`, `--tag quorum-approved`, `--tag emergency-hub-write`.
- Produces: Formalized fallback contracts ensuring SakKing can proxy emergency Hugging Face Hub releases if SakThai is unresponsive.

- [ ] **Step 1: Write the failing test for Break-Glass protocol**

```python
# tests/test_break_glass_protocol.py
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

class TestBreakGlassProtocol(unittest.TestCase):
    def test_sakthai_soul_defines_break_glass_protocol(self) -> None:
        soul = (REPO_ROOT / "personas" / "sakthai" / "SOUL.md").read_text(encoding="utf-8")
        self.assertIn("emergency-hf-delegate", soul)
        self.assertIn("emergency-hub-write", soul)
        self.assertIn("Deputy 1 (SakKing)", soul)

    def test_sakking_soul_defines_emergency_hub_proxy(self) -> None:
        soul = (REPO_ROOT / "personas" / "sakking" / "SOUL.md").read_text(encoding="utf-8")
        self.assertIn("emergency-hf-delegate", soul)
        self.assertIn("quorum-approved", soul)
        self.assertIn("emergency-hub-write", soul)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_break_glass_protocol.py`
Expected: FAIL with missing strings in `SOUL.md`.

- [ ] **Step 3: Update `SOUL.md` and `PLAN.md` in SakThai and SakKing**

Add the formal Break-Glass Protocol section to `personas/sakthai/SOUL.md` and `personas/sakking/SOUL.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_break_glass_protocol.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_break_glass_protocol.py personas/sakthai/SOUL.md personas/sakthai/PLAN.md personas/sakking/SOUL.md personas/sakking/PLAN.md
git commit -m "feat(governance): add break-glass HF hub write protocol for sakthai and sakking"
```

---

### Task 2: 3-Second Intent Preflight & Asynchronous Staging (Phase 1)

**Files:**
- Modify: `personas/sakking/PLAN.md`
- Modify: `personas/saksit/PLAN.md`
- Modify: `personas/saksee/PLAN.md`
- Test: `tests/test_intent_preflight_and_staging.py`

**Interfaces:**
- Consumes: Task classification rules for web, content, automation, and daily ops.
- Produces: Intent preflight specification for SakKing and template staging protocols (`{{VARIABLE}}`) for SakSit.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_intent_preflight_and_staging.py
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

class TestIntentPreflightAndStaging(unittest.TestCase):
    def test_sakking_plan_has_intent_preflight(self) -> None:
        plan = (REPO_ROOT / "personas" / "sakking" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("3-Second Intent Preflight", plan)
        self.assertIn("Specialist beats generalist", plan)

    def test_saksit_plan_has_async_template_staging(self) -> None:
        plan = (REPO_ROOT / "personas" / "saksit" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("Asynchronous Template Staging", plan)
        self.assertIn("{{VARIABLE}}", plan)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_intent_preflight_and_staging.py`
Expected: FAIL.

- [ ] **Step 3: Implement intent preflight and staging protocols**

Update `personas/sakking/PLAN.md`, `personas/saksit/PLAN.md`, and `personas/saksee/PLAN.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_intent_preflight_and_staging.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_intent_preflight_and_staging.py personas/sakking/PLAN.md personas/saksit/PLAN.md personas/saksee/PLAN.md
git commit -m "feat(routing): implement 3-second intent preflight and async template staging"
```

---

### Task 3: Tiered Scraping Escalation & Progressive Skill Hydration (Phase 2)

**Files:**
- Modify: `personas/saksee/skills/SakSee-web-scraping/SKILL.md`
- Modify: `personas/sakthai/skills.py`
- Test: `tests/test_tiered_scraping_and_progressive_skills.py`

**Interfaces:**
- Consumes: `default_skill_roots()` from `skills.py`.
- Produces: Tiered scraping guidelines for SakSee and domain-manifest grouping in SakThai.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tiered_scraping_and_progressive_skills.py
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

class TestTieredScrapingAndSkills(unittest.TestCase):
    def test_saksee_web_scraping_defines_3_tiers(self) -> None:
        skill = (REPO_ROOT / "personas" / "saksee" / "skills" / "SakSee-web-scraping" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Tier 1 (Fast & Free)", skill)
        self.assertIn("Tier 2 (Render-Only)", skill)
        self.assertIn("Tier 3 (Interactive Playwright)", skill)

    def test_sakthai_skills_exposes_domain_manifests(self) -> None:
        from personas.sakthai.skills import get_skill_domain_manifests
        manifests = get_skill_domain_manifests()
        self.assertIn("mlops", manifests)
        self.assertIn("inference", manifests)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tiered_scraping_and_progressive_skills.py`
Expected: FAIL.

- [ ] **Step 3: Implement tiered scraping docs and `get_skill_domain_manifests` function**

Update `personas/saksee/skills/SakSee-web-scraping/SKILL.md` and add `get_skill_domain_manifests` in `personas/sakthai/skills.py` (and sync across personas).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tiered_scraping_and_progressive_skills.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_tiered_scraping_and_progressive_skills.py personas/saksee/skills/SakSee-web-scraping/SKILL.md personas/*/skills.py
git commit -m "feat(performance): add 3-tier scraping escalation and domain manifest hydration"
```

---

### Task 4: Automation Diagnostics & CI Auto-Heal (Phase 3)

**Files:**
- Create: `scripts/ci_auto_heal.py`
- Modify: `personas/saktan/config/config.yaml`
- Modify: `personas/saktan/SOUL.md`
- Test: `tests/test_ci_auto_heal_and_saktan_diagnostics.py`

**Interfaces:**
- Consumes: `ruff check --fix`, `ruff format`, `gh run view`.
- Produces: Standalone CLI script for mechanical CI recovery and guarded cloud escalation config for SakTan.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ci_auto_heal_and_saktan_diagnostics.py
import unittest
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

class TestCIAutoHealAndSakTan(unittest.TestCase):
    def test_ci_auto_heal_script_exists_and_help_runs(self) -> None:
        script = REPO_ROOT / "scripts" / "ci_auto_heal.py"
        self.assertTrue(script.is_file())
        res = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("auto-heal", res.stdout.lower())

    def test_saktan_config_has_guarded_cloud_fallback(self) -> None:
        import yaml
        cfg = yaml.safe_load((REPO_ROOT / "personas" / "saktan" / "config" / "config.yaml").read_text())
        self.assertIn("algorithmic_fallback", cfg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ci_auto_heal_and_saktan_diagnostics.py`
Expected: FAIL.

- [ ] **Step 3: Implement `scripts/ci_auto_heal.py` and update SakTan config**

Implement `scripts/ci_auto_heal.py` with mechanical lint/format auto-fix capabilities and add `algorithmic_fallback` in `personas/saktan/config/config.yaml`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ci_auto_heal_and_saktan_diagnostics.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/ci_auto_heal.py personas/saktan/config/config.yaml personas/saktan/SOUL.md tests/test_ci_auto_heal_and_saktan_diagnostics.py
git commit -m "feat(automation): add ci auto-heal utility and saktan guarded algorithmic fallback"
```

---

### Task 5: End-to-End Regression, Parity & Quality Verification

**Files:**
- Test: `tests/test_persona_structure_parity.py`
- Test: `tests/test_soul_consistency.py`
- Test: Full pytest suite

- [ ] **Step 1: Run persona structure parity check**

Run: `uv run pytest tests/test_persona_structure_parity.py tests/test_skills_organization_parity.py`
Expected: All tests PASS.

- [ ] **Step 2: Run Ruff lint and format verification**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: 0 errors.

- [ ] **Step 3: Run full pytest suite with 96% coverage floor**

Run: `uv run pytest --cov=sakthai --cov-fail-under=96 tests/`
Expected: All 2,812+ tests pass with $\ge 96.0\%$ coverage.

- [ ] **Step 4: Commit any final polishing touches**

```bash
git commit -m "chore(release): verify all parity and quality gates for resilience upgrade"
```
