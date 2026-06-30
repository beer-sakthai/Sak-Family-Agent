import pytest
from evolution.core.dataset_builder import EvalExample, EvalDataset

class TestEvalExample:
    def test_eval_example_to_dict(self):
        example = EvalExample(
            task_input="input",
            expected_behavior="behavior",
            difficulty="hard",
            category="test",
            source="golden"
        )
        expected = {
            "task_input": "input",
            "expected_behavior": "behavior",
            "difficulty": "hard",
            "category": "test",
            "source": "golden"
        }
        assert example.to_dict() == expected

    def test_eval_example_from_dict(self):
        data = {
            "task_input": "input",
            "expected_behavior": "behavior",
            "difficulty": "easy",
            "category": "logic",
            "source": "synthetic",
            "extra_field": "ignored"
        }
        example = EvalExample.from_dict(data)
        assert example.task_input == "input"
        assert example.expected_behavior == "behavior"
        assert example.difficulty == "easy"
        assert example.category == "logic"
        assert example.source == "synthetic"

class TestEvalDataset:
    def test_all_examples_empty(self):
        dataset = EvalDataset()
        assert dataset.all_examples == []

    def test_all_examples_partial(self):
        ex1 = EvalExample("in1", "out1")
        ex2 = EvalExample("in2", "out2")

        dataset = EvalDataset(train=[ex1], holdout=[ex2])
        assert dataset.all_examples == [ex1, ex2]

        dataset2 = EvalDataset(val=[ex1])
        assert dataset2.all_examples == [ex1]

    def test_all_examples_full(self):
        ex_t = EvalExample("train", "train")
        ex_v = EvalExample("val", "val")
        ex_h = EvalExample("holdout", "holdout")

        dataset = EvalDataset(train=[ex_t], val=[ex_v], holdout=[ex_h])
        assert dataset.all_examples == [ex_t, ex_v, ex_h]
