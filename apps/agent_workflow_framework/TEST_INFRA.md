# E2E Test Infra: agent_workflow_framework

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design details.
- Methodology: Category-Partition + BVA (Boundary Value Analysis) + Pairwise Combinatorial + Real-World Workload Testing.

## Feature Inventory & Test Matrix
| # | Feature | Requirement | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Workloads) |
|---|---------|-------------|------------------|-------------------|-------------------|--------------------|
| 1 | Workflow Definition Schema & Parsing | R1 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 1 |
| 2 | DAG Dependency Graph & Cycle Detection | R1, R2 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 2 |
| 3 | State Passing & Interpolation | R1 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 4 |
| 4 | History Persistence & Log Store | R1 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 1..4 |
| 5 | Parallel Step Execution Engine | R1 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 2 |
| 6 | Step Retries & Downstream Short-Circuiting | R1 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 3 |
| 7 | CLI Commands (`validate`, `run`, `inspect`) | R2 | 5 test cases | 5 edge cases | Covered | Covered in Scenario 1..4 |

## Test Architecture
- Test Runner: `python verify.py` (executes scenario workflows programmatically and via CLI, asserting output state and zero exit code).
- Unit/Integration Runner: `python -m unittest discover -s tests`.
- Workflow Fixtures: Located in `tests/test_workflows/`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Scenario 1: Linear Workflow & Sequential State Passing | FEAT-ENG-01, FEAT-STA-01, FEAT-STA-02, FEAT-CLI-02 | Medium |
| 2 | Scenario 2: Parallel Fan-Out/Fan-In Execution DAG | FEAT-ENG-02, FEAT-ENG-04, FEAT-STA-01, FEAT-CLI-02 | High |
| 3 | Scenario 3: Transient Retry Recovery & Terminal Short-Circuit | FEAT-ENG-05, FEAT-ENG-06, FEAT-STA-02, FEAT-CLI-02 | High |
| 4 | Scenario 4: Multi-Step Data Mutation & Transformation Pipeline | FEAT-STA-01, FEAT-STA-02, FEAT-ENG-04, FEAT-CLI-03 | High |
| 5 | Scenario 5: Master Verification Benchmark Suite (`verify.py`) | FEAT-CLI-01..04, FEAT-VER-01..05 | High |

## Coverage Thresholds
- Tier 1: ≥5 test cases per feature area.
- Tier 2: ≥5 boundary & corner case tests (cycles, invalid keys, retry exhaustion, empty graphs).
- Tier 3: Pairwise coverage across state passing, parallel execution, and failure short-circuiting.
- Tier 4: 5 comprehensive application scenarios.
