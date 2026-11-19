# Update Every README.md in Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Comprehensively audit, synchronize, and modernize every `README.md` across the House of Sak repository, aligning all skill counts, persona roles, CLI usage (`uv run`), recent architectural upgrades, and subproject documentation while strictly honoring test invariants.

**Architecture:** Split documentation updates into four focused domain tiers (Monorepo Hub & Root, 6 Personas, Apps & Services, and Training/MLOps). Enforce on-disk parity tests (`test_personas_readme_skill_counts_match_disk`, `test_persona_markdown_files_match_disk_skills_and_canonical_paths`, `test_readme_documents_the_real_canonical_package_path`) at each step. Finalize with zero-whitespace validation, full coverage test run, and the mandatory GitHub PR and merge workflow.

**Tech Stack:** Markdown, Python 3.11/3.12, Pytest, `uv`, GitHub CLI (`gh`).

**Spec:** Self-contained within repository documentation standards and contract tests in `tests/test_soul_consistency.py` and `tests/test_repo_hygiene.py`.

## Global Constraints

- Financial Cost Policy: $0.00 USD Financial Spend (100% Local & Free Tier Execution).
- Persona Structural Parity: 51-item structural parity across all 6 personas must remain 100% intact (`test_persona_structure_parity.py`).
- Skill Count Verification: `personas/README.md` per-persona and total skill counts must match disk exactly (SakThai 170, SakSee 106, SakJules 56, SakKing 59, SakSit 45, SakTan 26 = 462 Overlay, 481 Total on-disk skills).
- Forbidden Strings in Persona Markdown: Every persona `README.md` must NOT contain `personas/sakthai/sakthai`, `personas/sakthai/agent-self-evolution`, or `hermes` (case-insensitive).
- Canonical Package Path: Root `README.md` must reference `personas/sakthai/` and must not contain `personas/sakthai/sakthai/`.
- Test Coverage Floor: Pytest suite must pass with `--cov-fail-under=96` (enforced $\ge 96.0\%$).
- Whitespace & Formatting: Zero trailing whitespace (`git diff --check` must return 0).
- GitHub PR Protocol (GEMINI.md): Branch `docs/update-every-readme-in-repo`, push with `--no-verify`, open PR, wait for green checks (`gh pr checks <PR> --watch`), merge with `--merge --delete-branch --admin`, and fast-forward local `main`.

---

### Task 1: Root & Personas Hub README Synchronization

**Files:**
- Modify: `README.md`
- Modify: `personas/README.md`
- Modify: `docs/README.md`
- Test: `tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk`
- Test: `tests/test_repo_hygiene.py::test_readme_documents_the_real_canonical_package_path`

**Interfaces:**
- Produces: Synchronized root and personas hub documentation reflecting 481 total skills, 462 overlay skills, SakSee 106 skills, 2,823+ tests, and Phase 1-3 resilience features.
- Consumes: Test assertions in `tests/test_soul_consistency.py` and `tests/test_repo_hygiene.py`.

- [ ] **Step 1: Run baseline tests to verify current status**

```bash
uv run pytest tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk tests/test_repo_hygiene.py::test_readme_documents_the_real_canonical_package_path -v
```
Expected: PASS.

- [ ] **Step 2: Update `README.md`**

In `README.md`:
1. Update skill badges and metrics:
   - `<img alt="480 skills" ...>` $\rightarrow$ `<img alt="481 skills" src="https://img.shields.io/badge/skills-481-10B981">`
   - Subsystem table: `480 On-Disk Skills (461 overlay + 19 shared)` $\rightarrow$ `481 On-Disk Skills (462 overlay + 19 shared)`
   - Subsystem table: `2,811 Unit Tests` $\rightarrow$ `2,823 Unit Tests across Python 3.11 & 3.12`
2. Update the Six Personas skill breakdown table (line 82):
   - Update SakSee skills from `105 skills` to `106 skills` (reflecting `SakSee-web-scraping`).
   - Update total description: `480 on-disk skills (461 persona overlays + 19 universal shared skills)` $\rightarrow$ `481 on-disk skills (462 persona overlays + 19 universal shared skills)`.
