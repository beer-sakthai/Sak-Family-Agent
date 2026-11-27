---
name: SakThai-research-paper-writing
version: 1.0.0
description: 'Write ML papers for NeurIPS/ICML/ICLR: design→submit.'
category: mlops
tags:
- huggingface
- paper
- research
- writing
---

# Research Paper Writing Pipeline

End-to-end pipeline for producing publication-ready ML/AI research papers targeting **NeurIPS, ICML, ICLR, ACL, AAAI, and COLM**. Covers the full research lifecycle: experiment design, execution, monitoring, analysis, paper writing, review, revision, and submission.

This is an **iterative loop** — results trigger new experiments, reviews trigger new analysis.

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

---

## When To Use This Skill

- Starting a new research paper from an existing codebase or idea.
- Designing and running experiments to support paper claims.
- Writing or revising any section of a research paper.
- Preparing submissions for ML conferences (NeurIPS, ICML, ICLR, etc.).
- Converting papers across formats or writing non-empirical papers.

## Core Philosophy

1. **Be proactive:** Deliver complete drafts, not open-ended questions.
2. **Never hallucinate citations:** AI citations have ~40% error rate. Always verify programmatically. Mark unverified ones as `[CITATION NEEDED]`.
3. **Paper is a story:** Every paper needs one clear contribution stated in a single sentence.
4. **Experiments serve claims:** Every experiment must explicitly connect to a claim.
5. **Commit discipline:** Commit each experiment batch and paper section draft.

| Confidence Level | Action |
|---|---|
| **High** (clear contribution) | Write full draft, deliver, iterate on feedback |
| **Medium** (some ambiguity) | Write draft with flagged uncertainties |
| **Low** (major unknowns) | Ask 1-2 targeted questions via `clarify`, then draft |

---

## Lifecycle Phases & Reference Index

### Phase 0: Project Setup
- Establish consistent directory structure: `paper/`, `experiments/`, `code/`, `results/`.
- Articulate the single-sentence contribution statement.
- See full methodology in [AutoReason Methodology](./references/autoreason-methodology.md).

### Phase 1: Literature Review
- Fetch papers programmatically via Semantic Scholar and arXiv APIs.
- Construct the bibTeX database with normalized citation keys.
- See [Citation Workflow](./references/citation-workflow.md) and [Sources Guide](./references/sources.md).

### Phase 2: Experiment Design
- Formulate specific falsifiable hypotheses tied to paper claims.
- Establish baseline models, compute budgets, and evaluation metrics.
- See [Experiment Patterns & Protocols](./references/experiment-patterns.md).

### Phase 3 & 4: Execution, Monitoring & Analysis
- Run structured ablation batches with seed replication and confidence intervals.
- Generate high-quality vector figures and camera-ready LaTeX tables.
- For human evaluations, consult [Human Evaluation Guide](./references/human-evaluation.md).

### Phase 5: Paper Drafting
- Draft sections in order: Methods → Experiments → Results → Introduction → Related Work → Abstract → Title.
- Adhere strictly to the conference style guidelines and page limits.
- See detailed templates in [Writing Guide](./references/writing-guide.md) and [Paper Types](./references/paper-types.md).

### Phase 6 & 7: Review, Revision & Submission
- Conduct rigorous self-review against official reviewer rubrics.
- Complete pre-submission verification checklist (anonymity, reproducibility, checklist answers).
- Consult [Reviewer Guidelines](./references/reviewer-guidelines.md) and [Submission Checklists](./references/checklists.md).
