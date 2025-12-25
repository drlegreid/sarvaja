"""
Session Evidence Viewer Tests (P9.3)
Created: 2024-12-25

Tests for enhanced session browsing UI.
Strategic Goal: Navigate session artifacts with timeline, search, and detail views.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


class TestSessionViewerModule:
    """Verify P9.3 session viewer module exists."""

    @pytest.mark.unit
    def test_session_viewer_module_exists(self):
        """Session viewer module must exist."""
        ui_file = AGENT_DIR / "session_viewer.py"
        assert ui_file.exists(), "agent/session_viewer.py not found"

    @pytest.mark.unit
    def test_session_viewer_class(self):
        """SessionViewer class must be importable."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        assert viewer is not None

    @pytest.mark.unit
    def test_viewer_has_required_methods(self):
        """Viewer must have required methods."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()

        assert hasattr(viewer, 'get_sessions_timeline')
        assert hasattr(viewer, 'get_session_detail')
        assert hasattr(viewer, 'search_in_session')
        assert hasattr(viewer, 'get_session_metadata')


class TestSessionTimeline:
    """Tests for session timeline functionality."""

    @pytest.mark.unit
    def test_get_sessions_timeline(self):
        """Should return sessions ordered by date."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline()

        assert isinstance(timeline, list)
        if len(timeline) >= 2:
            # Should be ordered by date (newest first by default)
            first_date = timeline[0].get('date', '')
            second_date = timeline[1].get('date', '')
            # Dates should be in descending order
            assert first_date >= second_date

    @pytest.mark.unit
    def test_timeline_has_required_fields(self):
        """Timeline entries should have required fields."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            entry = timeline[0]
            assert 'session_id' in entry
            assert 'date' in entry

    @pytest.mark.unit
    def test_timeline_with_date_filter(self):
        """Should filter timeline by date range."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        # Get sessions from December 2024
        timeline = viewer.get_sessions_timeline(
            start_date="2024-12-01",
            end_date="2024-12-31"
        )

        assert isinstance(timeline, list)
        for entry in timeline:
            date = entry.get('date', '')
            if date:
                assert '2024-12' in date


class TestSessionDetail:
    """Tests for session detail view."""

    @pytest.mark.unit
    def test_get_session_detail(self):
        """Should return full session details."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            detail = viewer.get_session_detail(session_id)

            assert 'session_id' in detail
            assert 'content' in detail

    @pytest.mark.unit
    def test_session_detail_parses_sections(self):
        """Should parse markdown sections."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            detail = viewer.get_session_detail(session_id)

            # Should have sections parsed
            assert 'sections' in detail
            assert isinstance(detail['sections'], list)

    @pytest.mark.unit
    def test_session_not_found(self):
        """Should handle missing sessions gracefully."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        detail = viewer.get_session_detail("SESSION-NONEXISTENT-999")

        assert 'error' in detail


class TestSessionMetadata:
    """Tests for session metadata extraction."""

    @pytest.mark.unit
    def test_get_session_metadata(self):
        """Should extract session metadata."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            metadata = viewer.get_session_metadata(session_id)

            assert isinstance(metadata, dict)
            assert 'session_id' in metadata

    @pytest.mark.unit
    def test_metadata_extracts_phase(self):
        """Should extract phase from session ID."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        # Parse session with known phase format
        metadata = viewer.parse_session_id("SESSION-2024-12-25-PHASE8-HEALTHCHECK")

        assert 'date' in metadata
        assert 'phase' in metadata
        assert metadata['phase'] == 'PHASE8'

    @pytest.mark.unit
    def test_metadata_extracts_topic(self):
        """Should extract topic from session ID."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        metadata = viewer.parse_session_id("SESSION-2024-12-25-PHASE8-HEALTHCHECK")

        assert 'topic' in metadata
        assert metadata['topic'] == 'HEALTHCHECK'


class TestSessionSearch:
    """Tests for search within sessions."""

    @pytest.mark.unit
    def test_search_in_session(self):
        """Should search within a session."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            results = viewer.search_in_session(session_id, "session")

            assert isinstance(results, list)

    @pytest.mark.unit
    def test_search_returns_context(self):
        """Search results should include context."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            results = viewer.search_in_session(session_id, "session")

            if results:
                result = results[0]
                assert 'match' in result
                assert 'line' in result or 'context' in result

    @pytest.mark.unit
    def test_search_all_sessions(self):
        """Should search across all sessions."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        results = viewer.search_all_sessions("evidence")

        assert isinstance(results, list)
        if results:
            result = results[0]
            assert 'session_id' in result


class TestSessionSummary:
    """Tests for session summary generation."""

    @pytest.mark.unit
    def test_generate_summary(self):
        """Should generate session summary."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            summary = viewer.get_session_summary(session_id)

            assert isinstance(summary, dict)
            assert 'session_id' in summary

    @pytest.mark.unit
    def test_summary_has_stats(self):
        """Summary should include statistics."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=1)

        if timeline:
            session_id = timeline[0]['session_id']
            summary = viewer.get_session_summary(session_id)

            # Should have basic stats
            assert 'word_count' in summary or 'line_count' in summary


class TestSessionNavigation:
    """Tests for session navigation helpers."""

    @pytest.mark.unit
    def test_get_adjacent_sessions(self):
        """Should find previous and next sessions."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        timeline = viewer.get_sessions_timeline(limit=10)

        if len(timeline) >= 3:
            middle_id = timeline[1]['session_id']
            adjacent = viewer.get_adjacent_sessions(middle_id)

            assert 'previous' in adjacent
            assert 'next' in adjacent

    @pytest.mark.unit
    def test_get_sessions_by_phase(self):
        """Should group sessions by phase."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        by_phase = viewer.get_sessions_by_phase()

        assert isinstance(by_phase, dict)

    @pytest.mark.unit
    def test_get_sessions_by_date(self):
        """Should group sessions by date."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        by_date = viewer.get_sessions_by_date()

        assert isinstance(by_date, dict)


class TestViewerIntegration:
    """Integration tests for session viewer."""

    @pytest.mark.unit
    def test_uses_mcp_tools(self):
        """Viewer should use MCP tools internally."""
        from agent.session_viewer import SessionViewer

        viewer = SessionViewer()
        assert hasattr(viewer, '_call_mcp_tool')

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create viewer."""
        from agent.session_viewer import create_session_viewer

        viewer = create_session_viewer()
        assert viewer is not None