3. Add summary of the 6-Agent Persona Resilience Architecture:
   - Phase 1: Break-Glass HF Hub write protocol and 3-second intent preflight.
   - Phase 2: 3-tier scraping escalation and progressive domain manifest hydration.
   - Phase 3: Autonomous CI auto-heal utility (`scripts/ci_auto_heal.py`) and guarded algorithmic cloud fallback.
   - Workflow & Actions: Event-driven PR cache cleanup (`.github/workflows/cache-cleanup.yml`) keeping cache usage under 500 MB.
4. Ensure `personas/sakthai/` is used and `personas/sakthai/sakthai/` is absent.

- [ ] **Step 3: Update `personas/README.md` and `docs/README.md`**

1. In `personas/README.md`:
   - Verify layout block reflects exact disk counts: SakThai 170, SakKing 59, SakTan 26, SakSit 45, SakJules 56, SakSee 106 = 462 overlay skills.
   - Mention the resilience improvements in the Agent Self-Evolution & Evaluation overview.
2. In `docs/README.md`:
   - Add reference section to Superpowers specifications (`docs/superpowers/specs/`) and implementation plans (`docs/superpowers/plans/`).

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
- Modify: `personas/sakthai/telegram/README.md`, `personas/sakking/telegram/README.md`, `personas/saksee/telegram/README.md`, `personas/saksit/telegram/README.md`, `personas/saktan/telegram/README.md`, `personas/sakjules/telegram/README.md`

**Interfaces:**
- Produces: Modernized persona READMEs with unified `uv run sakthai run --persona <name>` invocation, charge system v6, self-eval v9 rubrics, and resilience protocols.
- Constraints: Must satisfy `test_persona_markdown_files_match_disk_skills_and_canonical_paths` (no `hermes`, no `personas/sakthai/sakthai`, no `personas/sakthai/agent-self-evolution`).

- [ ] **Step 1: Run baseline persona markdown parity test**

```bash
uv run pytest tests/test_soul_consistency.py::test_persona_markdown_files_match_disk_skills_and_canonical_paths -v
```
Expected: PASS across all 6 personas.

- [ ] **Step 2: Update `personas/sakthai/README.md` and `personas/sakthai/skills/README.md`**

1. Replace legacy `pip install -e "personas/sakthai[dev]"` with standard monorepo invocation:
   ```bash
   uv sync --all-extras
   uv run sakthai run --persona sakthai "Analyze trending Hugging Face models"
   ```
2. Document SakThai's primary capabilities: Lead coordination, Hugging Face Hub operations (break-glass protocol enabled), progressive skill hydration manifests (`get_skill_domain_manifests`), and 170 overlay skills.
3. Verify forbidden strings are completely absent.

- [ ] **Step 3: Update `personas/sakking/README.md`**

1. Document SakKing's identity: Assistant & Runner, Primary Coder (TDD), First Deputy.
2. Document 3-second intent preflight classifier and async template staging.
3. Update run command: `uv run sakthai run --persona sakking "Implement feature with TDD"`.
4. Document break-glass HF hub authorization and 59 overlay skills.

- [ ] **Step 4: Update `personas/saksee/README.md`**

1. Document SakSee's identity: Web & Browser Lead, Creative Specialist.
2. Document 3-tier scraping escalation protocol (`SakSee-web-scraping`): Tier 1 (HTTP/httpx) $\rightarrow$ Tier 2 (Headless Browser) $\rightarrow$ Tier 3 (Stealth Browser + Human Review).
3. Document 106 overlay skills (including Manim video, ComfyUI, Remotion, and Stitch).
4. Update run command: `uv run sakthai run --persona saksee "Inspect and test web interface"`.

- [ ] **Step 5: Update `personas/saksit/README.md`**

1. Document SakSit's identity: Social, Brand & Content Lead.
2. Document 45 overlay skills (ASCII video, B2B SaaS thought leadership, multi-platform publishing).
3. Update run command: `uv run sakthai run --persona saksit "Draft technical release announcement"`.

- [ ] **Step 6: Update `personas/saktan/README.md`**

