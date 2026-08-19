"""Unit tests for agent_workflow.state StateContext module."""

import unittest
from concurrent.futures import ThreadPoolExecutor
from agent_workflow.state import StateContext, StateInterpolationError
from agent_workflow.models import StepResult, StepStatus


class TestStateContext(unittest.TestCase):
    """Test suite for StateContext state passing and template interpolation."""

    def setUp(self):
        self.ctx = StateContext()

    def test_set_and_get_step_output(self):
        output = {"msg": "hello", "code": 0}
        self.ctx.set_step_output("step_1", output)
        self.assertEqual(self.ctx.get_step_output("step_1"), output)
        self.assertEqual(self.ctx.get_step_output("unknown_step"), {})

        # Ensure deep copy isolation
        output["code"] = 999
        self.assertEqual(self.ctx.get_step_output("step_1")["code"], 0)

    def test_has_and_clear_step_output(self):
        self.assertFalse(self.ctx.has_step_output("step_1"))
        self.ctx.set_step_output("step_1", {"a": 1})
        self.assertTrue(self.ctx.has_step_output("step_1"))
        self.ctx.clear()
        self.assertFalse(self.ctx.has_step_output("step_1"))

    def test_set_step_result(self):
        result = StepResult(
            step_id="step_res",
            status=StepStatus.COMPLETED,
            output={"score": 95},
        )
        self.ctx.set_step_result(result)
        self.assertEqual(self.ctx.get_step_output("step_res"), {"score": 95})

    def test_interpolate_exact_scalar_types(self):
        self.ctx.set_step_output("step_1", {
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "list_val": [1, 2, 3],
            "dict_val": {"a": 1},
            "none_val": None,
        })
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.int_val}"), 42)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.int_val}"), int)

        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.float_val}"), 3.14)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.float_val}"), float)

        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.bool_val}"), True)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.bool_val}"), bool)

        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.list_val}"), [1, 2, 3])
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.dict_val}"), {"a": 1})
        self.assertIsNone(self.ctx.interpolate("${steps.step_1.output.none_val}"))

    def test_interpolate_full_step_output(self):
        self.ctx.set_step_output("step_1", {"x": 10, "y": 20})
        res = self.ctx.interpolate("${steps.step_1.output}")
        self.assertEqual(res, {"x": 10, "y": 20})

    def test_interpolate_string_literal_embedding(self):
        self.ctx.set_step_output("step_1", {"name": "Alice", "count": 5})
        res = self.ctx.interpolate("User ${steps.step_1.output.name} has ${steps.step_1.output.count} items.")
        self.assertEqual(res, "User Alice has 5 items.")

    def test_interpolate_multiple_expressions(self):
        self.ctx.set_step_output("s1", {"val": 10})
        self.ctx.set_step_output("s2", {"val": 20})
        res = self.ctx.interpolate("${steps.s1.output.val} + ${steps.s2.output.val}")
        self.assertEqual(res, "10 + 20")

    def test_interpolate_dict_structures(self):
        self.ctx.set_step_output("s1", {"host": "localhost", "port": 8080})
        template = {
            "url": "http://${steps.s1.output.host}:${steps.s1.output.port}/api",
            "port_num": "${steps.s1.output.port}",
        }
        expected = {
            "url": "http://localhost:8080/api",
            "port_num": 8080,
        }
        self.assertEqual(self.ctx.interpolate(template), expected)

    def test_interpolate_list_and_tuple_structures(self):
        self.ctx.set_step_output("s1", {"item1": "apple", "item2": "banana"})
        list_template = ["${steps.s1.output.item1}", "${steps.s1.output.item2}", "cherry"]
        tuple_template = ("${steps.s1.output.item1}", "orange")
        self.assertEqual(self.ctx.interpolate(list_template), ["apple", "banana", "cherry"])
        self.assertEqual(self.ctx.interpolate(tuple_template), ("apple", "orange"))

    def test_interpolate_nested_key_path(self):
        self.ctx.set_step_output("s1", {
            "user": {
                "profile": {
                    "role": "admin"
                }
            },
            "tags": ["alpha", "beta", "gamma"]
        })
        self.assertEqual(self.ctx.interpolate("${steps.s1.output.user.profile.role}"), "admin")
        self.assertEqual(self.ctx.interpolate("${steps.s1.output.tags.0}"), "alpha")
        self.assertEqual(self.ctx.interpolate("${steps.s1.output.tags.2}"), "gamma")

    def test_interpolate_direct_key_with_dots(self):
        self.ctx.set_step_output("s1", {"a.b.c": 123})
        res = self.ctx.interpolate("${steps.s1.output.a.b.c}")
        self.assertEqual(res, 123)

    def test_interpolate_missing_step_id(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.missing_step.output.key}")

    def test_interpolate_missing_output_key(self):
        self.ctx.set_step_output("s1", {"a": 1})
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.s1.output.b}")

    def test_interpolate_non_dict_traversal(self):
        self.ctx.set_step_output("s1", {"number": 123})
        with self.assertRaises((KeyError, StateInterpolationError, TypeError)):
            self.ctx.interpolate("${steps.s1.output.number.child}")

    def test_interpolate_malformed_expression(self):
        self.ctx.set_step_output("s1", {"a": 1})
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("Bad ${steps.s1.invalid} template")

    def test_interpolate_primitives_unchanged(self):
        self.assertEqual(self.ctx.interpolate(100), 100)
        self.assertEqual(self.ctx.interpolate(3.14), 3.14)
        self.assertEqual(self.ctx.interpolate(True), True)
        self.assertIsNone(self.ctx.interpolate(None))

    def test_state_context_thread_safety(self):
        def worker(i):
            self.ctx.set_step_output(f"step_{i}", {"val": i})
            return self.ctx.interpolate(f"${{steps.step_{i}.output.val}}")

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(worker, range(50)))
        self.assertEqual(results, list(range(50)))


if __name__ == "__main__":
    unittest.main()
