"""
File Viewer State (GAP-DATA-003)
================================
State transforms for file viewer dialog.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, Any


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_file_viewer(
    state: Dict[str, Any],
    show: bool = True,
    path: str = '',
    content: str = '',
    loading: bool = False,
    error: str = ''
) -> Dict[str, Any]:
    """
    Update file viewer state.

    Args:
        state: Current state
        show: Whether to show the dialog
        path: File path being viewed
        content: File content
        loading: Loading state
        error: Error message if any

    Returns:
        New state with file viewer updates
    """
    return {
        **state,
        'show_file_viewer': show,
        'file_viewer_path': path,
        'file_viewer_content': content,
        'file_viewer_html': '',
        'file_viewer_loading': loading,
        'file_viewer_error': error,
    }


def with_file_viewer_loading(state: Dict[str, Any], path: str) -> Dict[str, Any]:
    """Set file viewer to loading state for given path."""
    return {
        **state,
        'show_file_viewer': True,
        'file_viewer_path': path,
        'file_viewer_content': '',
        'file_viewer_html': '',
        'file_viewer_loading': True,
        'file_viewer_error': '',
    }


def with_file_viewer_content(state: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Set file viewer content after loading."""
    return {
        **state,
        'file_viewer_loading': False,
        'file_viewer_content': content,
        'file_viewer_error': '',
    }


def with_file_viewer_error(state: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Set file viewer error state."""
    return {
        **state,
        'file_viewer_loading': False,
        'file_viewer_content': '',
        'file_viewer_error': error,
    }


def close_file_viewer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Close file viewer dialog."""
    return {
        **state,
        'show_file_viewer': False,
        'file_viewer_path': '',
        'file_viewer_content': '',
        'file_viewer_html': '',
        'file_viewer_loading': False,
        'file_viewer_error': '',
    }
