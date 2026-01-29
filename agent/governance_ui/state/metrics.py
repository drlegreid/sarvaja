"""
Session Metrics State (GAP-SESSION-METRICS-UI)
===============================================
State properties and transforms for session metrics view.

Per RULE-012: DSP Semantic Code Structure
Per SESSION-METRICS-01-v1: Session analytics

Created: 2026-01-29
"""

from typing import Dict, Any


def get_metrics_initial_state() -> Dict[str, Any]:
    """Return initial state properties for session metrics view.

    Returns:
        Dict of state properties to merge into initial state.
    """
    return {
        # Summary data
        'metrics_data': None,
        'metrics_loading': False,
        'metrics_error': '',

        # Days filter
        'metrics_days_filter': 5,
        'metrics_days_options': [5, 7, 14, 30],

        # Tab navigation
        'metrics_active_tab': 'summary',

        # Search
        'metrics_search_query': '',
        'metrics_search_results': [],
        'metrics_search_loading': False,
        'metrics_search_total': 0,

        # Timeline
        'metrics_timeline': [],
        'metrics_timeline_loading': False,
    }
