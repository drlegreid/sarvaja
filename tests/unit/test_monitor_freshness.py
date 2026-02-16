"""TDD Tests for Cycle 7-8: Monitor Data Freshness Indicator.

Gap: GAP-MONITOR-FRESH-001
Problem: User doesn't know when monitoring data was last fetched.
Solution: Add monitor_last_updated timestamp to state, display in header.
"""
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Test Group 1: State variable exists
# ---------------------------------------------------------------------------

class TestMonitorFreshnessState:
    """monitor_last_updated state variable exists and is populated."""

    def test_initial_state_has_monitor_last_updated(self):
        """Initial state declares monitor_last_updated."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "monitor_last_updated" in state

    def test_initial_value_is_empty_string(self):
        """monitor_last_updated starts as empty string (no data loaded yet)."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["monitor_last_updated"] == ""


# ---------------------------------------------------------------------------
# Test Group 2: data_loaders load_monitor_data sets timestamp
# ---------------------------------------------------------------------------

class TestDataLoaderSetsTimestamp:
    """load_monitor_data in data_loaders sets monitor_last_updated."""

    @patch("agent.governance_ui.controllers.data_loaders.get_hourly_monitor_stats")
    @patch("agent.governance_ui.controllers.data_loaders.get_top_monitored_rules")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_stats")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_alerts")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_feed")
    def test_timestamp_is_iso_format(
        self, mock_feed, mock_alerts, mock_stats, mock_rules, mock_hourly
    ):
        """monitor_last_updated is set to ISO format datetime string."""
        mock_feed.return_value = []
        mock_alerts.return_value = []
        mock_stats.return_value = {}
        mock_rules.return_value = []
        mock_hourly.return_value = {}

        class SimpleState:
            def __init__(self):
                self.monitor_filter = None
                self.monitor_feed = []
                self.monitor_alerts = []
                self.monitor_stats = {}
                self.top_rules = []
                self.hourly_stats = {}
                self.monitor_last_updated = ""

        state = SimpleState()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)
        ctrl.set = MagicMock(return_value=lambda f: f)

        with patch("agent.governance_ui.controllers.data_loaders.httpx"):
            with patch("agent.governance_ui.controllers.data_loaders.register_infra_loader_controllers", return_value={"load_infra_status": MagicMock()}):
                with patch("agent.governance_ui.controllers.data_loaders.register_workflow_loader_controllers", return_value={"load_workflow_status": MagicMock()}):
                    with patch("agent.governance_ui.controllers.data_loaders.register_audit_loader_controllers", return_value={"load_audit_trail": MagicMock()}):
                        with patch("agent.governance_ui.controllers.data_loaders.register_refresh_controllers", return_value={"load_sessions_list": MagicMock()}):
                            from agent.governance_ui.controllers.data_loaders import register_data_loader_controllers
                            loaders = register_data_loader_controllers(state, ctrl, "http://localhost:8082")

        loaders["load_monitor_data"]()

        # Verify it's a valid ISO timestamp
        assert state.monitor_last_updated != ""
        parsed = datetime.fromisoformat(state.monitor_last_updated)
        assert isinstance(parsed, datetime)

    @patch("agent.governance_ui.controllers.data_loaders.get_hourly_monitor_stats")
    @patch("agent.governance_ui.controllers.data_loaders.get_top_monitored_rules")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_stats")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_alerts")
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_feed")
    def test_timestamp_populates_monitor_feed(
        self, mock_feed, mock_alerts, mock_stats, mock_rules, mock_hourly
    ):
        """Data is actually loaded alongside timestamp."""
        mock_feed.return_value = [{"event_id": "e1", "type": "violation"}]
        mock_alerts.return_value = []
        mock_stats.return_value = {"total_events": 1}
        mock_rules.return_value = []
        mock_hourly.return_value = {}

        class SimpleState:
            def __init__(self):
                self.monitor_filter = None
                self.monitor_feed = []
                self.monitor_alerts = []
                self.monitor_stats = {}
                self.top_rules = []
                self.hourly_stats = {}
                self.monitor_last_updated = ""

        state = SimpleState()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)
        ctrl.set = MagicMock(return_value=lambda f: f)

        with patch("agent.governance_ui.controllers.data_loaders.httpx"):
            with patch("agent.governance_ui.controllers.data_loaders.register_infra_loader_controllers", return_value={"load_infra_status": MagicMock()}):
                with patch("agent.governance_ui.controllers.data_loaders.register_workflow_loader_controllers", return_value={"load_workflow_status": MagicMock()}):
                    with patch("agent.governance_ui.controllers.data_loaders.register_audit_loader_controllers", return_value={"load_audit_trail": MagicMock()}):
                        with patch("agent.governance_ui.controllers.data_loaders.register_refresh_controllers", return_value={"load_sessions_list": MagicMock()}):
                            from agent.governance_ui.controllers.data_loaders import register_data_loader_controllers
                            loaders = register_data_loader_controllers(state, ctrl, "http://localhost:8082")

        loaders["load_monitor_data"]()

        assert len(state.monitor_feed) == 1
        assert state.monitor_last_updated != ""


