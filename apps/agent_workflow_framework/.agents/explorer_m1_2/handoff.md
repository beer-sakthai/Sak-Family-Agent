# Handoff Report: Explorer M1-2 (`agent_workflow/parser.py`)

## 1. Observation

### System Environment & Dependencies
- **Command executed**: `python3 -c "import sys, yaml, json, dataclasses, graphlib; print('Python:', sys.version); print('PyYAML:', yaml.__file__ if hasattr(yaml, '__file__') else 'builtin')"`
- **Output**:
  ```
  Python: 3.14.4 (main, Jun 18 2026, 14:25:02) [GCC 15.2.0]
  PyYAML: /usr/lib/python3/dist-packages/yaml/__init__.py
  ```
- Standard Python libraries (`json`, `dataclasses`, `pathlib`) and third-party library `PyYAML` (`yaml`) are installed and available in Python 3.14 environment.

### Project Specification & Contracts
- **`ORIGINAL_REQUEST.md` (lines 12–16, R1 & R2)**: Requirements specify loading workflow definitions from files and validating syntax errors prior to run.
- **`PROJECT.md` (lines 8, 19, 80–112)**:
  - Modules: `agent_workflow/parser.py` (YAML/JSON parsing & schema validation).
  - Feature `FEAT-ENG-01`: Workflow Definition Schema & Parsing (Parse YAML/JSON workflow definitions into Python dataclasses).
  - Dataclasses contract:
    - `StepDefinition`: `id` (str), `action` (str), `params` (Dict[str, Any]), `depends_on` (List[str]), `retry` (int), `retry_delay` (float).
    - `WorkflowDefinition`: `name` (str), `description` (Optional[str]), `steps` (List[StepDefinition]).
- **`.agents/sub_orch_m1/SCOPE.md` (lines 8–15)**: Milestone 1 target file includes `agent_workflow/parser.py`.
- **`.agents/explorer_m1_1/proposed_models.py` (lines 43–154)**: Models implementation defines `StepDefinition.from_dict()` and `WorkflowDefinition.from_dict()`, along with schema validation methods `validate_schema()`.

### Prototype Implementation & Unit Tests Verification
- Prototype implementation written to `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_2/proposed_parser.py`.
- Unit test suite written to `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_2/test_proposed_parser.py`.
- **Command executed**: `PYTHONPATH=.agents/explorer_m1_1:.agents/explorer_m1_2 python3 .agents/explorer_m1_2/test_proposed_parser.py`
- **Output**:
  ```
  ............
  ----------------------------------------------------------------------
  Ran 12 tests in 0.011s

  OK
  ```

## 2. Logic Chain

1. **Requirement Mapping**: `ORIGINAL_REQUEST.md` R1/R2 and `PROJECT.md` FEAT-ENG-01 require parsing both YAML (`.yaml`, `.yml`) and JSON (`.json`) files into `WorkflowDefinition` dataclasses, while validating syntax and schema errors.
2. **Library Selection**:
   - `PyYAML` (`yaml.safe_load`) is available in system site-packages and securely parses YAML content into standard Python dicts/lists without risk of arbitrary code execution.
   - `json.loads` natively parses JSON string content with standard `JSONDecodeError` handling.
   - `pathlib.Path` provides clean path inspection (`.suffix`, `.exists()`, `.is_file()`).
3. **Validation Strategy**:
   - **File I/O**: Check file existence, readability, and file extension dispatch.
   - **Syntax Validation**: Catch `yaml.YAMLError` and `json.JSONDecodeError` and wrap them in a unified `WorkflowParseError`.
   - **Root Data Type**: Validate root data structure is a non-empty `dict`.
   - **Strict Field Validation**:
     - Check top-level required fields (`name`, `steps`).
     - Reject unknown top-level keys to prevent silent typos (e.g. `workflow_name` instead of `name`).
     - Check step required fields (`id`, `action`).
     - Reject duplicate step IDs across the workflow.
     - Validate type and value bounds for step attributes (`params` must be dict, `depends_on` list of strings, `retry` int >= 0, `retry_delay` float/int >= 0.0).
     - Reject unknown step keys to prevent typos (e.g., `rety` instead of `retry`).
   - **Dataclass Construction**: Instantiate `StepDefinition` and `WorkflowDefinition` dataclass objects.
4. **API Function Boundaries**:
   - `parse_workflow_dict(data: Dict[str, Any]) -> WorkflowDefinition`
   - `parse_workflow_yaml(yaml_str: str) -> WorkflowDefinition`
   - `parse_workflow_json(json_str: str) -> WorkflowDefinition`
   - `parse_workflow_file(file_path: Union[str, Path]) -> WorkflowDefinition`
   - Custom exception `WorkflowParseError(Exception)` for all syntax, schema, and I/O failures.
5. **Separation of Concerns**:
   - `parser.py` validates file syntax, raw dictionary schema, field types, and step ID uniqueness.
   - `dag.py` receives the constructed `WorkflowDefinition` to perform graph dependency checks (missing dependency references, cycle detection, topological sorting).

## 3. Caveats

- **File Encoding**: The parser assumes UTF-8 file encoding when reading workflow definition files.
- **YAML vs JSON Supersets**: `yaml.safe_load` natively parses valid JSON strings. However, explicit extension dispatching to `json.loads` is implemented for `.json` files to provide precise `JSONDecodeError` error messages with line/column numbers.
- **Dependency Topology**: `parser.py` checks duplicate step IDs within the `steps` list, but leaves missing target step ID verification (e.g., `depends_on: ["nonexistent_step"]`) and cyclic dependency validation to `dag.validate_workflow_dag()`.

## 4. Conclusion

`agent_workflow/parser.py` should be implemented with the custom exception `WorkflowParseError` and the four parsing entry points (`parse_workflow_file`, `parse_workflow_yaml`, `parse_workflow_json`, `parse_workflow_dict`).
The complete reference implementation is tested and verified at `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_2/proposed_parser.py`.

## 5. Verification Method

1. Inspect proposed implementation file:
   `view_file` on `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_2/proposed_parser.py`
2. Run test suite verifying 12 parsing edge cases:
   `PYTHONPATH=.agents/explorer_m1_1:.agents/explorer_m1_2 python3 .agents/explorer_m1_2/test_proposed_parser.py`
3. Verify exit code 0 and all 12 tests passing.
