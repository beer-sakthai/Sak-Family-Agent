import pytest
from evolution.core.dataset_builder import EvalDataset, EvalExample

class TestEvalDatasetAllExamples:
    """Tests for the EvalDataset.all_examples property."""

    def test_all_examples_empty(self):
        """Test with all splits being empty."""
        dataset = EvalDataset(train=[], val=[], holdout=[])
        assert dataset.all_examples == []

    def test_all_examples_partially_empty(self):
        """Test with some splits being empty."""
        ex1 = EvalExample(task_input="task1", expected_behavior="behavior1")
        ex2 = EvalExample(task_input="task2", expected_behavior="behavior2")

        # Only train has examples
        dataset = EvalDataset(train=[ex1, ex2], val=[], holdout=[])
        assert dataset.all_examples == [ex1, ex2]

        # Only val has examples
        dataset = EvalDataset(train=[], val=[ex1], holdout=[])
        assert dataset.all_examples == [ex1]

        # Only holdout has examples
        dataset = EvalDataset(train=[], val=[], holdout=[ex2])
        assert dataset.all_examples == [ex2]

    def test_all_examples_full(self):
        """Test with all splits containing examples."""
        train_ex = EvalExample(task_input="train", expected_behavior="train_b")
        val_ex = EvalExample(task_input="val", expected_behavior="val_b")
        holdout_ex = EvalExample(task_input="holdout", expected_behavior="holdout_b")

        dataset = EvalDataset(
            train=[train_ex],
            val=[val_ex],
            holdout=[holdout_ex]
        )

        all_ex = dataset.all_examples
        assert len(all_ex) == 3
        assert all_ex == [train_ex, val_ex, holdout_ex]

    def test_default_initialization(self):
        """Test that default factory lists work as expected."""
        dataset = EvalDataset()
        assert dataset.train == []
        assert dataset.val == []
        assert dataset.holdout == []
        assert dataset.all_examples == []
