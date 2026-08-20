# Handoff Report: State Context & Expression Interpolation Design (`agent_workflow/state.py`)

## 1. Observation

Direct observations from codebase inspection, context files, and verification scenarios:

- **Interface Contract (`PROJECT.md:147-152`)**:
  ```python
  class StateContext:
      def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None: ...
      def get_step_output(self, step_id: str) -> Dict[str, Any]: ...
      def interpolate(self, template: Any) -> Any: ...
      """Interpolates strings like '${steps.step_id.output.key}' using recorded step outputs."""
  ```

- **Data Models (`agent_workflow/models.py:157-205`)**:
  `StepResult` encapsulates individual step execution outputs:
  ```python
  @dataclass
  class StepResult:
      step_id: str
      status: StepStatus
      output: Dict[str, Any] = field(default_factory=dict)
      ...
  ```

- **Scope Requirements (`.agents/sub_orch_m2/SCOPE.md:12-21`)**:
  - `FEAT-STA-01`: Input/Output State Passing & Interpolation (`${steps.ID.output.KEY}` syntax, dictionary & string template resolution, nested path extraction).
  - Verification requires unit tests covering string, dict, list, int, bool, float interpolation, and invalid reference exceptions (`KeyError`/`StateInterpolationError`).

- **Scenario Workflows (`tests/test_workflows/`)**:
  - `linear_workflow.yaml:15-16`: Full-value primitive and string interpolation:
    `input_msg: "${steps.step_1.output.message}"`
    `input_val: "${steps.step_1.output.initial_value}"`
  - `mutation_workflow.yaml:20`: Full-value complex object (dict) interpolation:
    `user_obj: "${steps.step_init_data.output.user}"`
  - `mutation_workflow.yaml:30`: Full-value list object interpolation:
    `tags_list: "${steps.step_init_data.output.tags}"`
  - `parallel_workflow.yaml:15`: Full-value numeric interpolation across concurrent branches:
    `base: "${steps.step_root.output.seed}"`

- **Fallback Reference (`tests/engine_fallback.py:74-123`)**:
  In fallback implementation, regex `r"\$\{steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\}"` is used, but fallback uses plain dict without thread locking or deep copying.

---

## 2. Logic Chain

1. **Thread Safety & Mutability Isolation**:
   - *Observation*: Workflow DAG execution permits concurrent parallel step execution (`parallel_workflow.yaml`, `FEAT-ENG-04`). Multiple step tasks may write output or read interpolated params simultaneously.
   - *Reasoning*: Mutating dictionary state concurrently without locking causes race conditions. Furthermore, if step outputs return mutable containers (`dict`, `list`), downstream steps modifying those objects in-place could pollute state for other concurrent/downstream steps.
   - *Deduction*: `StateContext` must use a re-entrant lock (`threading.RLock()`) for internal state access, and must store and return deep copies (`copy.deepcopy`) of outputs during `set_step_output`, `get_step_output`, and `interpolate`.

2. **Exception Hierarchy (`KeyError` / `StateInterpolationError`)**:
   - *Observation*: `SCOPE.md` specifies invalid reference exceptions (`KeyError`/`StateInterpolationError`).
   - *Reasoning*: Standard Python dict access raises `KeyError`. Code expecting standard dictionary semantics should be able to catch `KeyError`, while custom code can catch `StateInterpolationError`.
   - *Deduction*: Defining `class StateInterpolationError(KeyError):` allows `issubclass(StateInterpolationError, KeyError)` to be `True`. Overriding `__str__` returns the clean error message without extra quotes.

3. **Type Preservation vs String Interpolation**:
   - *Observation*: Workflow definitions pass integers (`initial_value: 10`), booleans, dicts (`user_obj`), and lists (`tags_list`).
   - *Reasoning*: If an expression like `"${steps.step_1.output.initial_value}"` is converted to string `"10"`, downstream steps expecting arithmetic or structured data fail. However, `"User ${steps.s1.output.name}"` must yield a concatenated string.
   - *Deduction*: StateContext must perform a 2-pass string resolution:
     - Pass 1: If string is an exact match for a single expression (e.g. `^\s*\$\{\s*steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\s*\}\s*$`), return the raw target object with its native type intact.
     - Pass 2: If string contains surrounding text or multiple expressions, substitute each expression token with `str(val)` (or `json.dumps(val)` for dict/list).

