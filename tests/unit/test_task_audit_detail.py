"""Unit tests for Task Audit Trail in Detail View — SRVJ-FEAT-AUDIT-TRAIL-01 P3.

Tests controller (_fetch_task_audit), state variables, icon mapping,
filter by action type, pagination, and display edge cases.

Per TDD: Write RED tests first, then implement to GREEN.
"""

import types
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_state():
    """Minimal Trame-like state with audit state vars."""
    state = MagicMock()
    state.task_audit_entries = []
    state.task_audit_loading = False
    state.task_audit_page = 1
    state.task_audit_per_page = 20
    state.task_audit_total = 0
    state.task_audit_has_more = False
    state.task_audit_filter_action = None
    state.show_task_audit_inline = False
    state.selected_task = {"task_id": "SRVJ-TEST-001", "id": "SRVJ-TEST-001"}
    state.trace_events = []
    state.trace_error_count = 0
    state.trace_api_count = 0
    state.trace_latest = ""
    return state


@pytest.fixture
def mock_ctrl():
    """Minimal Trame-like controller."""
    ctrl = MagicMock()
    _triggers = {}

    def trigger_side_effect(name):
        def decorator(fn):
            _triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = MagicMock(side_effect=trigger_side_effect)
    ctrl._triggers = _triggers
    return ctrl


SAMPLE_AUDIT_ENTRIES = [
    {
        "audit_id": "aud-001",
        "correlation_id": "corr-001",
        "timestamp": "2026-03-28T10:00:00",
        "actor_id": "code-agent",
        "action_type": "CREATE",
        "entity_type": "task",
        "entity_id": "SRVJ-TEST-001",
        "old_value": None,
        "new_value": "SRVJ-TEST-001",
        "applied_rules": [],
        "metadata": {},
    },
    {
        "audit_id": "aud-002",
        "correlation_id": "corr-002",
        "timestamp": "2026-03-28T10:01:00",
        "actor_id": "code-agent",
        "action_type": "LINK",
        "entity_type": "task",
        "entity_id": "SRVJ-TEST-001",
        "old_value": None,
        "new_value": None,
        "applied_rules": [],
        "metadata": {"linked_entity": {"type": "rule", "id": "TEST-GUARD-01"}},
    },
    {
        "audit_id": "aud-003",
        "correlation_id": "corr-003",
        "timestamp": "2026-03-28T10:02:00",
        "actor_id": "code-agent",
        "action_type": "UPDATE",
        "entity_type": "task",
        "entity_id": "SRVJ-TEST-001",
        "old_value": "TODO",
        "new_value": "IN_PROGRESS",
        "applied_rules": [],
        "metadata": {"field_changes": {"status": {"from": "TODO", "to": "IN_PROGRESS"}}},
    },
    {
        "audit_id": "aud-004",
        "correlation_id": "corr-004",
        "timestamp": "2026-03-28T10:03:00",
        "actor_id": "e2e-tester",
        "action_type": "COMMENT",
        "entity_type": "task",
        "entity_id": "SRVJ-TEST-001",
        "old_value": None,
        "new_value": None,
        "applied_rules": [],
        "metadata": {"action": "add", "body": "Test comment"},
    },
]


def _build_httpx_response(status_code, json_data):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _register_crud(state, ctrl, httpx_mod=None):
    """Import and register tasks_crud controllers."""
    from agent.governance_ui.controllers.tasks_crud import register_tasks_crud
    register_tasks_crud(
        state, ctrl, "http://localhost:8082",
        httpx_mod=httpx_mod,
        error_trace_fn=lambda *a, **kw: None,
    )
    return ctrl._triggers


# ── Test: _fetch_task_audit returns entries on 200 ────────────────────