# ---------------------------------------------------------------------------
# Test Group 3: Monitor controller sets timestamp (including on error)
# ---------------------------------------------------------------------------

class TestMonitorControllerTimestamp:
    """Register monitor controller sets timestamp."""

    @patch("agent.governance_ui.controllers.monitor.get_top_monitored_rules")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_stats")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_alerts")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_feed")
    def test_timestamp_set_on_success(
        self, mock_feed, mock_alerts, mock_stats, mock_rules
    ):
        """load_monitor_data sets timestamp on successful load."""
        mock_feed.return_value = []
        mock_alerts.return_value = []
        mock_stats.return_value = {}
        mock_rules.return_value = []

        class SimpleState:
            def __init__(self):
                self.monitor_filter = None
                self.monitor_feed = []
                self.monitor_alerts = []
                self.monitor_stats = {}
                self.top_rules = []
                self.monitor_last_updated = ""
                self.status_message = ""

        state = SimpleState()
        registered_fns = {}

        def capture_trigger(name):
            def decorator(fn):
                registered_fns[name] = fn
                return fn
            return decorator

        ctrl = MagicMock()
        ctrl.trigger = capture_trigger
        ctrl.set = MagicMock(return_value=lambda f: f)

        from agent.governance_ui.controllers.monitor import register_monitor_controllers
        register_monitor_controllers(state, ctrl, "http://localhost:8082")

        registered_fns["load_monitor_data"]()

        assert state.monitor_last_updated != ""
        parsed = datetime.fromisoformat(state.monitor_last_updated)
        assert isinstance(parsed, datetime)

    @patch("agent.governance_ui.controllers.monitor.get_top_monitored_rules")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_stats")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_alerts")
    @patch("agent.governance_ui.controllers.monitor.get_monitor_feed")
    def test_timestamp_set_even_on_error(
        self, mock_feed, mock_alerts, mock_stats, mock_rules
    ):
        """When load_monitor_data fails, timestamp still records last attempt."""
        mock_feed.side_effect = Exception("Connection refused")

        class SimpleState:
            def __init__(self):
                self.monitor_filter = None
                self.monitor_feed = []
                self.monitor_alerts = []
                self.monitor_stats = {}
                self.top_rules = []
                self.monitor_last_updated = ""
                self.status_message = ""
                self.has_error = False
                self.error_message = ""

        state = SimpleState()
        registered_fns = {}

        def capture_trigger(name):
            def decorator(fn):
                registered_fns[name] = fn
                return fn
            return decorator

        ctrl = MagicMock()
        ctrl.trigger = capture_trigger
        ctrl.set = MagicMock(return_value=lambda f: f)

        from agent.governance_ui.controllers.monitor import register_monitor_controllers
        register_monitor_controllers(state, ctrl, "http://localhost:8082")

        registered_fns["load_monitor_data"]()

        # Timestamp set even on error (shows last attempt time)
        assert state.monitor_last_updated != ""
        # BUG-UI-LOAD-003: Now uses error_message + has_error, not status_message
        assert state.has_error is True
        assert "Monitor load failed" in state.error_message


# ---------------------------------------------------------------------------
# Test Group 4: View shows freshness badge
# ---------------------------------------------------------------------------

class TestMonitorViewShowsFreshness:
    """Monitor view header includes a freshness indicator."""

    def test_build_monitor_header_references_last_updated(self):
        """build_monitor_header source includes monitor_last_updated."""
        import inspect
        from agent.governance_ui.views.monitor_view import build_monitor_header
        source = inspect.getsource(build_monitor_header)
        assert "monitor_last_updated" in source

    def test_build_monitor_header_has_freshness_testid(self):
        """Freshness chip has data-testid for E2E testing."""
        import inspect
        from agent.governance_ui.views.monitor_view import build_monitor_header
        source = inspect.getsource(build_monitor_header)
        assert "monitor-freshness" in source
