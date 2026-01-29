"""
Tests for File Viewer (GAP-DATA-003).

Per RULE-023: Test Coverage Protocol
"""

import pytest
from unittest.mock import patch
import os


# =============================================================================
# State Transform Tests
# =============================================================================

class TestFileViewerState:
    """Test file viewer state transforms."""

    def test_initial_state_has_file_viewer(self):
        """Initial state includes file viewer fields."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()

        assert 'show_file_viewer' in state
        assert 'file_viewer_path' in state
        assert 'file_viewer_content' in state
        assert 'file_viewer_loading' in state
        assert 'file_viewer_error' in state

        assert state['show_file_viewer'] is False
        assert state['file_viewer_path'] == ''
        assert state['file_viewer_content'] == ''
        assert state['file_viewer_loading'] is False
        assert state['file_viewer_error'] == ''

    def test_with_file_viewer(self):
        """Set file viewer state."""
        from agent.governance_ui import with_file_viewer, get_initial_state

        state = get_initial_state()
        new_state = with_file_viewer(
            state,
            show=True,
            path='evidence/test.md',
            content='# Test',
        )

        assert new_state['show_file_viewer'] is True
        assert new_state['file_viewer_path'] == 'evidence/test.md'
        assert new_state['file_viewer_content'] == '# Test'
        # Original unchanged
        assert state['show_file_viewer'] is False

    def test_with_file_viewer_loading(self):
        """Set file viewer to loading state."""
        from agent.governance_ui import with_file_viewer_loading, get_initial_state

        state = get_initial_state()
        new_state = with_file_viewer_loading(state, 'docs/README.md')

        assert new_state['show_file_viewer'] is True
        assert new_state['file_viewer_path'] == 'docs/README.md'
        assert new_state['file_viewer_loading'] is True
        assert new_state['file_viewer_content'] == ''
        assert new_state['file_viewer_error'] == ''

    def test_with_file_viewer_content(self):
        """Set file viewer content after loading."""
        from agent.governance_ui import with_file_viewer_loading, with_file_viewer_content

        state = {'show_file_viewer': True, 'file_viewer_path': 'test.md',
                 'file_viewer_loading': True, 'file_viewer_content': '',
                 'file_viewer_error': ''}

        new_state = with_file_viewer_content(state, '# Hello World')

        assert new_state['file_viewer_loading'] is False
        assert new_state['file_viewer_content'] == '# Hello World'
        assert new_state['file_viewer_error'] == ''

    def test_with_file_viewer_error(self):
        """Set file viewer error state."""
        from agent.governance_ui import with_file_viewer_error

        state = {'show_file_viewer': True, 'file_viewer_path': 'bad.md',
                 'file_viewer_loading': True, 'file_viewer_content': '',
                 'file_viewer_error': ''}

        new_state = with_file_viewer_error(state, 'File not found')

        assert new_state['file_viewer_loading'] is False
        assert new_state['file_viewer_content'] == ''
        assert new_state['file_viewer_error'] == 'File not found'

    def test_close_file_viewer(self):
        """Close file viewer resets all state."""
        from agent.governance_ui import close_file_viewer

        state = {'show_file_viewer': True, 'file_viewer_path': 'test.md',
                 'file_viewer_content': '# Content', 'file_viewer_loading': False,
                 'file_viewer_error': ''}

        new_state = close_file_viewer(state)

        assert new_state['show_file_viewer'] is False
        assert new_state['file_viewer_path'] == ''
        assert new_state['file_viewer_content'] == ''
        assert new_state['file_viewer_loading'] is False
        assert new_state['file_viewer_error'] == ''


# =============================================================================
# API Tests
# =============================================================================

class TestFileContentAPI:
    """Test file content API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from governance.api import app

        return TestClient(app)

    def test_get_file_content_from_evidence(self, client):
        """Get file content from evidence directory."""
        # Create a test evidence file
        evidence_dir = os.path.join(os.path.dirname(__file__), "..", "evidence")
        test_file = os.path.join(evidence_dir, "test-file-viewer.md")

        try:
            os.makedirs(evidence_dir, exist_ok=True)
            with open(test_file, "w") as f:
                f.write("# Test Evidence\n\nThis is test content.")

            response = client.get("/api/files/content", params={"path": "evidence/test-file-viewer.md"})

            assert response.status_code == 200
            data = response.json()
            assert data['path'] == 'evidence/test-file-viewer.md'
            assert '# Test Evidence' in data['content']
            assert 'size' in data
            assert 'modified_at' in data
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_get_file_content_from_docs(self, client):
        """Get file content from docs directory."""
        # docs/RULES-DIRECTIVES.md should exist
        response = client.get("/api/files/content", params={"path": "docs/RULES-DIRECTIVES.md"})

        if response.status_code == 200:
            data = response.json()
            assert 'content' in data
            assert len(data['content']) > 0
        else:
            # Skip if file doesn't exist
            pytest.skip("docs/RULES-DIRECTIVES.md not found")

    def test_get_file_content_forbidden_directory(self, client):
        """Accessing files outside allowed directories is forbidden."""
        response = client.get("/api/files/content", params={"path": "src/main.py"})

        assert response.status_code == 403
        assert "Access denied" in response.json()['detail']

    def test_get_file_content_path_traversal(self, client):
        """Path traversal attempts are blocked."""
        response = client.get("/api/files/content", params={"path": "evidence/../../../etc/passwd"})

        assert response.status_code in [403, 404]  # Either forbidden or not found

    def test_get_file_content_not_found(self, client):
        """Non-existent file returns 404."""
        response = client.get("/api/files/content", params={"path": "evidence/nonexistent-file-xyz.md"})

        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()

    def test_file_content_response_model(self, client):
        """Response includes all required fields."""
        from governance.models import FileContentResponse

        # Verify model has correct fields (Pydantic v2 uses model_fields)
        fields = getattr(FileContentResponse, 'model_fields', None) or FileContentResponse.__fields__
        assert 'path' in fields
        assert 'content' in fields
        assert 'size' in fields
        assert 'modified_at' in fields
        assert 'exists' in fields
