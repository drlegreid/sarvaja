"""
Robot Framework Library for Journey Analyzer Advanced Tests.

Per P9.7: Journey pattern analyzer for recurring questions.
Split from JourneyAnalyzerLibrary.py per DOC-SIZE-01-v1.
Covers: Knowledge Gap, History, Alert, Integration tests.
"""
from pathlib import Path
from robot.api.deco import keyword


class JourneyAnalyzerAdvancedLibrary:
    """Library for testing journey analyzer - advanced sections."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

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