1. Document SakTan's identity: Daily Ops, System Rhythm, Cloud & Infrastructure Lead.
2. Document guarded algorithmic cloud fallback in `config/config.yaml` (resilience against LLM quota exhaustions).
3. Document local Ollama execution (`127.0.0.1:11434`, zero external API cost) and 26 overlay skills.
4. Update run command: `uv run sakthai run --persona saktan "Audit daily workspace health"`.

- [ ] **Step 7: Update `personas/sakjules/README.md`**

1. Document SakJules' identity: GitHub, CI/CD, Autonomous Automation & Code Evolution Lead.
2. Document autonomous CI auto-heal utility (`scripts/ci_auto_heal.py`) and 56 overlay skills.
3. Update run command: `uv run sakthai run --persona sakjules "Run automated CI health diagnostics"`.

- [ ] **Step 8: Synchronize persona Telegram READMEs**

Ensure `personas/*/telegram/README.md` files accurately document bot configuration, webhook mode vs polling, and persona routing.

- [ ] **Step 9: Run verification tests and whitespace checks**

```bash
uv run pytest tests/test_soul_consistency.py::test_persona_markdown_files_match_disk_skills_and_canonical_paths tests/test_persona_structure_parity.py -v
git diff --check
```
Expected: All tests PASS, 0 whitespace errors.

- [ ] **Step 10: Commit Task 2 deliverable**

```bash
git add personas/
git commit -m "docs: modernize all six persona readmes and sub-readmes"
```

---

### Task 3: Apps, Services & Automation README Standardization

**Files:**
- Modify: `apps/agent_workflow_framework/README.md`
- Modify: `services/inference-endpoint/README.md`
- Modify: `services/teams-copilot-mcp/README.md`
- Modify: `automation/n8n/README.md`
- Modify: `infra/pw-poc/README.md`
- Modify: `infra/sakthai-training-space/README.md`
- Modify: `infra/vm-agents/README.md`
- Modify: `dataset-cards/sakthai-combined-v7/README.md`

**Interfaces:**
- Produces: Clear, reproducible setup, test, and execution commands using `uv` across monorepo apps and services.

- [ ] **Step 1: Update `apps/agent_workflow_framework/README.md`**

1. Add `uv run` command equivalents:
   ```bash
   uv run python -m agent_workflow.cli validate tests/test_workflows/linear_workflow.yaml
   uv run python -m unittest discover -s apps/agent_workflow_framework/tests
   ```
2. Document integration with `apps.yml` CI workflow.

- [ ] **Step 2: Update `services/inference-endpoint/README.md` and `services/teams-copilot-mcp/README.md`**

1. Document FastAPI and MCP endpoints, schema generation, and local testing.
2. Provide local Docker / uv run testing commands.

- [ ] **Step 3: Update `automation/n8n/README.md` and `infra/*/README.md`**

1. Clarify n8n local webhook triggers and workflow JSON imports.
2. Update `infra/vm-agents/README.md` with systemd unit configuration and environment variable isolation.
3. Update `dataset-cards/sakthai-combined-v7/README.md` with dataset schema, split statistics, and Hugging Face Hub link.

- [ ] **Step 4: Run whitespace check**

```bash
git diff --check
```
Expected: 0 whitespace errors.

- [ ] **Step 5: Commit Task 3 deliverable**

```bash
git add apps/ services/ automation/ infra/ dataset-cards/
git commit -m "docs: standardize apps, services, and infrastructure readmes"
```

---

### Task 4: Training & Fine-Tuning Pipeline README Upgrades

**Files:**
- Modify: `training/hf-jobs/README.md`
- Modify: `training/run2-dataset-v10/README.md`
- Modify: `training/run2-model-7b-128k/README.md`
- Modify: `training/run2-model-coder-browser/README.md`
- Modify: `training/sakthai-1.5b-lora/README.md`
- Modify: `training/sakthai-7b-lora/README.md`
- Modify: `training/serving/README.md`

**Interfaces:**
- Produces: Documented LoRA training configurations, tokenizer formats (ChatML), evaluation datasets, and serving instructions.

- [ ] **Step 1: Update LoRA training READMEs (`training/sakthai-1.5b-lora/README.md` & `training/sakthai-7b-lora/README.md`)**

