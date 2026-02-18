"""Batch 245 — Evidence + DSM + Metrics defense tests.

Validates fixes for:
- BUG-245-PAR-001: tz-naive datetime normalization in _parse_timestamp
- BUG-245-TRK-001: ValueError guard on unknown phase enum
- BUG-245-NOD-001: Duplicate phase dedup in LangGraph nodes
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-245-PAR-001: tz-aware datetime normalization ────────────────

class TestParserTimezoneNormalization:
    """_parse_timestamp must always produce tz-aware datetime."""

    def test_timezone_import_present(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def _parse_timestamp")
        block = src[idx:idx + 400]
        assert "timezone" in block

    def test_tzinfo_none_check(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def _parse_timestamp")
        block = src[idx:idx + 400]
        assert "dt.tzinfo is None" in block

    def test_replace_tzinfo(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def _parse_timestamp")
        block = src[idx:idx + 600]
        assert "replace(tzinfo=" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        assert "BUG-245-PAR-001" in src

    def test_parse_naive_returns_tzaware(self):
        """Naive ISO string must get UTC timezone."""
        from governance.session_metrics.parser import _parse_timestamp
        dt = _parse_timestamp("2026-01-17T10:30:00")
        assert dt.tzinfo is not None

    def test_parse_z_returns_tzaware(self):
        """Z-suffix ISO string must be tz-aware."""
        from governance.session_metrics.parser import _parse_timestamp
        dt = _parse_timestamp("2026-01-17T10:30:00Z")
        assert dt.tzinfo is not None

    def test_parse_offset_returns_tzaware(self):
        """Offset ISO string must be tz-aware."""
        from governance.session_metrics.parser import _parse_timestamp
        dt = _parse_timestamp("2026-01-17T10:30:00+05:30")
        assert dt.tzinfo is not None


# ── BUG-245-TRK-001: ValueError guard on unknown phase ──────────────

class TestTrackerPhaseGuard:
    """get_current_phase must not crash on unknown phase strings."""

    def test_try_except_present(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        idx = src.index("def get_current_phase")
        block = src[idx:idx + 400]
        assert "except ValueError:" in block

    def test_returns_idle_on_unknown(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        idx = src.index("except ValueError:")
        block = src[idx:idx + 100]
        assert "IDLE" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        assert "BUG-245-TRK-001" in src


# ── BUG-245-NOD-001: Phase dedup in LangGraph nodes ─────────────────

class TestLangGraphPhaseDedup:
    """LangGraph nodes must dedup phases_completed."""

    def test_optimize_has_dedup(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert '"optimize" not in state' in src

    def test_validate_has_dedup(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert '"validate" not in state' in src

    def test_dream_has_dedup(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert '"dream" not in state' in src

    def test_report_has_dedup(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert '"report" not in state' in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert "BUG-245-NOD-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch245Imports:
    def test_parser_importable(self):
        import governance.session_metrics.parser
        assert governance.session_metrics.parser is not None

    def test_correlation_importable(self):
        import governance.session_metrics.correlation
        assert governance.session_metrics.correlation is not None

    def test_models_importable(self):
        import governance.session_metrics.models
        assert governance.session_metrics.models is not None

    def test_tracker_importable(self):
        import governance.dsm.tracker
        assert governance.dsm.tracker is not None

    def test_nodes_execution_importable(self):
        import governance.dsm.langgraph.nodes_execution
        assert governance.dsm.langgraph.nodes_execution is not None

    def test_extractors_importable(self):
        import governance.evidence_scanner.extractors
        assert governance.evidence_scanner.extractors is not None

    def test_embedding_config_importable(self):
        import governance.embedding_config
        assert governance.embedding_config is not None

    def test_embedding_pipeline_importable(self):
        import governance.embedding_pipeline.pipeline
        assert governance.embedding_pipeline.pipeline is not None
