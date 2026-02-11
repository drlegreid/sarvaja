"""
Unit tests for Journey Pattern Detection Mixin.

Per DOC-SIZE-01-v1: Tests for extracted journey_patterns.py module.
Tests: get_recurring_questions, detect_patterns, get_knowledge_gaps,
       _extract_topic, _generate_ui_suggestion, _get_ui_recommendation.
"""

import pytest
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.journey_patterns import JourneyPatternsMixin


class MockJourneyAnalyzer(JourneyPatternsMixin):
    """Host class for mixin testing."""

    def __init__(self, questions=None, time_window=30):
        self.questions = questions or []
        self.time_window_days = time_window

    def _normalize_question(self, question):
        return question.lower().strip()

    def _compute_semantic_hash(self, question):
        return f"hash-{question[:10]}"


def _q(text, source="chat", ts_delta_days=0, answered=True, category=None, semantic_hash=None):
    """Helper to create question dicts."""
    ts = (datetime.now() - timedelta(days=ts_delta_days)).isoformat()
    q = {"question": text, "source": source, "timestamp": ts, "answered": answered}
    if category:
        q["category"] = category
    if semantic_hash:
        q["semantic_hash"] = semantic_hash
    return q


class TestGetRecurringQuestions:
    """Tests for get_recurring_questions()."""

    def test_empty(self):
        analyzer = MockJourneyAnalyzer()
        assert analyzer.get_recurring_questions() == []

    def test_finds_recurring(self):
        questions = [
            _q("How do I deploy?"),
            _q("How do I deploy?"),
            _q("How do I deploy?"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.get_recurring_questions(min_count=2)
        assert len(result) == 1
        assert result[0]["count"] == 3

    def test_min_count_filter(self):
        questions = [_q("Q1"), _q("Q2")]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.get_recurring_questions(min_count=2)
        assert len(result) == 0

    def test_excludes_old_questions(self):
        questions = [
            _q("Old question", ts_delta_days=60),
            _q("Old question", ts_delta_days=60),
        ]
        analyzer = MockJourneyAnalyzer(questions, time_window=30)
        result = analyzer.get_recurring_questions(min_count=2)
        assert len(result) == 0

    def test_sorted_by_count(self):
        questions = [
            _q("A"), _q("A"),
            _q("B"), _q("B"), _q("B"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.get_recurring_questions(min_count=2)
        assert result[0]["question"] == "B"

    def test_tracks_sources(self):
        questions = [
            _q("Q", source="chat"),
            _q("Q", source="mcp"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.get_recurring_questions(min_count=2)
        assert len(result) == 1
        assert set(result[0]["sources"]) == {"chat", "mcp"}


class TestDetectPatterns:
    """Tests for detect_patterns()."""

    def test_empty(self):
        analyzer = MockJourneyAnalyzer()
        assert analyzer.detect_patterns() == []

    def test_clusters_by_hash(self):
        questions = [
            _q("Trust Q1", semantic_hash="trust-h"),
            _q("Trust Q2", semantic_hash="trust-h"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.detect_patterns()
        assert len(result) == 1
        assert result[0]["question_count"] == 2

    def test_has_suggestion(self):
        questions = [
            _q("Q1", semantic_hash="h1"),
            _q("Q2", semantic_hash="h1"),
            _q("Q3", semantic_hash="h1"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        result = analyzer.detect_patterns()
        assert "suggestion" in result[0]
        assert "ui_recommendation" in result[0]


class TestExtractTopic:
    """Tests for _extract_topic()."""

    def test_uses_category_if_available(self):
        analyzer = MockJourneyAnalyzer()
        questions = [
            _q("Q1", category="trust"),
            _q("Q2", category="trust"),
        ]
        topic = analyzer._extract_topic(questions)
        assert topic == "trust"

    def test_falls_back_to_word_frequency(self):
        analyzer = MockJourneyAnalyzer()
        questions = [
            _q("deploy application today"),
            _q("deploy service again"),
        ]
        topic = analyzer._extract_topic(questions)
        assert topic == "deploy"

    def test_empty_returns_general(self):
        analyzer = MockJourneyAnalyzer()
        assert analyzer._extract_topic([]) == "general"


class TestGenerateUiSuggestion:
    """Tests for _generate_ui_suggestion()."""

    def test_high_count_dashboard(self):
        analyzer = MockJourneyAnalyzer()
        assert "dashboard" in analyzer._generate_ui_suggestion("trust", 5).lower()

    def test_medium_count_menu(self):
        analyzer = MockJourneyAnalyzer()
        assert "quick access" in analyzer._generate_ui_suggestion("trust", 3).lower()

    def test_low_count_faq(self):
        analyzer = MockJourneyAnalyzer()
        assert "FAQ" in analyzer._generate_ui_suggestion("trust", 2)


class TestGetUiRecommendation:
    """Tests for _get_ui_recommendation()."""

    def test_trust_topic(self):
        analyzer = MockJourneyAnalyzer()
        rec = analyzer._get_ui_recommendation("trust metrics")
        assert rec["component"] == "TrustQuickView"

    def test_agent_topic(self):
        analyzer = MockJourneyAnalyzer()
        rec = analyzer._get_ui_recommendation("agent status")
        assert rec["component"] == "AgentStatusWidget"

    def test_unknown_topic(self):
        analyzer = MockJourneyAnalyzer()
        rec = analyzer._get_ui_recommendation("unknown topic")
        assert rec["component"] == "InfoWidget"


class TestGetKnowledgeGaps:
    """Tests for get_knowledge_gaps()."""

    def test_empty(self):
        analyzer = MockJourneyAnalyzer()
        assert analyzer.get_knowledge_gaps() == []

    def test_finds_unanswered(self):
        questions = [
            _q("How to deploy?", answered=False, semantic_hash="h1"),
            _q("Deploy issues", answered=False, semantic_hash="h1"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        gaps = analyzer.get_knowledge_gaps()
        assert len(gaps) == 1
        assert gaps[0]["count"] == 2

    def test_high_priority_for_frequent(self):
        questions = [
            _q("Q1", answered=False, semantic_hash="h1"),
            _q("Q2", answered=False, semantic_hash="h1"),
            _q("Q3", answered=False, semantic_hash="h1"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        gaps = analyzer.get_knowledge_gaps()
        assert gaps[0]["priority"] == "high"

    def test_skips_answered(self):
        questions = [
            _q("Answered Q", answered=True, semantic_hash="h1"),
        ]
        analyzer = MockJourneyAnalyzer(questions)
        assert analyzer.get_knowledge_gaps() == []