1. Document base models: `Qwen/Qwen2.5-1.5B-Instruct` and `Qwen/Qwen2.5-7B-Instruct`.
2. Document LoRA hyperparameters: rank $r=16$, $\alpha=32$, target modules `q,k,v,o_proj`, learning rate $5\times 10^{-5}$.
3. Document merge and export steps for Hugging Face Hub deployment.

- [ ] **Step 2: Update dataset & serving READMEs**

1. Document `training/run2-dataset-v10/README.md` with dataset mixing weights and formatting.
2. Document `training/serving/README.md` with vLLM / Hugging Face TGI deployment guidelines.

- [ ] **Step 3: Run whitespace check**

```bash
git diff --check
```
Expected: 0 whitespace errors.

- [ ] **Step 4: Commit Task 4 deliverable**

```bash
git add training/
git commit -m "docs: update training pipelines and dataset card readmes"
```

---

### Task 5: Monorepo Verification & Automated Quality Validation

**Files:**
- None modified (validation and testing).

**Interfaces:**
- Verifies that all updated markdown files pass formatting, parity, contract tests, and full test suite with $\ge 96.0\%$ coverage.

- [ ] **Step 1: Check formatting and whitespace across git tree**

```bash
git diff --check origin/main
uv run ruff check personas/sakthai tests
uv run ruff format --check personas/sakthai tests
```
Expected: 0 whitespace errors, all files formatted.

- [ ] **Step 2: Run static typing and security analysis**

```bash
uv run mypy
uv run bandit -c pyproject.toml -r personas/sakthai
```
Expected: 0 type errors in 135 source files, 0 security issues.

- [ ] **Step 3: Run persona contract & parity tests**

```bash
make compose-personas
uv run pytest -q tests/test_soul_consistency.py tests/test_compose_persona.py tests/test_export_agent_repo.py tests/test_persona_guardrails_parity.py tests/test_persona_security_config.py tests/test_persona_structure_parity.py tests/test_repo_hygiene.py tests/test_workflow_cache_hygiene.py
```
Expected: 100% PASS.

- [ ] **Step 4: Run full test suite with coverage**

```bash
uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/
```
Expected: All 2,823+ tests pass, coverage $\ge 96.0\%$.

---

### Task 6: Mandatory GitHub PR & Merge Workflow (GEMINI.md)

**Files:**
- None (remote GitHub operations).

**Interfaces:**
- Produces: Merged PR on GitHub `main` and synchronized local workspace.

- [ ] **Step 1: Create and push feature branch**

```bash
git checkout -b docs/update-every-readme-in-repo
git push -u origin docs/update-every-readme-in-repo --no-verify
```

- [ ] **Step 2: Open Pull Request on GitHub**

```bash
gh pr create --base main --head docs/update-every-readme-in-repo \
  --title "docs: update and synchronize all readmes across monorepo" \
  --body "## Summary
- Synchronizes root \`README.md\` and \`personas/README.md\` with 481 total skills (462 overlay + 19 shared), 2,823+ tests, and 6-agent resilience architecture.
- Modernizes all 6 individual persona READMEs (\`sakthai\`, \`sakking\`, \`saksee\`, \`saksit\`, \`saktan\`, \`sakjules\`) with \`uv run\` execution commands, domain roles, and resilience protocol documentation.
- Updates apps, services, n8n automation, and training/serving READMEs.
- Strictly honors all parity and forbidden string invariants.

## Verification
- \`test_personas_readme_skill_counts_match_disk\` passed.
- \`test_persona_markdown_files_match_disk_skills_and_canonical_paths\` passed across all 6 personas.
- Full pytest suite passing with >=96% coverage floor.
- Ruff, Mypy, Bandit 0 issues."
```

- [ ] **Step 3: Monitor CI Checks until all are Green**

```bash
gh pr checks <PR_NUMBER> --watch
```
Expected: All 25 checks pass green.

- [ ] **Step 4: Merge PR to Main and Fast-Forward Local**

```bash
gh pr merge <PR_NUMBER> --merge --delete-branch --admin
git checkout main
git pull origin main
```
Expected: Merged cleanly and local `main` synchronized.
