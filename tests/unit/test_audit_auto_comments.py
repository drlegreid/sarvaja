"""Unit tests for auto-generated activity comments — SRVJ-FEAT-AUDIT-TRAIL-01 P7.

TDD: RED phase — all tests written BEFORE implementation.
Tests cover:
  - Comment text generation for every action_type
  - Actor + source attribution in comment body
  - Deliverable references (evidence snippet, rule ID, session ID, doc path)
  - Infinite loop prevention (COMMENT action -> None)
  - Batch: multi-field update -> single comment
  - Pagination for list_comments()
  - Adversarial: recursive call guards, missing metadata, None values
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_comments_store():
    """Reset in-memory comments store between tests."""
    from governance.services.task_comments import _comments_store
    _comments_store.clear()
    yield
    _comments_store.clear()


@pytest.fixture(autouse=True)
def _clean_audit_store():
    """Reset in-memory audit store between tests."""
    from governance.stores.audit import _audit_store
    _audit_store.clear()
    yield
    _audit_store.clear()


@pytest.fixture
def seed_task():
    """Seed a task in _tasks_store for mutation tests."""
    from governance.stores import _tasks_store
    task_id = "SRVJ-TEST-AUTOCOMMENT-001"
    _tasks_store[task_id] = {
        "task_id": task_id,
        "description": "Auto-comment test task",
        "status": "OPEN",
        "priority": "MEDIUM",
        "phase": "P1",
        "agent_id": None,
        "task_type": "test",
        "evidence": None,
        "summary": "Original summary",
        "linked_rules": [],
        "linked_sessions": [],
        "linked_documents": [],
        "linked_commits": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "workspace_id": "WS-TEST-SANDBOX",
        "body": None,
        "gap_id": None,
        "resolution_notes": None,
        "layer": None,
        "concern": None,
        "method": None,
        "persistence_status": "memory_only",
    }
    yield task_id
    _tasks_store.pop(task_id, None)


# ===========================================================================
# A. Comment text generation — format_activity_text()
# ===========================================================================

class TestFormatActivityText:
    """Test the pure text formatting function."""

    def test_status_change_includes_old_new_actor_source(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="mcp",
            old_value="OPEN",
            new_value="IN_PROGRESS",
            metadata={"field_changes": {"status": {"from": "OPEN", "to": "IN_PROGRESS"}}},
        )
        assert text is not None
        assert "OPEN" in text
        assert "IN_PROGRESS" in text
        assert "code-agent" in text
        assert "mcp" in text

    def test_status_change_format_human_readable(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="rest",
            old_value="OPEN",
            new_value="IN_PROGRESS",
            metadata={"field_changes": {"status": {"from": "OPEN", "to": "IN_PROGRESS"}}},
        )
        assert "Status changed from OPEN to IN_PROGRESS" in text

    def test_link_rule_includes_rule_id_and_actor(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="mcp",
            metadata={"linked_entity": {"type": "rule", "id": "TEST-E2E-01-v1", "action": "link"}},
        )
        assert "Rule TEST-E2E-01-v1 linked" in text
        assert "system" in text
        assert "mcp" in text

    def test_link_session_includes_session_id(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="rest",
            metadata={
                "linked_entity": {"type": "session", "id": "SESSION-2026-03-29-P7", "action": "link"},
                "session_id": "SESSION-2026-03-29-P7",
            },
        )
        assert "Session SESSION-2026-03-29-P7 linked" in text

    def test_link_document_includes_path(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="rest",
            metadata={"linked_entity": {"type": "document", "id": "docs/spec.md", "action": "link"}},
        )
        assert "Document docs/spec.md linked" in text

    def test_unlink_document_says_unlinked(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UNLINK",
            actor_id="system",
            source="rest",
            metadata={"linked_entity": {"type": "document", "id": "docs/spec.md", "action": "unlink"}},
        )
        assert "Document docs/spec.md unlinked" in text

    def test_link_commit_includes_sha(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="rest",
            metadata={"linked_entity": {"type": "commit", "id": "abc123def", "action": "link"}},
        )
        assert "Commit abc123def linked" in text

    def test_link_evidence_includes_path(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="rest",
            metadata={"linked_entity": {"type": "evidence", "id": "evidence/test.json", "action": "link"}},
        )
        assert "Evidence evidence/test.json linked" in text

    def test_delete_includes_actor_and_source(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="DELETE",
            actor_id="code-agent",
            source="rest",
        )
        assert text is not None
        assert "deleted" in text.lower()
        assert "code-agent" in text
        assert "rest" in text

    def test_field_change_single_priority(self):
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="mcp",
            metadata={"field_changes": {"priority": {"from": "MEDIUM", "to": "HIGH"}}},
        )
        assert "priority" in text.lower()
        assert "MEDIUM" in text
        assert "HIGH" in text

    def test_field_change_multiple_fields_single_text(self):
        """Multiple field changes -> single text block listing all changes."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="rest",
            metadata={
                "field_changes": {
                    "summary": {"from": "Old", "to": "New"},
                    "phase": {"from": "P1", "to": "P2"},
                    "priority": {"from": "LOW", "to": "HIGH"},
                }
            },
        )
        # All three fields mentioned in one text
        assert "summary" in text.lower()
        assert "phase" in text.lower()
        assert "priority" in text.lower()

    def test_evidence_update_includes_snippet(self):
        """Evidence field change includes a snippet of the new evidence text."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="rest",
            metadata={
                "field_changes": {
                    "evidence": {
                        "from": None,
                        "to": "[Verification: L2] All 42 tests passed",
                    }
                }
            },
        )
        assert "Evidence updated" in text
        assert "Verification: L2" in text

    def test_evidence_long_snippet_truncated(self):
        """Evidence text >120 chars is truncated with ellipsis."""
        from governance.services.task_activity_comments import format_activity_text
        long_evidence = "[Verification: L3] " + "x" * 200
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="system",
            source="rest",
            metadata={
                "field_changes": {
                    "evidence": {"from": None, "to": long_evidence}
                }
            },
        )
        assert "..." in text
        assert len(text) < 500  # Reasonable cap


# ===========================================================================
# B. Infinite loop prevention
# ===========================================================================

class TestInfiniteLoopPrevention:
    """CRITICAL: COMMENT action must NEVER generate an auto-comment."""

    def test_comment_action_returns_none(self):
        """format_activity_text returns None for COMMENT action_type."""
        from governance.services.task_activity_comments import format_activity_text
        result = format_activity_text(
            action_type="COMMENT",
            actor_id="human-user",
            source="rest",
            metadata={"action": "add", "comment_id": "CMT-abc12345"},
        )
        assert result is None

    def test_maybe_add_skips_comment_action(self):
        """maybe_add_activity_comment returns None for COMMENT, never calls add_comment."""
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment") as mock_add:
            result = maybe_add_activity_comment(
                task_id="TASK-001",
                action_type="COMMENT",
                actor_id="user",
                source="rest",
            )
        assert result is None
        mock_add.assert_not_called()

    def test_add_comment_does_not_call_maybe_add(self):
        """Adversarial: add_comment() must NOT call maybe_add_activity_comment.
        Verifies the loop cannot form even if someone rewires the code."""
        import inspect
        from governance.services.task_comments import add_comment
        source = inspect.getsource(add_comment)
        assert "maybe_add_activity_comment" not in source
        assert "generate_activity_comment" not in source
        assert "task_activity_comments" not in source

    def test_record_audit_does_not_call_maybe_add(self):
        """Adversarial: record_audit() must NOT call auto-comment functions."""
        import inspect
        from governance.stores.audit import record_audit
        source = inspect.getsource(record_audit)
        assert "maybe_add_activity_comment" not in source
        assert "task_activity_comments" not in source

    def test_system_audit_author_comment_does_not_recurse(self):
        """Adding a comment with author=system-audit still calls record_audit
        but the COMMENT audit entry produces no further auto-comment."""
        from governance.services.task_comments import add_comment
        from governance.services.task_activity_comments import maybe_add_activity_comment

        # Simulate: auto-comment was added -> record_audit("COMMENT") fires
        # -> if someone mistakenly wired maybe_add from record_audit, it would loop
        # We verify that maybe_add for COMMENT returns None
        result = maybe_add_activity_comment(
            task_id="TASK-001",
            action_type="COMMENT",
            actor_id="system-audit",
            source="rest",
            metadata={"action": "add"},
        )
        assert result is None

    def test_rapid_updates_linear_comment_growth(self):
        """Adversarial: 10 rapid updates produce exactly 10 auto-comments, not exponential."""
        from governance.services.task_activity_comments import maybe_add_activity_comment
        from governance.services.task_comments import _comments_store

        task_id = "TASK-RAPID-001"
        for i in range(10):
            with patch("governance.services.task_activity_comments.add_comment") as mock_add:
                mock_add.return_value = {"comment_id": f"CMT-{i}", "author": "system-audit"}
                maybe_add_activity_comment(
                    task_id=task_id,
                    action_type="UPDATE",
                    actor_id="code-agent",
                    source="mcp",
                    old_value=f"STATUS_{i}",
                    new_value=f"STATUS_{i+1}",
                    metadata={"field_changes": {"status": {"from": f"S{i}", "to": f"S{i+1}"}}},
                )
                mock_add.assert_called_once()


# ===========================================================================
# C. Integration: maybe_add_activity_comment()
# ===========================================================================

class TestMaybeAddActivityComment:
    """Test the orchestrator function that generates text + calls add_comment."""

    def test_update_calls_add_comment_with_system_audit_author(self):
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment") as mock_add:
            mock_add.return_value = {"comment_id": "CMT-test", "author": "system-audit"}
            maybe_add_activity_comment(
                task_id="TASK-001",
                action_type="UPDATE",
                actor_id="code-agent",
                source="rest",
                old_value="OPEN",
                new_value="IN_PROGRESS",
                metadata={"field_changes": {"status": {"from": "OPEN", "to": "IN_PROGRESS"}}},
            )
        mock_add.assert_called_once()
        call_kwargs = mock_add.call_args
        assert call_kwargs[1].get("author") == "system-audit" or call_kwargs[0][2] == "system-audit" if len(call_kwargs[0]) > 2 else call_kwargs[1].get("author") == "system-audit"

    def test_update_passes_correct_task_id(self):
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment") as mock_add:
            mock_add.return_value = {"comment_id": "CMT-test", "author": "system-audit"}
            maybe_add_activity_comment(
                task_id="MY-TASK-42",
                action_type="UPDATE",
                actor_id="agent",
                source="rest",
                metadata={"field_changes": {"status": {"from": "A", "to": "B"}}},
            )
        args, kwargs = mock_add.call_args
        assert args[0] == "MY-TASK-42" or kwargs.get("task_id") == "MY-TASK-42"

    def test_link_calls_add_comment(self):
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment") as mock_add:
            mock_add.return_value = {"comment_id": "CMT-link", "author": "system-audit"}
            result = maybe_add_activity_comment(
                task_id="TASK-001",
                action_type="LINK",
                actor_id="system",
                source="mcp",
                metadata={"linked_entity": {"type": "rule", "id": "R-01", "action": "link"}},
            )
        mock_add.assert_called_once()
        assert result is not None

    def test_delete_calls_add_comment(self):
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment") as mock_add:
            mock_add.return_value = {"comment_id": "CMT-del", "author": "system-audit"}
            result = maybe_add_activity_comment(
                task_id="TASK-001",
                action_type="DELETE",
                actor_id="code-agent",
                source="rest",
            )
        mock_add.assert_called_once()
        assert result is not None

    def test_create_action_skipped(self):
        """CREATE actions don't produce auto-comments (task just appeared,
        the CREATE audit entry is sufficient)."""
        from governance.services.task_activity_comments import format_activity_text
        result = format_activity_text(
            action_type="CREATE",
            actor_id="system",
            source="rest",
        )
        assert result is None

    def test_missing_metadata_graceful(self):
        """UPDATE with no metadata (no field_changes) still produces a comment."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="code-agent",
            source="rest",
            metadata=None,
        )
        # Should produce generic "Task updated by code-agent (rest)" or similar
        assert text is not None
        assert "code-agent" in text

    def test_empty_field_changes_graceful(self):
        """UPDATE with empty field_changes dict still produces a comment."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="agent",
            source="mcp",
            metadata={"field_changes": {}},
        )
        assert text is not None

    def test_none_old_value_in_field_change(self):
        """Field change from None -> value shown as 'set to X' or 'None -> X'."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UPDATE",
            actor_id="agent",
            source="rest",
            metadata={"field_changes": {"agent_id": {"from": None, "to": "code-agent"}}},
        )
        assert "agent_id" in text.lower() or "agent" in text.lower()
        assert "code-agent" in text

    def test_link_missing_linked_entity_graceful(self):
        """LINK with no linked_entity in metadata -> still produces a comment."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="LINK",
            actor_id="system",
            source="rest",
            metadata={},
        )
        # Graceful fallback: generic link comment
        assert text is not None

    def test_unlink_action_type(self):
        """UNLINK produces comment with 'unlinked' verb."""
        from governance.services.task_activity_comments import format_activity_text
        text = format_activity_text(
            action_type="UNLINK",
            actor_id="system",
            source="rest",
            metadata={"linked_entity": {"type": "rule", "id": "R-01", "action": "unlink"}},
        )
        assert "unlinked" in text.lower()

    def test_add_comment_failure_does_not_raise(self):
        """If add_comment raises, maybe_add catches and logs (never crashes mutation)."""
        from governance.services.task_activity_comments import maybe_add_activity_comment
        with patch("governance.services.task_activity_comments.add_comment", side_effect=Exception("DB down")):
            result = maybe_add_activity_comment(
                task_id="TASK-001",
                action_type="UPDATE",
                actor_id="agent",
                source="rest",
                metadata={"field_changes": {"status": {"from": "A", "to": "B"}}},
            )
        assert result is None  # Failed gracefully


# ===========================================================================
# D. Pagination for list_comments()
# ===========================================================================

class TestCommentsPagination:
    """list_comments() should support offset + limit."""

    def _seed_comments(self, task_id, count):
        from governance.services.task_comments import add_comment
        for i in range(count):
            with patch("governance.services.task_comments._get_typedb_client", return_value=None):
                add_comment(task_id, body=f"Comment #{i}", author="test-user")

    def test_default_returns_all(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE", 5)
        result = list_comments("T-PAGE")
        assert len(result) == 5

    def test_limit_caps_results(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE2", 10)
        result = list_comments("T-PAGE2", limit=3)
        assert len(result) == 3

    def test_offset_skips_earlier(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE3", 5)
        all_comments = list_comments("T-PAGE3")
        page = list_comments("T-PAGE3", offset=2, limit=2)
        assert len(page) == 2
        assert page[0]["comment_id"] == all_comments[2]["comment_id"]

    def test_offset_beyond_total_returns_empty(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE4", 3)
        result = list_comments("T-PAGE4", offset=100, limit=10)
        assert result == []

    def test_limit_zero_returns_empty(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE5", 5)
        result = list_comments("T-PAGE5", limit=0)
        assert result == []

    def test_negative_offset_treated_as_zero(self):
        from governance.services.task_comments import list_comments
        self._seed_comments("T-PAGE6", 5)
        result = list_comments("T-PAGE6", offset=-1, limit=2)
        all_c = list_comments("T-PAGE6")
        assert result[0]["comment_id"] == all_c[0]["comment_id"]


# ===========================================================================
# E. Anti-rot cap with auto-comments
# ===========================================================================

class TestAntiRotCap:
    """Auto-comments share the 100-comment cap with user comments."""

    def test_auto_comments_count_toward_cap(self):
        from governance.services.task_comments import _comments_store, _MAX_COMMENTS_PER_TASK, add_comment
        task_id = "T-CAP"
        # Seed 98 user comments
        with patch("governance.services.task_comments._get_typedb_client", return_value=None):
            for i in range(98):
                add_comment(task_id, body=f"User #{i}", author="user")
        assert len(_comments_store[task_id]) == 98

        # Add 5 auto-comments (system-audit)
        with patch("governance.services.task_comments._get_typedb_client", return_value=None):
            for i in range(5):
                add_comment(task_id, body=f"Auto #{i}", author="system-audit")
        # Should be capped at 100
        assert len(_comments_store[task_id]) <= _MAX_COMMENTS_PER_TASK

    def test_oldest_comments_evicted_first(self):
        from governance.services.task_comments import _comments_store, add_comment
        task_id = "T-EVICT"
        with patch("governance.services.task_comments._get_typedb_client", return_value=None):
            for i in range(105):
                add_comment(task_id, body=f"Comment #{i}", author="user")
        comments = _comments_store[task_id]
        assert len(comments) == 100
        # First comment should be #5 (0-4 evicted)
        assert "Comment #5" in comments[0]["body"]


# ===========================================================================
# F. Wiring tests: mutations call maybe_add_activity_comment
# ===========================================================================

class TestMutationWiring:
    """Verify tasks_mutations.py calls maybe_add_activity_comment after record_audit."""

    def test_update_task_calls_auto_comment(self, seed_task):
        """update_task() should call maybe_add_activity_comment for UPDATE."""
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations import update_task
            update_task(seed_task, priority="HIGH", source="rest")
        mock_ac.assert_called_once()
        call_kwargs = mock_ac.call_args[1] if mock_ac.call_args[1] else {}
        call_args = mock_ac.call_args[0] if mock_ac.call_args[0] else ()
        # Verify task_id passed correctly
        assert seed_task in str(call_args) or call_kwargs.get("task_id") == seed_task

    def test_delete_task_calls_auto_comment(self, seed_task):
        """delete_task() should call maybe_add_activity_comment for DELETE."""
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
             patch("governance.services.tasks_mutations.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations import delete_task
            delete_task(seed_task, source="rest")
        mock_ac.assert_called_once()


class TestLinkingWiring:
    """Verify tasks_mutations_linking.py calls maybe_add_activity_comment."""

    def test_link_rule_calls_auto_comment(self):
        """link_task_to_rule should trigger auto-comment after _record_link_audit."""
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_rule.return_value = True
        with patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations_linking.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations_linking import link_task_to_rule
            link_task_to_rule("TASK-001", "RULE-01", source="mcp")
        mock_ac.assert_called_once()

    def test_link_session_calls_auto_comment(self):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_session.return_value = True
        with patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations_linking._tasks_store", {"TASK-001": {"linked_sessions": []}}), \
             patch("governance.services.tasks_mutations_linking.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations_linking import link_task_to_session
            link_task_to_session("TASK-001", "SESSION-01", source="mcp")
        mock_ac.assert_called_once()

    def test_unlink_document_calls_auto_comment(self):
        mock_client = MagicMock()
        mock_client.unlink_task_from_document.return_value = True
        with patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations_linking.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations_linking import unlink_task_from_document
            unlink_task_from_document("TASK-001", "docs/spec.md", source="rest")
        mock_ac.assert_called_once()

    def test_link_evidence_calls_auto_comment(self):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_evidence_to_task.return_value = True
        with patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations_linking.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations_linking import link_task_to_evidence
            link_task_to_evidence("TASK-001", "evidence/e.json", source="rest")
        mock_ac.assert_called_once()

    def test_link_commit_calls_auto_comment(self):
        mock_client = MagicMock()
        mock_client.get_task.return_value = MagicMock()
        mock_client.link_task_to_commit.return_value = True
        with patch("governance.services.tasks_mutations_linking.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations_linking._tasks_store", {"TASK-001": {"linked_commits": []}}), \
             patch("governance.services.tasks_mutations_linking.maybe_add_activity_comment") as mock_ac:
            from governance.services.tasks_mutations_linking import link_task_to_commit
            link_task_to_commit("TASK-001", "sha123", "msg", source="rest")
        mock_ac.assert_called_once()


# ===========================================================================
# G. Cross-Process Comment Read-Through (P8 — GAP 2)
# ===========================================================================

class TestCrossProcessReadThrough:
    """list_comments() must merge in-memory + TypeDB, dedup by comment_id.

    GAP 2: MCP-created comments are in TypeDB but not in the container's
    _comments_store. list_comments() must read-through from TypeDB.
    """

    def test_returns_in_memory_when_typedb_unavailable(self):
        """Fallback: TypeDB down → return only in-memory comments."""
        from governance.services.task_comments import add_comment, list_comments
        with patch("governance.services.task_comments._get_typedb_client", return_value=None):
            add_comment("T-XPROC-1", body="In-memory comment", author="user")
        with patch("governance.services.task_comments._get_typedb_client", return_value=None):
            result = list_comments("T-XPROC-1")
        assert len(result) == 1
        assert result[0]["body"] == "In-memory comment"

    def test_returns_typedb_comments_when_memory_empty(self):
        """TypeDB has comments but in-memory is empty → return TypeDB comments."""
        from governance.services.task_comments import list_comments
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = [
            {"comment_id": "CMT-typedb01", "task_id": "T-XPROC-2",
             "body": "TypeDB-only comment", "author": "mcp-agent",
             "created_at": "2026-03-29T10:00:00"},
        ]
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-2")
        assert len(result) == 1
        assert result[0]["comment_id"] == "CMT-typedb01"
        assert result[0]["body"] == "TypeDB-only comment"

    def test_merges_both_sources_dedup_by_comment_id(self):
        """Both sources have comments, some overlapping → dedup by comment_id."""
        from governance.services.task_comments import _comments_store, list_comments
        # Seed in-memory with 2 comments
        _comments_store["T-XPROC-3"] = [
            {"comment_id": "CMT-shared", "task_id": "T-XPROC-3",
             "body": "Shared (memory ver)", "author": "user",
             "created_at": "2026-03-29T09:00:00"},
            {"comment_id": "CMT-mem-only", "task_id": "T-XPROC-3",
             "body": "Memory-only pending", "author": "user",
             "created_at": "2026-03-29T09:01:00"},
        ]
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = [
            {"comment_id": "CMT-shared", "task_id": "T-XPROC-3",
             "body": "Shared (TypeDB ver)", "author": "user",
             "created_at": "2026-03-29T09:00:00"},
            {"comment_id": "CMT-typedb-only", "task_id": "T-XPROC-3",
             "body": "TypeDB-only from MCP", "author": "mcp-agent",
             "created_at": "2026-03-29T09:02:00"},
        ]
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-3")
        ids = [c["comment_id"] for c in result]
        assert len(ids) == len(set(ids)), f"Duplicates found: {ids}"
        assert len(result) == 3  # shared + mem-only + typedb-only
        # TypeDB wins on conflict
        shared = [c for c in result if c["comment_id"] == "CMT-shared"][0]
        assert shared["body"] == "Shared (TypeDB ver)"

    def test_typedb_query_failure_fallback_to_memory(self):
        """TypeDB get_comments_for_task() raises → graceful fallback to in-memory."""
        from governance.services.task_comments import _comments_store, list_comments
        _comments_store["T-XPROC-4"] = [
            {"comment_id": "CMT-fallback", "task_id": "T-XPROC-4",
             "body": "Still here", "author": "user",
             "created_at": "2026-03-29T10:00:00"},
        ]
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.side_effect = Exception("TypeDB timeout")
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-4")
        assert len(result) == 1
        assert result[0]["comment_id"] == "CMT-fallback"

    def test_preserves_chronological_order_after_merge(self):
        """Merged comments are sorted by created_at ascending."""
        from governance.services.task_comments import _comments_store, list_comments
        _comments_store["T-XPROC-5"] = [
            {"comment_id": "CMT-late", "task_id": "T-XPROC-5",
             "body": "Late memory", "author": "user",
             "created_at": "2026-03-29T12:00:00"},
        ]
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = [
            {"comment_id": "CMT-early", "task_id": "T-XPROC-5",
             "body": "Early TypeDB", "author": "mcp-agent",
             "created_at": "2026-03-29T08:00:00"},
            {"comment_id": "CMT-mid", "task_id": "T-XPROC-5",
             "body": "Mid TypeDB", "author": "mcp-agent",
             "created_at": "2026-03-29T10:00:00"},
        ]
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-5")
        assert result[0]["comment_id"] == "CMT-early"
        assert result[1]["comment_id"] == "CMT-mid"
        assert result[2]["comment_id"] == "CMT-late"

    def test_handles_typedb_comments_not_in_memory(self):
        """TypeDB returns comments that are completely absent from in-memory store."""
        from governance.services.task_comments import list_comments
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = [
            {"comment_id": "CMT-mcp-1", "task_id": "T-XPROC-6",
             "body": "MCP comment 1", "author": "system-audit",
             "created_at": "2026-03-29T09:00:00"},
            {"comment_id": "CMT-mcp-2", "task_id": "T-XPROC-6",
             "body": "MCP comment 2", "author": "system-audit",
             "created_at": "2026-03-29T09:01:00"},
        ]
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-6")
        assert len(result) == 2
        assert all(c["author"] == "system-audit" for c in result)

    def test_handles_memory_comments_not_in_typedb(self):
        """In-memory has pending comments not yet synced to TypeDB."""
        from governance.services.task_comments import _comments_store, list_comments
        _comments_store["T-XPROC-7"] = [
            {"comment_id": "CMT-pending-1", "task_id": "T-XPROC-7",
             "body": "Pending sync", "author": "user",
             "created_at": "2026-03-29T11:00:00"},
        ]
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = []  # TypeDB empty
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-7")
        assert len(result) == 1
        assert result[0]["comment_id"] == "CMT-pending-1"

    def test_pagination_works_after_merge(self):
        """offset/limit applied AFTER merge, not before."""
        from governance.services.task_comments import _comments_store, list_comments
        _comments_store["T-XPROC-8"] = [
            {"comment_id": f"CMT-mem-{i}", "task_id": "T-XPROC-8",
             "body": f"Mem {i}", "author": "user",
             "created_at": f"2026-03-29T0{i}:00:00"}
            for i in range(3)
        ]
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.get_comments_for_task.return_value = [
            {"comment_id": f"CMT-tdb-{i}", "task_id": "T-XPROC-8",
             "body": f"TDB {i}", "author": "mcp-agent",
             "created_at": f"2026-03-29T0{i+3}:00:00"}
            for i in range(3)
        ]
        with patch("governance.services.task_comments._get_typedb_client", return_value=mock_client):
            result = list_comments("T-XPROC-8", offset=2, limit=2)
        assert len(result) == 2  # Total 6, skip 2, take 2
