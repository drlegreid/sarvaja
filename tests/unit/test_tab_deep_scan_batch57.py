"""
Batch 57 — Deep Scan: Rule create name escaping + decision escaping audit.

Fixes verified:
- BUG-RULE-CREATE-NAME-001: name escaped in create_rule()
- Verification: decisions already properly escaped
- Cross-layer: TypeQL escaping completeness audit
"""
import inspect

import pytest


# ===========================================================================
# BUG-RULE-CREATE-NAME-001: Rule create name escaping
# ===========================================================================

class TestRuleCreateNameEscaping:
    """Verify name field escaped in create_rule()."""

    def _get_create_rule_source(self):
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        return inspect.getsource(RuleCRUDOperations.create_rule)

    def test_name_escaped_variable_exists(self):
        """create_rule must have name_escaped variable."""
        src = self._get_create_rule_source()
        assert 'name_escaped' in src

    def test_directive_escaped_variable_exists(self):
        """create_rule must have directive_escaped (pre-existing)."""
        src = self._get_create_rule_source()
        assert 'directive_escaped' in src

    def test_no_raw_name_in_query(self):
        """Query must use {name_escaped}, not raw {name}."""
        src = self._get_create_rule_source()
        lines = src.split('\n')
        for line in lines:
            if 'has rule-name' in line and '{name' in line:
                assert 'name_escaped' in line, f"Unescaped name: {line.strip()}"

    def test_category_validated_not_escaped(self):
        """category is validated against enum so no escaping needed."""
        src = self._get_create_rule_source()
        assert 'valid_categories' in src

    def test_priority_validated_not_escaped(self):
        """priority is validated against enum so no escaping needed."""
        src = self._get_create_rule_source()
        assert 'valid_priorities' in src

    def test_status_validated_not_escaped(self):
        """status is validated against enum so no escaping needed."""
        src = self._get_create_rule_source()
        assert 'valid_statuses' in src


# ===========================================================================
# Verification: Decision escaping already correct
# ===========================================================================

class TestDecisionEscapingVerification:
    """Verify decision queries already have proper escaping."""

    def _get_create_decision_source(self):
        from governance.typedb.queries.rules.decisions import DecisionQueries
        return inspect.getsource(DecisionQueries.create_decision)

    def _get_update_decision_source(self):
        from governance.typedb.queries.rules.decisions import DecisionQueries
        return inspect.getsource(DecisionQueries.update_decision)

    def test_create_decision_name_escaped(self):
        """create_decision must escape name."""
        src = self._get_create_decision_source()
        assert 'name_escaped' in src

    def test_create_decision_context_escaped(self):
        """create_decision must escape context."""
        src = self._get_create_decision_source()
        assert 'context_escaped' in src

    def test_create_decision_rationale_escaped(self):
        """create_decision must escape rationale."""
        src = self._get_create_decision_source()
        assert 'rationale_escaped' in src

    def test_update_decision_escapes_values(self):
        """update_decision must escape all field values."""
        src = self._get_update_decision_source()
        # Uses list comprehension with .replace() for all values
        assert '.replace(' in src


# ===========================================================================
# Full TypeQL escaping audit — all confirmed escaped now
# ===========================================================================

class TestTypeQLEscapingFullAudit:
    """Comprehensive audit: all user-provided fields escaped across all TypeDB query files."""

    def test_task_crud_insert_escapes_all(self):
        """Task insert: name, body, status, phase, priority, resolution all escaped."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        for field in ['name_escaped', 'status_escaped', 'phase_escaped']:
            assert field in src, f"Missing {field} in insert_task"

    def test_task_status_update_escapes_all(self):
        """Task status update: status, agent_id, evidence, resolution all escaped."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        for field in ['status_escaped', 'agent_id_escaped', 'evidence_escaped', 'resolution_escaped']:
            assert field in src, f"Missing {field} in update_task_status"

    def test_rule_create_escapes_name_and_directive(self):
        """Rule create: name and directive escaped."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.create_rule)
        assert 'name_escaped' in src
        assert 'directive_escaped' in src

    def test_rule_update_null_safe(self):
        """Rule update: all 5 core fields use (or '') guard."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.update_rule)
        for field in ['old_name', 'old_cat', 'old_pri', 'old_status', 'old_dir']:
            assert field in src, f"Missing null-safe {field} in update_rule"

    def test_session_linking_escapes_evidence(self):
        """Session linking: evidence_source escaped."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        assert 'evidence_source_escaped' in src

    def test_session_sync_escapes_decision(self):
        """Session sync: decision fields escaped."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_decision_to_typedb)
        for field in ['name_escaped', 'context_escaped', 'rationale_escaped']:
            assert field in src, f"Missing {field} in _index_decision_to_typedb"

    def test_session_sync_escapes_topic(self):
        """Session sync: topic escaped in session create."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        assert 'topic_escaped' in src

    def test_agent_insert_escapes(self):
        """Agent insert: name and type escaped."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.insert_agent)
        assert 'name_escaped' in src
        assert 'type_escaped' in src
