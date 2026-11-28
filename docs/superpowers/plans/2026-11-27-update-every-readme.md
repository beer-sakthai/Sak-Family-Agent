# Monorepo-Wide README.md Modernization & Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit, synchronize, and modernize every tracked `README.md` across the House of Sak repository, aligning all metrics with recent architectural upgrades: Gemini 4 Neon (`gemini-4-neon`) flagship default, Dependabot daily automation across all ecosystems, `sak.cli/v1` output contract with full vibrant rainbow UI, exact on-disk skill counts (460 overlay + 3 shared = 463 total), and 4,333 unit/integration tests across 216 pytest files.

**Architecture:** Split documentation updates into four focused domain tiers (Monorepo Hub & Root, 6 Personas & Overlays, Apps & Infrastructure, and Services/Training/MLOps). Enforce strict contract parity tests (`test_personas_readme_skill_counts_match_disk`, `test_persona_markdown_files_match_disk_skills_and_canonical_paths`, `test_readme_documents_the_real_canonical_package_path`, `test_no_forbidden_strings_in_persona_markdown`) at each step. Conclude with zero-whitespace validation, linter pass, Bandit security scan, and Pull Request submission for Beer's manual review.

**Tech Stack:** Markdown, Python 3.11/3.12, Pytest, `uv`, GitHub CLI (`gh`).

**Spec:** Self-contained within repository documentation standards and contract tests in `tests/test_soul_consistency.py`, `tests/test_repo_hygiene.py`, and `tests/test_persona_structure_parity.py`.

## Global Constraints

- **Financial Cost Policy**: $0.00 USD Financial Spend (100% Local & Free Tier Execution).
- **Flagship Model Identity**: Google Gemini flagship model is **Gemini 4 Neon** (`gemini-4-neon`), with `GEMINI_FREE_ONLY=true` fallback to **Gemini 4 Hydrogen** (`gemini-4-hydrogen`).
- **CLI Output Contract**: `sak.cli/v1` envelope (`{schema, ok, data, error, warnings}`) with schema `https://schemas.sakthai.family/v1/cli-envelope.json`, standard exit codes (0=ok, 1=fail, 2=usage, 3=not ready, 130=interrupted), `--json`, `-q`/`--quiet`, `--no-color`, and Full Vibrant Spectrum Rainbow UI in TTY mode.
- **Dependency Automation**: Dependabot runs on a daily schedule (`interval: "daily"`) across all 4 ecosystems (`uv`, `npm`, `github-actions`, `docker`).
- **Exact Skill Parity**: 463 total skills (460 persona overlays + 3 shared in `.agents/skills/`), with exact breakdown: SakThai 174, SakSee 98, SakJules 48, SakKing 64, SakSit 50, SakTan 26.
- **Test Metric Invariant**: 216 pytest test files (`tests/`) containing 4,333 collected tests + 24 dashboard test suites.
- **Forbidden Strings in Persona Markdown**: Every persona `README.md` must NOT contain `personas/sakthai/sakthai`, `personas/sakthai/agent-self-evolution`, or `hermes` (case-insensitive).
- **Canonical Package Path**: Root and subproject READMEs must reference `personas/sakthai/` and must never contain `personas/sakthai/sakthai/`.
- **Test Coverage Floor**: Pytest suite must satisfy `--cov-fail-under=96` (enforced $\ge 96.0\%$).
- **Whitespace & Formatting**: Zero trailing whitespace (`git diff --check` must exit 0).
- **Pull Request Protocol**: Branch `docs/update-every-readme-in-repo`, create PR, never auto-merge (`gh pr merge` or `--auto` forbidden), leave open for Beer's manual review.

## Review Focus

1. **Skill Count Drift**: If any persona README reports a skill count that differs from the on-disk count of directories with `SKILL.md`, `test_personas_readme_skill_counts_match_disk` will fail.
2. **Forbidden Substring Leak**: If any legacy references to `hermes` or doubled path `personas/sakthai/sakthai` are copied into persona READMEs, `test_no_forbidden_strings_in_persona_markdown` will fail.
3. **Canonical Package Path**: If any documentation refers to the root as holding the python package rather than `personas/sakthai/`, `test_readme_documents_the_real_canonical_package_path` will fail.
4. **Exit Code & Output Contract Documentation**: Ensure CLI examples accurately document exit code 3 for unready state and standard `--json` envelope usage rather than deprecated raw dicts.
5. **Markdown Table & Badge Formatting**: Ensure markdown table columns and shield badges render without syntax breakage or broken links.

