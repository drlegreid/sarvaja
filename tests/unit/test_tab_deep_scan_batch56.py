"""
Batch 56 — Deep Scan: TypeQL injection in session linking + collector sync.

Fixes verified:
- BUG-TYPEDB-INJECTION-001: evidence_source escaped in link_evidence_to_session
- BUG-TYPEDB-INJECTION-002: topic + session_type escaped in _index_task_to_typedb
- BUG-TYPEDB-INJECTION-003: decision fields escaped in _index_decision_to_typedb
"""
import inspect

import pytest


# ===========================================================================
# BUG-TYPEDB-INJECTION-001: Session linking escaping
# ===========================================================================

class TestSessionLinkingEscaping:
    """Verify evidence_source is escaped in link_evidence_to_session."""

    def _get_link_evidence_source(self):
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        return inspect.getsource(SessionLinkingOperations.link_evidence_to_session)

    def test_evidence_source_escaped(self):
        """evidence_source must be escaped before TypeQL interpolation."""
        src = self._get_link_evidence_source()
        assert 'evidence_source_escaped' in src

    def test_evidence_id_escaped(self):
        """evidence_id must be escaped before TypeQL interpolation."""
        src = self._get_link_evidence_source()
        assert 'evidence_id_escaped' in src

    def test_no_raw_evidence_source_in_insert(self):
        """Must not have unescaped {evidence_source} in insert query."""
        src = self._get_link_evidence_source()
        lines = src.split('\n')
        for line in lines:
            if 'has evidence-source' in line and '{evidence_source' in line:
                assert 'evidence_source_escaped' in line, f"Unescaped: {line.strip()}"

    def test_no_raw_evidence_source_in_match(self):
        """Match clause must use escaped version too."""
        src = self._get_link_evidence_source()
        lines = src.split('\n')
        for line in lines:
            if 'evidence-source' in line and '{evidence_source' in line:
                assert 'evidence_source_escaped' in line, f"Unescaped: {line.strip()}"


# ===========================================================================
# BUG-TYPEDB-INJECTION-002: Session sync topic + type escaping
# ===========================================================================

class TestSessionSyncTopicEscaping:
    """Verify topic and session_type escaped when creating work-session."""

    def _get_index_task_source(self):
        from governance.session_collector.sync import SessionSyncMixin
        return inspect.getsource(SessionSyncMixin._index_task_to_typedb)

    def test_topic_escaped(self):
        """self.topic must be escaped before TypeQL interpolation."""
        src = self._get_index_task_source()
        assert 'topic_escaped' in src

    def test_session_type_escaped(self):
        """self.session_type must be escaped before TypeQL interpolation."""
        src = self._get_index_task_source()
        assert 'type_escaped' in src

    def test_task_status_escaped(self):
        """task.status must be escaped in insert task query."""
        src = self._get_index_task_source()
        assert 'task_status_escaped' in src

    def test_task_name_escaped(self):
        """task.name was already escaped (pre-existing)."""
        src = self._get_index_task_source()
        assert 'task_name_escaped' in src

    def test_agent_id_escaped_in_session_create(self):
        """agent_id must be escaped when creating work-session."""
        src = self._get_index_task_source()
        assert 'agent_escaped' in src


# ===========================================================================
# BUG-TYPEDB-INJECTION-003: Decision field escaping
# ===========================================================================

class TestDecisionIndexEscaping:
    """Verify all decision fields escaped in _index_decision_to_typedb."""

    def _get_index_decision_source(self):
        from governance.session_collector.sync import SessionSyncMixin
        return inspect.getsource(SessionSyncMixin._index_decision_to_typedb)

    def test_decision_name_escaped(self):
        """decision.name must be escaped."""
        src = self._get_index_decision_source()
        assert 'name_escaped' in src

    def test_decision_context_escaped(self):
        """decision.context must be escaped."""
        src = self._get_index_decision_source()
        assert 'context_escaped' in src

    def test_decision_rationale_escaped(self):
        """decision.rationale must be escaped."""
        src = self._get_index_decision_source()
        assert 'rationale_escaped' in src

    def test_decision_status_escaped(self):
        """decision.status must be escaped."""
        src = self._get_index_decision_source()
        assert 'status_escaped' in src

    def test_decision_id_escaped(self):
        """decision.id must be escaped."""
        src = self._get_index_decision_source()
        assert 'id_escaped' in src

    def test_no_raw_decision_name_in_query(self):
        """Must not have unescaped {decision.name} in query."""
        src = self._get_index_decision_source()
        assert '{decision.name}' not in src

    def test_no_raw_decision_context_in_query(self):
        """Must not have unescaped {decision.context} in query."""
        src = self._get_index_decision_source()
        assert '{decision.context}' not in src


# ===========================================================================
# Cross-layer: TypeQL escaping audit across session-related files
# ===========================================================================

class TestSessionTypeQLEscapingAudit:
    """Verify consistent escaping across all session-related TypeDB queries."""

    def test_linking_operations_all_escaped(self):
        """All session linking methods should use escaped variables."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        # Count .replace patterns
        escape_count = src.count('.replace(')
        assert escape_count >= 2, f"Expected 2+ escape calls, found {escape_count}"

    def test_sync_decision_fully_escaped(self):
        """Decision sync should escape all 5 string fields."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_decision_to_typedb)
        escape_count = src.count('.replace(')
        assert escape_count >= 5, f"Expected 5+ escape calls, found {escape_count}"

    def test_sync_task_fully_escaped(self):
        """Task sync should escape name, description, topic, type, status, agent."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        escape_count = src.count('.replace(')
        assert escape_count >= 5, f"Expected 5+ escape calls, found {escape_count}"
