# Agent Workflow Framework

A Python workflow engine and CLI for dependency-aware execution, state interpolation, retries, persistence, and run inspection.

## Setup

Use Python 3.11 or newer and install the app dependency:

```bash
python -m pip install -r requirements.txt
```

CI uses the hash-locked repository dependency set at `.github/apps-requirements.lock`.

## Validate and run a workflow

```bash
python -m agent_workflow.cli validate tests/test_workflows/linear_workflow.yaml
python -m agent_workflow.cli run tests/test_workflows/linear_workflow.yaml
python -m agent_workflow.cli list
```

Run commands from this directory, or add it to `PYTHONPATH`.

## Evaluation

The full verification runner executes unit tests, adversarial tests, CLI checks, and four end-to-end workflow scenarios:

```bash
python verify.py
```

The focused unit suite can be run independently with:

```bash
python -m unittest discover -s tests
```

See [TEST_INFRA.md](TEST_INFRA.md) for the test matrix and [docs/superpowers/plans/2026-09-22-framework-improvement-plan.md](docs/superpowers/plans/2026-09-22-framework-improvement-plan.md) for the improvement backlog and current evaluation findings.
