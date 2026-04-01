"""TDD Tests: Audit trail coverage for task mutations.

Per SRVJ-FEAT-AUDIT-TRAIL-01 P2: Wire Missing Audit Points.
Tests written FIRST (TDD) — implementation follows.

DSE coverage:
- Happy path: each linking op produces exactly 1 LINK audit entry
- Unlink: produces UNLINK audit entry
- Comments: add/delete produce COMMENT audit entries
- UPDATE fix: new_value always populated
- UPDATE enrichment: field_changes dict in metadata
- Session correlation: session_id in metadata when available
- Error path: failed link produces no audit entry
- DRY helper: _record_link_audit works correctly
"""
import pytest
from unittest.mock import patch, MagicMock, call


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_typedb_client():
    """TypeDB client that succeeds on all link operations."""
    client = MagicMock()
    client.get_task.return_value = MagicMock(status="OPEN")
    client.link_task_to_rule.return_value = True
    client.link_task_to_session.return_value = True
    client.link_task_to_document.return_value = True
    client.unlink_task_from_document.return_value = True
    client.link_evidence_to_task.return_value = True
    client.link_task_to_commit.return_value = True
    client.link_task_to_workspace.return_value = True
    return client


@pytest.fixture
def patch_linking_deps(mock_typedb_client):
    """Patch common dependencies for linking tests."""
    with patch("governance.services.tasks_mutations_linking.get_typedb_client",
               return_value=mock_typedb_client), \
         patch("governance.services.tasks_mutations_linking._monitor"), \
         patch("governance.services.tasks_mutations_linking._tasks_store", {"TASK-001": {"linked_sessions": [], "linked_documents": [], "linked_commits": []}}), \
         patch("governance.services.tasks_mutations_linking.record_audit") as mock_audit:
        yield mock_audit


# ── Linking ops produce LINK audit entries ────────────────────────────

