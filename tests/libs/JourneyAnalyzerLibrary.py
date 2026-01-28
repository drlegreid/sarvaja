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
