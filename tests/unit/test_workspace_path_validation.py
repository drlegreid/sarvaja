"""TDD Tests: Path traversal prevention in detect_workspace_type.

Gap: POST /workspace-types/detect accepts any filesystem path.
Fix: Validate path is within allowed project roots.
"""
from unittest.mock import patch

import pytest


class TestWorkspacePathValidation:
    """detect_workspace_type rejects dangerous paths."""

    @patch("governance.routes.projects.crud.detect_project_type")
    @patch("governance.routes.projects.crud.get_workspace_type")
    def test_normal_path_accepted(self, mock_get_wt, mock_detect):
        """Normal project paths work fine."""
        mock_detect.return_value = "python-governance"
        mock_get_wt.return_value = None

        from governance.routes.projects.crud import detect_workspace_type
        result = detect_workspace_type(path="/home/user/project")
        assert result["detected_type"] == "python-governance"

    def test_etc_path_rejected(self):
        """Sensitive system paths like /etc/ are rejected."""
        from governance.routes.projects.crud import detect_workspace_type
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            detect_workspace_type(path="/etc/passwd")
        assert exc_info.value.status_code == 400
        assert "path" in str(exc_info.value.detail).lower()

    def test_root_path_rejected(self):
        """Root filesystem scan is rejected."""
        from governance.routes.projects.crud import detect_workspace_type
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            detect_workspace_type(path="/")
        assert exc_info.value.status_code == 400

    def test_proc_path_rejected(self):
        """/proc paths are rejected."""
        from governance.routes.projects.crud import detect_workspace_type
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            detect_workspace_type(path="/proc/1/environ")
        assert exc_info.value.status_code == 400

    def test_relative_path_traversal_rejected(self):
        """Path with .. traversal is rejected."""
        from governance.routes.projects.crud import detect_workspace_type
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            detect_workspace_type(path="/home/user/../../etc/shadow")
        assert exc_info.value.status_code == 400
