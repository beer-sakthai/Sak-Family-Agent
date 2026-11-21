# Contributing to the House of Sak

Thank you for your interest in the House of Sak! This repository represents a local-first, autonomous AI agent workspace created by **Beer** (`beer-sakthai`) and operated by the six Sak family companion agents (`SakThai`, `SakSee`, `SakJules`, `SakKing`, `SakSit`, and `SakTan`).

While the repository is distributed under a proprietary intellectual property license and is not an open-source project open for unsolicited external code, we actively maintain rigorous development, security, and quality standards for all development and agent-driven contributions.

---

## Development Environment & Setup

The core Python package lives at `personas/sakthai/` (editable install). Environment management is handled via [`uv`](https://docs.astral.sh/uv/):

```bash
# 1. Clone repository and install full environment with all extras
git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
cd Sak-Family-Agent
uv sync --all-extras --dev

# 2. Configure environment credentials
cp .env.example .env
# Edit .env with your local credentials (HF_TOKEN, ANTHROPIC_API_KEY, etc.)
```

---

## Quality Gates & Verification Standards

All changes must satisfy our automated quality and security gates prior to opening a Pull Request:

1. **Test Suite & Coverage Floor**:
   - `make test`: Executes the 3,142+ unit and seam test suite.
   - Enforces a strict **$\ge 96\%$ code coverage floor** (`--cov-fail-under=96`). Any drop below the floor fails CI.
2. **Linting & Formatting**:
   - `make lint`: Enforces Ruff formatting, import order, and lint rules across all Python modules and workflows.
3. **Strict Type Checking**:
   - `uv run mypy personas/sakthai`: Ensures zero type errors on public and internal interfaces.
4. **Security Vulnerability Scanning**:
   - `uv run bandit -c pyproject.toml -r personas/sakthai`: Zero high- or medium-severity security issues.
   - `gitleaks`: Zero committed secrets, keys, or credentials across git history.
5. **Workflow Security**:
   - All GitHub Actions workflows are pinned to full 40-character commit SHAs, audited via `zizmor`, and protected with [StepSecurity Harden-Runner](https://stepsecurity.io) egress monitoring.

---

## Pull Request and Merge Governance Protocol

To ensure stability, supply chain security, and human-in-the-loop oversight:

1. **Maintainer Review & Manual Merge Only**:
   - **Never auto-merge pull requests.** Automated agent merges (`gh pr merge`, `--auto`, or fast-forward triggers) are strictly forbidden across all branches.
   - Every Pull Request must remain open for manual review and merge by **Beer** (`beer-sakthai`).
2. **Check for Overlapping PRs**:
   - Before opening a Pull Request, check active open PRs (`gh pr list --state open`). If an overlapping branch or fix already exists, extend that branch instead of creating duplicate PRs.
3. **Conventional Commits**:
   - Format commits using conventional prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
4. **Targeted Diffs**:
   - Avoid monolithic PRs or bundling unrelated changes. Keep diffs focused on the specific subsystem or task.

---

## Reporting Issues & Security Disclosures

- **Bug Reports**: Open an issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) with reproduction steps and environment logs.
- **Feature Proposals**: Open an issue using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).
- **Security Vulnerabilities**: **Never open public issues for security vulnerabilities.** Report privately through GitHub Security Advisories or email **beernanthasit@gmail.com** as detailed in [`SECURITY.md`](SECURITY.md).

---

## Code of Conduct

All contributors and collaborators are expected to uphold a respectful, welcoming, and inclusive community environment as outlined in our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

This repository is distributed under the [House of Sak Intellectual Property License](LICENSE), copyright © 2026 Beer (`beer-sakthai`). All rights reserved.
