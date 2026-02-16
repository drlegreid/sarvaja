"""
Batch 70 — Deep Scan: Services + Stores data integrity fixes.

Fixes verified:
- BUG-SYNC-FIELDS-001: CC fields passed atomically to insert_session on orphan sync
- BUG-AGENTS-YAML-FILE-NO-ERROR-HANDLING-001: Type guard for malformed YAML values
- BUG-TYPEDB-QUERIES-ESCAPE-INCOMPLETE-001: Newline escaping in TypeQL query builders
"""
import inspect
from unittest.mock import patch, MagicMock

import pytest


# ===========================================================================
# BUG-SYNC-FIELDS-001: CC fields atomic insert on orphan sync
# ===========================================================================

class TestOrphanSessionSyncCCFields:
    """Verify sync_pending_sessions passes CC fields to insert_session."""

    def test_sync_passes_cc_session_uuid(self):
        """sync_pending_sessions must pass cc_session_uuid to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_session_uuid=session_data.get(" in src

    def test_sync_passes_cc_project_slug(self):
        """sync_pending_sessions must pass cc_project_slug to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_project_slug=session_data.get(" in src

    def test_sync_passes_cc_git_branch(self):
        """sync_pending_sessions must pass cc_git_branch to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_git_branch=session_data.get(" in src

    def test_sync_passes_cc_tool_count(self):
        """sync_pending_sessions must pass cc_tool_count to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_tool_count=session_data.get(" in src

    def test_sync_passes_cc_thinking_chars(self):
        """sync_pending_sessions must pass cc_thinking_chars to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_thinking_chars=session_data.get(" in src

    def test_sync_passes_cc_compaction_count(self):
        """sync_pending_sessions must pass cc_compaction_count to insert_session."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        assert "cc_compaction_count=session_data.get(" in src

    def test_no_separate_update_for_cc_fields(self):
        """CC fields should NOT require a separate update_session call."""
        from governance.services.sessions import sync_pending_sessions
        src = inspect.getsource(sync_pending_sessions)
        # The old pattern had a loop over CC field names for update_kwargs
        assert "cc_session_uuid\", \"cc_project_slug\"" not in src


# ===========================================================================
# BUG-AGENTS-YAML-FILE-NO-ERROR-HANDLING-001: YAML type guard
# ===========================================================================

class TestAgentsYamlTypeGuard:
    """Verify agents.yaml loading guards against non-dict values."""

    def test_yaml_loader_has_isinstance_check(self):
        """_load_workflow_configs must check isinstance(agent_conf, dict)."""
        from governance.stores.agents import _load_workflow_configs
        src = inspect.getsource(_load_workflow_configs)
        assert "isinstance(agent_conf, dict)" in src

    def test_yaml_loader_continues_on_non_dict(self):
        """Non-dict values must be skipped with continue."""
        from governance.stores.agents import _load_workflow_configs
        src = inspect.getsource(_load_workflow_configs)
        # Pattern: if not isinstance(...): continue
        assert "continue" in src

    def test_yaml_loader_skips_scalar_values(self):
        """_load_workflow_configs must skip non-dict agent configs without crashing."""
        import yaml as yaml_mod
        mock_data = {
            "agents": {
                "code_agent": "invalid_scalar_value",
                "review_agent": {"description": "Valid agent"},
            }
        }
        with patch("governance.stores.agents.os.path.exists", return_value=True), \
             patch("builtins.open", MagicMock()), \
             patch.object(yaml_mod, "safe_load", return_value=mock_data):
            from governance.stores.agents import _load_workflow_configs
            result = _load_workflow_configs()
            assert isinstance(result, dict)


# ===========================================================================
# BUG-TYPEDB-QUERIES-ESCAPE-INCOMPLETE-001: Newline escaping
# ===========================================================================

class TestTypeQLNewlineEscaping:
    """Verify TypeQL query builders escape newlines and backslashes."""

    def test_escape_helper_exists(self):
        """_escape_typeql helper function must exist."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        assert callable(_escape_typeql)

    def test_escape_handles_newlines(self):
        """_escape_typeql must convert \\n to \\\\n."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql("line1\nline2")
        assert "\\n" in result
        assert "\n" not in result

    def test_escape_handles_carriage_returns(self):
        """_escape_typeql must convert \\r to \\\\r."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql("line1\rline2")
        assert "\\r" in result
        assert "\r" not in result

    def test_escape_handles_backslashes(self):
        """_escape_typeql must escape backslashes before quotes."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql('path\\to\\file')
        assert "\\\\" in result

    def test_escape_handles_double_quotes(self):
        """_escape_typeql must escape double quotes."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql('say "hello"')
        assert '\\"' in result

    def test_escape_order_matters(self):
        """Backslash must be escaped BEFORE quotes to avoid double-escaping."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        # Input: backslash followed by quote
        result = _escape_typeql('test\\"end')
        # Should escape backslash first (\ -> \\), then quote (" -> \\")
        assert '\\\\\\"' in result

    def test_metrics_query_uses_escape_helper(self):
        """build_metrics_insert_query must use _escape_typeql."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        src = inspect.getsource(build_metrics_insert_query)
        assert "_escape_typeql(" in src

    def test_evidence_query_uses_escape_helper(self):
        """build_evidence_insert_query must use _escape_typeql."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        src = inspect.getsource(build_evidence_insert_query)
        assert "_escape_typeql(" in src

    def test_link_query_uses_escape_helper(self):
        """build_evidence_link_query must use _escape_typeql."""
        from governance.session_metrics.typedb_queries import build_evidence_link_query
        src = inspect.getsource(build_evidence_link_query)
        assert "_escape_typeql(" in src

    def test_evidence_preview_with_newlines(self):
        """Evidence preview with newlines must produce valid TypeQL."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        query = build_evidence_insert_query(
            evidence_id="EVID-001",
            source="test",
            evidence_type="metrics",
            content_preview="line1\nline2\nline3",
        )
        # Query must not contain raw newlines in the string value
        # (newlines from f-string formatting are OK, but not in values)
        for line in query.split("\n"):
            if "evidence-content-preview" in line:
                # The value should have escaped newlines
                assert "\\n" in line
                break
