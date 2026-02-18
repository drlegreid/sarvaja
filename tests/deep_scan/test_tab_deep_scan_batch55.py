"""
Batch 55 — Deep Scan: Rule update null safety + task status TypeQL escaping.

Fixes verified:
- BUG-RULE-NULL-001: update_rule() guards existing.X with (X or "") before .replace()
- BUG-STATUS-ESCAPE-001: status, agent_id, resolution escaped in update_task_status()
"""
import inspect

import pytest


# ===========================================================================
# BUG-RULE-NULL-001: Rule update null-safe .replace()
# ===========================================================================

class TestRuleUpdateNullSafety:
    """Verify update_rule() guards all .replace() calls against None."""

    def _get_update_rule_source(self):
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        return inspect.getsource(RuleCRUDOperations.update_rule)

    def test_name_null_guarded(self):
        """existing.name must use (or '') before .replace()."""
        src = self._get_update_rule_source()
        # Should have pattern like (existing.name or "").replace
        assert '(existing.name or "")' in src or 'old_name' in src

    def test_category_null_guarded(self):
        src = self._get_update_rule_source()
        assert '(existing.category or "")' in src or 'old_cat' in src

    def test_priority_null_guarded(self):
        src = self._get_update_rule_source()
        assert '(existing.priority or "")' in src or 'old_pri' in src

    def test_status_null_guarded(self):
        src = self._get_update_rule_source()
        assert '(existing.status or "")' in src or 'old_status' in src

    def test_directive_null_guarded(self):
        src = self._get_update_rule_source()
        assert '(existing.directive or "")' in src or 'old_dir' in src

    def test_rule_type_already_guarded(self):
        """rule_type already has 'existing.rule_type is None' check."""
        src = self._get_update_rule_source()
        assert 'existing.rule_type is None' in src

    def test_semantic_id_already_guarded(self):
        """semantic_id already has 'existing.semantic_id is None' check."""
        src = self._get_update_rule_source()
        assert 'existing.semantic_id is None' in src

    def test_applicability_already_guarded(self):
        """applicability already has 'existing.applicability is None' check."""
        src = self._get_update_rule_source()
        assert 'existing.applicability is None' in src

    def test_no_direct_existing_name_replace(self):
        """Must not have bare existing.name.replace() without guard."""
        src = self._get_update_rule_source()
        assert 'existing.name.replace' not in src

    def test_no_direct_existing_category_replace(self):
        src = self._get_update_rule_source()
        assert 'existing.category.replace' not in src

    def test_no_direct_existing_directive_replace(self):
        src = self._get_update_rule_source()
        assert 'existing.directive.replace' not in src


# ===========================================================================
# BUG-STATUS-ESCAPE-001: TypeQL escaping in update_task_status
# ===========================================================================

class TestStatusEscaping:
    """Verify status, agent_id, resolution escaped in update_task_status."""

    def _get_status_source(self):
        from governance.typedb.queries.tasks.status import update_task_status
        return inspect.getsource(update_task_status)

    def test_status_escaped_before_insert(self):
        """status parameter must be escaped before TypeQL interpolation."""
        src = self._get_status_source()
        assert 'status_escaped' in src

    def test_agent_id_escaped_before_insert(self):
        """agent_id parameter must be escaped before TypeQL interpolation."""
        src = self._get_status_source()
        assert 'agent_id_escaped' in src

    def test_resolution_escaped_before_insert(self):
        """resolution parameter must be escaped before TypeQL interpolation."""
        src = self._get_status_source()
        assert 'resolution_escaped' in src

    def test_evidence_was_already_escaped(self):
        """evidence was already escaped (pre-existing)."""
        src = self._get_status_source()
        assert 'evidence_escaped' in src

    def test_current_status_escaped(self):
        """current.status used in delete query must also be escaped."""
        src = self._get_status_source()
        assert 'current_status_escaped' in src

    def test_current_agent_id_escaped(self):
        """current.agent_id used in delete query must also be escaped."""
        src = self._get_status_source()
        assert 'current_agent_escaped' in src

    def test_no_raw_agent_id_in_insert(self):
        """Must not have unescaped {agent_id} in insert query."""
        src = self._get_status_source()
        # The raw pattern should NOT appear (only escaped version)
        lines = src.split('\n')
        for line in lines:
            if 'has agent-id' in line and '{agent_id}' in line:
                # Must use {agent_id_escaped} not {agent_id}
                assert 'agent_id_escaped' in line, f"Unescaped agent_id in: {line.strip()}"

    def test_no_raw_status_in_insert(self):
        """Must not have unescaped {status} in insert query."""
        src = self._get_status_source()
        lines = src.split('\n')
        for line in lines:
            if 'has task-status' in line and '{status' in line:
                assert 'status_escaped' in line, f"Unescaped status in: {line.strip()}"


# ===========================================================================
# Cross-layer: Consistent escaping across all TypeDB query files
# ===========================================================================

class TestCrossLayerEscapingConsistency:
    """Verify escaping patterns are consistent across TypeDB query modules."""

    def test_task_crud_escapes_status(self):
        """Task CRUD insert_task escapes status field."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        assert 'status_escaped' in src

    def test_task_status_escapes_status(self):
        """Task status update escapes status parameter."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert 'status_escaped' in src

    def test_agent_insert_escapes_name(self):
        """Agent insert escapes name field."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.insert_agent)
        assert 'name_escaped' in src

    def test_rule_create_escapes_directive(self):
        """Rule create escapes directive field."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.create_rule)
        assert 'directive_escaped' in src
