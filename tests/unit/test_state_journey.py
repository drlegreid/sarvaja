"""
Unit tests for Journey Pattern Analyzer State.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/journey.py.
Tests: with_recurring_questions, with_journey_patterns, with_knowledge_gaps,
       with_question_history, get_gap_priority_color,
       format_recurring_question, format_knowledge_gap, format_journey_pattern.
"""

from agent.governance_ui.state.journey import (
    with_recurring_questions, with_journey_patterns,
    with_knowledge_gaps, with_question_history,
    get_gap_priority_color, format_recurring_question,
    format_knowledge_gap, format_journey_pattern,
)


# ── State Transforms ─────────────────────────────────────


class TestWithRecurringQuestions:
    def test_sets_questions(self):
        qs = [{"question": "Q1"}]
        assert with_recurring_questions({}, qs)["recurring_questions"] == qs

    def test_preserves_state(self):
        result = with_recurring_questions({"x": 1}, [])
        assert result["x"] == 1


class TestWithJourneyPatterns:
    def test_sets_patterns(self):
        patterns = [{"topic": "auth"}]
        assert with_journey_patterns({}, patterns)["journey_patterns"] == patterns


class TestWithKnowledgeGaps:
    def test_sets_gaps(self):
        gaps = [{"topic": "testing"}]
        assert with_knowledge_gaps({}, gaps)["knowledge_gaps"] == gaps


class TestWithQuestionHistory:
    def test_sets_history(self):
        hist = [{"q": "Q1", "ts": "2026-01-01"}]
        assert with_question_history({}, hist)["question_history"] == hist


# ── UI Helpers ────────────────────────────────────────────


class TestGetGapPriorityColor:
    def test_known(self):
        assert get_gap_priority_color("high") == "error"
        assert get_gap_priority_color("medium") == "warning"
        assert get_gap_priority_color("low") == "info"

    def test_case_insensitive(self):
        assert get_gap_priority_color("HIGH") == "error"
        assert get_gap_priority_color("Medium") == "warning"

    def test_unknown(self):
        assert get_gap_priority_color("xyz") == "grey"


# ── Format Functions ──────────────────────────────────────


class TestFormatRecurringQuestion:
    def test_critical_urgency(self):
        result = format_recurring_question({"question": "Why?", "count": 5})
        assert result["urgency"] == "critical"
        assert result["urgency_color"] == "error"

    def test_high_urgency(self):
        result = format_recurring_question({"count": 3})
        assert result["urgency"] == "high"
        assert result["urgency_color"] == "warning"

    def test_moderate_urgency(self):
        result = format_recurring_question({"count": 1})
        assert result["urgency"] == "moderate"
        assert result["urgency_color"] == "info"

    def test_defaults(self):
        result = format_recurring_question({})
        assert result["question"] == ""
        assert result["count"] == 0
        assert result["sources"] == []


class TestFormatKnowledgeGap:
    def test_full_gap(self):
        gap = {"topic": "auth", "priority": "high", "count": 3,
               "question_pattern": "How to authenticate?", "sources": ["s1"]}
        result = format_knowledge_gap(gap)
        assert result["topic"] == "auth"
        assert result["priority_color"] == "error"
        assert result["count"] == 3

    def test_defaults(self):
        result = format_knowledge_gap({})
        assert result["topic"] == "Unknown"
        assert result["priority"] == "medium"
        assert result["priority_color"] == "warning"


class TestFormatJourneyPattern:
    def test_full_pattern(self):
        pattern = {
            "topic": "deployment",
            "question_count": 8,
            "questions": ["Q1", "Q2", "Q3", "Q4"],
            "suggestion": "Add docs",
            "ui_recommendation": {"component": "DocWidget", "location": "main"},
        }
        result = format_journey_pattern(pattern)
        assert result["topic"] == "deployment"
        assert result["question_count"] == 8
        assert len(result["questions"]) == 3  # max 3
        assert result["component"] == "DocWidget"
        assert result["location"] == "main"

    def test_defaults(self):
        result = format_journey_pattern({})
        assert result["topic"] == "Unknown"
        assert result["component"] == "InfoWidget"
        assert result["location"] == "sidebar"