---

### Task 1: Root, Hub & Docs README Modernization

**Files:**
- Modify: `README.md`
- Modify: `personas/README.md`
- Modify: `docs/README.md`
- Test: `tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk`
- Test: `tests/test_repo_hygiene.py::test_readme_documents_the_real_canonical_package_path`

**Interfaces:**
- Produces: Synchronized root badges, subsystem tables, persona breakdown, CLI output contract docs, daily Dependabot cadence, and Gemini 4 Neon specifications.
- Consumes: Test assertions in `tests/test_soul_consistency.py` and `tests/test_repo_hygiene.py`.

- [ ] **Step 1: Run baseline tests to verify current status**

```bash
uv run pytest tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk tests/test_repo_hygiene.py::test_readme_documents_the_real_canonical_package_path -v
```
Expected: PASS.

- [ ] **Step 2: Update `README.md`**

In `README.md`:
1. Update skill badges and metrics in the header:
   - Update skills badge to `463 standardized` (`https://img.shields.io/badge/skills-463%20standardized-10B981`).
   - Update tests badge to `216 pytest files (4,333 tests) + 24 dashboard suites` (`https://img.shields.io/badge/tests-216%20pytest%20files%20%284%2C333%20tests%29%20%2B%2024%20dashboard%20suites-brightgreen`).
2. Update the Subsystem Table:
   - **Skills Catalog**: `463 On-Disk Skills (460 overlay + 3 shared)` · `🟢 STANDARDIZED` · Structured `Sak<Agent>-<domain>-<topic>` taxonomy.
   - **Test Quality**: `216 pytest files (4,333 tests) + 24 dashboard suites` · `🟢 PASS (≥96%)` · Enforced strict coverage floor (`--cov-fail-under=96`).
   - **CI/CD Automation**: `StepSecurity, AutoHeal-CI, Daily Dependabot & PR Automations` · `⚙️ HARDENED` · Egress audit, daily dependency updates (`interval: "daily"`) & manual user review.
   - **CLI Output Contract**: Note `sak.cli/v1` envelope (`--json`, `-q`, `--no-color`, exit codes 0/1/2/3/130, and Rainbow UI).
3. Update "What is included" and "The Six Personas":
   - Update persona skills total line to: `463 on-disk skills (460 persona overlays + 3 shared skills in .agents/skills/)`.
   - Update Google Gemini references to highlight **Gemini 4 Neon** as flagship default with `GEMINI_FREE_ONLY=true` fallback to **Gemini 4 Hydrogen**.
   - Add subsection on the new **CLI Output Contract & Rainbow UI** under `CLI Ergonomics`.
4. Ensure `personas/sakthai/` is used and `personas/sakthai/sakthai/` is absent.

- [ ] **Step 3: Update `personas/README.md` and `docs/README.md`**

1. In `personas/README.md`:
   - Verify layout block reflects exact disk counts: SakThai 174, SakKing 64, SakTan 26, SakSit 50, SakJules 48, SakSee 98 = 460 overlay skills (+ 3 shared in `.agents/skills/`).
   - Update test metric to reflect 4,333 pytest tests.
   - Document the `sak.cli/v1` output contract and daily Dependabot cadence.
2. In `docs/README.md`:
   - Ensure all subdocument indexes link to current architecture specs and plans.

- [ ] **Step 4: Run tests and whitespace check to verify compliance**

```bash
uv run pytest tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk tests/test_repo_hygiene.py::test_readme_documents_the_real_canonical_package_path -v
git diff --check
```
Expected: PASS, 0 whitespace errors.

- [ ] **Step 5: Commit Task 1 deliverable**

```bash
git add README.md personas/README.md docs/README.md
git commit -m "docs: update root, personas hub, and docs index readmes"
```

---

### Task 2: The 6 Individual Persona README Modernization

