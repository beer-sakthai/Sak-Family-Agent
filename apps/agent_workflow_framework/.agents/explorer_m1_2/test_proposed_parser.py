"""Unit tests for proposed_parser.py."""

import unittest
from pathlib import Path
import tempfile
try:
    from .proposed_parser import (
        parse_workflow_dict,
        parse_workflow_yaml,
        parse_workflow_json,
        parse_workflow_file,
        WorkflowParseError,
    )
except ImportError:
    from proposed_parser import (
        parse_workflow_dict,
        parse_workflow_yaml,
        parse_workflow_json,
        parse_workflow_file,
        WorkflowParseError,
    )


class TestWorkflowParser(unittest.TestCase):

    def test_valid_yaml_parsing(self):
        yaml_str = """
name: "Test Workflow"
description: "A test description"
steps:
  - id: "step1"
    action: "echo"
    params:
      message: "hello"
  - id: "step2"
    action: "python"
    depends_on: ["step1"]
    retry: 2
    retry_delay: 1.5
"""
        wf = parse_workflow_yaml(yaml_str)
        self.assertEqual(wf.name, "Test Workflow")
        self.assertEqual(wf.description, "A test description")
        self.assertEqual(len(wf.steps), 2)
        self.assertEqual(wf.steps[0].id, "step1")
        self.assertEqual(wf.steps[0].action, "echo")
        self.assertEqual(wf.steps[1].id, "step2")
        self.assertEqual(wf.steps[1].depends_on, ["step1"])
        self.assertEqual(wf.steps[1].retry, 2)
        self.assertEqual(wf.steps[1].retry_delay, 1.5)

    def test_valid_json_parsing(self):
        json_str = """{
            "name": "JSON Workflow",
            "steps": [
                {
                    "id": "step_a",
                    "action": "shell",
                    "params": {"cmd": "ls"}
                }
            ]
        }"""
        wf = parse_workflow_json(json_str)
        self.assertEqual(wf.name, "JSON Workflow")
        self.assertEqual(len(wf.steps), 1)
        self.assertEqual(wf.steps[0].id, "step_a")
        self.assertEqual(wf.steps[0].action, "shell")
        self.assertEqual(wf.steps[0].params, {"cmd": "ls"})

    def test_invalid_syntax_yaml(self):
        bad_yaml = "name: [unclosed list"
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(bad_yaml)
        self.assertIn("YAML syntax error", str(ctx.exception))

    def test_invalid_syntax_json(self):
        bad_json = '{"name": "bad",}'
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_json(bad_json)
        self.assertIn("JSON syntax error", str(ctx.exception))

    def test_missing_name(self):
        yaml_str = """
steps:
  - id: "s1"
    action: "echo"
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("missing required field 'name'", str(ctx.exception))

    def test_missing_steps(self):
        yaml_str = 'name: "No steps"'
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("missing required field 'steps'", str(ctx.exception))

    def test_empty_steps(self):
        yaml_str = """
name: "Empty steps"
steps: []
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("must contain at least one step", str(ctx.exception))

    def test_duplicate_step_ids(self):
        yaml_str = """
name: "Dup steps"
steps:
  - id: "step1"
    action: "echo"
  - id: "step1"
    action: "echo"
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("Duplicate step ID 'step1'", str(ctx.exception))

    def test_unknown_top_level_attribute(self):
        yaml_str = """
name: "Unknown field"
invalid_key: 123
steps:
  - id: "s1"
    action: "echo"
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("Unknown top-level attribute(s)", str(ctx.exception))

    def test_unknown_step_attribute(self):
        yaml_str = """
name: "Unknown step field"
steps:
  - id: "s1"
    action: "echo"
    rety: 5
"""
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_yaml(yaml_str)
        self.assertIn("unknown attribute(s)", str(ctx.exception))

    def test_file_parsing(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: File WF\nsteps:\n  - id: s1\n    action: echo\n")
            f_path = Path(f.name)

        try:
            wf = parse_workflow_file(f_path)
            self.assertEqual(wf.name, "File WF")
        finally:
            f_path.unlink(missing_ok=True)

    def test_nonexistent_file(self):
        with self.assertRaises(WorkflowParseError) as ctx:
            parse_workflow_file("/non/existent/file.yaml")
        self.assertIn("Workflow file not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
