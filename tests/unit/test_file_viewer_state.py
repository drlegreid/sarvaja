"""
Unit tests for File Viewer State Transforms.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/file_viewer.py module.
Tests: with_file_viewer, with_file_viewer_loading, with_file_viewer_content,
       with_file_viewer_error, close_file_viewer.
"""

from agent.governance_ui.state.file_viewer import (
    with_file_viewer,
    with_file_viewer_loading,
    with_file_viewer_content,
    with_file_viewer_error,
    close_file_viewer,
)


# ── with_file_viewer ───────────────────────────────────────


class TestWithFileViewer:
    def test_defaults(self):
        state = {"existing": "value"}
        result = with_file_viewer(state)
        assert result["show_file_viewer"] is True
        assert result["file_viewer_path"] == ""
        assert result["file_viewer_content"] == ""
        assert result["file_viewer_html"] == ""
        assert result["file_viewer_loading"] is False
        assert result["file_viewer_error"] == ""
        assert result["existing"] == "value"

    def test_custom_values(self):
        result = with_file_viewer(
            {}, show=False, path="/tmp/f.py", content="code",
            loading=True, error="oops",
        )
        assert result["show_file_viewer"] is False
        assert result["file_viewer_path"] == "/tmp/f.py"
        assert result["file_viewer_content"] == "code"
        assert result["file_viewer_loading"] is True
        assert result["file_viewer_error"] == "oops"

    def test_does_not_mutate_original(self):
        original = {"key": "val"}
        result = with_file_viewer(original, path="test")
        assert "show_file_viewer" not in original
        assert result["file_viewer_path"] == "test"

    def test_preserves_existing_state(self):
        state = {"rules": [1, 2], "sessions": [3]}
        result = with_file_viewer(state, path="f.py")
        assert result["rules"] == [1, 2]
        assert result["sessions"] == [3]


# ── with_file_viewer_loading ──────────────────────────────


class TestWithFileViewerLoading:
    def test_sets_loading_state(self):
        result = with_file_viewer_loading({}, "/tmp/f.py")
        assert result["show_file_viewer"] is True
        assert result["file_viewer_path"] == "/tmp/f.py"
        assert result["file_viewer_content"] == ""
        assert result["file_viewer_html"] == ""
        assert result["file_viewer_loading"] is True
        assert result["file_viewer_error"] == ""

    def test_clears_previous_content(self):
        state = {"file_viewer_content": "old code", "file_viewer_error": "old err"}
        result = with_file_viewer_loading(state, "/new/path")
        assert result["file_viewer_content"] == ""
        assert result["file_viewer_error"] == ""

    def test_preserves_state(self):
        state = {"agents": ["a1"]}
        result = with_file_viewer_loading(state, "f.py")
        assert result["agents"] == ["a1"]


# ── with_file_viewer_content ──────────────────────────────


class TestWithFileViewerContent:
    def test_sets_content(self):
        result = with_file_viewer_content({}, "def main():\n    pass")
        assert result["file_viewer_content"] == "def main():\n    pass"
        assert result["file_viewer_loading"] is False
        assert result["file_viewer_error"] == ""

    def test_clears_loading(self):
        state = {"file_viewer_loading": True}
        result = with_file_viewer_content(state, "content")
        assert result["file_viewer_loading"] is False

    def test_clears_error(self):
        state = {"file_viewer_error": "previous error"}
        result = with_file_viewer_content(state, "content")
        assert result["file_viewer_error"] == ""


# ── with_file_viewer_error ─────────────────────────────────


class TestWithFileViewerError:
    def test_sets_error(self):
        result = with_file_viewer_error({}, "File not found")
        assert result["file_viewer_error"] == "File not found"
        assert result["file_viewer_loading"] is False
        assert result["file_viewer_content"] == ""

    def test_clears_loading(self):
        state = {"file_viewer_loading": True}
        result = with_file_viewer_error(state, "error")
        assert result["file_viewer_loading"] is False

    def test_clears_content(self):
        state = {"file_viewer_content": "old content"}
        result = with_file_viewer_error(state, "error")
        assert result["file_viewer_content"] == ""


# ── close_file_viewer ──────────────────────────────────────


class TestCloseFileViewer:
    def test_resets_all(self):
        state = {
            "show_file_viewer": True,
            "file_viewer_path": "/tmp/f.py",
            "file_viewer_content": "code",
            "file_viewer_html": "<p>rendered</p>",
            "file_viewer_loading": True,
            "file_viewer_error": "err",
        }
        result = close_file_viewer(state)
        assert result["show_file_viewer"] is False
        assert result["file_viewer_path"] == ""
        assert result["file_viewer_content"] == ""
        assert result["file_viewer_html"] == ""
        assert result["file_viewer_loading"] is False
        assert result["file_viewer_error"] == ""

    def test_preserves_other_state(self):
        state = {"rules": [1], "show_file_viewer": True}
        result = close_file_viewer(state)
        assert result["rules"] == [1]
        assert result["show_file_viewer"] is False

    def test_idempotent(self):
        state = {}
        result1 = close_file_viewer(state)
        result2 = close_file_viewer(result1)
        assert result1 == result2
