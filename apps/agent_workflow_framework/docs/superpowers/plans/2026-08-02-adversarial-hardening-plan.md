# Milestone M6: Adversarial Hardening Implementation Plan

## Goal
Implement Tier 5 Adversarial Hardening for `agent_workflow_framework` covering path traversal defense, state recursion depth caps, high-concurrency race condition safety, scale testing (1,000-node DAGs), and master `verify.py` integration.

## Tasks

### Task 1: Path Traversal Defense in `agent_workflow/persistence.py`
- [ ] Add `validate_run_id(run_id: str)` helper validating `^[a-zA-Z0-9_-]+$`.
- [ ] Check `run_id` in `save_run_history`, `get_run_history`, and log saving methods.
- [ ] Verification: `python3 -m unittest tests/test_persistence.py` passes cleanly.

### Task 2: State Interpolation Recursion Guard in `agent_workflow/state.py`
- [ ] Add `max_depth: int = 10` parameter and depth counter to `StateContext.interpolate()`.
- [ ] Raise `ValueError("Circular or nested state interpolation depth exceeded")` when `current_depth > max_depth`.
- [ ] Verification: `python3 -m unittest tests/test_state.py` passes cleanly.

### Task 3: Implement `tests/test_adversarial.py` Suite
- [ ] Create `tests/test_adversarial.py` with 5 Tier 5 security and stress test scenarios:
  1. `test_path_traversal_attack_vector`
  2. `test_interpolation_infinite_recursion`
  3. `test_scale_1000_nodes_dag`
  4. `test_high_concurrency_race_condition`
  5. `test_malformed_definition_fuzzing`
- [ ] Verification: `python3 -m unittest tests/test_adversarial.py` passes 5/5 tests.

### Task 4: Integrate Phase 2 into `verify.py`
- [ ] Update `verify.py` to run Phase 2 (Adversarial Audit) via `unittest.defaultTestLoader.loadTestsFromName("tests.test_adversarial")`.
- [ ] Verification: `python3 verify.py` runs both Phase 1 and Phase 2 and returns `ALL VERIFICATION SCENARIOS AND TESTS PASSED!`.
