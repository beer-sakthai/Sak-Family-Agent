# Subagent-Driven Development Workflow & Prompt Templates

This reference contains the end-to-end process workflows, subagent prompt templates, review stages, and ledger tracking patterns for Subagent-Driven Development (SDD).

---

## 1. Process Overview & State Machine

```
Task Execution Loop (Per Task):
1. Dispatch Implementer Subagent (isolated context, targeted files, TDD requirement)
2. Implementer Returns: commits code, runs tests, reports result
3. Dispatch Spec Reviewer Subagent (verifies all requirements are met)
4. Dispatch Quality Reviewer Subagent (verifies clean code, types, linting)
5. If issues found: Dispatch Fixer Subagent -> Repeat review
6. Mark Task Complete in Plan & Ledger

Final Phase:
7. Whole-Branch Review Subagent (broad holistic architectural audit)
8. Synthesis & Completion Summary
```

---

## 2. Implementer Subagent Prompt Template

```markdown
You are an implementer subagent executing Task <X> of an implementation plan.

TASK SPECIFICATION:
<Paste exact task text from plan>

CONTEXT & TARGET FILES:
- Files to modify: <file paths>
- Test files: <test paths>

REQUIREMENTS:
1. Follow Test-Driven Development (write tests first or verify existing tests fail).
2. Make minimal, surgical edits matching the codebase style.
3. Run verification commands: `uv run pytest <target_test> -v`.
4. Commit your changes with conventional prefix: `git commit -m "feat(<scope>): <description>"`.
5. Return a summary of changes, files modified, and verification evidence.
```

---

## 3. Reviewer Subagent Prompt Templates

### A. Spec Compliance Reviewer
```markdown
You are a spec compliance reviewer. Compare the implementation in commit <hash> against the plan requirements.
- Did the implementer satisfy every requirement?
- Are there unrequested additions or missing edge cases?
Return: `STATUS: APPROVED` or `STATUS: REVISION_REQUIRED` with bulleted feedback.
```

### B. Code Quality & Security Reviewer
```markdown
You are a code quality and security reviewer.
- Run `uv run ruff check <files>`
- Run `uv run mypy <files>`
- Check for secret leaks, anti-patterns, or test gaps.
Return: `STATUS: APPROVED` or `STATUS: REVISION_REQUIRED` with specific line numbers.
```

---

## 4. Ledger & Progress Tracking Pattern

Maintain an in-session markdown ledger:
```markdown
| Task ID | Description | Implementer | Spec Review | Quality Review | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| 1.1 | Model config update | Done | Approved | Approved | COMPLETE |
| 1.2 | Unit tests | In Progress | Pending | Pending | ACTIVE |
```
