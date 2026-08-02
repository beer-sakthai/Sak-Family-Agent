"""Unit tests for agent_workflow.state module (StateContext and template interpolation)."""

import concurrent.futures
import unittest
from agent_workflow.models import StepResult, StepStatus
from agent_workflow.state import StateContext, StateInterpolationError


class TestStateContextBasic(unittest.TestCase):
    """Test suite for basic StateContext storage and retrieval."""

    def setUp(self):
        self.ctx = StateContext()

    def test_set_and_get_step_output(self):
        self.ctx.set_step_output("step_1", {"msg": "hello", "count": 42})
        self.assertTrue(self.ctx.has_step_output("step_1"))
        self.assertFalse(self.ctx.has_step_output("step_2"))
        self.assertEqual(self.ctx.get_step_output("step_1"), {"msg": "hello", "count": 42})
        self.assertEqual(self.ctx.get_step_output("non_existent"), {})

    def test_set_step_result(self):
        res = StepResult(
            step_id="step_calc",
            status=StepStatus.COMPLETED,
            output={"result": 100, "status": "ok"},
        )
        self.ctx.set_step_result(res)
        self.assertTrue(self.ctx.has_step_output("step_calc"))
        self.assertEqual(self.ctx.get_step_output("step_calc"), {"result": 100, "status": "ok"})

    def test_clear_state(self):
        self.ctx.set_step_output("s1", {"a": 1})
        self.ctx.set_step_output("s2", {"b": 2})
        self.ctx.clear()
        self.assertFalse(self.ctx.has_step_output("s1"))
        self.assertFalse(self.ctx.has_step_output("s2"))


class TestStateContextInterpolationTypes(unittest.TestCase):
    """Test suite for type preservation during full-value template interpolation."""

    def setUp(self):
        self.ctx = StateContext()
        self.ctx.set_step_output("step_init", {
            "str_val": "hello_world",
            "int_val": 100,
            "float_val": 3.14159,
            "bool_val": True,
            "null_val": None,
            "dict_val": {"user": "alice", "role": "admin"},
            "list_val": ["alpha", "beta", "gamma"],
        })

    def test_full_value_type_preservation(self):
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.str_val}"), "hello_world")
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.int_val}"), 100)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_init.output.int_val}"), int)
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.float_val}"), 3.14159)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_init.output.float_val}"), float)
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.bool_val}"), True)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_init.output.bool_val}"), bool)
        self.assertIsNone(self.ctx.interpolate("${steps.step_init.output.null_val}"))
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.dict_val}"), {"user": "alice", "role": "admin"})
        self.assertIsInstance(self.ctx.interpolate("${steps.step_init.output.dict_val}"), dict)
        self.assertEqual(self.ctx.interpolate("${steps.step_init.output.list_val}"), ["alpha", "beta", "gamma"])
        self.assertIsInstance(self.ctx.interpolate("${steps.step_init.output.list_val}"), list)

    def test_full_step_output_interpolation(self):
        full_out = self.ctx.interpolate("${steps.step_init.output}")
        self.assertIsInstance(full_out, dict)
        self.assertIn("str_val", full_out)
        self.assertEqual(full_out["int_val"], 100)


class TestStateContextNestedPath(unittest.TestCase):
    """Test suite for nested key paths and list index resolution."""

    def setUp(self):
        self.ctx = StateContext()
        self.ctx.set_step_output("step_nested", {
            "user": {
                "profile": {
                    "name": "Bob",
                    "scores": [95, 88, 100],
                }
            },
            "tags": ["red", "green", "blue"],
            "direct.key": "direct_value",
        })

    def test_nested_dict_navigation(self):
        self.assertEqual(self.ctx.interpolate("${steps.step_nested.output.user.profile.name}"), "Bob")

    def test_list_index_navigation(self):
        self.assertEqual(self.ctx.interpolate("${steps.step_nested.output.tags.0}"), "red")
        self.assertEqual(self.ctx.interpolate("${steps.step_nested.output.tags.2}"), "blue")
        self.assertEqual(self.ctx.interpolate("${steps.step_nested.output.user.profile.scores.1}"), 88)

    def test_direct_dot_key(self):
        self.assertEqual(self.ctx.interpolate("${steps.step_nested.output.direct.key}"), "direct_value")


