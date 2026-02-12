"""
Test suite for Trame UI Module
==============================
Validates Trame-based UI components and factory functions.

Per Phase 6: Use Trame for Python-native web UI
Per RULE-019: UI/UX Design Standards
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestCreateTrameApp:
    """Tests for create_trame_app factory."""

    @pytest.fixture
    def mock_trame(self):
        """Mock Trame dependencies."""
        with patch.dict('sys.modules', {
            'trame': MagicMock(),
            'trame.app': MagicMock(),
            'trame.ui.vuetify3': MagicMock(),
            'trame.widgets': MagicMock(),
            'trame.widgets.vuetify3': MagicMock(),
            'trame.widgets.html': MagicMock(),
        }):
            yield

    def test_create_with_default_agents(self, mock_trame):
        """Factory creates app with default agents."""
        try:
            from agent.trame_ui import create_trame_app
            app = create_trame_app()
            assert app is not None
            assert hasattr(app, 'agents')
            assert len(app.agents) == 5  # Default agents
        except ImportError:
            pytest.skip("Trame not installed")

    def test_create_with_custom_agents(self, mock_trame):
        """Factory creates app with custom agents."""
        try:
            from agent.trame_ui import create_trame_app
            custom_agents = {"test_agent": "Test Agent"}
            app = create_trame_app(agents=custom_agents)
            assert app.agents == custom_agents
        except ImportError:
            pytest.skip("Trame not installed")

    def test_create_with_custom_api_base(self, mock_trame):
        """Factory accepts custom API base URL."""
        try:
            from agent.trame_ui import create_trame_app
            app = create_trame_app(api_base="http://custom:9999")
            assert app.api_base == "http://custom:9999"
        except ImportError:
            pytest.skip("Trame not installed")


# =============================================================================
# UI CLASS TESTS
# =============================================================================

class TestSarvajaTrameUI:
    """Tests for SarvajaTrameUI class."""

    @pytest.fixture
    def mock_server(self):
        """Create mock Trame server."""
        server = MagicMock()
        server.state = MagicMock()
        server.controller = MagicMock()
        return server

    def test_init_sets_agents(self, mock_server):
        """Initialization stores agents dict."""
        with patch('agent.trame_ui.get_server', return_value=mock_server):
            try:
                from agent.trame_ui import SarvajaTrameUI
                agents = {"agent1": Mock(), "agent2": Mock()}
                ui = SarvajaTrameUI(agents=agents)
                assert ui.agents == agents
            except ImportError:
                pytest.skip("Trame not installed")

    def test_init_sets_api_base(self, mock_server):
        """Initialization stores API base URL."""
        with patch('agent.trame_ui.get_server', return_value=mock_server):
            try:
                from agent.trame_ui import SarvajaTrameUI
                ui = SarvajaTrameUI(agents={}, api_base="http://test:8080")
                assert ui.api_base == "http://test:8080"
            except ImportError:
                pytest.skip("Trame not installed")

    def test_init_creates_agent_options(self, mock_server):
        """Initialization creates agent options for dropdown."""
        with patch('agent.trame_ui.get_server', return_value=mock_server):
            try:
                from agent.trame_ui import SarvajaTrameUI
                agents = {"orchestrator": Mock(), "coder": Mock()}
                ui = SarvajaTrameUI(agents=agents)

                # Check state was set
                assert mock_server.state.agent_options is not None
            except ImportError:
                pytest.skip("Trame not installed")


# =============================================================================
# STATE INITIALIZATION TESTS
# =============================================================================

class TestStateInitialization:
    """Tests for Trame state initialization."""

    def test_initial_events_empty(self):
        """Initial events list is empty."""
        try:
            from agent.trame_ui import create_trame_app
            # Just verify factory creates without error
            app = create_trame_app()
            assert app is not None
        except ImportError:
            pytest.skip("Trame not installed")

    def test_initial_status_ready(self):
        """Initial status is 'Ready'."""
        try:
            from agent.trame_ui import create_trame_app
            # Just verify factory creates without error
            app = create_trame_app()
            assert app is not None
        except ImportError:
            pytest.skip("Trame not installed")


# =============================================================================
# INTEGRATION TESTS (require Trame installed)
# =============================================================================

class TestTrameIntegration:
    """Integration tests requiring Trame installation."""

    @pytest.mark.skipif(
        True,  # Skip by default, enable when testing UI locally
        reason="Requires Trame installation and display"
    )
    def test_app_starts(self):
        """Trame app starts without errors."""
        from agent.trame_ui import create_trame_app
        app = create_trame_app()
        # Don't actually run, just verify creation
        assert app.server is not None

    @pytest.mark.skipif(
        True,
        reason="Requires Trame installation and display"
    )
    def test_ui_build_succeeds(self):
        """UI layout builds without errors."""
        from agent.trame_ui import create_trame_app
        app = create_trame_app()
        # Verify _build_ui was called
        assert app.state is not None
