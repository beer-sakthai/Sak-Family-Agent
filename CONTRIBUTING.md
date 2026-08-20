# Contributing to the House of Sak

Thank you for your interest in the **House of Sak** (`Sak-Family-Agent`)!

This repository is the active, clean-room workspace of the Sak Family autonomous AI agents (**SakKing**, **SakSee**, **SakSit**, **SakTan**, **SakJules**, and **SakThai**), maintained by **Beer**.

While this project is personal in nature, we deeply welcome discussions, architectural questions, security disclosures, and feedback. If you have been invited to contribute code or are running experiments, this document describes our setup, testing workflow, and strict quality standards.

---

## 🛠️ Development Setup

### Prerequisites
- **Python >= 3.11** (CI validates strictly on 3.11 and 3.12)
- **`uv`** (fast Python package and project manager)
- **Node.js >= 20** & **pnpm >= 9** (for `apps/sak_agent_dashboard`)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
cd Sak-Family-Agent

# 2. Environment configuration
cp .env.example .env    # Configure your API keys (e.g. GEMINI_API_KEY, ANTHROPIC_API_KEY)

# 3. Synchronize Python virtual environment & dependencies
uv sync --all-extras

# 4. Install dashboard dependencies (if working on the web UI)
cd apps/sak_agent_dashboard && pnpm install && cd ../..
```

---

## 🧪 Quality Bar & Local Verification

**Green CI across all matrix dimensions is the mandatory bar for `main`.**
Before submitting a pull request or committing changes, run the full validation suite locally:

```bash
# 1. Code Formatting & Linting
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests

# 2. Strict Static Typing
uv run mypy personas/sakthai/sakthai

# 3. SAST Security Scan
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai

# 4. Unit & Branch Coverage (Floor >= 96%)
uv run pytest tests/ -m "not integration" -q

# 5. Dashboard Verification
cd apps/sak_agent_dashboard
pnpm lint && pnpm typecheck && pnpm test && pnpm build
cd ../..
```

---

## 📐 Architecture & Coding Standards

1. **Deterministic Path Validation & Security**:
   - All filesystem operations must pass through `_resolve_and_validate_path`.
   - Paths with ASCII control characters (`\x00-\x1f\x7f`) or suspicious multi-prefix schemes (`@@`) are strictly rejected.
2. **Shared Package Parity (`tests/test_shared_package_divergence.py`)**:
   - Modules in `personas/shared/sakthai/` must maintain exact byte parity with `personas/sakthai/sakthai/` unless explicitly declared in `KNOWN_DIVERGENCES`.
3. **Skill Authoring Guidelines**:
   - Every skill must have a valid `SKILL.md` with proper YAML frontmatter (`name` and `description`).
   - Run `sakthai skills validate` to ensure skill formatting compliance.
4. **Persona Conventions**:
   - Maintain persona boundaries (e.g. `SakKing` for high-level strategy, `SakJules` for automation/CI, `SakSee` for vision/UI, `SakSit` for research, `SakTan` for operations, `SakThai` for core agent runtime).

---

## ✅ Code Review Checklist

Before opening a PR or marking as ready for review, verify all these locally:

- [ ] **Green CI locally**: Run all commands under "Quality Bar & Local Verification" above
- [ ] **No new linting errors**: `uv run ruff check` passes
- [ ] **Code is formatted**: `uv run ruff format --check` passes (or run without `--check` to auto-fix)
- [ ] **Types are strict**: `uv run mypy personas/sakthai/sakthai` returns 0 issues
- [ ] **No security issues**: `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` is clean
- [ ] **Tests pass**: `uv run pytest tests/ -m "not integration" -q` passes with ≥96% coverage
- [ ] **Branch is up-to-date**: Merge the latest `main` into your branch to catch CI conflicts early
- [ ] **Commit messages are clear**: Follow conventional commit style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, etc.
- [ ] **Documentation updated**: If you changed behavior, update relevant `.md` files
- [ ] **No breaking changes** (or clearly documented): Backwards compatibility matters
- [ ] **Related issues linked**: Reference any GitHub issues your PR closes or relates to

---

## 📬 Submitting Feedback & PRs

- **Bug Reports & Ideas**: Open a [GitHub Issue](https://github.com/beer-sakthai/Sak-Family-Agent/issues).
- **Security Disclosures**: Please see [`SECURITY.md`](SECURITY.md) and email **beer-sakthai@users.noreply.github.com** directly.
- **Code Reviews**: Every pull request requires **green CI across all workflows** AND a **non-author approval** before merge. (Auto-approving bots are explicitly out of bounds — a human review is required for `main`.)

---

## 📄 License & Code of Conduct

- **License**: All code in this repository is governed by our [Intellectual Property License](LICENSE).
- **Code of Conduct**: All participants and contributors must abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