**Files:**
- Modify: `personas/sakthai/README.md`
- Modify: `personas/sakking/README.md`
- Modify: `personas/saksee/README.md`
- Modify: `personas/saksit/README.md`
- Modify: `personas/saktan/README.md`
- Modify: `personas/sakjules/README.md`
- Modify: `personas/sakthai/skills/README.md`
- Modify: `personas/*/telegram/README.md`
- Test: `tests/test_soul_consistency.py::test_persona_markdown_files_match_disk_skills_and_canonical_paths`
- Test: `tests/test_soul_consistency.py::test_no_forbidden_strings_in_persona_markdown`

**Interfaces:**
- Produces: 6 individual persona README files reflecting exact on-disk skill counts, Gemini 4 Neon default, daily Dependabot cadence, and `sak.cli/v1` output contract with rainbow flourishes.
- Consumes: Test invariants in `tests/test_soul_consistency.py`.

- [ ] **Step 1: Run baseline persona consistency tests**

```bash
uv run pytest tests/test_soul_consistency.py::test_persona_markdown_files_match_disk_skills_and_canonical_paths tests/test_soul_consistency.py::test_no_forbidden_strings_in_persona_markdown -v
```
Expected: PASS.

- [ ] **Step 2: Update `personas/sakthai/README.md` and `personas/sakthai/skills/README.md`**

1. In `personas/sakthai/README.md`:
   - Confirm 174 skills count.
   - Update model defaults: Gemini 4 Neon (`gemini-4-neon`) flagship default, Hugging Face router, and reachable Ollama.
   - Document `sak.cli/v1` envelope formatting on `sak doctor`, `status`, `tools`.
2. In `personas/sakthai/skills/README.md`:
   - Update taxonomy and total overlay skill count (174).

- [ ] **Step 3: Update `personas/sakking/README.md` and `personas/saksee/README.md`**

1. In `personas/sakking/README.md`:
   - Confirm 64 skills count (general assistant, runner, break-glass hub quorum).
   - Document dual runner execution, Gemini 4 Neon reasoning tier, and `sak` CLI integration.
2. In `personas/saksee/README.md`:
   - Confirm 98 skills count (web, browser automation, CSS, DOM distillation).
   - Document 3-tier scraping escalation, zero-cost HTML distillation (`web_distill.py`), and Chromium reaper (`browser_reaper.py`).

- [ ] **Step 4: Update `personas/saksit/README.md`, `personas/saktan/README.md`, and `personas/sakjules/README.md`**

1. In `personas/saksit/README.md`:
   - Confirm 50 skills count (social, content creation, editorial quality evaluator, multimodal presets).
2. In `personas/saktan/README.md`:
   - Confirm 26 skills count (daily ops, rhythm, local Ollama, WAL compaction daemon).
3. In `personas/sakjules/README.md`:
   - Confirm 48 skills count (CI/CD master, DevSecOps, daily Dependabot, PR rebase sentinel, auto-heal).

- [ ] **Step 5: Update Telegram READMEs (`personas/*/telegram/README.md`)**

1. Confirm all 6 persona telegram READMEs reflect Gemini 4 Neon `/model` recommendation and webhook architecture.

- [ ] **Step 6: Run verification tests and whitespace checks**

```bash
uv run pytest tests/test_soul_consistency.py -v
git diff --check
```
Expected: PASS (all 59 tests in test_soul_consistency.py pass), 0 whitespace errors.

- [ ] **Step 7: Commit Task 2 deliverable**

```bash
git add personas/
git commit -m "docs(personas): synchronize 6 persona readmes and skill counts"
```

---

### Task 3: Apps, Dashboard & Infrastructure README Synchronization

**Files:**
- Modify: `apps/sak_agent_dashboard/README.md`
- Modify: `apps/sak_agent_dashboard/workflow_engine/README.md`
- Modify: `infra/cloudflare/README.md`
- Modify: `infra/pw-poc/README.md`
- Modify: `infra/sakthai-training-space/README.md`
- Modify: `infra/sakthai-training-space/data/README.md`
- Modify: `infra/vm-agents/README.md`
- Modify: `.github/codeql/README.md`
- Test: `make lint`

