"""
Unit tests for Session Pagination & Filter Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/sessions_pagination.py.
Tests: load_sessions_page, sessions_prev_page, sessions_next_page,
       sessions_change_page_size, _compute_pivot.
"""

from unittest.mock import patch, MagicMock

from agent.governance_ui.controllers.sessions_pagination import register_sessions_pagination


def _make_state(**attrs):
    s = MagicMock()
    defaults = {
        "sessions_page": 1,
        "sessions_per_page": 20,
        "sessions_filter_status": None,
        "sessions_filter_agent": None,
        "sessions_view_mode": "table",
        "sessions_pivot_group_by": "agent_id",
    }
    defaults.update(attrs)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    ctrl = MagicMock()
    triggers = {}
    changes = {}

    def trigger_decorator(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    def change_decorator(name):
        def decorator(fn):
            changes[name] = fn
            return fn
        return decorator

    ctrl.trigger = trigger_decorator
    ctrl._triggers = triggers

    # Mock state.change as well
    return ctrl, triggers, changes


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _setup(**state_attrs):
    state = _make_state(**state_attrs)
    ctrl, triggers, changes = _make_ctrl()
    # Override state.change
    state.change = lambda name: (lambda fn: changes.update({name: fn}) or fn)
    loader = register_sessions_pagination(state, ctrl, "http://localhost:8082")
    return state, triggers, changes, loader


# ── Registration ───────────────────────────────────────


class TestRegistration:
    def test_returns_callable(self):
        _, _, _, loader = _setup()
        assert callable(loader)

    def test_registers_triggers(self):
        _, triggers, _, _ = _setup()
        expected = {"sessions_prev_page", "sessions_next_page",
                    "sessions_change_page_size", "sessions_apply_filters",
                    "sessions_toggle_view", "sessions_compute_pivot"}
        assert expected.issubset(set(triggers.keys()))

    def test_registers_state_changes(self):
        _, _, changes, _ = _setup()
        assert "sessions_filter_status" in changes
        assert "sessions_filter_agent" in changes
        assert "sessions_view_mode" in changes
        assert "sessions_pivot_group_by" in changes


# ── load_sessions_page ─────────────────────────────────


class TestLoadSessionsPage:
    @patch("agent.governance_ui.controllers.sessions_pagination.has_plotly", return_value=False)
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_duration",
           return_value="5m")
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_metrics",
           return_value={"duration": "10m", "avg_tasks": 2})
    @patch("agent.governance_ui.controllers.sessions_pagination.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_success_dict_response(self, MockClient, mock_fmt, mock_metrics,
                                     mock_dur, mock_tl, mock_plotly):
        items = [{"session_id": "S-1", "agent_id": "a1", "start_time": "", "end_time": ""}]
        pagination = {"total": 1, "offset": 0, "limit": 20, "has_more": False}
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items, "pagination": pagination})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()

        assert state.is_loading is False
        assert state.sessions_pagination == pagination
        assert state.sessions_metrics_duration == "10m"

    @patch("agent.governance_ui.controllers.sessions_pagination.has_plotly", return_value=False)
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_duration",
           return_value="5m")
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_metrics",
           return_value={"duration": "0", "avg_tasks": 0})
    @patch("agent.governance_ui.controllers.sessions_pagination.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_success_list_response(self, MockClient, mock_fmt, mock_metrics,
                                    mock_dur, mock_tl, mock_plotly):
        items = [{"session_id": "S-1"}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, items)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()

        assert state.sessions_pagination["total"] == 1
        assert state.sessions_pagination["has_more"] is False

    @patch("httpx.Client")
    def test_exception_sets_error(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("timeout"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()

        assert state.is_loading is False
        assert state.has_error is True

    @patch("agent.governance_ui.controllers.sessions_pagination.has_plotly", return_value=False)
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_duration",
           return_value="0")
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_metrics",
           return_value={"duration": "0", "avg_tasks": 0})
    @patch("agent.governance_ui.controllers.sessions_pagination.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_normalizes_date_to_start_time(self, MockClient, mock_fmt,
                                            mock_metrics, mock_dur, mock_tl,
                                            mock_plotly):
        items = [{"session_id": "S-1", "date": "2026-01-01", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": items})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup()
        loader()

        # The item should have start_time filled from date
        assert items[0]["start_time"] == "2026-01-01"

    @patch("agent.governance_ui.controllers.sessions_pagination.has_plotly", return_value=False)
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_duration",
           return_value="0")
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_session_metrics",
           return_value={"duration": "0", "avg_tasks": 0})
    @patch("agent.governance_ui.controllers.sessions_pagination.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_applies_filters(self, MockClient, mock_fmt, mock_metrics,
                              mock_dur, mock_tl, mock_plotly):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": []})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, _, loader = _setup(
            sessions_filter_status="COMPLETED",
            sessions_filter_agent="code-agent",
        )
        loader()

        call_kwargs = mc.get.call_args[1]
        assert call_kwargs["params"]["status"] == "COMPLETED"
        assert call_kwargs["params"]["agent_id"] == "code-agent"


# ── Pagination Triggers ───────────────────────────────


class TestPaginationTriggers:
    @patch("httpx.Client")
    def test_prev_page_decrements(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("skip load"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, triggers, _, _ = _setup(sessions_page=3)
        triggers["sessions_prev_page"]()

        assert state.sessions_page == 2

    def test_prev_page_at_one_noop(self):
        state, triggers, _, _ = _setup(sessions_page=1)
        original_page = state.sessions_page
        # Won't call load, so no httpx mock needed
        triggers["sessions_prev_page"]()
        assert state.sessions_page == original_page

    @patch("httpx.Client")
    def test_next_page_increments(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("skip load"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, triggers, _, _ = _setup(sessions_page=1)
        state.sessions_pagination = {"has_more": True}
        triggers["sessions_next_page"]()

        assert state.sessions_page == 2

    def test_next_page_no_more_noop(self):
        state, triggers, _, _ = _setup(sessions_page=1)
        state.sessions_pagination = {"has_more": False}
        triggers["sessions_next_page"]()
        assert state.sessions_page == 1


# ── _compute_pivot ─────────────────────────────────────


class TestComputePivot:
    @patch("agent.governance_ui.controllers.sessions_pagination.compute_pivot_data",
           return_value=[{"group": "a1", "count": 5}])
    @patch("httpx.Client")
    def test_computes_pivot(self, MockClient, mock_pivot):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, [{"session_id": "S-1"}])
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, triggers, _, _ = _setup(sessions_view_mode="pivot")
        triggers["sessions_toggle_view"]()

        assert state.sessions_pivot_data == [{"group": "a1", "count": 5}]

    @patch("httpx.Client")
    def test_pivot_exception(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("timeout"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, triggers, _, _ = _setup(sessions_view_mode="pivot")
        triggers["sessions_toggle_view"]()

        assert state.sessions_pivot_data == []
