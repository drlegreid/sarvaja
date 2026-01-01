"""
Journey Pattern Analyzer Functions (GAP-FILE-006)
==================================================
Journey pattern analyzer for P9.7.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

# Singleton journey analyzer instance
_journey_analyzer_instance = None


def get_journey_analyzer():
    """
    Get or create singleton JourneyAnalyzer instance.

    Returns:
        JourneyAnalyzer instance
    """
    global _journey_analyzer_instance
    if _journey_analyzer_instance is None:
        from agent.journey_analyzer import create_journey_analyzer
        _journey_analyzer_instance = create_journey_analyzer()
    return _journey_analyzer_instance


def log_journey_question(
    question: str,
    source: str,
    category: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    answered: bool = True
) -> Dict[str, Any]:
    """
    Log a governance question for pattern analysis.

    Args:
        question: Question text
        source: Source of question (user, agent, etc.)
        category: Optional category tag
        context: Optional context dictionary
        answered: Whether the question was answered

    Returns:
        Question record with ID and recurrence info
    """
    analyzer = get_journey_analyzer()
    return analyzer.log_question(question, source, category, context, answered)


def get_recurring_questions(
    min_count: int = 2,
    days: Optional[int] = None,
    semantic_match: bool = False
) -> List[Dict[str, Any]]:
    """
    Get questions that recur frequently.

    Args:
        min_count: Minimum occurrences to be considered recurring
        days: Time window in days
        semantic_match: Whether to use semantic matching

    Returns:
        List of recurring questions with counts
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_recurring_questions(min_count, days, semantic_match)


def get_journey_patterns() -> List[Dict[str, Any]]:
    """
    Detect patterns in question history.

    Returns:
        List of detected patterns with topics and suggestions
    """
    analyzer = get_journey_analyzer()
    return analyzer.detect_patterns()


def get_knowledge_gaps() -> List[Dict[str, Any]]:
    """
    Identify knowledge gaps from unanswered questions.

    Returns:
        List of knowledge gaps with frequency and topics
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_knowledge_gaps()


def get_question_history(
    limit: int = 50,
    source: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get question history with optional filters.

    Args:
        limit: Maximum questions to return
        source: Filter by source
        category: Filter by category

    Returns:
        List of questions (newest first)
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_question_history(limit, source, category)
