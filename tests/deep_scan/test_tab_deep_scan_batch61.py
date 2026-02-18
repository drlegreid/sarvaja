"""
Batch 61 — Deep Scan: TypeQL metrics escaping + ingestion stat guard.

Fixes verified:
- BUG-TYPEQL-METRICS-001: All fields escaped in typedb_queries.py
- BUG-INGEST-STAT-001: .stat() guarded in ingest_all()
"""
import inspect

import pytest


# ===========================================================================
# BUG-TYPEQL-METRICS-001: TypeQL metrics query escaping
# ===========================================================================

class TestTypeQLMetricsEscaping:
    """Verify all fields escaped in session metrics TypeDB queries."""

    def _get_metrics_insert_source(self):
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        return inspect.getsource(build_metrics_insert_query)

    def _get_evidence_insert_source(self):
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        return inspect.getsource(build_evidence_insert_query)

    def _get_evidence_link_source(self):
        from governance.session_metrics.typedb_queries import build_evidence_link_query
        return inspect.getsource(build_evidence_link_query)

    def test_session_id_escaped_in_metrics_insert(self):
        """session_id must be escaped in build_metrics_insert_query."""
        src = self._get_metrics_insert_source()
        assert "session_id_escaped" in src

    def test_name_escaped_in_metrics_insert(self):
        """name must be escaped in build_metrics_insert_query."""
        src = self._get_metrics_insert_source()
        assert "name_escaped" in src

    def test_description_was_already_escaped(self):
        """description should already be escaped (pre-existing)."""
        src = self._get_metrics_insert_source()
        assert "desc_escaped" in src

    def test_evidence_id_escaped_in_evidence_insert(self):
        """evidence_id must be escaped in build_evidence_insert_query."""
        src = self._get_evidence_insert_source()
        assert "evidence_id_escaped" in src

    def test_source_escaped_in_evidence_insert(self):
        """source must be escaped in build_evidence_insert_query."""
        src = self._get_evidence_insert_source()
        assert "source_escaped" in src

    def test_type_escaped_in_evidence_insert(self):
        """evidence_type must be escaped in build_evidence_insert_query."""
        src = self._get_evidence_insert_source()
        assert "type_escaped" in src

    def test_preview_was_already_escaped(self):
        """content_preview should already be escaped (pre-existing or via helper)."""
        src = self._get_evidence_insert_source()
        assert "preview" in src and ("_escape_typeql" in src or ".replace" in src)

    def test_session_id_escaped_in_link_query(self):
        """session_id must be escaped in build_evidence_link_query."""
        src = self._get_evidence_link_source()
        assert "session_id_escaped" in src

    def test_evidence_id_escaped_in_link_query(self):
        """evidence_id must be escaped in build_evidence_link_query."""
        src = self._get_evidence_link_source()
        assert "evidence_id_escaped" in src

    def test_no_raw_session_id_in_metrics_query(self):
        """Must use escaped version in the query string."""
        src = self._get_metrics_insert_source()
        # The query should use session_id_escaped, not raw session_id
        assert 'session-id "{session_id_escaped}"' in src

    def test_no_raw_evidence_id_in_evidence_query(self):
        """Must use escaped version in the evidence query string."""
        src = self._get_evidence_insert_source()
        assert 'evidence-id "{evidence_id_escaped}"' in src


# ===========================================================================
# BUG-INGEST-STAT-001: Ingestion stat() guard
# ===========================================================================

class TestIngestionStatGuard:
    """Verify ingest_all wraps .stat() in try-except."""

    def _get_ingest_all_source(self):
        from governance.services.cc_session_ingestion import ingest_all
        return inspect.getsource(ingest_all)

    def test_stat_has_try_except(self):
        """stat() call must be wrapped in try-except."""
        src = self._get_ingest_all_source()
        stat_idx = src.index(".stat()")
        # Find the nearest try before the stat
        try_idx = src.rfind("try:", 0, stat_idx)
        assert try_idx > 0, "stat() must be inside try block"

    def test_catches_file_not_found(self):
        """Must catch FileNotFoundError for TOCTOU protection."""
        src = self._get_ingest_all_source()
        assert "FileNotFoundError" in src

    def test_catches_os_error(self):
        """Must catch OSError for broader protection."""
        src = self._get_ingest_all_source()
        assert "OSError" in src


# ===========================================================================
# Cross-layer: TypeQL escaping completeness across metrics module
# ===========================================================================

class TestTypeQLMetricsEscapingAudit:
    """Verify consistent escaping across all metrics TypeQL query builders."""

    def test_metrics_insert_escapes_count(self):
        """build_metrics_insert_query must escape all string fields."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        src = inspect.getsource(build_metrics_insert_query)
        escape_count = src.count('_escape_typeql(') + src.count('.replace(')
        assert escape_count >= 3, f"Expected 3+ escape calls, found {escape_count}"

    def test_evidence_insert_escapes_count(self):
        """build_evidence_insert_query must escape all string fields."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        src = inspect.getsource(build_evidence_insert_query)
        escape_count = src.count('_escape_typeql(') + src.count('.replace(')
        assert escape_count >= 4, f"Expected 4+ escape calls, found {escape_count}"

    def test_evidence_link_escapes_count(self):
        """build_evidence_link_query must escape all string fields."""
        from governance.session_metrics.typedb_queries import build_evidence_link_query
        src = inspect.getsource(build_evidence_link_query)
        escape_count = src.count('_escape_typeql(') + src.count('.replace(')
        assert escape_count >= 2, f"Expected 2+ escape calls, found {escape_count}"

    def test_functional_metrics_query(self):
        """build_metrics_insert_query must return valid TypeQL."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query("SESSION-TEST", {"totals": {}})
        assert 'insert $s isa work-session' in query
        assert 'has session-id "SESSION-TEST"' in query

    def test_functional_evidence_query(self):
        """build_evidence_insert_query must return valid TypeQL."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        query = build_evidence_insert_query("EV-001", "metrics", "report", "preview text")
        assert 'insert $e isa evidence-file' in query
        assert 'has evidence-id "EV-001"' in query

    def test_functional_link_query(self):
        """build_evidence_link_query must return valid TypeQL."""
        from governance.session_metrics.typedb_queries import build_evidence_link_query
        query = build_evidence_link_query("SESSION-TEST", "EV-001")
        assert 'match' in query
        assert 'insert' in query
        assert 'isa has-evidence' in query