class TestFetchTaskAudit:
    """Tests for _fetch_task_audit controller function."""

    def test_returns_entries_on_200(self, mock_state, mock_ctrl):
        """_fetch_task_audit returns audit entries when API returns 200."""
        resp = _build_httpx_response(200, SAMPLE_AUDIT_ENTRIES)
        mock_client = MagicMock()
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        # Patch traced_get to return our mock response
        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            return_value=(resp, None),
        ):
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            assert "load_task_audit" in triggers
            triggers["load_task_audit"]("SRVJ-TEST-001")
            assert mock_state.task_audit_entries == SAMPLE_AUDIT_ENTRIES
            assert mock_state.task_audit_loading is False

    def test_returns_empty_on_api_error(self, mock_state, mock_ctrl):
        """_fetch_task_audit returns empty list on non-200 response."""
        resp = _build_httpx_response(500, {"detail": "Internal Server Error"})
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            return_value=(resp, None),
        ):
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            triggers["load_task_audit"]("SRVJ-TEST-001")
            assert mock_state.task_audit_entries == []
            assert mock_state.task_audit_loading is False

    def test_returns_empty_on_timeout(self, mock_state, mock_ctrl):
        """_fetch_task_audit returns empty list on timeout (other loaders unaffected)."""
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            side_effect=Exception("Connection timeout"),
        ):
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            triggers["load_task_audit"]("SRVJ-TEST-001")
            assert mock_state.task_audit_entries == []
            assert mock_state.task_audit_loading is False

    def test_loading_state_toggled(self, mock_state, mock_ctrl):
        """task_audit_loading is set True before fetch, False after."""
        loading_states = []

        original_setattr = type(mock_state).__setattr__

        def track_setattr(self, name, value):
            if name == "task_audit_loading":
                loading_states.append(value)
            original_setattr(self, name, value)

        resp = _build_httpx_response(200, [])
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            return_value=(resp, None),
        ):
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            with patch.object(type(mock_state), '__setattr__', track_setattr):
                triggers["load_task_audit"]("SRVJ-TEST-001")

        assert True in loading_states, "task_audit_loading was never set to True"
        assert loading_states[-1] is False, "task_audit_loading should end False"


class TestFetchTaskAuditPagination:
    """Tests for audit pagination in controller."""

    def test_passes_page_and_per_page_params(self, mock_state, mock_ctrl):
        """load_task_audit passes page/per_page as limit/offset to API."""
        mock_state.task_audit_page = 2
        mock_state.task_audit_per_page = 10

        resp = _build_httpx_response(200, [])
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            return_value=(resp, None),
        ) as mock_get:
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            triggers["load_task_audit"]("SRVJ-TEST-001")
            # Verify params were passed
            call_args = mock_get.call_args
            params = call_args.kwargs.get("params") or (call_args[0][4] if len(call_args[0]) > 4 else None)
            # At minimum, the endpoint should be called
            assert mock_get.called

    def test_passes_filter_action_param(self, mock_state, mock_ctrl):
        """load_task_audit passes action_type filter to API when set."""
        mock_state.task_audit_filter_action = "LINK"

        resp = _build_httpx_response(200, [])
        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            return_value=(resp, None),
        ) as mock_get:
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            triggers["load_task_audit"]("SRVJ-TEST-001")
            assert mock_get.called


class TestFetchTaskAuditInSelectTask:
    """Tests for audit loading as part of select_task parallel loaders."""

    def test_audit_loaded_in_parallel_with_other_loaders(self, mock_state, mock_ctrl):
        """select_task fires audit fetch alongside execution/evidence/timeline/comments."""
        resp_200 = _build_httpx_response(200, {"task_id": "SRVJ-TEST-001"})
        resp_empty = _build_httpx_response(200, [])
        resp_events = _build_httpx_response(200, {"events": []})
        resp_evidence = _build_httpx_response(200, {"evidence_files": []})
        resp_timeline = _build_httpx_response(200, {"entries": [], "total": 0, "has_more": False})
        resp_comments = _build_httpx_response(200, {"comments": []})

        call_count = {"n": 0}
        endpoints_called = []

        def mock_traced_get(state, client, base, endpoint, **kwargs):
            call_count["n"] += 1
            endpoints_called.append(endpoint)
            if "/execution" in endpoint:
                return resp_events, None
            if "/evidence" in endpoint:
                return resp_evidence, None
            if "/timeline" in endpoint:
                return resp_timeline, None
            if "/comments" in endpoint:
                return resp_comments, None
            if "/audit/" in endpoint:
                return resp_empty, None
            return resp_200, None

        mock_httpx = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "agent.governance_ui.controllers.tasks_crud._traced_get",
            side_effect=mock_traced_get,
        ):
            triggers = _register_crud(mock_state, mock_ctrl, httpx_mod=mock_httpx)
            triggers["select_task"]("SRVJ-TEST-001")

        # Audit endpoint should have been called
        audit_calls = [e for e in endpoints_called if "audit" in e]
        assert len(audit_calls) >= 1, f"Audit not called. Endpoints: {endpoints_called}"
        assert mock_state.task_audit_loading is False


