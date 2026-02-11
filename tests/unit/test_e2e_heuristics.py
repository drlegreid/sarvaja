"""
Unit tests for E2E Exploration Heuristics & LLM Prompts.

Per DOC-SIZE-01-v1: Tests for extracted e2e_heuristics.py.
Tests: EXPLORATION_HEURISTICS constants, prompt templates.
"""

import pytest

from agent.e2e_heuristics import (
    EXPLORATION_HEURISTICS,
    EXPLORATION_SYSTEM_PROMPT,
    FAILURE_ANALYSIS_PROMPT,
)


class TestExplorationHeuristics:
    """Tests for EXPLORATION_HEURISTICS dict."""

    def test_has_required_keys(self):
        expected = {
            "page_structure",
            "form_discovery",
            "navigation_flow",
            "error_handling",
            "accessibility_quick",
        }
        assert set(EXPLORATION_HEURISTICS.keys()) == expected

    def test_all_values_non_empty(self):
        for key, value in EXPLORATION_HEURISTICS.items():
            assert len(value.strip()) > 0, f"{key} is empty"

    def test_all_have_numbered_steps(self):
        for key, value in EXPLORATION_HEURISTICS.items():
            assert "1." in value, f"{key} missing numbered steps"


class TestExplorationSystemPrompt:
    """Tests for EXPLORATION_SYSTEM_PROMPT."""

    def test_non_empty(self):
        assert len(EXPLORATION_SYSTEM_PROMPT.strip()) > 0

    def test_mentions_playwright(self):
        assert "playwright" in EXPLORATION_SYSTEM_PROMPT.lower()

    def test_has_output_format(self):
        assert "action" in EXPLORATION_SYSTEM_PROMPT
        assert "target" in EXPLORATION_SYSTEM_PROMPT


class TestFailureAnalysisPrompt:
    """Tests for FAILURE_ANALYSIS_PROMPT template."""

    def test_has_placeholders(self):
        assert "{test_name}" in FAILURE_ANALYSIS_PROMPT
        assert "{failed_step}" in FAILURE_ANALYSIS_PROMPT
        assert "{error_message}" in FAILURE_ANALYSIS_PROMPT

    def test_format_works(self):
        result = FAILURE_ANALYSIS_PROMPT.format(
            test_name="test_login",
            failed_step="click submit",
            error_message="timeout",
            screenshot_path="/tmp/ss.png",
        )
        assert "test_login" in result
        assert "timeout" in result
