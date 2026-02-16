"""
Batch 64 — Deep Scan: Session TypeQL escaping (mutations + linking).

Fixes verified:
- BUG-TYPEQL-ESCAPE-SESSION-001: session_id escaped in all session mutation queries
- BUG-TYPEQL-ESCAPE-SESSION-002: session_id/rule_id/decision_id escaped in session linking
"""
import inspect

import pytest


# ===========================================================================
# BUG-TYPEQL-ESCAPE-SESSION-001: Session mutation queries
# ===========================================================================

class TestSessionMutationEscaping:
    """Verify session_id escaped in all mutation queries."""

    def _get_source(self):
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        return inspect.getsource(SessionMutationOperations)

    def test_update_session_has_escape_variable(self):
        """update_session must define session_id_escaped."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.update_session)
        assert "session_id_escaped" in src

    def test_delete_session_has_escape_variable(self):
        """delete_session must define session_id_escaped."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.delete_session)
        assert "session_id_escaped" in src

    def test_no_raw_session_id_in_queries(self):
        """No raw session_id in TypeQL query strings (must use _escaped)."""
        src = self._get_source()
        # Count session-id usages in query strings
        import re
        # Match: has session-id "{session_id}" (NOT _escaped)
        raw_matches = re.findall(r'session-id "\{session_id\}"', src)
        escaped_matches = re.findall(r'session-id "\{session_id_escaped\}"', src)
        assert len(raw_matches) == 0, f"Found {len(raw_matches)} raw session_id in queries"
        assert len(escaped_matches) >= 10, f"Expected 10+ escaped, found {len(escaped_matches)}"

    def test_update_session_escape_is_before_queries(self):
        """session_id_escaped must be defined before first query usage."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.update_session)
        escape_pos = src.find("session_id_escaped")
        first_query_pos = src.find('has session-id')
        assert escape_pos < first_query_pos, "Escape must come before first query"

    def test_delete_session_escape_is_before_queries(self):
        """session_id_escaped must be defined before first query in delete."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.delete_session)
        escape_pos = src.find("session_id_escaped")
        first_query_pos = src.find('has session-id')
        assert escape_pos < first_query_pos, "Escape must come before first query"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-SESSION-002: Session linking queries
# ===========================================================================

class TestSessionLinkingEscaping:
    """Verify session_id, rule_id, decision_id escaped in linking."""

    def _get_source(self):
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        return inspect.getsource(SessionLinkingOperations)

    def test_link_evidence_has_session_id_escaped(self):
        """link_evidence_to_session must escape session_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        assert "session_id_escaped" in src

    def test_link_rule_has_both_ids_escaped(self):
        """link_rule_to_session must escape both session_id and rule_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_rule_to_session)
        assert "session_id_escaped" in src
        assert "rule_id_escaped" in src

    def test_link_decision_has_both_ids_escaped(self):
        """link_decision_to_session must escape both session_id and decision_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_decision_to_session)
        assert "session_id_escaped" in src
        assert "decision_id_escaped" in src

    def test_get_session_evidence_escapes(self):
        """get_session_evidence must escape session_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.get_session_evidence)
        assert "session_id_escaped" in src

    def test_get_session_rules_escapes(self):
        """get_session_rules must escape session_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.get_session_rules)
        assert "session_id_escaped" in src

    def test_get_session_decisions_escapes(self):
        """get_session_decisions must escape session_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.get_session_decisions)
        assert "session_id_escaped" in src

    def test_total_escape_count_linking(self):
        """SessionLinkingOperations must have comprehensive escaping."""
        src = self._get_source()
        escape_count = src.count('.replace(')
        assert escape_count >= 10, f"Expected 10+ escape calls, found {escape_count}"


# ===========================================================================
# Cross-file: Session TypeQL escaping audit
# ===========================================================================

class TestSessionTypeQLEscapingAudit:
    """Cross-file audit of session TypeQL escaping."""

    def test_crud_mutations_no_unescaped_session_id(self):
        """crud_mutations.py must not have any unescaped session_id in queries."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations)
        import re
        raw = re.findall(r'session-id "\{session_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped session_id in crud_mutations"

    def test_linking_no_unescaped_session_id_in_writes(self):
        """linking.py write methods must not have unescaped session_id."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        for method_name in ["link_evidence_to_session", "link_rule_to_session", "link_decision_to_session"]:
            src = inspect.getsource(getattr(SessionLinkingOperations, method_name))
            import re
            raw = re.findall(r'session-id "\{session_id\}"', src)
            assert len(raw) == 0, f"{method_name} has {len(raw)} unescaped session_id"

    def test_evidence_source_still_escaped(self):
        """Existing evidence_source escaping must not be broken."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        assert "evidence_source_escaped" in src
        assert "evidence_id_escaped" in src
