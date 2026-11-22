# Agent Workflow Framework

A Python workflow engine and CLI for dependency-aware execution, state interpolation, retries, persistence, and run inspection.

## Setup

Use Python 3.11 or newer. You can install dependencies via pip or use `uv`:

```bash
uv sync --all-extras
# Or standalone:
python -m pip install -r requirements.txt
```

CI uses the hash-locked repository dependency set at `.github/apps-requirements.lock`.

## Validate and run a workflow

```bash
# Using uv run (from monorepo root)
uv run python -m agent_workflow.cli validate apps/sak_agent_dashboard/workflow_engine/tests/test_workflows/linear_workflow.yaml
uv run python -m agent_workflow.cli run apps/sak_agent_dashboard/workflow_engine/tests/test_workflows/linear_workflow.yaml
uv run python -m agent_workflow.cli list

# Or from this directory
python -m agent_workflow.cli validate tests/test_workflows/linear_workflow.yaml
python -m agent_workflow.cli run tests/test_workflows/linear_workflow.yaml
```

Run commands from this directory, or add it to `PYTHONPATH`.

## Evaluation

The full verification runner executes unit tests, adversarial tests, CLI checks, and four end-to-end workflow scenarios:

```bash
python verify.py
```

The focused unit suite can be run independently with:

```bash
uv run python -m unittest discover -s apps/sak_agent_dashboard/workflow_engine/tests
# Or from this directory:
python -m unittest discover -s tests
```

See [TEST_INFRA.md](TEST_INFRA.md) for the test matrix and [framework-improvement-plan](docs/superpowers/plans/2026-09-22-framework-improvement-plan.md) for the improvement backlog.

## Gateway Team Pipeline Integration

Workflows authored for multi-agent delegation can also be executed as distributed team pipelines via the Runtime Gateway (`sakthai.team.gateway`):
- Streaming execution endpoint: `POST /v1/team/pipelines/stream`
- Live SVG DAG visualizer: Hosted directly in the Next.js dashboard at `/pipelines` (`TeamPipelineVisualizer.tsx`) with real-time SSE token terminal.

