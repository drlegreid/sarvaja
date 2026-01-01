"""
Executive Reports State (GAP-UI-044)
====================================
State transforms and helpers for executive reports.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

from .constants import EXECUTIVE_STATUS_COLORS, SECTION_STATUS_COLORS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_executive_report(
    state: Dict[str, Any],
    report: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add executive report to state.

    Args:
        state: Current state
        report: Executive report data from API

    Returns:
        New state with executive_report
    """
    return {**state, 'executive_report': report}


def with_executive_loading(
    state: Dict[str, Any],
    loading: bool = True
) -> Dict[str, Any]:
    """
    Pure transform: set executive report loading state.

    Args:
        state: Current state
        loading: Loading state

    Returns:
        New state with executive_loading
    """
    return {**state, 'executive_loading': loading}


def with_executive_period(
    state: Dict[str, Any],
    period: str
) -> Dict[str, Any]:
    """
    Pure transform: set executive report period filter.

    Args:
        state: Current state
        period: Period (week, month, quarter)

    Returns:
        New state with executive_period
    """
    return {**state, 'executive_period': period}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_executive_status_color(status: str) -> str:
    """
    Get color for executive report overall status.

    Args:
        status: Overall status (healthy, warning, critical)

    Returns:
        Vuetify color string
    """
    return EXECUTIVE_STATUS_COLORS.get(status.lower(), 'grey')


def get_section_status_color(status: str) -> str:
    """
    Get color for section status.

    Args:
        status: Section status (success, warning, error)

    Returns:
        Vuetify color string
    """
    return SECTION_STATUS_COLORS.get(status.lower(), 'grey')


def _get_section_icon(title: str) -> str:
    """Get icon for section title."""
    title_lower = title.lower()
    if 'summary' in title_lower:
        return 'mdi-clipboard-text'
    elif 'compliance' in title_lower:
        return 'mdi-check-decagram'
    elif 'risk' in title_lower:
        return 'mdi-alert-circle'
    elif 'alignment' in title_lower:
        return 'mdi-compass'
    elif 'resource' in title_lower:
        return 'mdi-account-group'
    elif 'recommendation' in title_lower:
        return 'mdi-lightbulb'
    elif 'objective' in title_lower:
        return 'mdi-target'
    else:
        return 'mdi-file-document'


def format_executive_section(section: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format executive report section for display.

    Pure function: same input -> same output.

    Args:
        section: Section dict from API

    Returns:
        Formatted section for UI
    """
    status = section.get('status', 'success')
    return {
        'title': section.get('title', 'Section'),
        'content': section.get('content', ''),
        'status': status,
        'status_color': get_section_status_color(status),
        'metrics': section.get('metrics', {}),
        'icon': _get_section_icon(section.get('title', '')),
    }


def format_executive_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format executive report for display.

    Pure function: same input -> same output.

    Args:
        report: Report dict from API

    Returns:
        Formatted report for UI
    """
    overall_status = report.get('overall_status', 'healthy')
    sections = [format_executive_section(s) for s in report.get('sections', [])]

    return {
        'report_id': report.get('report_id', 'Unknown'),
        'generated_at': report.get('generated_at', ''),
        'period': report.get('period', 'Unknown Period'),
        'overall_status': overall_status,
        'status_color': get_executive_status_color(overall_status),
        'sections': sections,
        'metrics_summary': report.get('metrics_summary', {}),
    }
