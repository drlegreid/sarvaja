"""
Batch 65 — Deep Scan: Session read + rules/decisions TypeQL escaping.

Fixes verified:
- BUG-TYPEQL-ESCAPE-SESSION-003: session_id escaped in all session read queries
- BUG-TYPEQL-ESCAPE-DECISION-001: decision_id escaped in all decision CRUD queries
- BUG-TYPEQL-ESCAPE-RULE-001: rule_id escaped in all rule CRUD queries
"""
import inspect
import re

import pytest


# ===========================================================================
# BUG-TYPEQL-ESCAPE-SESSION-003: Session read queries
# ===========================================================================

class TestSessionReadEscaping:
    """Verify session_id escaped in all session read queries."""

    def _get_source(self):
        from governance.typedb.queries.sessions.read import SessionReadQueries
        return inspect.getsource(SessionReadQueries)

    def test_build_session_from_id_has_escape(self):
        """_build_session_from_id must define escaped session_id."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._build_session_from_id)
        assert 'session_id.replace(' in src or "sid = session_id" in src

    def test_no_raw_session_id_in_build(self):
        """_build_session_from_id must not have raw session_id in queries."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._build_session_from_id)
        raw = re.findall(r'session-id "\{session_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped session_id"

    def test_get_session_escapes(self):
        """get_session must escape session_id."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries.get_session)
        assert '.replace(' in src

    def test_get_tasks_for_session_escapes(self):
        """get_tasks_for_session must escape session_id."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries.get_tasks_for_session)
        assert '.replace(' in src

    def test_escaped_id_used_in_all_queries(self):
        """All f-string queries in _build_session_from_id must use escaped var."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._build_session_from_id)
        # Count escaped usages
        escaped = re.findall(r'session-id "\{sid\}"', src)
        assert len(escaped) >= 10, f"Expected 10+ escaped uses, found {len(escaped)}"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-DECISION-001: Decision CRUD queries
# ===========================================================================

class TestDecisionEscaping:
    """Verify decision_id escaped in all decision queries."""

    def _get_source(self):
        from governance.typedb.queries.rules.decisions import DecisionQueries
        return inspect.getsource(DecisionQueries)

    def test_update_decision_attr_escapes(self):
        """_update_decision_attr must escape decision_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries._update_decision_attr)
        assert '.replace(' in src

    def test_create_decision_escapes(self):
        """create_decision must escape decision_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.create_decision)
        assert "decision_id_escaped" in src

    def test_delete_decision_escapes(self):
        """delete_decision must escape decision_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.delete_decision)
        assert '.replace(' in src

    def test_link_decision_to_rule_escapes_both(self):
        """link_decision_to_rule must escape both decision_id and rule_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.link_decision_to_rule)
        assert "decision_id.replace" in src or "did = decision_id" in src
        assert "rule_id.replace" in src or "rid = rule_id" in src

    def test_no_raw_decision_id_in_link(self):
        """link_decision_to_rule must not have raw decision_id in queries."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.link_decision_to_rule)
        raw_did = re.findall(r'decision-id "\{decision_id\}"', src)
        raw_rid = re.findall(r'rule-id "\{rule_id\}"', src)
        assert len(raw_did) == 0, f"Found {len(raw_did)} unescaped decision_id"
        assert len(raw_rid) == 0, f"Found {len(raw_rid)} unescaped rule_id"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-RULE-001: Rule CRUD queries
# ===========================================================================

class TestRuleCRUDEscaping:
    """Verify rule_id escaped in all rule CRUD queries."""

    def _get_source(self):
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        return inspect.getsource(RuleCRUDOperations)

    def test_create_rule_escapes_rule_id(self):
        """create_rule must escape rule_id."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.create_rule)
        assert "rule_id_escaped" in src

    def test_update_rule_escapes_rule_id(self):
        """update_rule must escape rule_id."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.update_rule)
        assert "rule_id_escaped" in src

    def test_delete_rule_escapes_rule_id(self):
        """delete_rule must escape rule_id."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.delete_rule)
        assert "rule_id_escaped" in src

    def test_no_raw_rule_id_in_update_queries(self):
        """update_rule must not have raw rule_id in TypeQL queries."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.update_rule)
        raw = re.findall(r'rule-id "\{rule_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped rule_id in update_rule"

    def test_no_raw_rule_id_in_delete_query(self):
        """delete_rule must not have raw rule_id in TypeQL queries."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.delete_rule)
        raw = re.findall(r'rule-id "\{rule_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped rule_id in delete_rule"


# ===========================================================================
# Cross-file: TypeQL escaping completeness audit
# ===========================================================================

class TestTypeQLEscapingCompleteness:
    """Cross-file audit of TypeQL escaping across session/rule/decision layers."""

    def test_session_read_total_escape_calls(self):
        """SessionReadQueries must have comprehensive escaping."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 3, f"Expected 3+ escape calls, found {escape_count}"

    def test_decision_total_escape_calls(self):
        """DecisionQueries must have comprehensive escaping."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 10, f"Expected 10+ escape calls, found {escape_count}"

    def test_rule_crud_total_escape_calls(self):
        """RuleCRUDOperations must have comprehensive escaping."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 20, f"Expected 20+ escape calls, found {escape_count}"
