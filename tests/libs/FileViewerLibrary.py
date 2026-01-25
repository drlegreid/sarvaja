"""
Robot Framework Library for File Viewer Tests.

Per GAP-DATA-003: File viewer functionality.
Migrated from tests/test_file_viewer.py
"""
from robot.api.deco import keyword


class FileViewerLibrary:
    """Library for testing file viewer state transforms."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # State Transform Tests
    # =============================================================================

    @keyword("Initial State Has File Viewer Fields")
    def initial_state_has_file_viewer_fields(self):
        """Initial state includes file viewer fields."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()

            return {
                "has_show": 'show_file_viewer' in state,
                "has_path": 'file_viewer_path' in state,
                "has_content": 'file_viewer_content' in state,
                "has_loading": 'file_viewer_loading' in state,
                "has_error": 'file_viewer_error' in state,
                "show_false": state.get('show_file_viewer') is False,
                "path_empty": state.get('file_viewer_path') == '',
                "content_empty": state.get('file_viewer_content') == '',
                "loading_false": state.get('file_viewer_loading') is False,
                "error_empty": state.get('file_viewer_error') == ''
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With File Viewer Sets State")
    def with_file_viewer_sets_state(self):
        """Set file viewer state."""
        try:
            from agent.governance_ui import with_file_viewer, get_initial_state

            state = get_initial_state()
            new_state = with_file_viewer(
                state,
                show=True,
                path='evidence/test.md',
                content='# Test',
            )

            return {
                "show_true": new_state['show_file_viewer'] is True,
                "path_correct": new_state['file_viewer_path'] == 'evidence/test.md',
                "content_correct": new_state['file_viewer_content'] == '# Test',
                "original_unchanged": state['show_file_viewer'] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With File Viewer Loading Sets State")
    def with_file_viewer_loading_sets_state(self):
        """Set file viewer to loading state."""
        try:
            from agent.governance_ui import with_file_viewer_loading, get_initial_state

            state = get_initial_state()
            new_state = with_file_viewer_loading(state, 'docs/README.md')

            return {
                "show_true": new_state['show_file_viewer'] is True,
                "path_correct": new_state['file_viewer_path'] == 'docs/README.md',
                "loading_true": new_state['file_viewer_loading'] is True,
                "content_empty": new_state['file_viewer_content'] == '',
                "error_empty": new_state['file_viewer_error'] == ''
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With File Viewer Content Sets Content")
    def with_file_viewer_content_sets_content(self):
        """Set file viewer content after loading."""
        try:
            from agent.governance_ui import with_file_viewer_content

            state = {
                'show_file_viewer': True,
                'file_viewer_path': 'test.md',
                'file_viewer_loading': True,
                'file_viewer_content': '',
                'file_viewer_error': ''
            }

            new_state = with_file_viewer_content(state, '# Hello World')

            return {
                "loading_false": new_state['file_viewer_loading'] is False,
                "content_correct": new_state['file_viewer_content'] == '# Hello World',
                "error_empty": new_state['file_viewer_error'] == ''
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With File Viewer Error Sets Error")
    def with_file_viewer_error_sets_error(self):
        """Set file viewer error state."""
        try:
            from agent.governance_ui import with_file_viewer_error

            state = {
                'show_file_viewer': True,
                'file_viewer_path': 'bad.md',
                'file_viewer_loading': True,
                'file_viewer_content': '',
                'file_viewer_error': ''
            }

            new_state = with_file_viewer_error(state, 'File not found')

            return {
                "loading_false": new_state['file_viewer_loading'] is False,
                "content_empty": new_state['file_viewer_content'] == '',
                "error_correct": new_state['file_viewer_error'] == 'File not found'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Close File Viewer Resets State")
    def close_file_viewer_resets_state(self):
        """Close file viewer resets all state."""
        try:
            from agent.governance_ui import close_file_viewer

            state = {
                'show_file_viewer': True,
                'file_viewer_path': 'test.md',
                'file_viewer_content': '# Content',
                'file_viewer_loading': False,
                'file_viewer_error': ''
            }

            new_state = close_file_viewer(state)

            return {
                "show_false": new_state['show_file_viewer'] is False,
                "path_empty": new_state['file_viewer_path'] == '',
                "content_empty": new_state['file_viewer_content'] == '',
                "loading_false": new_state['file_viewer_loading'] is False,
                "error_empty": new_state['file_viewer_error'] == ''
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Response Model Tests
    # =============================================================================

    @keyword("File Content Response Model Has Fields")
    def file_content_response_model_has_fields(self):
        """Response model has correct fields."""
        try:
            from governance.api import FileContentResponse

            has_fields = hasattr(FileContentResponse, 'model_fields') or hasattr(FileContentResponse, '__fields__')
            if has_fields:
                fields = getattr(FileContentResponse, 'model_fields', None) or getattr(FileContentResponse, '__fields__', {})
                return {
                    "has_path": 'path' in fields,
                    "has_content": 'content' in fields,
                    "has_size": 'size' in fields,
                    "has_modified_at": 'modified_at' in fields,
                    "has_exists": 'exists' in fields
                }
            return {"skipped": True, "reason": "No model fields found"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
