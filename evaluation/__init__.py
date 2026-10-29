"""Evaluation framework package for testing, benchmarking, and comparing the research agent."""

from evaluation.test_cases import EVAL_TEST_CASES, TestCase
from evaluation.baseline import NonAgenticBaseline
from evaluation.eval_runner import run_evaluation_suite

__all__ = [
    "EVAL_TEST_CASES",
    "TestCase",
    "NonAgenticBaseline",
    "run_evaluation_suite"
]
