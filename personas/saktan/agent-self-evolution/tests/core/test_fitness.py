from unittest.mock import MagicMock, patch

import dspy
import pytest
from evolution.core.config import EvolutionConfig
from evolution.core.fitness import FitnessScore, LLMJudge, _parse_score, skill_fitness_metric


class TestSkillFitnessMetric:
    def test_empty_agent_output(self):
        example = dspy.Example(expected_behavior="Do something")
        prediction = dspy.Prediction(output="")
        assert skill_fitness_metric(example, prediction) == 0.0

        prediction = dspy.Prediction(output="   ")
        assert skill_fitness_metric(example, prediction) == 0.0

    def test_non_empty_output_empty_expected(self):
        example = dspy.Example(expected_behavior="")
        prediction = dspy.Prediction(output="Some output")
        # score = 0.5 base
        assert skill_fitness_metric(example, prediction) == 0.5

    def test_keyword_overlap(self):
        # expected: "hello world" (2 words)
        # output: "hello" (1 word overlap)
        # overlap = 1/2 = 0.5
        # score = 0.3 + 0.7 * 0.5 = 0.65
        example = dspy.Example(expected_behavior="hello world")
        prediction = dspy.Prediction(output="hello")
        assert skill_fitness_metric(example, prediction) == pytest.approx(0.65)

    def test_full_overlap(self):
        example = dspy.Example(expected_behavior="hello world")
        prediction = dspy.Prediction(output="world hello")
        assert skill_fitness_metric(example, prediction) == 1.0

    def test_no_overlap(self):
        # overlap = 0
        # score = 0.3 + 0.7 * 0 = 0.3
        example = dspy.Example(expected_behavior="hello world")
        prediction = dspy.Prediction(output="foo bar")
        assert skill_fitness_metric(example, prediction) == pytest.approx(0.3)

    def test_clamping(self):
        example = dspy.Example(expected_behavior="test")
        prediction = dspy.Prediction(output="test")
        assert skill_fitness_metric(example, prediction) == 1.0


class TestFitnessScore:
    def test_composite_score(self):
        score = FitnessScore(correctness=1.0, procedure_following=1.0, conciseness=1.0)
        # 0.5*1.0 + 0.3*1.0 + 0.2*1.0 = 1.0
        assert score.composite == 1.0

        score = FitnessScore(correctness=0.5, procedure_following=0.5, conciseness=0.5)
        # 0.5*0.5 + 0.3*0.5 + 0.2*0.5 = 0.5
        assert score.composite == 0.5

        score = FitnessScore(
            correctness=1.0, procedure_following=0.0, conciseness=0.0, length_penalty=0.1
        )
        # 0.5*1.0 + 0 - 0.1 = 0.4
        assert score.composite == pytest.approx(0.4)

    def test_composite_min_zero(self):
        score = FitnessScore(correctness=0.1, length_penalty=0.5)
        # 0.5 * 0.1 - 0.5 = -0.45 -> should be 0.0
        assert score.composite == 0.0


class TestParseScore:
    def test_parse_numeric(self):
        assert _parse_score(0.8) == 0.8
        assert _parse_score(1.5) == 1.0
        assert _parse_score(-0.1) == 0.0

    def test_parse_string(self):
        assert _parse_score("0.7") == 0.7
        assert _parse_score("  0.9  ") == 0.9

    def test_parse_invalid(self):
        assert _parse_score("abc") == 0.5
        assert _parse_score(None) == 0.5


class TestLLMJudge:
    @pytest.fixture
    def config(self):
        return EvolutionConfig()

    @pytest.fixture
    def judge(self, config):
        return LLMJudge(config)

    def test_score_basic(self, judge):
        mock_result = MagicMock()
        mock_result.correctness = 0.9
        mock_result.procedure_following = 0.8
        mock_result.conciseness = 0.7
        mock_result.feedback = "Good job"

        with (
            patch.object(judge, "judge", return_value=mock_result),
            patch("dspy.LM"),
            patch("dspy.context"),
        ):
            score = judge.score(
                task_input="input",
                expected_behavior="behavior",
                agent_output="output",
                skill_text="skill",
            )

            assert score.correctness == 0.9
            assert score.procedure_following == 0.8
            assert score.conciseness == 0.7
            assert score.feedback == "Good job"
            assert score.length_penalty == 0.0

    def test_length_penalty(self, judge):
        mock_result = MagicMock()
        mock_result.correctness = 1.0
        mock_result.procedure_following = 1.0
        mock_result.conciseness = 1.0
        mock_result.feedback = ""

        with (
            patch.object(judge, "judge", return_value=mock_result),
            patch("dspy.LM"),
            patch("dspy.context"),
        ):
            # 95% size
            score = judge.score(
                task_input="i",
                expected_behavior="e",
                agent_output="o",
                skill_text="s",
                artifact_size=95,
                max_size=100,
            )
            # ratio = 0.95
            # penalty = (0.95 - 0.9) * 3.0 = 0.05 * 3 = 0.15
            assert score.length_penalty == pytest.approx(0.15)

            # 110% size
            score = judge.score(
                task_input="i",
                expected_behavior="e",
                agent_output="o",
                skill_text="s",
                artifact_size=110,
                max_size=100,
            )
            # ratio = 1.1
            # penalty = min(0.3, (1.1 - 0.9) * 3.0) = min(0.3, 0.6) = 0.3
            assert score.length_penalty == 0.3

            # 80% size (no penalty)
            score = judge.score(
                task_input="i",
                expected_behavior="e",
                agent_output="o",
                skill_text="s",
                artifact_size=80,
                max_size=100,
            )
            assert score.length_penalty == 0.0
