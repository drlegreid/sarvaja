"""
Journey Pattern Analyzer State (P9.7)
=====================================
State transforms and helpers for journey pattern analysis.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any

from .constants import GAP_PRIORITY_COLORS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_recurring_questions(
    state: Dict[str, Any],
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add recurring questions to state.

    Args:
        state: Current state
        questions: List of recurring questions

    Returns:
        New state with recurring_questions
    """
    return {**state, 'recurring_questions': questions}


def with_journey_patterns(
    state: Dict[str, Any],
    patterns: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add journey patterns to state.

    Args:
        state: Current state
        patterns: List of detected patterns

    Returns:
        New state with journey_patterns
    """
    return {**state, 'journey_patterns': patterns}


def with_knowledge_gaps(
    state: Dict[str, Any],
    gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add knowledge gaps to state.

    Args:
        state: Current state
        gaps: List of knowledge gaps

    Returns:
        New state with knowledge_gaps
    """
    return {**state, 'knowledge_gaps': gaps}


def with_question_history(
    state: Dict[str, Any],
    history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add question history to state.

    Args:
        state: Current state
        history: Question history list

    Returns:
        New state with question_history
    """
    return {**state, 'question_history': history}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_gap_priority_color(priority: str) -> str:
    """
    Get color for knowledge gap priority.

    Args:
        priority: Priority level (high, medium, low)

    Returns:
        Vuetify color string
    """
    return GAP_PRIORITY_COLORS.get(priority.lower(), 'grey')


def format_recurring_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format recurring question for display.

    Pure function: same input -> same output.

    Args:
        question: Recurring question dict

    Returns:
        Formatted question for UI
    """
    count = question.get('count', 0)

    # Determine urgency color based on count
    if count >= 5:
        urgency_color = 'error'
        urgency = 'critical'
    elif count >= 3:
        urgency_color = 'warning'
        urgency = 'high'
    else:
        urgency_color = 'info'
        urgency = 'moderate'

    return {
        'question': question.get('question', ''),
        'count': count,
        'urgency': urgency,
        'urgency_color': urgency_color,
        'sources': question.get('sources', []),
        'first_asked': question.get('first_asked', ''),
        'last_asked': question.get('last_asked', ''),
    }


def format_knowledge_gap(gap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format knowledge gap for display.

    Pure function: same input -> same output.

    Args:
        gap: Knowledge gap dict

    Returns:
        Formatted gap for UI
    """
    priority = gap.get('priority', 'medium')

    return {
        'topic': gap.get('topic', 'Unknown'),
        'question_pattern': gap.get('question_pattern', ''),
        'count': gap.get('count', 0),
        'priority': priority,
        'priority_color': get_gap_priority_color(priority),
        'sources': gap.get('sources', []),
    }


def format_journey_pattern(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format journey pattern for display.

    Pure function: same input -> same output.

    Args:
        pattern: Pattern dict from analyzer

    Returns:
        Formatted pattern for UI
    """
    return {
        'topic': pattern.get('topic', 'Unknown'),
        'question_count': pattern.get('question_count', 0),
        'questions': pattern.get('questions', [])[:3],  # Show max 3
        'suggestion': pattern.get('suggestion', ''),
        'ui_recommendation': pattern.get('ui_recommendation', {}),
        'component': pattern.get('ui_recommendation', {}).get('component', 'InfoWidget'),
        'location': pattern.get('ui_recommendation', {}).get('location', 'sidebar'),
    }
