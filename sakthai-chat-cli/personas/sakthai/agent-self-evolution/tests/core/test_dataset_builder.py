import json
from unittest.mock import MagicMock, patch

import pytest

from evolution.core.config import EvolutionConfig
from evolution.core.dataset_builder import EvalDataset, EvalExample, LayoutDatasetBuilder


class TestEvalExample:
    def test_eval_example_to_dict(self):
        example = EvalExample(
            task_input="input",
            expected_behavior="behavior",
            difficulty="hard",
            category="test",
            source="golden",
        )
        expected = {
            "task_input": "input",
            "expected_behavior": "behavior",
            "difficulty": "hard",
            "category": "test",
            "source": "golden",
        }
        assert example.to_dict() == expected

    def test_eval_example_from_dict(self):
        data = {
            "task_input": "input",
            "expected_behavior": "behavior",
            "difficulty": "easy",
            "category": "logic",
            "source": "synthetic",
            "extra_field": "ignored",
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


@patch("dspy.LM")
@patch("dspy.ChainOfThought")
def test_layout_dataset_builder(mock_cot, mock_lm):
    # Arrange
    mock_config = MagicMock(spec=EvolutionConfig)
    mock_config.eval_dataset_size = 1
    mock_config.train_ratio = 1.0
    mock_config.val_ratio = 0.0
    mock_config.judge_model = "mock_model"

    builder = LayoutDatasetBuilder(mock_config)

    # Mock the dspy generator call
    mock_generator_instance = mock_cot.return_value
    mock_result = MagicMock()
    mock_result.test_cases = json.dumps(
        [
            {
                "task_input": "Generate a bar chart.",
                "expected_behavior": "- Use colorblind-safe palette\n- Save as PDF",
                "difficulty": "easy",
                "category": "visualization",
            }
        ]
    )
    mock_generator_instance.return_value = mock_result

    # Act
    dataset = builder.generate(
        artifact_text="A skill about charts.", reference_guides=["A guide about charts."]
    )

    # Assert
    assert len(dataset.all_examples) == 1
    example = dataset.train[0]
    assert example.task_input == "Generate a bar chart."
    assert "Use colorblind-safe palette" in example.expected_behavior
    assert "Save as PDF" in example.expected_behavior
    assert example.difficulty == "easy"
    assert example.category == "layout"  # The builder should override this
    assert example.source == "synthetic_layout"

    mock_generator_instance.assert_called_once()
