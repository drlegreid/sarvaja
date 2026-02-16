"""
Batch 62 — Deep Scan: Task linking TypeQL escaping + trust MCP escaping.

Fixes verified:
- BUG-LINK-ESCAPE-001: All fields escaped in TaskLinkingOperations
- BUG-LINK-ESCAPE-002: document_path escaped in link/unlink_task_to_document
- BUG-TRUST-ESCAPE-001: agent_id escaped in governance_get_trust_score
"""
import inspect

import pytest


# ===========================================================================
# BUG-LINK-ESCAPE-001: Task linking evidence escaping
# ===========================================================================

class TestTaskLinkingEvidenceEscaping:
    """Verify all fields escaped in link_evidence_to_task."""

    def _get_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.link_evidence_to_task)

    def test_evidence_source_escaped(self):
        """evidence_source must be escaped."""
        src = self._get_source()
        assert "evidence_source_escaped" in src

    def test_evidence_id_escaped(self):
        """evidence_id must be escaped."""
        src = self._get_source()
        assert "evidence_id_escaped" in src

    def test_task_id_escaped(self):
        """task_id must be escaped."""
        src = self._get_source()
        assert "task_id_escaped" in src

    def test_no_raw_evidence_source_in_query(self):
        """Must not have unescaped evidence_source in queries."""
        src = self._get_source()
        lines = src.split('\n')
        for line in lines:
            if 'evidence-source' in line and '{evidence_source' in line:
                assert 'evidence_source_escaped' in line, f"Unescaped: {line.strip()}"


# ===========================================================================
# BUG-LINK-ESCAPE-001: Task-session linking escaping
# ===========================================================================

class TestTaskSessionLinkingEscaping:
    """Verify fields escaped in link_task_to_session."""

    def _get_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.link_task_to_session)

    def test_task_id_escaped(self):
        src = self._get_source()
        assert "task_id_escaped" in src

    def test_session_id_escaped(self):
        src = self._get_source()
        assert "session_id_escaped" in src


# ===========================================================================
# BUG-LINK-ESCAPE-001: Task-rule linking escaping
# ===========================================================================

class TestTaskRuleLinkingEscaping:
    """Verify fields escaped in link_task_to_rule."""

    def _get_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.link_task_to_rule)

    def test_task_id_escaped(self):
        src = self._get_source()
        assert "task_id_escaped" in src

    def test_rule_id_escaped(self):
        src = self._get_source()
        assert "rule_id_escaped" in src


# ===========================================================================
# BUG-LINK-ESCAPE-002: Document linking escaping
# ===========================================================================

class TestDocumentLinkingEscaping:
    """Verify document_path escaped in link/unlink operations."""

    def _get_link_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.link_task_to_document)

    def _get_unlink_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.unlink_task_from_document)

    def test_document_path_escaped_in_link(self):
        src = self._get_link_source()
        assert "document_path_escaped" in src

    def test_doc_id_escaped_in_link(self):
        src = self._get_link_source()
        assert "doc_id_escaped" in src

    def test_task_id_escaped_in_link(self):
        src = self._get_link_source()
        assert "task_id_escaped" in src

    def test_document_path_escaped_in_unlink(self):
        src = self._get_unlink_source()
        assert "document_path_escaped" in src

    def test_task_id_escaped_in_unlink(self):
        src = self._get_unlink_source()
        assert "task_id_escaped" in src


# ===========================================================================
# BUG-LINK-ESCAPE-001: Commit linking escaping
# ===========================================================================

class TestCommitLinkingEscaping:
    """Verify commit_sha and commit_message escaped."""

    def _get_source(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        return inspect.getsource(TaskLinkingOperations.link_task_to_commit)

    def test_commit_sha_escaped(self):
        src = self._get_source()
        assert "commit_sha_escaped" in src

    def test_commit_message_was_already_escaped(self):
        """commit_message was already escaped (pre-existing)."""
        src = self._get_source()
        assert "msg_escaped" in src

    def test_task_id_escaped(self):
        src = self._get_source()
        assert "task_id_escaped" in src


# ===========================================================================
# BUG-TRUST-ESCAPE-001: Trust MCP agent_id escaping
# ===========================================================================

class TestTrustMCPEscaping:
    """Verify agent_id escaped in trust score query."""

    def _get_trust_source(self):
        from governance.mcp_tools.trust import register_trust_tools
        return inspect.getsource(register_trust_tools)

    def test_agent_id_escaped(self):
        src = self._get_trust_source()
        assert "agent_id_escaped" in src

    def test_no_raw_agent_id_in_query(self):
        src = self._get_trust_source()
        lines = src.split('\n')
        for line in lines:
            if 'agent-id' in line and '{agent_id' in line:
                assert 'agent_id_escaped' in line, f"Unescaped: {line.strip()}"


# ===========================================================================
# Cross-layer: Comprehensive linking escaping audit
# ===========================================================================

class TestLinkingEscapingAudit:
    """Verify ALL methods in TaskLinkingOperations use escaping."""

    def test_all_write_methods_escape(self):
        """All write (link/unlink) methods must have .replace patterns."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        write_methods = [
            "link_evidence_to_task", "link_task_to_session",
            "link_task_to_rule", "link_task_to_commit",
            "link_task_to_document", "unlink_task_from_document",
        ]
        for method_name in write_methods:
            method = getattr(TaskLinkingOperations, method_name)
            src = inspect.getsource(method)
            assert '.replace(' in src, f"{method_name} must escape fields"

    def test_all_read_methods_escape(self):
        """All read (get) methods must also escape for consistency."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        read_methods = [
            "get_task_evidence", "get_task_commits", "get_task_documents",
        ]
        for method_name in read_methods:
            method = getattr(TaskLinkingOperations, method_name)
            src = inspect.getsource(method)
            assert 'task_id_escaped' in src, f"{method_name} must escape task_id"

    def test_total_escape_count(self):
        """TaskLinkingOperations as a whole must have 15+ escape calls."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        src = inspect.getsource(TaskLinkingOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 15, f"Expected 15+ escape calls, found {escape_count}"
