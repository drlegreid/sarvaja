"""
Unit tests for Journey Pattern Analyzer.

Per DOC-SIZE-01-v1: Tests for agent/journey_analyzer.py module.
Tests: JourneyAnalyzer — _normalize_question, _compute_semantic_hash,
       _count_recurrences, log_question, _generate_suggestion,
       get_question_history, clear_history; create_journey_analyzer.
"""

import pytest

from agent.journey_analyzer import JourneyAnalyzer, create_journey_analyzer


# ── _normalize_question ───────────────────────────────────────


class TestNormalizeQuestion:
    def test_lowercases(self):
        a = JourneyAnalyzer()
        assert a._normalize_question("HOW DO I?") == "how do i"

    def test_strips_trailing_punctuation(self):
        a = JourneyAnalyzer()
        assert a._normalize_question("What is this???") == "what is this"

    def test_collapses_whitespace(self):
        a = JourneyAnalyzer()
        assert a._normalize_question("too   many    spaces") == "too many spaces"

    def test_strips_leading_trailing(self):
        a = JourneyAnalyzer()
        assert a._normalize_question("  padded  ") == "padded"


# ── _compute_semantic_hash ────────────────────────────────────


class TestComputeSemanticHash:
    def test_deterministic(self):
        a = JourneyAnalyzer()
        h1 = a._compute_semantic_hash("How do I check trust?")
        h2 = a._compute_semantic_hash("How do I check trust?")
        assert h1 == h2

    def test_ignores_stop_words(self):
        a = JourneyAnalyzer()
        h1 = a._compute_semantic_hash("check trust score")
        h2 = a._compute_semantic_hash("how do I check the trust score?")
        assert h1 == h2

    def test_different_content_different_hash(self):
        a = JourneyAnalyzer()
        h1 = a._compute_semantic_hash("check rules")
        h2 = a._compute_semantic_hash("update sessions")
        assert h1 != h2

    def test_hash_length(self):
        a = JourneyAnalyzer()
        h = a._compute_semantic_hash("any question")
        assert len(h) == 12


# ── log_question ──────────────────────────────────────────────


class TestLogQuestion:
    def test_basic_log(self):
        a = JourneyAnalyzer()
        record = a.log_question("What are the rules?", source="chat")
        assert record["question"] == "What are the rules?"
        assert record["source"] == "chat"
        assert record["recurrence_count"] == 1
        assert "alert" not in record

    def test_unique_ids(self):
        a = JourneyAnalyzer()
        r1 = a.log_question("Q1", source="chat")
        r2 = a.log_question("Q2", source="chat")
        assert r1["question_id"] != r2["question_id"]

    def test_context_default(self):
        a = JourneyAnalyzer()
        r = a.log_question("Q", source="test")
        assert r["context"] == {}

    def test_context_passed(self):
        a = JourneyAnalyzer()
        r = a.log_question("Q", source="test", context={"key": "val"})
        assert r["context"]["key"] == "val"

    def test_category(self):
        a = JourneyAnalyzer()
        r = a.log_question("Q", source="test", category="rules")
        assert r["category"] == "rules"

    def test_recurrence_alert_triggered(self):
        a = JourneyAnalyzer(recurrence_threshold=3)
        a.log_question("same question", source="chat")
        a.log_question("same question", source="chat")
        r3 = a.log_question("same question", source="chat")
        assert "alert" in r3
        assert r3["alert"]["type"] == "recurring_question"

    def test_no_alert_below_threshold(self):
        a = JourneyAnalyzer(recurrence_threshold=5)
        a.log_question("same question", source="chat")
        r2 = a.log_question("same question", source="chat")
        assert "alert" not in r2


# ── _count_recurrences ────────────────────────────────────────


class TestCountRecurrences:
    def test_no_history(self):
        a = JourneyAnalyzer()
        assert a._count_recurrences("new question") == 0

    def test_exact_match(self):
        a = JourneyAnalyzer()
        a.log_question("Test question", source="test")
        assert a._count_recurrences("Test question") == 1

    def test_semantic_match(self):
        a = JourneyAnalyzer()
        a.log_question("How do I check trust?", source="test")
        count = a._count_recurrences("How do I check the trust?")
        assert count >= 1


# ── _generate_suggestion ─────────────────────────────────────


class TestGenerateSuggestion:
    def test_agent_question(self):
        a = JourneyAnalyzer()
        s = a._generate_suggestion("How is agent trust calculated?", 3)
        assert "Trust Dashboard" in s

    def test_rule_question(self):
        a = JourneyAnalyzer()
        s = a._generate_suggestion("What governance rules apply?", 3)
        assert "governance FAQ" in s

    def test_session_question(self):
        a = JourneyAnalyzer()
        s = a._generate_suggestion("Where is the session evidence?", 3)
        assert "session search" in s

    def test_monitor_question(self):
        a = JourneyAnalyzer()
        s = a._generate_suggestion("What are the monitor alerts?", 3)
        assert "monitoring" in s

    def test_generic_question(self):
        a = JourneyAnalyzer()
        s = a._generate_suggestion("How do I deploy?", 3)
        assert "3 times" in s


# ── get_question_history ──────────────────────────────────────


class TestGetQuestionHistory:
    def test_empty(self):
        a = JourneyAnalyzer()
        assert a.get_question_history() == []

    def test_limit(self):
        a = JourneyAnalyzer()
        for i in range(10):
            a.log_question(f"Q-{i}", source="test")
        result = a.get_question_history(limit=3)
        assert len(result) == 3

    def test_filter_by_source(self):
        a = JourneyAnalyzer()
        a.log_question("Q1", source="chat")
        a.log_question("Q2", source="api")
        result = a.get_question_history(source="chat")
        assert len(result) == 1

    def test_filter_by_category(self):
        a = JourneyAnalyzer()
        a.log_question("Q1", source="test", category="rules")
        a.log_question("Q2", source="test", category="tasks")
        result = a.get_question_history(category="rules")
        assert len(result) == 1

    def test_sorted_newest_first(self):
        a = JourneyAnalyzer()
        a.log_question("first", source="test")
        a.log_question("second", source="test")
        result = a.get_question_history()
        assert result[0]["question"] == "second"


# ── clear_history ─────────────────────────────────────────────


class TestClearHistory:
    def test_clears_all(self):
        a = JourneyAnalyzer()
        a.log_question("Q", source="test")
        a.clear_history()
        assert len(a.questions) == 0
        assert a._question_counter == 0


# ── create_journey_analyzer ───────────────────────────────────


class TestFactory:
    def test_creates_instance(self):
        a = create_journey_analyzer()
        assert isinstance(a, JourneyAnalyzer)
        assert a.recurrence_threshold == 3

    def test_custom_params(self):
        a = create_journey_analyzer(recurrence_threshold=5, time_window_days=14)
        assert a.recurrence_threshold == 5
        assert a.time_window_days == 14
