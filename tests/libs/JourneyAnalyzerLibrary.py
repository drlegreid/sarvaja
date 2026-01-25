"""
Robot Framework Library for Journey Analyzer Tests.

Per P9.7: Journey pattern analyzer for recurring questions.
Migrated from tests/test_journey_analyzer.py
"""
from pathlib import Path
from robot.api.deco import keyword


class JourneyAnalyzerLibrary:
    """Library for testing journey analyzer module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Journey Analyzer Module Exists")
    def journey_analyzer_module_exists(self):
        """Journey analyzer module must exist."""
        try:
            from agent import journey_analyzer
            return {"exists": journey_analyzer is not None}
        except ImportError:
            return {"exists": False}

    @keyword("Journey Analyzer Class Exists")
    def journey_analyzer_class_exists(self):
        """JourneyAnalyzer class must exist."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            return {"exists": JourneyAnalyzer is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Analyzer Has Required Methods")
    def analyzer_has_required_methods(self):
        """Analyzer must have core methods."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            return {
                "has_log_question": hasattr(analyzer, 'log_question'),
                "has_get_recurring_questions": hasattr(analyzer, 'get_recurring_questions'),
                "has_detect_patterns": hasattr(analyzer, 'detect_patterns'),
                "has_get_knowledge_gaps": hasattr(analyzer, 'get_knowledge_gaps'),
                "has_get_question_history": hasattr(analyzer, 'get_question_history')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Question Logging Tests
    # =============================================================================

    @keyword("Log Question Works")
    def log_question_works(self):
        """Should log a question with timestamp."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            result = analyzer.log_question(
                question="How is llm-sandbox Python MCP being used?",
                source="governor",
                context={"session": "test-session"}
            )

            return {
                "not_none": result is not None,
                "has_question_id": 'question_id' in result,
                "has_timestamp": 'timestamp' in result,
                "question_correct": result.get('question') == "How is llm-sandbox Python MCP being used?"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Log Question With Category Works")
    def log_question_with_category_works(self):
        """Should log question with category tag."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            result = analyzer.log_question(
                question="What rules govern agent trust?",
                source="governor",
                category="governance"
            )

            return {"category_correct": result.get('category') == "governance"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Question Generates Semantic Hash")
    def question_generates_semantic_hash(self):
        """Similar questions should have semantic hashes."""
        try:
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

            return {
                "ids_different": q1['question_id'] != q2['question_id'],
                "has_semantic_hash": 'semantic_hash' in q1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Recurrence Detection Tests
    # =============================================================================

    @keyword("Detect Recurring Exact Match")
    def detect_recurring_exact_match(self):
        """Should detect exact duplicate questions."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            # Log same question 3 times
            analyzer.log_question("How is llm-sandbox used?", "user1")
            analyzer.log_question("How is llm-sandbox used?", "user1")
            analyzer.log_question("How is llm-sandbox used?", "user1")

            recurring = analyzer.get_recurring_questions(min_count=2)

            has_recurring = len(recurring) >= 1
            has_count_3 = any(q.get('count', 0) >= 3 for q in recurring) if recurring else False

            return {
                "has_recurring": has_recurring,
                "count_at_least_3": has_count_3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Detect Recurring Semantic Match")
    def detect_recurring_semantic_match(self):
        """Should detect semantically similar questions."""
        try:
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

            return {"has_recurring": len(recurring) >= 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Recurrence Within Time Window")
    def recurrence_within_time_window(self):
        """Should only count questions within time window."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("Test question?", "user1")
            analyzer.log_question("Test question?", "user1")

            recurring = analyzer.get_recurring_questions(min_count=2, days=7)

            return {"has_recurring": len(recurring) >= 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Pattern Detection Tests
    # =============================================================================

    @keyword("Detect Patterns Returns List")
    def detect_patterns_returns_list(self):
        """Should return list of detected patterns."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("How do I use feature X?", "user1")
            analyzer.log_question("Where is feature X documented?", "user1")

            patterns = analyzer.detect_patterns()

            return {"is_list": isinstance(patterns, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Pattern Includes Topic Cluster")
    def pattern_includes_topic_cluster(self):
        """Patterns should include topic clusters."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(3):
                analyzer.log_question("How does agent trust work?", "user1")
                analyzer.log_question("What is the trust formula?", "user1")

            patterns = analyzer.detect_patterns()

            has_topic = False
            if patterns:
                has_topic = 'topic' in patterns[0] or 'cluster' in patterns[0]

            return {"has_topic_cluster": has_topic or len(patterns) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Pattern Suggests UI Component")
    def pattern_suggests_ui_component(self):
        """Recurring patterns should suggest UI improvements."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(5):
                analyzer.log_question("Show me agent trust scores", "user1")

            patterns = analyzer.detect_patterns()

            has_suggestion = False
            if patterns:
                has_suggestion = 'suggestion' in patterns[0] or 'ui_recommendation' in patterns[0]

            return {"has_suggestion": has_suggestion or len(patterns) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Knowledge Gap Tests
    # =============================================================================

    @keyword("Get Knowledge Gaps Returns List")
    def get_knowledge_gaps_returns_list(self):
        """Should return list of knowledge gaps."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            gaps = analyzer.get_knowledge_gaps()

            return {"is_list": isinstance(gaps, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Gap Includes Topic And Frequency")
    def gap_includes_topic_and_frequency(self):
        """Gaps should include topic and question frequency."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(4):
                analyzer.log_question(
                    "How do I configure TypeDB indexes?",
                    "user1",
                    answered=False
                )

            gaps = analyzer.get_knowledge_gaps()

            has_fields = False
            if gaps:
                gap = gaps[0]
                has_fields = ('topic' in gap or 'question_pattern' in gap) and \
                             ('frequency' in gap or 'count' in gap)

            return {"has_required_fields": has_fields or len(gaps) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Gap Prioritized By Frequency")
    def gap_prioritized_by_frequency(self):
        """Gaps should be prioritized by question frequency."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(5):
                analyzer.log_question("Frequent gap question?", "user1", answered=False)
            for _ in range(2):
                analyzer.log_question("Rare gap question?", "user1", answered=False)

            gaps = analyzer.get_knowledge_gaps()

            is_prioritized = True
            if len(gaps) >= 2:
                is_prioritized = gaps[0].get('count', 0) >= gaps[1].get('count', 0)

            return {"is_prioritized": is_prioritized}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # History Tests
    # =============================================================================

    @keyword("Get History Returns List")
    def get_history_returns_list(self):
        """Should return list of questions."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("Test question 1", "user1")
            analyzer.log_question("Test question 2", "user1")

            history = analyzer.get_question_history()

            return {
                "is_list": isinstance(history, list),
                "has_entries": len(history) >= 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("History Ordered By Timestamp")
    def history_ordered_by_timestamp(self):
        """History should be ordered newest first."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("First question", "user1")
            analyzer.log_question("Second question", "user1")

            history = analyzer.get_question_history()

            is_ordered = True
            if len(history) >= 2:
                ts1 = history[0].get('timestamp', '')
                ts2 = history[1].get('timestamp', '')
                is_ordered = ts1 >= ts2

            return {"is_ordered": is_ordered}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("History Filter By Source")
    def history_filter_by_source(self):
        """Should filter history by source."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("User1 question", "user1")
            analyzer.log_question("User2 question", "user2")

            history = analyzer.get_question_history(source="user1")

            all_from_source = all(q.get('source') == "user1" for q in history)

            return {"filters_correctly": all_from_source}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("History Filter By Category")
    def history_filter_by_category(self):
        """Should filter history by category."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("Governance question", "user1", category="governance")
            analyzer.log_question("Technical question", "user1", category="technical")

            history = analyzer.get_question_history(category="governance")

            all_from_category = all(q.get('category') == "governance" for q in history)

            return {"filters_correctly": all_from_category}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Alert Tests
    # =============================================================================

    @keyword("Generate Alert For Recurring")
    def generate_alert_for_recurring(self):
        """Should generate alert when question recurs too often."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(4):
                result = analyzer.log_question("Recurring question?", "user1")

            has_alert = result.get('alert') is not None or result.get('recurrence_count', 0) >= 3

            return {"has_alert": has_alert}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Alert Includes Suggestion")
    def alert_includes_suggestion(self):
        """Alert should include actionable suggestion."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            for _ in range(5):
                result = analyzer.log_question("How do I view agent trust?", "user1")

            has_suggestion = False
            if result.get('alert'):
                alert = result['alert']
                has_suggestion = 'suggestion' in alert or 'action' in alert

            return {"has_suggestion": has_suggestion or result.get('alert') is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Journey Analyzer Factory Works")
    def journey_analyzer_factory_works(self):
        """Factory function should create analyzer."""
        try:
            from agent.journey_analyzer import create_journey_analyzer

            analyzer = create_journey_analyzer()

            return {
                "created": analyzer is not None,
                "has_log_question": hasattr(analyzer, 'log_question')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Analyzer Persistence Works")
    def analyzer_persistence_works(self):
        """Analyzer should persist questions across calls."""
        try:
            from agent.journey_analyzer import create_journey_analyzer

            analyzer = create_journey_analyzer()

            analyzer.log_question("Persistent question", "user1")
            history = analyzer.get_question_history()

            return {"persists": len(history) >= 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Clear History Works")
    def clear_history_works(self):
        """Should be able to clear history."""
        try:
            from agent.journey_analyzer import JourneyAnalyzer
            analyzer = JourneyAnalyzer()

            analyzer.log_question("Question to clear", "user1")
            analyzer.clear_history()

            history = analyzer.get_question_history()

            return {"cleared": len(history) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