**Interfaces:**
- Produces: Updated application and infrastructure READMEs aligning with Next.js 16, Gemini 4 Neon, daily Dependabot cadence, and current toolchain.

- [ ] **Step 1: Update `apps/sak_agent_dashboard/README.md` and `workflow_engine/README.md`**

1. In `apps/sak_agent_dashboard/README.md`:
   - Verify frontend dependencies: Next.js 16, React 19, Tailwind CSS v3, TypeScript 5.8.
   - Document Gateway integration (`/v1/chat/completions` SSE, `/v1/memory/shards`, `/v1/team/pipelines/stream`).
   - Note daily Dependabot scanning on `/apps/sak_agent_dashboard`.
2. In `apps/sak_agent_dashboard/workflow_engine/README.md`:
   - Align workflow engine documentation with multi-agent DAG executor.

- [ ] **Step 2: Update Infrastructure READMEs (`infra/`)**

1. In `infra/pw-poc/README.md`:
   - Document Playwright accessibility probe and daily Dependabot updates.
2. In `infra/sakthai-training-space/README.md` and `data/README.md`:
   - Document training space Docker base image digest maintenance (daily cadence).
3. In `infra/cloudflare/README.md` and `infra/vm-agents/README.md`:
   - Document DNS provisioning and VM agent deployment tooling.

- [ ] **Step 3: Run linter and whitespace checks**

```bash
make lint
git diff --check
```
Expected: PASS.

- [ ] **Step 4: Commit Task 3 deliverable**

```bash
git add apps/ infra/ .github/
git commit -m "docs(infra): update dashboard and infrastructure readmes"
```

---

### Task 4: Services, Skills, Automation & Training Subsystems README Updates

**Files:**
- Modify: `services/inference-endpoint/README.md`
- Modify: `services/patchflow/README.md`
- Modify: `services/teams-copilot-mcp/README.md`
- Modify: `.agents/skills/launchdarkly-release-autopilot-onboarding/README.md`
- Modify: `automation/n8n/README.md`
- Modify: `data/README.md`
- Modify: `dataset-cards/sakthai-combined-v7/README.md`
- Modify: `training/README.md`
- Modify: `training/hf-jobs/README.md`
- Modify: `training/run2-dataset-v10/README.md`
- Modify: `training/run2-model-7b-128k/README.md`
- Modify: `training/run2-model-coder-browser/README.md`
- Modify: `training/sakthai-1.5b-lora/README.md`
- Modify: `training/sakthai-7b-lora/README.md`
- Modify: `training/serving/README.md`
- Test: `uv run pytest tests/test_repo_hygiene.py tests/test_soul_consistency.py -v`

**Interfaces:**
- Produces: Completely modernized subsystem documentation with zero broken links, accurate package paths, and OpenEnv RL references.

- [ ] **Step 1: Update Services READMEs (`services/`)**

1. Update `services/inference-endpoint/README.md`, `services/patchflow/README.md`, and `services/teams-copilot-mcp/README.md` to reference portable `sakthai` CLI commands and current API contracts.

- [ ] **Step 2: Update Shared Skills and Automation READMEs**

1. In `.agents/skills/launchdarkly-release-autopilot-onboarding/README.md`:
   - Document onboarding wizard steps, environment release plans, and AI model configuration.
2. In `automation/n8n/README.md`:
   - Update webhook dispatch documentation.
3. In `data/README.md` and `dataset-cards/sakthai-combined-v7/README.md`:
   - Document memory snapshot formats and Hugging Face dataset card sync.

- [ ] **Step 3: Update Training & MLOps READMEs (`training/`)**

1. In `training/README.md` and subdirectories (`training/hf-jobs/`, `run2-*/`, `sakthai-*-lora/`, `serving/`):
   - Align model architectures with SakThai 7B and 1.5B LoRA recipes.
   - Document first-class OpenEnv RL integration (`sakthai train openenv`, GRPO, A2A protocol).
   - Ensure `personas/sakthai/` is used for package references.

- [ ] **Step 4: Run hygiene and consistency tests**

```bash
uv run pytest tests/test_repo_hygiene.py tests/test_soul_consistency.py -v
git diff --check
```
Expected: PASS, 0 whitespace errors.

- [ ] **Step 5: Commit Task 4 deliverable**

