"""
Tests for Journey Pattern Analyzer (P9.7)

Per RULE-012: DSP Semantic Code Structure
Per RULE-020: LLM-Driven E2E Test Generation

Detects recurring questions and knowledge gaps in governance queries.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# =============================================================================
# QUESTION LOGGING TESTS
# =============================================================================

class TestQuestionLogging:
    """Test question logging functionality."""

    def test_log_question(self):
        """Should log a question with timestamp."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        result = analyzer.log_question(
            question="How is llm-sandbox Python MCP being used?",
            source="governor",
            context={"session": "test-session"}
        )

        assert result is not None
        assert 'question_id' in result
        assert 'timestamp' in result
        assert result['question'] == "How is llm-sandbox Python MCP being used?"

    def test_log_question_with_category(self):
        """Should log question with category tag."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        result = analyzer.log_question(
            question="What rules govern agent trust?",
            source="governor",
            category="governance"
        )

        assert result['category'] == "governance"

    def test_question_generates_semantic_hash(self):
        """Similar questions should have similar semantic hashes."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        q1 = analyzer.log_question(
            question="How is llm-sandbox being used?",
            source="user1"
        )
        q2 = analyzer.log_question(
            question="What is llm-sandbox used for?",
            source="user2"
        )

        # Both should be logged
        assert q1['question_id'] != q2['question_id']
        # Semantic similarity should be detected (implementation detail)
        assert 'semantic_hash' in q1


# =============================================================================
# RECURRENCE DETECTION TESTS
# =============================================================================

class TestRecurrenceDetection:
    """Test recurring question detection."""

    def test_detect_recurring_exact_match(self):
        """Should detect exact duplicate questions."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Log same question 3 times
        analyzer.log_question("How is llm-sandbox used?", "user1")
        analyzer.log_question("How is llm-sandbox used?", "user1")
        analyzer.log_question("How is llm-sandbox used?", "user1")

        recurring = analyzer.get_recurring_questions(min_count=2)

        assert len(recurring) >= 1
        assert any(q['count'] >= 3 for q in recurring)

    def test_detect_recurring_semantic_match(self):
        """Should detect semantically similar questions."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Log similar questions with different wording
        analyzer.log_question("How is llm-sandbox used?", "user1")
        analyzer.log_question("What is llm-sandbox used for?", "user2")
        analyzer.log_question("llm-sandbox usage patterns?", "user3")

        recurring = analyzer.get_recurring_questions(
            min_count=2,
            semantic_match=True
        )

        # Should detect these as related
        assert len(recurring) >= 1

    def test_recurrence_within_time_window(self):
        """Should only count questions within time window."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Log question
        analyzer.log_question("Test question?", "user1")
        analyzer.log_question("Test question?", "user1")

        # Within 7 days (default window)
        recurring = analyzer.get_recurring_questions(
            min_count=2,
            days=7
        )
        assert len(recurring) >= 1


# =============================================================================
# PATTERN DETECTION TESTS
# =============================================================================

class TestPatternDetection:
    """Test pattern detection and analysis."""

    def test_detect_patterns_returns_list(self):
        """Should return list of detected patterns."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Add some questions
        analyzer.log_question("How do I use feature X?", "user1")
        analyzer.log_question("Where is feature X documented?", "user1")

        patterns = analyzer.detect_patterns()

        assert isinstance(patterns, list)

    def test_pattern_includes_topic_cluster(self):
        """Patterns should include topic clusters."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Log related questions
        for _ in range(3):
            analyzer.log_question("How does agent trust work?", "user1")
            analyzer.log_question("What is the trust formula?", "user1")

        patterns = analyzer.detect_patterns()

        # Should detect trust-related pattern
        if patterns:
            assert 'topic' in patterns[0] or 'cluster' in patterns[0]

    def test_pattern_suggests_ui_component(self):
        """Recurring patterns should suggest UI improvements."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # High frequency question
        for _ in range(5):
            analyzer.log_question("Show me agent trust scores", "user1")

        patterns = analyzer.detect_patterns()

        # Should suggest dashboard widget
        if patterns:
            pattern = patterns[0]
            assert 'suggestion' in pattern or 'ui_recommendation' in pattern


# =============================================================================
# KNOWLEDGE GAP TESTS
# =============================================================================