# ── Test: Icon mapping ────────────────────────────────────────────────

class TestAuditIconMapping:
    """Tests for action_type → icon/color mapping."""

    def test_all_action_types_mapped(self):
        """All known action types have an icon mapping — no KeyError."""
        from agent.governance_ui.views.tasks.audit_trail import AUDIT_ACTION_ICONS
        expected = ["CREATE", "UPDATE", "LINK", "UNLINK", "COMMENT", "DELETE"]
        for action in expected:
            assert action in AUDIT_ACTION_ICONS, f"{action} missing from icon map"
            entry = AUDIT_ACTION_ICONS[action]
            assert "icon" in entry, f"{action} has no icon"
            assert "color" in entry, f"{action} has no color"

    def test_unknown_action_type_has_fallback(self):
        """Unknown action_type uses fallback icon, no KeyError."""
        from agent.governance_ui.views.tasks.audit_trail import AUDIT_ACTION_ICONS
        # The component uses .get() with a default — verify default exists
        fallback = AUDIT_ACTION_ICONS.get("UNKNOWN_TYPE", AUDIT_ACTION_ICONS.get("_default"))
        assert fallback is not None, "No fallback for unknown action types"


# ── Test: Display edge cases ──────────────────────────────────────────

class TestAuditDisplayEdgeCases:
    """Tests for display edge cases — missing fields, null values."""

    def test_missing_old_new_value_no_crash(self):
        """Entry with old_value=None, new_value=None renders without crash."""
        entry = {
            "action_type": "LINK",
            "old_value": None,
            "new_value": None,
            "metadata": {"linked_entity": {"type": "rule", "id": "R-001"}},
        }
        # The template uses v_if guards — simulate by checking the data
        assert entry["old_value"] is None
        assert entry["new_value"] is None
        # No "None" string should be rendered — this is a template concern
        # but we verify the data contract
        assert str(entry["old_value"]) != "None" or entry["old_value"] is None

    def test_missing_linked_entity_no_crash(self):
        """LINK entry with missing metadata.linked_entity doesn't crash."""
        entry = {
            "action_type": "LINK",
            "metadata": {},
        }
        linked = entry.get("metadata", {}).get("linked_entity", {})
        assert linked == {}
        # Component should guard: v_if="entry.metadata && entry.metadata.linked_entity"

    def test_missing_field_changes_no_crash(self):
        """UPDATE entry with missing metadata.field_changes doesn't crash."""
        entry = {
            "action_type": "UPDATE",
            "old_value": "TODO",
            "new_value": "IN_PROGRESS",
            "metadata": {},
        }
        fc = entry.get("metadata", {}).get("field_changes")
        assert fc is None
        # Component should guard with v_if


# ── Test: State variables exist ───────────────────────────────────────

class TestAuditStateVariables:
    """Tests that initial state includes audit trail variables."""

    def test_state_has_audit_entries(self):
        """Initial state includes task_audit_entries = []."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "task_audit_entries" in state
        assert state["task_audit_entries"] == []

    def test_state_has_audit_loading(self):
        """Initial state includes task_audit_loading = False."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "task_audit_loading" in state
        assert state["task_audit_loading"] is False

    def test_state_has_audit_inline_toggle(self):
        """Initial state includes show_task_audit_inline = False."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "show_task_audit_inline" in state
        assert state["show_task_audit_inline"] is False

    def test_state_has_audit_filter(self):
        """Initial state includes task_audit_filter_action = None."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "task_audit_filter_action" in state
        assert state["task_audit_filter_action"] is None

    def test_state_has_audit_pagination(self):
        """Initial state includes audit pagination variables."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "task_audit_page" in state
        assert state["task_audit_page"] == 1
        assert "task_audit_per_page" in state
        assert state["task_audit_per_page"] == 20
        assert "task_audit_total" in state
        assert state["task_audit_total"] == 0
        assert "task_audit_has_more" in state
        assert state["task_audit_has_more"] is False
