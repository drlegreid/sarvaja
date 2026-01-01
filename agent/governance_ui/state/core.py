"""
Core State Transforms and Helpers
=================================
Base transforms for loading, error, navigation, and rule selection.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, Any, Optional

from .constants import (
    STATUS_COLORS,
    PRIORITY_COLORS,
    CATEGORY_ICONS,
    RISK_COLORS,
)


# =============================================================================
# PURE STATE TRANSFORMS
# =============================================================================

def with_loading(state: Dict[str, Any], loading: bool = True) -> Dict[str, Any]:
    """Return new state with loading flag set."""
    return {**state, 'is_loading': loading}


def with_error(state: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Return new state with error set."""
    return {**state, 'has_error': True, 'error_message': error}


def clear_error(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return new state with error cleared."""
    return {**state, 'has_error': False, 'error_message': ''}


def with_status(state: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Return new state with status message."""
    return {**state, 'status_message': message}


def with_active_view(state: Dict[str, Any], view: str) -> Dict[str, Any]:
    """Return new state with active view changed."""
    return {**state, 'active_view': view}


def with_selected_rule(state: Dict[str, Any], rule: Optional[Dict]) -> Dict[str, Any]:
    """Return new state with selected rule."""
    return {
        **state,
        'selected_rule': rule,
        'show_rule_detail': rule is not None,
    }


def with_rule_form(state: Dict[str, Any], mode: str = 'create', show: bool = True) -> Dict[str, Any]:
    """Return new state for rule form."""
    return {
        **state,
        'show_rule_form': show,
        'rule_form_mode': mode,
    }


def with_filters(
    state: Dict[str, Any],
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: str = ''
) -> Dict[str, Any]:
    """Return new state with filters applied."""
    return {
        **state,
        'rules_status_filter': status,
        'rules_category_filter': category,
        'rules_search_query': search,
    }


def with_sort(state: Dict[str, Any], column: str, ascending: bool = True) -> Dict[str, Any]:
    """Return new state with sort applied."""
    return {
        **state,
        'rules_sort_column': column,
        'rules_sort_asc': ascending,
    }


def with_impact_analysis(
    state: Dict[str, Any],
    rule_id: Optional[str] = None,
    analysis: Optional[Dict] = None,
    graph: Optional[Dict] = None,
    mermaid: str = ''
) -> Dict[str, Any]:
    """Return new state with impact analysis results."""
    return {
        **state,
        'impact_selected_rule': rule_id,
        'impact_analysis': analysis,
        'dependency_graph': graph,
        'mermaid_diagram': mermaid,
    }


def with_graph_view(state: Dict[str, Any], show_graph: bool = True) -> Dict[str, Any]:
    """Return new state with graph view toggle."""
    return {**state, 'show_graph_view': show_graph}


# =============================================================================
# UI HELPERS (Pure functions)
# =============================================================================

def get_status_color(status: str) -> str:
    """Get color for status (pure function)."""
    return STATUS_COLORS.get(status, 'grey')


def get_priority_color(priority: str) -> str:
    """Get color for priority (pure function)."""
    return PRIORITY_COLORS.get(priority, 'grey')


def get_category_icon(category: str) -> str:
    """Get icon for category (pure function)."""
    return CATEGORY_ICONS.get(category, 'mdi-file')


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level (pure function)."""
    return RISK_COLORS.get(risk_level, 'grey')


def format_rule_card(rule: Dict[str, Any]) -> Dict[str, str]:
    """
    Format rule data for card display.

    Pure function: same input -> same output.

    Args:
        rule: Rule dict

    Returns:
        Formatted card data
    """
    status = rule.get('status', 'unknown')
    rule_id = rule.get('rule_id') or rule.get('id', 'Unknown')
    return {
        'title': rule_id,
        'subtitle': rule.get('title') or rule.get('name', ''),
        'color': get_status_color(status),
        'icon': get_category_icon(rule.get('category', 'governance')),
    }


def format_impact_summary(impact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format impact analysis for display.

    Pure function: same input -> same output.

    Args:
        impact: Impact analysis dict

    Returns:
        Formatted summary for UI
    """
    return {
        'rule_id': impact.get('rule_id', 'Unknown'),
        'risk_level': impact.get('risk_level', 'LOW'),
        'risk_color': get_risk_color(impact.get('risk_level', 'LOW')),
        'total_affected': impact.get('total_affected', 0),
        'direct_dependents': len(impact.get('direct_dependents', [])),
        'dependencies': len(impact.get('dependencies', [])),
        'recommendation': impact.get('recommendation', ''),
        'critical_affected': impact.get('critical_rules_affected', []),
    }
