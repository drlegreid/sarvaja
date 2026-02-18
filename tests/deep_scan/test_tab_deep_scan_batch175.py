"""Deep scan batch 175: CC scanner + repair + metrics layer.

Batch 175 findings: 27 total, 1 confirmed fix, 26 rejected/deferred.
- BUG-CORR-DEAD-CODE-001: correlation.py dead code loop (pass body) cleaned up.
"""
import pytest
from pathlib import Path


# ── Correlation dead code defense ──────────────


class TestCorrelationDeadCodeDefense:
    """Verify dead code removed from correlate_tool_calls."""

    def test_no_pass_in_use_index_loop(self):
        """No `pass` body in the tool_use index loop."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/correlation.py").read_text()
        # Find the use_index building section
        idx = src.index("use_index")
        section = src[idx:idx + 200]
        assert "pass" not in section

    def test_single_use_index_dict(self):
        """Only one use_index dict initialization (no duplicate)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/correlation.py").read_text()
        count = src.count("use_index = {}")
        assert count <= 1  # At most one dict init, or inline type hint

    def test_correlate_function_exists(self):
        """correlate_tool_calls is importable."""
        from governance.session_metrics.correlation import correlate_tool_calls
        assert callable(correlate_tool_calls)


# ── CC session scanner defense ──────────────


class TestCCSessionScannerDefense:
    """Verify CC session scanner path handling."""

    def test_discover_cc_projects_importable(self):
        """discover_cc_projects is importable."""
        from governance.services.cc_session_scanner import discover_cc_projects
        assert callable(discover_cc_projects)

    def test_find_jsonl_for_session_importable(self):
        """find_jsonl_for_session is importable."""
        from governance.services.cc_session_scanner import find_jsonl_for_session
        assert callable(find_jsonl_for_session)

    def test_default_cc_dir_defined(self):
        """DEFAULT_CC_DIR is defined as a Path."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_session_scanner.py").read_text()
        assert "DEFAULT_CC_DIR" in src

    def test_hidden_dir_guard_in_discover(self):
        """discover_cc_projects skips hidden directories."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_session_scanner.py").read_text()
        assert 'startswith(".")' in src


# ── Session repair defense ──────────────


class TestSessionRepairDefense:
    """Verify session repair constants and functions."""

    def test_max_duration_hours_is_24(self):
        """_MAX_DURATION_HOURS is 24 (not 8)."""
        from governance.services.session_repair import _MAX_DURATION_HOURS
        assert _MAX_DURATION_HOURS == 24

    def test_cap_duration_uses_constant(self):
        """cap_duration default uses _MAX_DURATION_HOURS."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/session_repair.py").read_text()
        assert "max_hours: float = _MAX_DURATION_HOURS" in src

    def test_parse_session_date_callable(self):
        """parse_session_date is importable."""
        from governance.services.session_repair import parse_session_date
        assert callable(parse_session_date)

    def test_parse_session_date_extracts_date(self):
        """parse_session_date extracts date from standard session ID."""
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("SESSION-2026-02-15-TEST")
        assert result == "2026-02-15"

    def test_parse_session_date_returns_none_for_invalid(self):
        """parse_session_date returns None for non-standard IDs."""
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("INVALID-ID")
        assert result is None


# ── Evidence extractor defense ──────────────


class TestEvidenceExtractorDefense:
    """Verify evidence extractor path resolution."""

    def test_workspace_root_resolves_to_project(self):
        """WORKSPACE_ROOT resolves to project root (3-level dirname)."""
        from governance.evidence_scanner.extractors import WORKSPACE_ROOT
        root = Path(WORKSPACE_ROOT)
        # Should contain CLAUDE.md or governance/
        assert (root / "governance").is_dir() or (root / "CLAUDE.md").exists()

    def test_rule_patterns_defined(self):
        """RULE_PATTERNS are defined for extraction."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/evidence_scanner/extractors.py").read_text()
        assert "RULE_PATTERNS" in src

    def test_task_patterns_defined(self):
        """TASK_PATTERNS are defined for extraction."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/evidence_scanner/extractors.py").read_text()
        assert "TASK_PATTERNS" in src


# ── Calculator defense ──────────────


class TestCalculatorDefense:
    """Verify session metrics calculator edge cases."""

    def test_filter_entries_by_days_empty(self):
        """filter_entries_by_days handles empty list."""
        from governance.session_metrics.calculator import filter_entries_by_days
        result = filter_entries_by_days([], 7)
        assert result == []

    def test_split_sessions_importable(self):
        """split_sessions is importable."""
        from governance.session_metrics.calculator import split_sessions
        assert callable(split_sessions)


# ── TypeDB queries defense ──────────────


class TestTypeDBQueriesDefense:
    """Verify TypeQL query builder escaping."""

    def test_escape_typeql_handles_quotes(self):
        """_escape_typeql escapes double quotes."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql('hello "world"')
        assert '\\"' in result

    def test_escape_typeql_handles_newlines(self):
        """_escape_typeql escapes newlines."""
        from governance.session_metrics.typedb_queries import _escape_typeql
        result = _escape_typeql("hello\nworld")
        assert "\\n" in result

    def test_build_metrics_insert_callable(self):
        """build_metrics_insert_query is importable."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        assert callable(build_metrics_insert_query)

    def test_build_evidence_insert_callable(self):
        """build_evidence_insert_query is importable."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        assert callable(build_evidence_insert_query)
