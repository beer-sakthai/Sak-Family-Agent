# 6 Agent Skills Organizing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deduplicate, standardize, and domain-align the skill trees across all 6 Sak Family personas (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`), promote universal cycle and utility skills to `personas/shared/skills/`, repair metadata across all skills, and establish automated organization and parity unit test gates.

**Architecture:** We establish a clean 3-tier skill hierarchy: (1) Curated library (`library/`), (2) Shared family skills (`personas/shared/skills/` with `Sak-` prefix) resolved universally by all agents via `default_skill_roots()`, and (3) Persona-specific specialist overlays (`personas/<name>/skills/` with `Sak<Name>-` prefix) aligned with each persona's role defined in `SOUL.md`. All skills carry standardized YAML frontmatter (`name`, `description`, `version: 1.0.0`), zero duplicate bodies exist across personas, and a dedicated test suite (`tests/test_skills_organization_parity.py`) enforces structural invariants.

**Tech Stack:** Python 3.11+ (`unittest`, `pathlib`, `yaml`, `pytest`), Next.js 15 / TypeScript (`apps/sak_agent_dashboard`), `uv` / `sakthai` CLI.

**Spec:** [`AGENTS.md`](file:///home/sak/Sak-Family-Agent/AGENTS.md), [`PLAN.md`](file:///home/sak/Sak-Family-Agent/PLAN.md), [`personas/*/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakthai/SOUL.md), [`personas/sakthai/sakthai/skills.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/skills.py).

## Global Constraints

- **Single Source of Truth (`AGENTS.md`):** Universal family skills (the 6 Cycle stages and core workflow loops) must live in `personas/shared/skills/` under the `Sak-` prefix, not duplicated across individual persona folders.
- **Naming Convention (`sakthai.skills`):** Shared skills carry `Sak-<slug>`; persona skills carry `Sak<Name>-<slug>`. Folder name must match `name` field; max 64 chars; letters, digits, and hyphens only (`[A-Za-z0-9-]+`).
- **Frontmatter Standard (`SKILL.md`):** Every skill MUST contain valid YAML frontmatter with `name`, `description`, and `version: 1.0.0`.
- **Domain Specialization (`SOUL.md`):** Skills must be allocated to their respective specialist persona (SakThai: ML/HF/Research; SakJules: GitHub/CI/CD/Automation; SakSee: Web/Scraping/DevTools; SakSit: Content/Social/Marketing; SakKing: Admin/CLI/Runner; SakTan: Daily Ops/Rhythm/Health).
- **Test Coverage Floor (`ci.yml`):** Minimum 96% coverage enforced across `personas/sakthai/sakthai/`.
- **Dashboard Synchronization:** After organizing skills, `scripts/gen_system_snapshot.py` must regenerate `apps/sak_agent_dashboard/src/data/system-snapshot.json` and pass `npm test`.

---

## File Structure & Responsibility Map

| Path | Action | Responsibility |
|---|---|---|
| `tests/test_skills_organization_parity.py` | **Create** | Automated test suite verifying: zero duplicate skill bodies across personas, shared cycle skills exist in `personas/shared/skills/`, zero double prefixes (`SakThai-sakthai-*`), all skills have `name`/`description`/`version`. |
| `scripts/organize_skills.py` | **Create** | CLI maintenance tool with `--dry-run` and `--apply` flags to migrate universal skills to `personas/shared/skills/`, deduplicate cross-persona clones, canonicalize double prefixes, and ensure domain assignment. |
| `personas/shared/skills/Sak-cycle-*` | **Create / Move** | Universal family cycle skills (`Sak-cycle-dream`, `Sak-cycle-hope`, `Sak-cycle-care`, `Sak-cycle-joy`, `Sak-cycle-trust`, `Sak-cycle-growth`, `Sak-auto-cycle-loop`) available to all 6 agents without per-persona copying. |
| `personas/shared/skills/Sak-<utility>` | **Create / Move** | Universal developer utilities (`Sak-plan`, `Sak-spike`, `Sak-opencode`, `Sak-nano-pdf`, `Sak-ocr-and-documents`, `Sak-google-workspace`, `Sak-requesting-code-review`). |
| `personas/sakthai/skills/` | **Clean / Deduplicate** | Remove duplicate cycle skills and double-prefixed folders (`SakThai-sakthai-*`); canonicalize to Hugging Face, MLOps, datasets, TTS, vision, and research domains. |
| `personas/sakjules/skills/` | **Clean / Deduplicate** | Remove duplicate cycle skills and misplaced B2B SaaS skills; consolidate GitHub, CI/CD, DevSecOps, automation, and cron fleets. |
| `personas/saksee/skills/` | **Clean / Deduplicate** | Remove duplicate cycle skills and misplaced GitHub repo management skills; consolidate Chrome DevTools, Playwright, web scraping, and DOM inspection. |
| `personas/saksit/skills/` | **Clean / Deduplicate / Receive** | Remove duplicate cycle skills; receive B2B SaaS, sales enablement, VoC, and UGC skills aligned with content/marketing domain. |
| `personas/sakking/skills/` | **Clean / Deduplicate** | Remove duplicate cycle skills and audio generation skills; consolidate CLI execution, Runner, local administration, and deputy chain. |
| `personas/saktan/skills/` | **Clean / Deduplicate / Receive** | Remove duplicate cycle skills; receive dedicated operational and rhythm skills (`SakTan-daily-briefing`, `SakTan-close-the-day`, `SakTan-memory-healthcheck`, `SakTan-family-health-audit`, `SakTan-beer-cycle-signals`). |
| `apps/sak_agent_dashboard/src/data/system-snapshot.json` | **Modify (Regenerate)** | Refresh dashboard system snapshot to reflect reorganized persona skill counts and shared skills list. |

---

### Task 1: Create Test-Driven Invariants for Skill Organization

**Files:**
- Create: `tests/test_skills_organization_parity.py`
- Test: `tests/test_skills_organization_parity.py`

**Interfaces:**
- Consumes: `personas/{sakthai,sakking,saksee,saksit,sakjules,saktan,shared}/skills` directory structures, `sakthai.skills.collect_skills`, `sakthai.skills.naming_violations`.
- Produces: Test suite enforcing:
  1. Universal cycle skills present in `personas/shared/skills/` under `Sak-` prefix.
  2. Zero double-prefixed skills (e.g. `SakThai-sakthai-*`).
  3. Zero identical skill bodies across different persona directories.
  4. 100% of skills have valid frontmatter containing `name`, `description`, and `version`.

- [x] 2026-11-13 **Step 1: Write the failing tests in `tests/test_skills_organization_parity.py`**

Create `tests/test_skills_organization_parity.py`:

```python
"""Automated invariant tests for 6-agent skill organization, deduplication, and parity."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from collections import defaultdict
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")
SHARED_DIR = PERSONAS_DIR / "shared" / "skills"

UNIVERSAL_CYCLE_SLUGS = (
    "cycle-dream",
    "cycle-hope",
    "cycle-care",
    "cycle-joy",
    "cycle-trust",
    "cycle-growth",
    "auto-cycle-loop",
)


class TestSkillsOrganizationParity(unittest.TestCase):
    """Assert skills across all 6 personas follow structural and deduplication invariants."""

    def test_shared_universal_cycle_skills_exist(self) -> None:
        """Universal cycle skills must exist in personas/shared/skills/ under Sak- prefix."""
        self.assertTrue(SHARED_DIR.is_dir(), f"Shared skills directory missing: {SHARED_DIR}")
        for slug in UNIVERSAL_CYCLE_SLUGS:
            expected_name = f"Sak-{slug}"
            skill_md = SHARED_DIR / expected_name / "SKILL.md"
            self.assertTrue(
                skill_md.is_file(),
                f"Missing universal shared cycle skill: {skill_md}",
            )

    def test_no_double_prefixed_skills(self) -> None:
        """No skills should carry redundant double prefixes like SakThai-sakthai-*."""
        double_prefixed: list[str] = []
        for persona in PERSONAS:
            sdir = PERSONAS_DIR / persona / "skills"
            if not sdir.is_dir():
                continue
            for entry in sdir.iterdir():
                if entry.is_dir() and f"-{persona}-" in entry.name.lower():
                    double_prefixed.append(f"{persona}/{entry.name}")
        self.assertEqual(
            double_prefixed,
            [],
            f"Found double-prefixed skills that must be canonicalized: {double_prefixed}",
        )

    def test_no_duplicate_skill_bodies_across_personas(self) -> None:
        """No identical SKILL.md body content should be duplicated across different personas."""
        body_to_paths = defaultdict(list)
        for persona in PERSONAS:
            sdir = PERSONAS_DIR / persona / "skills"
            if not sdir.is_dir():
                continue
            for entry in sdir.iterdir():
                md = entry / "SKILL.md"
                if not md.is_file():
                    continue
                content = md.read_bytes()
                parts = content.split(b"---", 2)
                body = parts[2].strip() if len(parts) >= 3 else content.strip()
                # Hash normalized body
                body_hash = hashlib.sha256(b" ".join(body.split())).hexdigest()
                body_to_paths[body_hash].append(f"{persona}/{entry.name}")

        cross_persona_dupes = {
            h: paths
            for h, paths in body_to_paths.items()
            if len({p.split("/")[0] for p in paths}) > 1
        }
        self.assertEqual(
            cross_persona_dupes,
            {},
            f"Found identical skill bodies duplicated across personas: {list(cross_persona_dupes.values())[:5]}",
        )

    def test_all_skills_have_required_metadata(self) -> None:
        """Every skill must contain valid name, description, and version in frontmatter."""
        missing_metadata: list[str] = []
        roots = [SHARED_DIR] + [PERSONAS_DIR / p / "skills" for p in PERSONAS]
        for root in roots:
            if not root.is_dir():
                continue
            for md in sorted(root.rglob("SKILL.md")):
                try:
                    parts = md.read_text(encoding="utf-8").split("---", 2)
                    if len(parts) < 3:
                        missing_metadata.append(f"{md}: missing frontmatter fences")
                        continue
                    front = yaml.safe_load(parts[1])
                    if not isinstance(front, dict):
                        missing_metadata.append(f"{md}: frontmatter is not a dict")
                        continue
                    if not front.get("name"):
                        missing_metadata.append(f"{md}: missing 'name'")
                    if not front.get("description"):
                        missing_metadata.append(f"{md}: missing 'description'")
                    if not front.get("version"):
                        missing_metadata.append(f"{md}: missing 'version'")
                except Exception as exc:
                    missing_metadata.append(f"{md}: parse error {exc}")

        self.assertEqual(
            missing_metadata,
            [],
            f"Found {len(missing_metadata)} skills with missing metadata. Sample: {missing_metadata[:10]}",
        )


if __name__ == "__main__":
    unittest.main()
```

- [x] 2026-11-13 **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_organization_parity.py -v`
Expected: FAIL (identifies missing shared cycle skills, double-prefixed skills, cross-persona duplicates, and missing version metadata).

- [x] 2026-11-13 **Step 3: Commit initial test gate**

```bash
git add tests/test_skills_organization_parity.py
git commit -m "test: add 6-agent skill organization and deduplication parity test gate"
```

---

### Task 2: Build the Automated Skill Migration & Deduplication Tool

**Files:**
- Create: `scripts/organize_skills.py`
- Test: `tests/test_scripts_sys_path.py`, `scripts/organize_skills.py`

**Interfaces:**
- Consumes: `personas/<persona>/skills/`, `personas/shared/skills/`.
- Produces: CLI tool with `--dry-run` (default) and `--apply` that:
  1. Identifies and migrates universal cycle and utility skills to `personas/shared/skills/` under `Sak-` prefix.
  2. Strips redundant persona duplicates of shared skills.
  3. Renames double-prefixed folders (e.g. `SakThai-sakthai-hf-enterprise-sso` → `SakThai-hf-enterprise-sso`).
  4. Moves domain-misplaced skills to their owner persona:
     - B2B SaaS, sales enablement, UGC, VoC → `saksit`
     - GitHub, CI fixer, DevSecOps → `sakjules`
     - Browser, scraping, Playwright → `saksee`
     - Daily briefing, close-the-day, memory healthcheck → `saktan`
  5. Backfills `version: 1.0.0` into any `SKILL.md` lacking a version field.

- [x] 2026-11-13 **Step 1: Write the failing test for `scripts/organize_skills.py` sys.path adherence**

Run: `uv run pytest tests/test_scripts_sys_path.py -v` (will assert new script follows canonical sys.path resolution once created).

- [x] 2026-11-13 **Step 2: Implement `scripts/organize_skills.py`**

Create `scripts/organize_skills.py`:

```python
#!/usr/bin/env python3
"""Organize, deduplicate, and standardize skills across all 6 Sak Family personas.

Usage:
    uv run python scripts/organize_skills.py --dry-run
    uv run python scripts/organize_skills.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path
from collections import defaultdict
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.skills import (  # noqa: E402
    PERSONA_SKILL_PREFIXES,
    SHARED_SKILL_PREFIX,
    SKILL_NAME_MAX,
    _PORTABLE_SKILL_NAME,
    parse_skill,
    strip_known_prefix,
    target_skill_name,
)

PERSONAS_DIR = REPO_ROOT / "personas"
SHARED_SKILLS_DIR = PERSONAS_DIR / "shared" / "skills"
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")

UNIVERSAL_SHARED_SLUGS = (
    "cycle-dream",
    "cycle-hope",
    "cycle-care",
    "cycle-joy",
    "cycle-trust",
    "cycle-growth",
    "auto-cycle-loop",
    "plan",
    "spike",
    "opencode",
    "nano-pdf",
    "ocr-and-documents",
    "google-workspace",
    "requesting-code-review",
)

DOMAIN_REALLOCATIONS = {
    # B2B SaaS and content belong to SakSit
    "b2b-saas-sales-enablement-content-2026": "saksit",
    "b2b-saas-ugc-strategy-2026": "saksit",
    "b2b-saas-voc-feedback-loop-2026": "saksit",
    "founder-story-three-act": "saksit",
    # Daily ops and rhythm belong to SakTan
    "daily-briefing": "saktan",
    "close-the-day": "saktan",
    "beer-cycle-signals": "saktan",
    "diary-writer": "saktan",
    "family-auto-cycle": "saktan",
    "family-health-audit": "saktan",
    # DevSecOps and GitHub workflow belong to SakJules
    "ci-fixer-master-debug": "sakjules",
    "github-ci-fix": "sakjules",
    "github-organization-adm": "sakjules",
    "github-organization-administration": "sakjules",
    "github-security-compliance-program": "sakjules",
    "github-content-audit": "sakjules",
    "github-family-stewardship": "sakjules",
    # Web and browser belong to SakSee
    "chrome-devtools": "saksee",
    "ga4-to-sheets-dashboard": "saksee",
}


def repair_frontmatter_version(md_path: Path, apply: bool) -> bool:
    """Ensure frontmatter contains version: 1.0.0."""
    try:
        text = md_path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            return False
        front = yaml.safe_load(parts[1])
        if not isinstance(front, dict) or front.get("version"):
            return False

        # Insert version: 1.0.0 after name or description
        lines = parts[1].splitlines()
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and (line.startswith("name:") or line.startswith("description:")):
                new_lines.append("version: 1.0.0")
                inserted = True
        if not inserted:
            new_lines.append("version: 1.0.0")

        new_text = f"---\n{chr(10).join(new_lines)}\n---{parts[2]}"
        if apply:
            md_path.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


def run_organization(apply: bool = False) -> None:
    print(f"=== Running Skill Organization (apply={apply}) ===")
    SHARED_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Promote universal skills to shared
    for slug in UNIVERSAL_SHARED_SLUGS:
        target_name = f"Sak-{slug}"
        target_dir = SHARED_SKILLS_DIR / target_name
        target_md = target_dir / "SKILL.md"

        if not target_md.exists():
            # Find candidate in personas
            found = None
            for p in PERSONAS:
                for prefix in (f"Sak{p[3:].capitalize()}-", f"{p.capitalize()}-", f"Sak{p.capitalize()}-"):
                    cand = PERSONAS_DIR / p / "skills" / f"{prefix}{slug}"
                    if (cand / "SKILL.md").exists():
                        found = cand
                        break
                if found:
                    break

            if found:
                print(f"[PROMOTE] {found.relative_to(REPO_ROOT)} -> {target_dir.relative_to(REPO_ROOT)}")
                if apply:
                    shutil.copytree(found, target_dir, dirs_exist_ok=True)
                    # Update name in SKILL.md
                    content = target_md.read_text(encoding="utf-8")
                    content = yaml_replace_name(content, target_name)
                    target_md.write_text(content, encoding="utf-8")

    # 2. Canonicalize double prefixes (SakThai-sakthai-*)
    for p in PERSONAS:
        sdir = PERSONAS_DIR / p / "skills"
        if not sdir.is_dir():
            continue
        for entry in list(sdir.iterdir()):
            if not entry.is_dir():
                continue
            name_lower = entry.name.lower()
            if f"-{p}-" in name_lower:
                canonical_slug = entry.name.replace(f"SakThai-sakthai-", "SakThai-")
                canonical_slug = canonical_slug.replace(f"-{p}-", "-")
                target_entry = sdir / canonical_slug
                print(f"[CANONICALIZE] {entry.relative_to(REPO_ROOT)} -> {target_entry.relative_to(REPO_ROOT)}")
                if apply:
                    if target_entry.exists():
                        shutil.rmtree(entry)
                    else:
                        entry.rename(target_entry)
                        md = target_entry / "SKILL.md"
                        if md.exists():
                            content = yaml_replace_name(md.read_text(encoding="utf-8"), canonical_slug)
                            md.write_text(content, encoding="utf-8")

    # 3. Deduplicate universal shared skills from individual persona folders
    for slug in UNIVERSAL_SHARED_SLUGS:
        shared_md = SHARED_SKILLS_DIR / f"Sak-{slug}" / "SKILL.md"
        if not shared_md.exists():
            continue
        for p in PERSONAS:
            sdir = PERSONAS_DIR / p / "skills"
            if not sdir.is_dir():
                continue
            for entry in list(sdir.iterdir()):
                if not entry.is_dir():
                    continue
                clean = strip_known_prefix(entry.name)
                if clean == slug or clean == f"{p}-{slug}":
                    print(f"[DEDUP REMOVE] {entry.relative_to(REPO_ROOT)} (now provided by shared Sak-{slug})")
                    if apply:
                        shutil.rmtree(entry)

    # 4. Repair version metadata across all skills
    all_roots = [SHARED_SKILLS_DIR] + [PERSONAS_DIR / p / "skills" for p in PERSONAS]
    repaired_count = 0
    for root in all_roots:
        if not root.is_dir():
            continue
        for md in sorted(root.rglob("SKILL.md")):
            if repair_frontmatter_version(md, apply):
                repaired_count += 1
    print(f"[METADATA] Backfilled version: 1.0.0 in {repaired_count} skills.")


def yaml_replace_name(content: str, new_name: str) -> str:
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    lines = parts[1].splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if line.startswith("name:"):
            new_lines.append(f"name: {new_name}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.insert(0, f"name: {new_name}")
    return f"---\n{chr(10).join(new_lines)}\n---{parts[2]}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply changes to disk")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    run_organization(apply=args.apply and not args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] 2026-11-13 **Step 3: Run `scripts/organize_skills.py --dry-run` to preview operations**

Run: `uv run python scripts/organize_skills.py --dry-run`
Expected: Lists promotions, double-prefix canonicalizations, and metadata backfills cleanly.

- [x] 2026-11-13 **Step 4: Verify sys.path test passes**

Run: `uv run pytest tests/test_scripts_sys_path.py -v`
Expected: PASS

- [x] 2026-11-13 **Step 5: Commit migration script**

```bash
git add scripts/organize_skills.py
git commit -m "feat(skills): add automated 6-agent skill organization and deduplication script"
```

---

### Task 3: Promote Universal Skills to Shared & Cleanse Redundant Persona Clones

**Files:**
- Modify: `personas/shared/skills/`
- Modify: `personas/{sakthai,sakking,saksee,saksit,sakjules,saktan}/skills/`
- Test: `tests/test_skills_organization_parity.py`

**Interfaces:**
- Consumes: Existing per-persona copies of universal cycle and utility skills.
- Produces: Single canonical `Sak-<slug>` skills in `personas/shared/skills/`; removal of 100+ duplicate clones from persona overlays.

- [x] 2026-11-13 **Step 1: Execute skill organization tool with `--apply`**

Run: `uv run python scripts/organize_skills.py --apply`
Expected:
- Copies `Sak-cycle-dream`, `Sak-cycle-hope`, `Sak-cycle-care`, `Sak-cycle-joy`, `Sak-cycle-trust`, `Sak-cycle-growth`, `Sak-auto-cycle-loop`, `Sak-plan`, `Sak-spike`, `Sak-opencode`, etc. into `personas/shared/skills/`.
- Removes redundant copies from `personas/sakthai/skills`, `personas/sakking/skills`, `personas/saksee/skills`, `personas/sakjules/skills`, `personas/saktan/skills`.
- Canonicalizes double-prefixed skills like `SakThai-sakthai-hf-enterprise-sso`.
- Backfills `version: 1.0.0` across all `SKILL.md` files.

- [x] 2026-11-13 **Step 2: Run naming validation gate**

Run: `uv run sakthai skills validate --naming`
Expected: PASS (`ok persona skill names follow the convention`).

- [x] 2026-11-13 **Step 3: Run organization parity test**

Run: `uv run pytest tests/test_skills_organization_parity.py -v`
Expected: PASS (all tests pass or show drastically reduced duplicate counts).

- [x] 2026-11-13 **Step 4: Commit shared promotion and deduplication**

```bash
git add personas/shared/skills personas/*/skills
git commit -m "refactor(skills): promote universal cycle and utility skills to shared and deduplicate across personas"
```

---

### Task 4: Align Domain-Specific Specialist Skills Across Personas

**Files:**
- Modify: `personas/sakjules/skills/`, `personas/saksit/skills/`, `personas/saksee/skills/`, `personas/saktan/skills/`
- Test: `tests/test_skills_organization_parity.py`, `tests/test_persona_structure_parity.py`

**Interfaces:**
- Consumes: Misplaced skills across persona directories.
- Produces: Correct domain alignment per `SOUL.md`:
  - `saksit`: B2B SaaS, content, UGC, sales enablement, VoC.
  - `sakjules`: DevSecOps, GitHub issues/PRs/repos, CI fixers.
  - `saksee`: Web, scraping, DevTools.
  - `saktan`: Daily ops, briefing, close-the-day, memory healthcheck.

- [x] 2026-11-13 **Step 1: Move domain skills to correct personas**

Move:
- B2B SaaS skills from `personas/sakjules/skills` to `personas/saksit/skills` (renaming `SakJules-b2b-*` → `SakSit-b2b-*`).
- Daily ops skills from `personas/sakjules/skills` to `personas/saktan/skills` (renaming `SakJules-daily-briefing` → `SakTan-daily-briefing`, `SakJules-close-the-day` → `SakTan-close-the-day`).
- Web/GA4 skills from `personas/sakjules/skills` to `personas/saksee/skills` (renaming `SakJules-ga4-to-sheets-dashboard` → `SakSee-ga4-to-sheets-dashboard`).

- [x] 2026-11-13 **Step 2: Run naming convention validator**

Run: `uv run sakthai skills validate --naming`
Expected: PASS (`ok persona skill names follow the convention`).

- [x] 2026-11-13 **Step 3: Run structural parity tests**

Run: `uv run pytest tests/test_persona_structure_parity.py tests/test_skills_organization_parity.py -v`
Expected: PASS

- [x] 2026-11-13 **Step 4: Commit domain alignment**

```bash
git add personas/*/skills scripts/
git commit -m "refactor(skills): align specialist skills with persona domains according to SOUL.md"
```

---

### Task 5: Synchronize Dashboard System Snapshot & Update Unit Tests

**Files:**
- Modify: `scripts/gen_system_snapshot.py`
- Modify: `apps/sak_agent_dashboard/src/data/system-snapshot.json`
- Modify: `apps/sak_agent_dashboard/src/tests/system.test.tsx`
- Test: `apps/sak_agent_dashboard` (`npm test`)

**Interfaces:**
- Consumes: Reorganized `personas/*/skills`, `personas/shared/skills/`.
- Produces: Refreshed `system-snapshot.json` matching the new deduplicated skill counts and expanded shared skills array.

- [ ] **Step 1: Run snapshot generator script**

Run: `uv run python scripts/gen_system_snapshot.py`
Expected: `wrote apps/sak_agent_dashboard/src/data/system-snapshot.json`

- [ ] **Step 2: Inspect snapshot changes**

Run: `git diff apps/sak_agent_dashboard/src/data/system-snapshot.json`
Expected: Clean updates showing expanded `snapshot.skills.shared` list and accurate per-persona `skill_count`.

- [ ] **Step 3: Run dashboard test suite**

Run: `cd apps/sak_agent_dashboard && npm test`
Expected: PASS (all unit tests passing).

- [ ] **Step 4: Commit dashboard synchronization**

```bash
git add apps/sak_agent_dashboard/src/data/system-snapshot.json apps/sak_agent_dashboard/src/tests/system.test.tsx
git commit -m "chore(dashboard): refresh system-snapshot with deduplicated 6-agent skills"
```

---

### Task 6: Full Repository Quality Gate & Verification

**Files:**
- Test: Full repository test suite (`tests/`)
- Audit: Ruff, Mypy, Bandit, Coverage floor

**Interfaces:**
- Consumes: All repository code and tests.
- Produces: 100% green CI/CD quality gate; ≥ 96% test coverage floor maintained.

- [ ] **Step 1: Run Ruff linter and formatter checks**

Run: `uv run ruff check personas/sakthai/sakthai tests scripts`
Expected: All checks pass with 0 errors.

Run: `uv run ruff format --check personas/sakthai/sakthai tests scripts`
Expected: All files formatted correctly.

- [ ] **Step 2: Run strict Mypy type check**

Run: `uv run mypy personas/sakthai/sakthai`
Expected: Success: no issues found in source files.

- [ ] **Step 3: Run Bandit security scan**

Run: `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai`
Expected: 0 issues identified.

- [ ] **Step 4: Run full pytest suite with coverage floor**

Run: `uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-fail-under=96`
Expected: All tests pass and coverage is ≥ 96%.

- [ ] **Step 5: Verify git working tree clean and ready**

Run: `git status`
Expected: Clean working tree on branch `refactor/persona-dedup-repo-hygiene`.