class TestStateContextEmbeddedString(unittest.TestCase):
    """Test suite for embedded string interpolation."""

    def setUp(self):
        self.ctx = StateContext()
        self.ctx.set_step_output("s1", {"name": "Alice", "score": 99})
        self.ctx.set_step_output("s2", {"role": "admin"})

    def test_single_embedded_token(self):
        res = self.ctx.interpolate("User name is ${steps.s1.output.name}")
        self.assertEqual(res, "User name is Alice")

    def test_multiple_embedded_tokens(self):
        res = self.ctx.interpolate("User ${steps.s1.output.name} (${steps.s2.output.role}) scored ${steps.s1.output.score}")
        self.assertEqual(res, "User Alice (admin) scored 99")

    def test_embedded_container_token(self):
        self.ctx.set_step_output("s3", {"data": {"a": 1}})
        res = self.ctx.interpolate("Data: ${steps.s3.output.data}")
        self.assertEqual(res, 'Data: {"a": 1}')


class TestStateContextRecursive(unittest.TestCase):
    """Test suite for recursive dict/list parameter interpolation."""

    def setUp(self):
        self.ctx = StateContext()
        self.ctx.set_step_output("s1", {"v1": 10, "v2": "hello"})

    def test_dict_recursive_interpolation(self):
        params = {
            "param_a": "${steps.s1.output.v1}",
            "nested_dict": {
                "msg": "Greeting: ${steps.s1.output.v2}",
                "count": "${steps.s1.output.v1}",
            },
            "literal_int": 500,
        }
        res = self.ctx.interpolate(params)
        self.assertEqual(res, {
            "param_a": 10,
            "nested_dict": {
                "msg": "Greeting: hello",
                "count": 10,
            },
            "literal_int": 500,
        })

    def test_list_recursive_interpolation(self):
        params = [
            "${steps.s1.output.v1}",
            "Value is ${steps.s1.output.v2}",
            {"inner": "${steps.s1.output.v1}"},
        ]
        res = self.ctx.interpolate(params)
        self.assertEqual(res, [
            10,
            "Value is hello",
            {"inner": 10},
        ])


class TestStateContextErrors(unittest.TestCase):
    """Test suite for StateInterpolationError handling."""

    def setUp(self):
        self.ctx = StateContext()
        self.ctx.set_step_output("s1", {"val": 42, "items": [10, 20]})

    def test_exception_inheritance(self):
        self.assertTrue(issubclass(StateInterpolationError, KeyError))
        err = StateInterpolationError("test error")
        self.assertIsInstance(err, KeyError)
        self.assertEqual(str(err), "test error")

    def test_missing_step_raises_error(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.ghost.output.val}")

    def test_missing_key_raises_error(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.s1.output.non_existent_key}")

    def test_invalid_list_index_raises_error(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.s1.output.items.99}")

    def test_access_key_on_scalar_raises_error(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.s1.output.val.sub_key}")

    def test_malformed_expression_raises_error(self):
        with self.assertRaises((KeyError, StateInterpolationError)):
            self.ctx.interpolate("${steps.s1.invalid}")


class TestStateContextThreadSafety(unittest.TestCase):
    """Test suite verifying thread-safe operations on StateContext."""

    def test_concurrent_reads_and_writes(self):
        ctx = StateContext()
        num_threads = 10
        iters_per_thread = 50

        def writer(thread_idx: int):
            for i in range(iters_per_thread):
                ctx.set_step_output(f"step_{thread_idx}", {"val": i, "meta": f"t_{thread_idx}"})

        def reader(thread_idx: int):
            for _ in range(iters_per_thread):
                target_step = f"step_{(thread_idx + 1) % num_threads}"
                if ctx.has_step_output(target_step):
                    val = ctx.interpolate(f"${{steps.{target_step}.output.val}}")
                    self.assertIsInstance(val, int)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads * 2) as executor:
            futures = []
            for t in range(num_threads):
                futures.append(executor.submit(writer, t))
                futures.append(executor.submit(reader, t))
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Re-raise any exceptions from threads


if __name__ == "__main__":
    unittest.main()