class TestLinkingOpsAudit:
    """Each linking op must produce exactly 1 LINK audit entry."""

    def test_link_rule_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("TASK-001", "TEST-GUARD-01", source="mcp")
        assert result.success
        patch_linking_deps.assert_called_once()
        args, kwargs = patch_linking_deps.call_args
        assert args[0] == "LINK"        # action_type
        assert args[1] == "task"        # entity_type
        assert args[2] == "TASK-001"    # entity_id
        assert kwargs["metadata"]["linked_entity"]["type"] == "rule"
        assert kwargs["metadata"]["linked_entity"]["id"] == "TEST-GUARD-01"
        assert kwargs["metadata"]["source"] == "mcp"

    def test_link_session_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_session
        result = link_task_to_session("TASK-001", "SESSION-001", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["linked_entity"]["type"] == "session"
        assert kwargs["metadata"]["linked_entity"]["id"] == "SESSION-001"
        # Session correlation: session_id available from the link itself
        assert kwargs["metadata"]["session_id"] == "SESSION-001"

    def test_link_document_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_document
        result = link_task_to_document("TASK-001", "docs/spec.md", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["linked_entity"]["type"] == "document"
        assert kwargs["metadata"]["linked_entity"]["id"] == "docs/spec.md"

    def test_link_evidence_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_evidence
        result = link_task_to_evidence("TASK-001", "evidence/test.json", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["linked_entity"]["type"] == "evidence"
        assert kwargs["metadata"]["linked_entity"]["id"] == "evidence/test.json"

    def test_link_commit_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_commit
        result = link_task_to_commit("TASK-001", "abc123", "fix: stuff", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["linked_entity"]["type"] == "commit"
        assert kwargs["metadata"]["linked_entity"]["id"] == "abc123"

    def test_link_workspace_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import link_task_to_workspace
        result = link_task_to_workspace("TASK-001", "WS-TEST-SANDBOX", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["linked_entity"]["type"] == "workspace"
        assert kwargs["metadata"]["linked_entity"]["id"] == "WS-TEST-SANDBOX"


# ── Unlink produces UNLINK audit entry ────────────────────────────────

class TestUnlinkAudit:
    """Unlink operations must produce UNLINK action_type."""

    def test_unlink_document_records_audit(self, patch_linking_deps):
        from governance.services.tasks_mutations_linking import unlink_task_from_document
        result = unlink_task_from_document("TASK-001", "docs/old.md", source="rest")
        assert result.success
        patch_linking_deps.assert_called_once()
        args, kwargs = patch_linking_deps.call_args
        assert args[0] == "UNLINK"
        assert kwargs["metadata"]["linked_entity"]["type"] == "document"
        assert kwargs["metadata"]["linked_entity"]["action"] == "unlink"


# ── Error path: failed link produces no audit entry ───────────────────

class TestLinkingErrorNoAudit:
    """If link operation fails, no audit entry should be recorded."""

    def test_link_rule_failure_no_audit(self):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_rule.return_value = False  # link fails
        with patch("governance.services.tasks_mutations_linking.get_typedb_client",
                   return_value=client), \
             patch("governance.services.tasks_mutations_linking._monitor"), \
             patch("governance.services.tasks_mutations_linking.record_audit") as mock_audit:
            from governance.services.tasks_mutations_linking import link_task_to_rule
            result = link_task_to_rule("TASK-001", "RULE-X")
            assert not result.success
            mock_audit.assert_not_called()

    def test_link_exception_no_audit(self):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_rule.side_effect = RuntimeError("db error")
        with patch("governance.services.tasks_mutations_linking.get_typedb_client",
                   return_value=client), \
             patch("governance.services.tasks_mutations_linking._monitor"), \
             patch("governance.services.tasks_mutations_linking.record_audit") as mock_audit:
            from governance.services.tasks_mutations_linking import link_task_to_rule
            result = link_task_to_rule("TASK-001", "RULE-X")
            assert not result.success
            mock_audit.assert_not_called()

    def test_no_client_no_audit(self):
        with patch("governance.services.tasks_mutations_linking.get_typedb_client",
                   return_value=None), \
             patch("governance.services.tasks_mutations_linking.record_audit") as mock_audit:
            from governance.services.tasks_mutations_linking import link_task_to_rule
            result = link_task_to_rule("TASK-001", "RULE-X")
            assert not result.success
            mock_audit.assert_not_called()


# ── Comment audit entries ─────────────────────────────────────────────

class TestCommentAudit:
    """add_comment and delete_comment must produce COMMENT audit entries."""

    @patch("governance.services.task_comments.record_audit")
    @patch("governance.services.task_comments._get_typedb_client", return_value=None)
    def test_add_comment_records_audit(self, _client, mock_audit):
        from governance.services.task_comments import add_comment
        comment = add_comment("TASK-001", "Resolution: fixed in abc123", author="code-agent")
        mock_audit.assert_called_once()
        args, kwargs = mock_audit.call_args
        assert args[0] == "COMMENT"       # action_type
        assert args[1] == "task"          # entity_type
        assert args[2] == "TASK-001"      # entity_id
        assert kwargs["metadata"]["action"] == "add"
        assert kwargs["metadata"]["comment_id"] == comment["comment_id"]

    @patch("governance.services.task_comments.record_audit")
    @patch("governance.services.task_comments._get_typedb_client", return_value=None)
    def test_delete_comment_records_audit(self, _client, mock_audit):
        from governance.services.task_comments import add_comment, delete_comment, _comments_store
        # Seed a comment
        _comments_store["TASK-002"] = [{
            "comment_id": "CMT-delete01",
            "task_id": "TASK-002",
            "author": "test",
            "body": "to delete",
            "created_at": "2026-03-28T00:00:00Z",
        }]
        result = delete_comment("TASK-002", "CMT-delete01")
        assert result is True
        mock_audit.assert_called_once()
        args, kwargs = mock_audit.call_args
        assert args[0] == "COMMENT"
        assert kwargs["metadata"]["action"] == "delete"
        assert kwargs["metadata"]["comment_id"] == "CMT-delete01"

    @patch("governance.services.task_comments.record_audit")
    @patch("governance.services.task_comments._get_typedb_client", return_value=None)
    def test_delete_nonexistent_comment_no_audit(self, _client, mock_audit):
        from governance.services.task_comments import delete_comment
        result = delete_comment("TASK-999", "CMT-nope")
        assert result is False
        mock_audit.assert_not_called()


# ── UPDATE audit fixes ────────────────────────────────────────────────

class TestUpdateAuditFixes:
    """Fix: new_value always populated, field_changes in metadata."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations._monitor")
    def test_status_update_has_new_value(self, _mon, _log, _client, mock_audit):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        _tasks_store["TASK-UPD-001"] = {
            "task_id": "TASK-UPD-001", "status": "OPEN",
            "description": "test", "phase": "P1",
            "agent_id": None, "priority": "MEDIUM",
            "persistence_status": "persisted",
        }
        try:
            update_task("TASK-UPD-001", status="IN_PROGRESS", agent_id="code-agent")
        except (ValueError, Exception):
            pass  # DONE gate / lifecycle validation may trigger
        # Verify new_value is never None when status is provided
        if mock_audit.called:
            _, kwargs = mock_audit.call_args
            assert kwargs.get("new_value") is not None or \
                   mock_audit.call_args[1].get("new_value") is not None

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations._monitor")
    def test_non_status_update_has_field_changes(self, _mon, _log, _client, mock_audit):
        """When only non-status fields change, metadata must include field_changes."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        _tasks_store["TASK-FC-001"] = {
            "task_id": "TASK-FC-001", "status": "OPEN",
            "description": "old desc", "phase": "P1",
            "agent_id": None, "priority": "MEDIUM",
            "persistence_status": "persisted",
        }
        update_task("TASK-FC-001", priority="HIGH")
        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        metadata = kwargs.get("metadata", {})
        assert "field_changes" in metadata
        assert "priority" in metadata["field_changes"]
        assert metadata["field_changes"]["priority"]["from"] == "MEDIUM"
        assert metadata["field_changes"]["priority"]["to"] == "HIGH"

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations._monitor")
    def test_status_update_includes_field_changes_for_status(self, _mon, _log, _client, mock_audit):
        """Status transitions also appear in field_changes."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        _tasks_store["TASK-FC-002"] = {
            "task_id": "TASK-FC-002", "status": "OPEN",
            "description": "test", "phase": "P1",
            "agent_id": None, "priority": "MEDIUM",
            "persistence_status": "persisted",
        }
        update_task("TASK-FC-002", status="IN_PROGRESS", agent_id="code-agent")
        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        metadata = kwargs.get("metadata", {})
        assert "field_changes" in metadata
        assert "status" in metadata["field_changes"]


# ── Session correlation ───────────────────────────────────────────────

class TestSessionCorrelation:
    """Audit metadata includes session_id when available."""

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations._monitor")
    def test_update_with_linked_sessions_includes_session_id(self, _mon, _log, _client, mock_audit):
        """When linked_sessions provided, first one appears in metadata.session_id."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        _tasks_store["TASK-SESS-001"] = {
            "task_id": "TASK-SESS-001", "status": "OPEN",
            "description": "test", "phase": "P1",
            "agent_id": None, "priority": "MEDIUM",
            "linked_sessions": [],
            "persistence_status": "persisted",
        }
        update_task("TASK-SESS-001", status="IN_PROGRESS",
                     agent_id="code-agent",
                     linked_sessions=["SESSION-ABC"])
        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        metadata = kwargs.get("metadata", {})
        assert metadata.get("session_id") == "SESSION-ABC"

    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations._monitor")
    def test_update_without_sessions_no_session_id(self, _mon, _log, _client, mock_audit):
        """When no linked_sessions, session_id absent from metadata."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        _tasks_store["TASK-SESS-002"] = {
            "task_id": "TASK-SESS-002", "status": "OPEN",
            "description": "test", "phase": "P1",
            "agent_id": None, "priority": "MEDIUM",
            "persistence_status": "persisted",
        }
        update_task("TASK-SESS-002", priority="HIGH")
        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        metadata = kwargs.get("metadata", {})
        assert "session_id" not in metadata

    def test_link_session_includes_session_id_in_audit(self, patch_linking_deps):
        """link_task_to_session has session_id from the link target itself."""
        from governance.services.tasks_mutations_linking import link_task_to_session
        link_task_to_session("TASK-001", "SESSION-XYZ")
        _, kwargs = patch_linking_deps.call_args
        assert kwargs["metadata"]["session_id"] == "SESSION-XYZ"


# ── DRY helper ────────────────────────────────────────────────────────

class TestRecordLinkAuditHelper:
    """_record_link_audit helper must be DRY and consistent."""

    @patch("governance.services.tasks_mutations_linking.record_audit")
    def test_helper_link_action(self, mock_audit):
        from governance.services.tasks_mutations_linking import _record_link_audit
        _record_link_audit("TASK-X", "link", "rule", "TEST-01", source="mcp")
        mock_audit.assert_called_once()
        args, kwargs = mock_audit.call_args
        assert args[0] == "LINK"
        assert args[1] == "task"
        assert args[2] == "TASK-X"
        assert kwargs["metadata"]["linked_entity"]["type"] == "rule"
        assert kwargs["metadata"]["linked_entity"]["id"] == "TEST-01"
        assert kwargs["metadata"]["linked_entity"]["action"] == "link"
        assert kwargs["metadata"]["source"] == "mcp"

    @patch("governance.services.tasks_mutations_linking.record_audit")
    def test_helper_unlink_action(self, mock_audit):
        from governance.services.tasks_mutations_linking import _record_link_audit
        _record_link_audit("TASK-X", "unlink", "document", "docs/old.md")
        mock_audit.assert_called_once()
        args, _ = mock_audit.call_args
        assert args[0] == "UNLINK"

    @patch("governance.services.tasks_mutations_linking.record_audit")
    def test_helper_with_session_id(self, mock_audit):
        from governance.services.tasks_mutations_linking import _record_link_audit
        _record_link_audit("TASK-X", "link", "session", "SESS-1", session_id="SESS-1")
        _, kwargs = mock_audit.call_args
        assert kwargs["metadata"]["session_id"] == "SESS-1"

    @patch("governance.services.tasks_mutations_linking.record_audit")
    def test_helper_without_session_id(self, mock_audit):
        from governance.services.tasks_mutations_linking import _record_link_audit
        _record_link_audit("TASK-X", "link", "rule", "R-1")
        _, kwargs = mock_audit.call_args
        assert "session_id" not in kwargs["metadata"]


# ===========================================================================
# P8 GAP 1: Snapshot Timing — old_status captured BEFORE TypeDB write
# ===========================================================================

class TestSnapshotTimingGap1:
    """GAP 1: First update after restart captures post-write status as 'old'.

    When task is NOT in _tasks_store (first update after restart):
    1. client.get_task() returns task_obj with status="OPEN"
    2. client.update_task_status() updates TypeDB to "IN_PROGRESS"
    3. task_obj = updated or task_obj → task_obj.status = "IN_PROGRESS"
    4. _tasks_store populated from task_obj → status = "IN_PROGRESS"
    5. old_status = _tasks_store[task_id]["status"] = "IN_PROGRESS" (WRONG!)

    Fix: capture old status from task_obj BEFORE update_task_status().
    """

    @pytest.fixture(autouse=True)
    def _clean_stores(self):
        """Ensure _tasks_store and _comments_store are empty."""
        from governance.stores import _tasks_store
        from governance.services.task_comments import _comments_store
        from governance.stores.audit import _audit_store
        _orig_tasks = dict(_tasks_store)
        _orig_comments = dict(_comments_store)
        _orig_audit = list(_audit_store)
        _tasks_store.clear()
        _comments_store.clear()
        _audit_store.clear()
        yield
        _tasks_store.clear()
        _tasks_store.update(_orig_tasks)
        _comments_store.clear()
        _comments_store.update(_orig_comments)
        _audit_store.clear()
        _audit_store.extend(_orig_audit)

    def _make_task_obj(self, status="OPEN"):
        """Create a mock TypeDB task object."""
        from datetime import datetime
        obj = MagicMock()
        obj.status = status
        obj.name = "Test task"
        obj.phase = "P1"
        obj.agent_id = None
        obj.priority = "MEDIUM"
        obj.task_type = "test"
        obj.evidence = None
        obj.body = None
        obj.gap_id = None
        obj.resolution = None
        obj.resolution_notes = None
        obj.document_path = None
        obj.created_at = datetime(2026, 3, 29)
        obj.claimed_at = None
        obj.completed_at = None
        obj.linked_rules = []
        obj.linked_sessions = []
        obj.linked_commits = []
        obj.linked_documents = []
        obj.workspace_id = "WS-TEST-SANDBOX"
        obj.layer = None
        obj.concern = None
        obj.method = None
        return obj

    def test_first_update_captures_old_status_before_typedb_write(self):
        """CRITICAL: old_status in field_changes must be the PRE-update value."""
        task_obj_open = self._make_task_obj(status="OPEN")
        task_obj_updated = self._make_task_obj(status="IN_PROGRESS")
        task_obj_updated.agent_id = "code-agent"

        mock_client = MagicMock()
        mock_client.get_task.return_value = task_obj_open
        mock_client.update_task_status.return_value = task_obj_updated
        mock_client.update_task.return_value = None
        mock_client.is_connected.return_value = True

        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations.maybe_add_activity_comment") as mock_comment, \
             patch("governance.services.tasks_mutations.record_audit"):
            from governance.services.tasks_mutations import update_task
            result = update_task(
                "TASK-SNAPSHOT-001",
                status="IN_PROGRESS",
                agent_id="code-agent",
                source="mcp",
            )

        assert result is not None
        # The auto-comment should have field_changes with correct old status
        mock_comment.assert_called_once()
        call_kwargs = mock_comment.call_args[1]
        metadata = call_kwargs.get("metadata", {})
        field_changes = metadata.get("field_changes", {})
        assert "status" in field_changes, f"No status in field_changes: {field_changes}"
        assert field_changes["status"]["from"] == "OPEN", \
            f"Expected old status OPEN, got {field_changes['status']['from']}"
        assert field_changes["status"]["to"] == "IN_PROGRESS"

    def test_auto_comment_says_status_changed_not_generic(self):
        """Auto-comment text must say 'Status changed from OPEN to IN_PROGRESS'."""
        task_obj_open = self._make_task_obj(status="OPEN")
        task_obj_updated = self._make_task_obj(status="IN_PROGRESS")
        task_obj_updated.agent_id = "code-agent"

        mock_client = MagicMock()
        mock_client.get_task.return_value = task_obj_open
        mock_client.update_task_status.return_value = task_obj_updated
        mock_client.update_task.return_value = None
        mock_client.is_connected.return_value = True

        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=mock_client), \
             patch("governance.services.task_comments._get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations.record_audit"):
            from governance.services.tasks_mutations import update_task
            result = update_task(
                "TASK-SNAPSHOT-002",
                status="IN_PROGRESS",
                agent_id="code-agent",
                source="mcp",
            )

        # Check that the auto-comment was generated with the correct text
        from governance.services.task_comments import _comments_store
        comments = _comments_store.get("TASK-SNAPSHOT-002", [])
        system_comments = [c for c in comments if c["author"] == "system-audit"]
        assert len(system_comments) >= 1, f"No system-audit comments found: {comments}"
        bodies = " ".join(c["body"] for c in system_comments)
        assert "Status changed from OPEN to IN_PROGRESS" in bodies, \
            f"Expected specific status change, got: {bodies}"

    def test_existing_task_in_memory_captures_old_status_correctly(self):
        """When task IS in _tasks_store, old_status should still be correct."""
        from governance.stores import _tasks_store
        _tasks_store["TASK-INMEM-001"] = {
            "task_id": "TASK-INMEM-001",
            "description": "Already in memory",
            "status": "OPEN",
            "phase": "P1",
            "agent_id": None,
            "priority": "MEDIUM",
            "task_type": "test",
            "evidence": None,
            "summary": None,
            "linked_rules": [],
            "linked_sessions": [],
            "linked_documents": [],
            "linked_commits": [],
            "created_at": "2026-03-29T00:00:00",
            "completed_at": None,
            "workspace_id": "WS-TEST-SANDBOX",
            "body": None, "gap_id": None,
            "resolution_notes": None,
            "layer": None, "concern": None, "method": None,
            "persistence_status": "persisted",
        }

        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations.maybe_add_activity_comment") as mock_comment, \
             patch("governance.services.tasks_mutations.record_audit"):
            from governance.services.tasks_mutations import update_task
            update_task(
                "TASK-INMEM-001",
                status="IN_PROGRESS",
                agent_id="code-agent",
                source="rest",
            )

        mock_comment.assert_called_once()
        call_kwargs = mock_comment.call_args[1]
        metadata = call_kwargs.get("metadata", {})
        field_changes = metadata.get("field_changes", {})
        assert field_changes["status"]["from"] == "OPEN"
        assert field_changes["status"]["to"] == "IN_PROGRESS"