4. **Nested Key Navigation & Path Resolution**:
   - *Observation*: `mutation_workflow.yaml` accesses nested dictionaries and list structures.
   - *Reasoning*: Paths like `user.profile.name` require traversing dictionaries step-by-step. Paths like `tags.0` require list index lookup. Additionally, some keys might directly contain dots.
   - *Deduction*: `_resolve_path` checks:
     a. Direct key match in top-level dictionary (`val[key_path]`).
     b. Split path by `.` and iterate: for dicts, lookup key; for lists, convert numeric key to integer index (`0 <= idx < len(list)`); for non-containers, raise `StateInterpolationError`.

5. **Recursive Parameter Structure Interpolation**:
   - *Observation*: Step parameters in `StepDefinition.params` are dicts containing nested dicts, lists, strings, numbers.
   - *Reasoning*: Template expressions can be deeply nested inside parameter dictionaries or lists.
   - *Deduction*: `interpolate(template)` must recursively process:
     - `dict`: `{interpolate(k): interpolate(v) for k, v in template.items()}`
     - `list`: `[interpolate(item) for item in template]`
     - `tuple`: `tuple(interpolate(item) for item in template)`
     - primitives: return unmodified.

6. **Compatibility with `models.py`**:
   - *Observation*: `StepResult` holds `step_id` and `output: Dict[str, Any]`.
   - *Reasoning*: `WorkflowExecutor` receives `StepResult` upon step completion.
   - *Deduction*: Adding `set_step_result(self, result: StepResult) -> None` provides a direct, clean helper method for `executor.py`.

---

## 3. Caveats

- **Dict Key Interpolation**: The design supports interpolating dictionary keys as well as dictionary values. If a key string contains a template expression (e.g., `{"${steps.s1.output.key_name}": "value"}`), it will be interpolated.
- **Embedded Complex Containers**: When a container object (dict or list) is embedded inside a string (e.g. `"Data is ${steps.s1.output.dict_val}"`), it is converted using `json.dumps()` to ensure valid string representation.
- **No Caveats regarding Scope**: The investigation covers all required requirements for FEAT-STA-01 and `state.py`.

---

## 4. Conclusion

`agent_workflow/state.py` has been fully designed and verified with a reference implementation (`proposed_state.py`) and a comprehensive unit test suite (`proposed_test_state.py` with 20 test cases).

### Architectural Overview of `agent_workflow/state.py`:

```python
class StateInterpolationError(KeyError):
    """Raised when state interpolation fails due to missing step, missing key, or malformed template."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

class StateContext:
    def __init__(self, initial_outputs: Optional[Dict[str, Dict[str, Any]]] = None)
    def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None
    def set_step_result(self, result: StepResult) -> None
    def get_step_output(self, step_id: str) -> Dict[str, Any]
    def has_step_output(self, step_id: str) -> bool
    def clear(self) -> None
    def interpolate(self, template: Any) -> Any
```

Implementation files written to working directory for implementation handoff:
1. `/home/beern/teamwork_projects/agent_workflow_framework/.agents/teamwork_preview_explorer_m2_1/proposed_state.py`
2. `/home/beern/teamwork_projects/agent_workflow_framework/.agents/teamwork_preview_explorer_m2_1/proposed_test_state.py`

---

## 5. Verification Method

### Command 1: Standalone Test Execution of Proposed Design
Run the following command from `/home/beern/teamwork_projects/agent_workflow_framework`:

```bash
python3 -c "
import sys
sys.path.insert(0, '.agents/teamwork_preview_explorer_m2_1')
sys.path.insert(0, '.')
import proposed_state
sys.modules['agent_workflow.state'] = proposed_state
import unittest
import proposed_test_state
suite = unittest.TestLoader().loadTestsFromModule(proposed_test_state)
runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)
sys.exit(0 if res.wasSuccessful() else 1)
"
```
**Expected Output**: `Ran 20 tests in 0.032s ... OK` with exit code `0`.

### Command 2: Post-Implementation Framework Test Suite
Once `Worker M2` writes `agent_workflow/state.py` and `tests/test_state.py`, run:

```bash
python3 -m unittest discover -s tests
```
**Expected Output**: All unit tests in `tests/` pass with exit code `0`.

### Command 3: Full Verification Runner
```bash
python3 verify.py
```
**Expected Output**: All E2E scenarios pass with exit code `0`.

### Invalidation Conditions:
- If `interpolate()` converts exact match numbers or dicts to strings (breaking type preservation).
- If concurrent threads calling `set_step_output` or `interpolate` cause race conditions or unhandled exceptions.
- If `StateInterpolationError` fails `issubclass(StateInterpolationError, KeyError)`.
- If nested path traversal (e.g. `user.profile.name` or `tags.0`) fails to resolve valid data.