```bash
git add services/ .agents/ automation/ data/ dataset-cards/ training/
git commit -m "docs(services,training): modernize services, skills, and training readmes"
```

---

### Task 5: Full Suite Verification, Quality Gates & Pull Request

**Files:**
- Modify: `PLAN.md` (mark Section 17 complete with date)
- Test: `make lint`
- Test: `uv run mypy personas/sakthai`
- Test: `uv run bandit -c pyproject.toml -r personas/sakthai -q`
- Test: `python3 scripts/sync_personas.py --check`
- Test: `uv run pytest tests/test_soul_consistency.py tests/test_repo_hygiene.py tests/test_cli_output_contract.py`

**Interfaces:**
- Produces: Fully verified, clean, rebased Pull Request open for Beer's review and manual merge.

- [ ] **Step 1: Run comprehensive quality gates**

```bash
make lint
uv run mypy personas/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai -q
python3 scripts/sync_personas.py --check
uv run pytest tests/test_soul_consistency.py tests/test_repo_hygiene.py tests/test_cli_output_contract.py -v
git diff --check
```
Expected: All checks PASS with 0 errors and 0 whitespace issues.

- [ ] **Step 2: Update `PLAN.md`**

Find Section 17 in `PLAN.md` and mark both phases complete:
```markdown
### 17. Monorepo-Wide README.md Modernization & Synchronization (2026-11-27)
- [x] 2026-11-27 **Phase 1: Implementation Plan & Repository Audit** `[SakJules]` — Author `docs/superpowers/plans/2026-11-27-update-every-readme.md` using `/writing-plans` skill, auditing all 60+ tracked `README.md` files across Root, 6 Personas, Apps, Infra, Services, and Training domains against Gemini 4 Neon defaults, daily Dependabot cadence, Phase 3/F6.1 output contract with Rainbow UI, exact on-disk skill counts (460 overlay + 3 shared = 463 total), and 4,333 collected tests.
- [x] 2026-11-27 **Phase 2: Execution & Quality Gate Verification** `[SakJules]` — Execute all plan tasks, verify on-disk parity tests (`test_soul_consistency.py`, `test_repo_hygiene.py`), zero whitespace errors (`git diff --check`), linting, Bandit, open PR, and request Beer's review.
```

- [ ] **Step 3: Commit and push branch**

```bash
git add PLAN.md
git commit -m "docs: complete monorepo-wide README modernization"
git push -u origin docs/update-every-readme-in-repo
```

- [ ] **Step 4: Create Pull Request (Auto-Merge Disabled)**

```bash
gh pr create --base main --head docs/update-every-readme-in-repo \
  --title "docs: modernize and synchronize all README.md files across monorepo" \
  --body "**SakJules · Master of Automation & CI/CD.**

### Summary of Changes

Comprehensively audited and synchronized all 60+ tracked \`README.md\` files across the House of Sak repository:
1. **Metrics & Invariants**: Updated skills to 463 total (460 persona overlays + 3 shared in \`.agents/skills/\`) matching exact on-disk counts (SakThai 174, SakSee 98, SakJules 48, SakKing 64, SakSit 50, SakTan 26), and test suite to 216 pytest files (4,333 collected tests) + 24 dashboard suites.
2. **Gemini 4 Neon Flagship**: Standardized all provider documentation around Gemini 4 Neon (\`gemini-4-neon\`) as flagship default with \`GEMINI_FREE_ONLY=true\` fallback to Gemini 4 Hydrogen.
3. **Daily Dependabot Cadence**: Documented daily dependency scanning across all 4 ecosystems (\`uv\`, \`npm\`, \`github-actions\`, \`docker\`).
4. **CLI Output Contract & Rainbow UI**: Documented \`sak.cli/v1\` envelope schema, exit codes (0, 1, 2, 3, 130), \`--json\`, \`-q\`, \`--no-color\`, and Full Vibrant Spectrum Rainbow UI.
5. **Quality Verification**: Passed all soul consistency and repo hygiene tests, zero whitespace errors, \`make lint\` clean, strict mypy clean, and Bandit clean."
```
Expected: PR created; auto-merge left disabled for Beer's manual review.
