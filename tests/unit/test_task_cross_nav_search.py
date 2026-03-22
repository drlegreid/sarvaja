"""
Tests for Phase 9d: Cross-Entity Navigation + Server-Side Search.

EPIC-GOV-TASKS-V2 Phase 9d — 4 concerns:
1. Task → Session navigation (clickable chips)
2. Task → Document references (type icons)
3. Session column + session_id filter
4. Server-side attribute-based search

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

_SVC = "governance.services.tasks"
_TDA = "governance.stores.typedb_access"
_ROUTE = "governance.routes.tasks.crud"


@pytest.fixture(autouse=True)
def _reset_stores():
    with patch(f"{_SVC}._tasks_store", {}) as tasks, \
         patch(f"{_SVC}._sessions_store", {}) as sessions, \
         patch(f"{_SVC}.record_audit"), \
         patch(f"{_SVC}.log_event"):
        yield tasks, sessions


def _make_task_entity(task_id, **overrides):
    defaults = dict(
        name="Test", status="OPEN", phase="P9", priority="MEDIUM",
        task_type="chore", agent_id=None, body=None, description="Test desc",
        resolution=None, gap_id=None, evidence=None, document_path=None,
        summary="Test summary",
        linked_rules=[], linked_sessions=[], linked_commits=[],
        linked_documents=[], workspace_id=None,
        created_at=datetime(2026, 3, 21, 10, 0, 0),
        claimed_at=None, completed_at=None,
    )
    defaults.update(overrides)
    t = MagicMock()
    for k, v in defaults.items():
        setattr(t, k, v)
    t.id = task_id
    return t


# ── Concern 1: Task → Session Navigation ──


class TestNavigateToSession:
    """navigate_to_session trigger must exist in tasks_navigation."""

    def test_navigate_to_session_controller_exists(self):
        import inspect
        from agent.governance_ui.controllers.tasks_navigation import register_tasks_navigation
        source = inspect.getsource(register_tasks_navigation)
        assert "navigate_to_session" in source

    def test_navigate_to_session_sets_active_view(self):
        """navigate_to_session must switch active_view to 'sessions'."""
        state = MagicMock()
        state.sessions = []
        ctrl = MagicMock()
        triggers = {}

        def fake_trigger(name):
            def deco(fn):
                triggers[name] = fn
                return fn
            return deco
        ctrl.trigger = fake_trigger

        from agent.governance_ui.controllers.tasks_navigation import register_tasks_navigation
        register_tasks_navigation(state, ctrl, "http://localhost:8082")

        assert "navigate_to_session" in triggers
        with patch("httpx.Client") as mock_http:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"session_id": "S-1", "status": "ACTIVE"}
            mock_http.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
            mock_http.return_value.__exit__ = MagicMock(return_value=False)
            triggers["navigate_to_session"]("S-1", "tasks", "T-1", "Back to Task T-1")

        assert state.active_view == "sessions"


# ── Concern 2: Task → Document Type Detection ──


class TestDocumentTypeDetection:
    """_detect_doc_type must classify paths into plan/evidence/spec/log."""

    def test_evidence_path(self):
        from governance.services.tasks import _detect_doc_type
        assert _detect_doc_type("evidence/test-results/EDS-001.png") == "evidence"

    def test_plan_path(self):
        from governance.services.tasks import _detect_doc_type
        assert _detect_doc_type("docs/backlog/phases/P9.md") == "plan"

    def test_spec_path(self):
        from governance.services.tasks import _detect_doc_type
        assert _detect_doc_type("docs/backlog/specs/E2E-T3-CRUD.gherkin.md") == "spec"

    def test_log_path(self):
        from governance.services.tasks import _detect_doc_type
        assert _detect_doc_type("logs/api-2026-03-21.log") == "log"

    def test_generic_path(self):
        from governance.services.tasks import _detect_doc_type
        assert _detect_doc_type("governance/schema.tql") == "document"


# ── Concern 3: Session Filter ──


class TestSessionFilter:
    """list_tasks must accept and apply session_id filter."""

    def test_list_tasks_accepts_session_id(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", linked_sessions=["SESSION-A"]),
            _make_task_entity("T-2", linked_sessions=["SESSION-B"]),
            _make_task_entity("T-3", linked_sessions=[]),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(session_id="SESSION-A")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-1" in ids
        assert "T-2" not in ids
        assert "T-3" not in ids

    def test_session_id_none_returns_all(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", linked_sessions=["SESSION-A"]),
            _make_task_entity("T-2", linked_sessions=[]),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(session_id=None)

        assert len(result["items"]) == 2

    def test_api_route_has_session_id_param(self):
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "session_id" in sig.parameters

    def test_api_route_has_search_param(self):
        import inspect
        from governance.routes.tasks.crud import list_tasks as route_fn
        sig = inspect.signature(route_fn)
        assert "search" in sig.parameters


# ── Concern 4: Server-Side Search ──


class TestServerSideSearch:
    """_apply_search must search across task_id, description, summary, body, gap_id."""

    def test_search_matches_task_id(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("AUTH-001", description="Fix login"),
            _make_task_entity("DEPLOY-002", description="Deploy pipeline"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="AUTH")

        ids = {t["task_id"] for t in result["items"]}
        assert "AUTH-001" in ids
        assert "DEPLOY-002" not in ids

    def test_search_matches_description(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", description="Fix authentication bug"),
            _make_task_entity("T-2", description="Add dark mode"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="authentication")

        ids = {t["task_id"] for t in result["items"]}
        assert "T-1" in ids
        assert "T-2" not in ids

    def test_search_matches_summary(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", summary="OAuth token refresh"),
            _make_task_entity("T-2", summary="CSS grid layout"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="oauth")

        assert len(result["items"]) == 1
        assert result["items"][0]["task_id"] == "T-1"

    def test_search_matches_body(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", body="The TypeDB schema needs migration"),
            _make_task_entity("T-2", body="Frontend styling fixes"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="typedb")

        assert len(result["items"]) == 1

    def test_search_matches_gap_id(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", gap_id="GAP-AUTH-001"),
            _make_task_entity("T-2", gap_id="GAP-UI-042"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="GAP-AUTH")

        assert len(result["items"]) == 1

    def test_search_case_insensitive(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", description="Fix Authentication Bug"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="authentication")

        assert len(result["items"]) == 1


class TestStructuredSearch:
    """Attribute-prefix syntax: 'type:bug priority:HIGH auth'."""

    def test_parse_structured_search(self):
        from governance.services.tasks import _parse_structured_search
        attrs, text = _parse_structured_search("type:bug priority:HIGH auth fix")
        assert attrs == {"type": "bug", "priority": "HIGH"}
        assert text == "auth fix"

    def test_parse_no_prefixes(self):
        from governance.services.tasks import _parse_structured_search
        attrs, text = _parse_structured_search("some free text")
        assert attrs == {}
        assert text == "some free text"

    def test_parse_only_prefixes(self):
        from governance.services.tasks import _parse_structured_search
        attrs, text = _parse_structured_search("type:feature status:DONE")
        assert attrs == {"type": "feature", "status": "DONE"}
        assert text == ""

    def test_structured_search_applies_filters(self, _reset_stores):
        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = [
            _make_task_entity("T-1", task_type="bug", priority="HIGH", description="Auth bug"),
            _make_task_entity("T-2", task_type="bug", priority="LOW", description="Auth issue"),
            _make_task_entity("T-3", task_type="feature", priority="HIGH", description="Auth feature"),
        ]
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="type:bug priority:HIGH auth")

        ids = {t["task_id"] for t in result["items"]}
        assert ids == {"T-1"}

    def test_search_with_pagination(self, _reset_stores):
        mock_client = MagicMock()
        tasks = [_make_task_entity(f"T-{i}", description=f"Deploy task {i}") for i in range(10)]
        tasks += [_make_task_entity(f"O-{i}", description=f"Other task {i}") for i in range(10)]
        mock_client.get_all_tasks.return_value = tasks
        with patch(f"{_TDA}.get_typedb_client", return_value=mock_client), \
             patch(f"{_TDA}._tasks_store", {}):
            from governance.services.tasks import list_tasks
            result = list_tasks(search="deploy", limit=5)

        assert result["total"] == 10  # 10 deploy tasks
        assert len(result["items"]) == 5
        assert result["has_more"] is True


# ── Controller passes search + session_id to API ──


class TestControllerPassesNewParams:
    def test_controller_references_search(self):
        import inspect
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_search_query" in source or "search" in source

    def test_controller_references_session_filter(self):
        import inspect
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_session_filter" in source or "session_id" in source