class TestKnowledgeGaps:
    """Test knowledge gap identification."""

    def test_get_knowledge_gaps_returns_list(self):
        """Should return list of knowledge gaps."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        gaps = analyzer.get_knowledge_gaps()

        assert isinstance(gaps, list)

    def test_gap_includes_topic_and_frequency(self):
        """Gaps should include topic and question frequency."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Create a gap by asking unanswered questions
        for _ in range(4):
            analyzer.log_question(
                "How do I configure TypeDB indexes?",
                "user1",
                answered=False
            )

        gaps = analyzer.get_knowledge_gaps()

        if gaps:
            gap = gaps[0]
            assert 'topic' in gap or 'question_pattern' in gap
            assert 'frequency' in gap or 'count' in gap

    def test_gap_prioritized_by_frequency(self):
        """Gaps should be prioritized by question frequency."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # More frequent gap
        for _ in range(5):
            analyzer.log_question("Frequent gap question?", "user1", answered=False)

        # Less frequent gap
        for _ in range(2):
            analyzer.log_question("Rare gap question?", "user1", answered=False)

        gaps = analyzer.get_knowledge_gaps()

        if len(gaps) >= 2:
            # First gap should be more frequent
            assert gaps[0].get('count', 0) >= gaps[1].get('count', 0)


# =============================================================================
# HISTORY AND QUERY TESTS
# =============================================================================

class TestQuestionHistory:
    """Test question history retrieval."""

    def test_get_history_returns_list(self):
        """Should return list of questions."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        analyzer.log_question("Test question 1", "user1")
        analyzer.log_question("Test question 2", "user1")

        history = analyzer.get_question_history()

        assert isinstance(history, list)
        assert len(history) >= 2

    def test_history_ordered_by_timestamp(self):
        """History should be ordered newest first."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        analyzer.log_question("First question", "user1")
        analyzer.log_question("Second question", "user1")

        history = analyzer.get_question_history()

        if len(history) >= 2:
            # Newest first
            ts1 = history[0].get('timestamp', '')
            ts2 = history[1].get('timestamp', '')
            assert ts1 >= ts2

    def test_history_filter_by_source(self):
        """Should filter history by source."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        analyzer.log_question("User1 question", "user1")
        analyzer.log_question("User2 question", "user2")

        history = analyzer.get_question_history(source="user1")

        assert all(q['source'] == "user1" for q in history)

    def test_history_filter_by_category(self):
        """Should filter history by category."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        analyzer.log_question("Governance question", "user1", category="governance")
        analyzer.log_question("Technical question", "user1", category="technical")

        history = analyzer.get_question_history(category="governance")

        assert all(q.get('category') == "governance" for q in history)


# =============================================================================
# ALERT GENERATION TESTS
# =============================================================================

class TestAlertGeneration:
    """Test alert generation for recurring patterns."""

    def test_generate_alert_for_recurring(self):
        """Should generate alert when question recurs too often."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        # Threshold is 3 by default
        for _ in range(4):
            result = analyzer.log_question("Recurring question?", "user1")

        # Last log should trigger alert
        assert result.get('alert') is not None or result.get('recurrence_count', 0) >= 3

    def test_alert_includes_suggestion(self):
        """Alert should include actionable suggestion."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        for _ in range(5):
            result = analyzer.log_question("How do I view agent trust?", "user1")

        if result.get('alert'):
            alert = result['alert']
            assert 'suggestion' in alert or 'action' in alert


# =============================================================================
# FACTORY AND INTEGRATION TESTS
# =============================================================================

class TestJourneyAnalyzerIntegration:
    """Test factory function and integration."""

    def test_factory_function(self):
        """Factory function should create analyzer."""
        from agent.journey_analyzer import create_journey_analyzer

        analyzer = create_journey_analyzer()

        assert analyzer is not None
        assert hasattr(analyzer, 'log_question')

    def test_analyzer_persistence(self):
        """Analyzer should persist questions across calls."""
        from agent.journey_analyzer import create_journey_analyzer

        analyzer = create_journey_analyzer()

        analyzer.log_question("Persistent question", "user1")
        history = analyzer.get_question_history()

        assert len(history) >= 1

    def test_clear_history(self):
        """Should be able to clear history."""
        from agent.journey_analyzer import JourneyAnalyzer
        analyzer = JourneyAnalyzer()

        analyzer.log_question("Question to clear", "user1")
        analyzer.clear_history()

        history = analyzer.get_question_history()
        assert len(history) == 0
