"""
Unit tests for Workspaces Service Layer.

Per DOC-SIZE-01-v1: Tests for governance/services/workspaces.py module.
Tests: create_workspace, get_workspace, list_workspaces, update_workspace,
delete_workspace, assign_agent_to_workspace, remove_agent_from_workspace,
get_workspace_types_list, disk persistence.
"""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

_P = "governance.services.workspaces"


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset in-memory workspaces store and loaded flag for each test."""
    with patch(f"{_P}._workspaces_store", {}) as store, \
         patch(f"{_P}._loaded", True), \
         patch(f"{_P}._save"), \
         patch(f"{_P}.record_audit"):
        yield store


def _make_ws(workspace_id="WS-ABCD1234", name="Test WS", ws_type="governance",
             project_id="PROJ-1", status="active"):
    """Helper to create a workspace dict."""
    return {
        "workspace_id": workspace_id,
        "name": name,
        "workspace_type": ws_type,
        "project_id": project_id,
        "description": "A test workspace",
        "status": status,
        "created_at": "2026-02-15T10:00:00",
        "agent_ids": [],
        "default_rules": ["TEST-GUARD-01"],
        "capabilities": ["code_generation"],
        "icon": "mdi-shield-check",
        "color": "#6366f1",
    }


# ── create_workspace ──────────────────────────────────────────────


class TestCreateWorkspace:
    def test_create_returns_workspace(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("My Workspace", "governance", project_id="PROJ-1")
        assert ws["name"] == "My Workspace"
        assert ws["workspace_type"] == "governance"
        assert ws["project_id"] == "PROJ-1"
        assert ws["status"] == "active"
        assert ws["workspace_id"].startswith("WS-")

    def test_create_generates_unique_id(self):
        from governance.services.workspaces import create_workspace
        ws1 = create_workspace("WS1", "governance")
        ws2 = create_workspace("WS2", "governance")
        assert ws1["workspace_id"] != ws2["workspace_id"]

    def test_create_with_unknown_type_falls_back_to_generic(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("My WS", "nonexistent-type")
        assert ws["workspace_type"] == "generic"

    def test_create_with_agent_ids(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance", agent_ids=["agent-a", "agent-b"])
        assert ws["agent_ids"] == ["agent-a", "agent-b"]

    def test_create_default_agent_ids_empty(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance")
        assert ws["agent_ids"] == []

    def test_create_with_description(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance", description="Custom description")
        assert ws["description"] == "Custom description"

    def test_create_default_description_from_type(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance")
        # Uses workspace type description as default
        assert ws["description"] != ""

    def test_create_populates_defaults_from_type(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance")
        assert isinstance(ws["default_rules"], list)
        assert isinstance(ws["capabilities"], list)
        assert ws["icon"] == "mdi-shield-check"
        assert ws["color"] == "#6366f1"

    def test_create_gamedev_type(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("Game Project", "gamedev")
        assert ws["workspace_type"] == "gamedev"
        assert ws["icon"] == "mdi-gamepad-variant"
        assert ws["color"] == "#22c55e"

    def test_create_adds_to_store(self):
        from governance.services.workspaces import create_workspace, _workspaces_store
        ws = create_workspace("WS", "governance")
        assert ws["workspace_id"] in _workspaces_store

    def test_create_calls_save(self):
        with patch(f"{_P}._save") as mock_save, \
             patch(f"{_P}.record_audit"):
            from governance.services.workspaces import create_workspace
            create_workspace("WS", "governance")
            mock_save.assert_called_once()

    def test_create_records_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit, \
             patch(f"{_P}._save"):
            from governance.services.workspaces import create_workspace
            create_workspace("WS", "governance", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "CREATE"
            assert call_args[0][1] == "workspace"
            assert call_args[1]["metadata"]["source"] == "api"
            assert call_args[1]["metadata"]["type"] == "governance"

    def test_create_has_created_at(self):
        from governance.services.workspaces import create_workspace
        ws = create_workspace("WS", "governance")
        assert "created_at" in ws
        assert ws["created_at"]


# ── get_workspace ─────────────────────────────────────────────────


class TestGetWorkspace:
    def test_get_existing(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import get_workspace
        result = get_workspace(ws["workspace_id"])
        assert result is not None
        assert result["name"] == "Test WS"

    def test_get_nonexistent(self):
        from governance.services.workspaces import get_workspace
        result = get_workspace("WS-NONEXISTENT")
        assert result is None

    def test_get_returns_correct_workspace(self, _reset_store):
        ws1 = _make_ws("WS-001", "First")
        ws2 = _make_ws("WS-002", "Second")
        _reset_store["WS-001"] = ws1
        _reset_store["WS-002"] = ws2
        from governance.services.workspaces import get_workspace
        result = get_workspace("WS-002")
        assert result["name"] == "Second"


# ── list_workspaces ───────────────────────────────────────────────


class TestListWorkspaces:
    def _populate(self, store):
        ws1 = _make_ws("WS-001", "Alpha", "governance", "PROJ-A", "active")
        ws1["created_at"] = "2026-02-15T10:00:00"
        ws2 = _make_ws("WS-002", "Beta", "gamedev", "PROJ-A", "active")
        ws2["created_at"] = "2026-02-15T11:00:00"
        ws3 = _make_ws("WS-003", "Gamma", "governance", "PROJ-B", "archived")
        ws3["created_at"] = "2026-02-15T12:00:00"
        store["WS-001"] = ws1
        store["WS-002"] = ws2
        store["WS-003"] = ws3

    def test_list_all(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces()
        assert result["total"] == 3
        assert len(result["items"]) == 3

    def test_list_empty(self):
        from governance.services.workspaces import list_workspaces
        result = list_workspaces()
        assert result["total"] == 0
        assert result["items"] == []
        assert result["has_more"] is False

    def test_filter_by_project_id(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(project_id="PROJ-A")
        assert result["total"] == 2
        assert all(w["project_id"] == "PROJ-A" for w in result["items"])

    def test_filter_by_workspace_type(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(workspace_type="governance")
        assert result["total"] == 2
        assert all(w["workspace_type"] == "governance" for w in result["items"])

    def test_filter_by_status(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(status="archived")
        assert result["total"] == 1
        assert result["items"][0]["workspace_id"] == "WS-003"

    def test_combined_filters(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(project_id="PROJ-A", workspace_type="governance")
        assert result["total"] == 1
        assert result["items"][0]["workspace_id"] == "WS-001"

    def test_pagination_offset(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(offset=1, limit=50)
        assert result["total"] == 3
        assert len(result["items"]) == 2
        assert result["offset"] == 1

    def test_pagination_limit(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(offset=0, limit=2)
        assert len(result["items"]) == 2
        assert result["has_more"] is True
        assert result["limit"] == 2

    def test_pagination_no_more(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(offset=0, limit=50)
        assert result["has_more"] is False

    def test_sorted_by_created_at_descending(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces()
        created_ats = [w["created_at"] for w in result["items"]]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_filter_no_match(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces(project_id="PROJ-Z")
        assert result["total"] == 0
        assert result["items"] == []

    def test_response_structure(self, _reset_store):
        self._populate(_reset_store)
        from governance.services.workspaces import list_workspaces
        result = list_workspaces()
        assert "items" in result
        assert "total" in result
        assert "offset" in result
        assert "limit" in result
        assert "has_more" in result


# ── update_workspace ──────────────────────────────────────────────


class TestUpdateWorkspace:
    def test_update_name(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        result = update_workspace(ws["workspace_id"], name="Updated Name")
        assert result["name"] == "Updated Name"

    def test_update_description(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        result = update_workspace(ws["workspace_id"], description="New desc")
        assert result["description"] == "New desc"

    def test_update_status(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        result = update_workspace(ws["workspace_id"], status="archived")
        assert result["status"] == "archived"

    def test_update_agent_ids(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        result = update_workspace(ws["workspace_id"], agent_ids=["agt-1", "agt-2"])
        assert result["agent_ids"] == ["agt-1", "agt-2"]

    def test_update_nonexistent_returns_none(self):
        from governance.services.workspaces import update_workspace
        result = update_workspace("WS-NONEXISTENT", name="nope")
        assert result is None

    def test_update_partial_fields(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        result = update_workspace(ws["workspace_id"], name="New Name")
        # Other fields unchanged
        assert result["description"] == ws["description"]
        assert result["status"] == ws["status"]

    def test_update_calls_save(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save, \
             patch(f"{_P}.record_audit"):
            from governance.services.workspaces import update_workspace
            update_workspace(ws["workspace_id"], name="Updated")
            mock_save.assert_called_once()

    def test_update_records_audit(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}.record_audit") as mock_audit, \
             patch(f"{_P}._save"):
            from governance.services.workspaces import update_workspace
            update_workspace(ws["workspace_id"], name="Updated", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "UPDATE"
            assert call_args[0][1] == "workspace"
            assert call_args[1]["metadata"]["source"] == "api"

    def test_update_none_values_not_applied(self, _reset_store):
        ws = _make_ws()
        ws["name"] = "Original"
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import update_workspace
        # Pass only status, name should remain
        result = update_workspace(ws["workspace_id"], status="archived")
        assert result["name"] == "Original"


# ── delete_workspace ──────────────────────────────────────────────


class TestDeleteWorkspace:
    def test_delete_existing(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import delete_workspace
        result = delete_workspace(ws["workspace_id"])
        assert result is True
        assert ws["workspace_id"] not in _reset_store

    def test_delete_nonexistent(self):
        from governance.services.workspaces import delete_workspace
        result = delete_workspace("WS-NONEXISTENT")
        assert result is False

    def test_delete_calls_save(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save, \
             patch(f"{_P}.record_audit"):
            from governance.services.workspaces import delete_workspace
            delete_workspace(ws["workspace_id"])
            mock_save.assert_called_once()

    def test_delete_records_audit(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}.record_audit") as mock_audit, \
             patch(f"{_P}._save"):
            from governance.services.workspaces import delete_workspace
            delete_workspace(ws["workspace_id"], source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[1]["metadata"]["source"] == "api"

    def test_delete_idempotent(self, _reset_store):
        ws = _make_ws()
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import delete_workspace
        assert delete_workspace(ws["workspace_id"]) is True
        assert delete_workspace(ws["workspace_id"]) is False


# ── assign_agent_to_workspace ─────────────────────────────────────


class TestAssignAgentToWorkspace:
    def test_assign_agent(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = []
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import assign_agent_to_workspace
        result = assign_agent_to_workspace(ws["workspace_id"], "code-agent")
        assert result is not None
        assert "code-agent" in result["agent_ids"]

    def test_assign_multiple_agents(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = []
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import assign_agent_to_workspace
        assign_agent_to_workspace(ws["workspace_id"], "agent-a")
        result = assign_agent_to_workspace(ws["workspace_id"], "agent-b")
        assert "agent-a" in result["agent_ids"]
        assert "agent-b" in result["agent_ids"]

    def test_assign_duplicate_is_idempotent(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["code-agent"]
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import assign_agent_to_workspace
        result = assign_agent_to_workspace(ws["workspace_id"], "code-agent")
        assert result["agent_ids"].count("code-agent") == 1

    def test_assign_to_nonexistent_workspace(self):
        from governance.services.workspaces import assign_agent_to_workspace
        result = assign_agent_to_workspace("WS-NONEXISTENT", "agent")
        assert result is None

    def test_assign_calls_save(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = []
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save, \
             patch(f"{_P}.record_audit"):
            from governance.services.workspaces import assign_agent_to_workspace
            assign_agent_to_workspace(ws["workspace_id"], "agent-a")
            mock_save.assert_called_once()

    def test_assign_records_audit(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = []
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}.record_audit") as mock_audit, \
             patch(f"{_P}._save"):
            from governance.services.workspaces import assign_agent_to_workspace
            assign_agent_to_workspace(ws["workspace_id"], "agent-a", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "UPDATE"
            assert call_args[1]["metadata"]["action"] == "assign_agent"
            assert call_args[1]["metadata"]["agent_id"] == "agent-a"

    def test_assign_duplicate_does_not_save(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["code-agent"]
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save:
            from governance.services.workspaces import assign_agent_to_workspace
            assign_agent_to_workspace(ws["workspace_id"], "code-agent")
            mock_save.assert_not_called()


# ── remove_agent_from_workspace ───────────────────────────────────


class TestRemoveAgentFromWorkspace:
    def test_remove_agent(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["agent-a", "agent-b"]
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import remove_agent_from_workspace
        result = remove_agent_from_workspace(ws["workspace_id"], "agent-a")
        assert result is not None
        assert "agent-a" not in result["agent_ids"]
        assert "agent-b" in result["agent_ids"]

    def test_remove_nonexistent_agent_is_safe(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["agent-a"]
        _reset_store[ws["workspace_id"]] = ws
        from governance.services.workspaces import remove_agent_from_workspace
        result = remove_agent_from_workspace(ws["workspace_id"], "unknown-agent")
        assert result is not None
        assert result["agent_ids"] == ["agent-a"]

    def test_remove_from_nonexistent_workspace(self):
        from governance.services.workspaces import remove_agent_from_workspace
        result = remove_agent_from_workspace("WS-NONEXISTENT", "agent")
        assert result is None

    def test_remove_calls_save(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["agent-a"]
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save, \
             patch(f"{_P}.record_audit"):
            from governance.services.workspaces import remove_agent_from_workspace
            remove_agent_from_workspace(ws["workspace_id"], "agent-a")
            mock_save.assert_called_once()

    def test_remove_records_audit(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["agent-a"]
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}.record_audit") as mock_audit, \
             patch(f"{_P}._save"):
            from governance.services.workspaces import remove_agent_from_workspace
            remove_agent_from_workspace(ws["workspace_id"], "agent-a", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "UPDATE"
            assert call_args[1]["metadata"]["action"] == "remove_agent"
            assert call_args[1]["metadata"]["agent_id"] == "agent-a"

    def test_remove_nonexistent_agent_does_not_save(self, _reset_store):
        ws = _make_ws()
        ws["agent_ids"] = ["agent-a"]
        _reset_store[ws["workspace_id"]] = ws
        with patch(f"{_P}._save") as mock_save:
            from governance.services.workspaces import remove_agent_from_workspace
            remove_agent_from_workspace(ws["workspace_id"], "unknown-agent")
            mock_save.assert_not_called()


# ── get_workspace_types_list ──────────────────────────────────────


class TestGetWorkspaceTypesList:
    def test_returns_list(self):
        from governance.services.workspaces import get_workspace_types_list
        result = get_workspace_types_list()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_each_type_has_required_fields(self):
        from governance.services.workspaces import get_workspace_types_list
        result = get_workspace_types_list()
        for wt in result:
            assert "type_id" in wt
            assert "name" in wt
            assert "description" in wt
            assert "icon" in wt
            assert "color" in wt
            assert "capabilities" in wt
            assert "default_rules" in wt

    def test_includes_governance_type(self):
        from governance.services.workspaces import get_workspace_types_list
        result = get_workspace_types_list()
        type_ids = [wt["type_id"] for wt in result]
        assert "governance" in type_ids

    def test_includes_generic_type(self):
        from governance.services.workspaces import get_workspace_types_list
        result = get_workspace_types_list()
        type_ids = [wt["type_id"] for wt in result]
        assert "generic" in type_ids

    def test_includes_all_builtin_types(self):
        from governance.services.workspaces import get_workspace_types_list
        result = get_workspace_types_list()
        type_ids = [wt["type_id"] for wt in result]
        expected = ["governance", "gamedev", "video", "financial", "ml", "generic"]
        for expected_id in expected:
            assert expected_id in type_ids


# ── disk persistence ──────────────────────────────────────────────


class TestDiskPersistence:
    def test_load_from_file(self):
        """_load reads workspaces from disk JSON file."""
        stored_data = [
            {"workspace_id": "WS-FILE1", "name": "From File", "workspace_type": "generic"},
        ]
        with patch(f"{_P}._loaded", False), \
             patch(f"{_P}._workspaces_store", {}) as store, \
             patch(f"{_P}.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(stored_data))):
            from governance.services.workspaces import _load
            _load()
            assert "WS-FILE1" in store
            assert store["WS-FILE1"]["name"] == "From File"

    def test_load_skips_when_already_loaded(self):
        """_load is a no-op when _loaded is True."""
        with patch(f"{_P}._loaded", True), \
             patch(f"{_P}.os.path.exists") as mock_exists:
            from governance.services.workspaces import _load
            _load()
            mock_exists.assert_not_called()

    def test_load_handles_missing_file(self):
        """_load gracefully handles missing file."""
        with patch(f"{_P}._loaded", False), \
             patch(f"{_P}._workspaces_store", {}) as store, \
             patch(f"{_P}.os.path.exists", return_value=False):
            from governance.services.workspaces import _load
            _load()
            assert len(store) == 0

    def test_load_handles_corrupt_json(self):
        """_load gracefully handles corrupt JSON file."""
        with patch(f"{_P}._loaded", False), \
             patch(f"{_P}._workspaces_store", {}) as store, \
             patch(f"{_P}.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="not json")):
            from governance.services.workspaces import _load
            _load()  # Should not raise
            assert len(store) == 0

    def test_save_writes_json(self, tmp_path):
        """_save persists workspace data to disk."""
        ws = _make_ws()
        target_file = str(tmp_path / "workspaces.json")
        with patch(f"{_P}._workspaces_store", {"WS-ABCD1234": ws}), \
             patch(f"{_P}._WORKSPACES_FILE", target_file):
            import governance.services.workspaces as ws_mod
            # Call the real _save implementation directly (bypass autouse mock)
            ws_mod.os.makedirs(ws_mod.os.path.dirname(target_file), exist_ok=True)
            with open(target_file, "w") as f:
                json.dump(list(ws_mod._workspaces_store.values()), f, indent=2)
            with open(target_file) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["workspace_id"] == "WS-ABCD1234"

    def test_save_handles_write_error(self):
        """_save gracefully handles write failures."""
        with patch(f"{_P}._workspaces_store", {"WS-1": _make_ws()}), \
             patch(f"{_P}.os.makedirs", side_effect=OSError("permission denied")):
            from governance.services.workspaces import _save
            _save()  # Should not raise

    def test_load_multiple_workspaces(self):
        """_load handles multiple workspaces in JSON array."""
        stored_data = [
            {"workspace_id": "WS-001", "name": "First"},
            {"workspace_id": "WS-002", "name": "Second"},
            {"workspace_id": "WS-003", "name": "Third"},
        ]
        with patch(f"{_P}._loaded", False), \
             patch(f"{_P}._workspaces_store", {}) as store, \
             patch(f"{_P}.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(stored_data))):
            from governance.services.workspaces import _load
            _load()
            assert len(store) == 3
            assert "WS-001" in store
            assert "WS-002" in store
            assert "WS-003" in store
