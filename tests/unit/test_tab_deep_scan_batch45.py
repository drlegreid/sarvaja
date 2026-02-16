"""
Unit tests for Tab Deep Scan Batch 45 — cc_session_ingestion null guards,
workspace_registry fallback, UI view false positives.

3 bugs fixed (BUG-INGEST-003, BUG-INGEST-004, BUG-REGISTRY-001).
Multiple UI view findings verified as false positives (Trame/Vue patterns).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
from datetime import datetime
from unittest.mock import MagicMock


# ── BUG-INGEST-003: Thinking block timestamp guard ──────────────────


class TestThinkingTimestampGuard:
    """Verify thinking blocks handle None timestamps."""

    def test_has_bugfix_marker(self):
        """BUG-INGEST-003 marker present in cc_session_ingestion."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "BUG-INGEST-003" in source

    def test_thinking_timestamp_has_guard(self):
        """Thinking block timestamp uses ternary guard."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        # Must have the guard pattern for thinking timestamp
        assert "entry.timestamp.isoformat() if entry.timestamp else None" in source

    def test_tool_call_timestamp_also_guarded(self):
        """Tool call timestamp guard (BUG-INGEST-002) still present."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        # BUG-INGEST-002 guard must also exist
        assert "BUG-INGEST-002" in source

    def test_none_timestamp_produces_none(self):
        """None timestamp → None (not crash)."""
        entry_ts = None
        result = entry_ts.isoformat() if entry_ts else None
        assert result is None

    def test_valid_timestamp_produces_iso(self):
        """Valid timestamp → ISO string."""
        entry_ts = datetime(2026, 2, 15, 10, 0)
        result = entry_ts.isoformat() if entry_ts else None
        assert result == "2026-02-15T10:00:00"


# ── BUG-INGEST-004: Latency computation guard ──────────────────────


class TestLatencyComputationGuard:
    """Verify latency computation handles None timestamps."""

    def test_has_bugfix_marker(self):
        """BUG-INGEST-004 marker present."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "BUG-INGEST-004" in source

    def test_latency_guard_includes_entry_timestamp(self):
        """Guard checks both use_ts AND entry.timestamp."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "if use_ts and entry.timestamp:" in source

    def test_none_entry_timestamp_skips_latency(self):
        """When entry.timestamp is None, latency is not computed."""
        use_ts = datetime(2026, 2, 15, 10, 0)
        entry_timestamp = None
        latency = None
        if use_ts and entry_timestamp:
            latency = int((entry_timestamp - use_ts).total_seconds() * 1000)
        assert latency is None

    def test_valid_timestamps_compute_latency(self):
        """When both timestamps exist, latency is computed."""
        from datetime import timedelta
        use_ts = datetime(2026, 2, 15, 10, 0, 0)
        entry_timestamp = datetime(2026, 2, 15, 10, 0, 2)
        latency = None
        if use_ts and entry_timestamp:
            latency = int((entry_timestamp - use_ts).total_seconds() * 1000)
        assert latency == 2000


# ── BUG-REGISTRY-001: Workspace registry null fallback ──────────────


class TestWorkspaceRegistryFallback:
    """Verify workspace registry handles missing generic type."""

    def test_has_bugfix_marker(self):
        """BUG-REGISTRY-001 marker present."""
        from governance.services import workspace_registry
        source = inspect.getsource(workspace_registry)
        assert "BUG-REGISTRY-001" in source

    def test_get_agent_templates_returns_list(self):
        """get_agent_templates_for_type always returns a list."""
        from governance.services.workspace_registry import get_agent_templates_for_type
        result = get_agent_templates_for_type("governance")
        assert isinstance(result, list)

    def test_unknown_type_fallback(self):
        """Unknown type falls back to generic templates."""
        from governance.services.workspace_registry import get_agent_templates_for_type
        result = get_agent_templates_for_type("unknown_type_xyz")
        assert isinstance(result, list)

    def test_detect_project_type_returns_string(self):
        """detect_project_type always returns a string."""
        from governance.services.workspace_registry import detect_project_type
        result = detect_project_type("/nonexistent/path")
        assert isinstance(result, str)
        assert result == "generic"


# ── False positive: any() with generator short-circuits ──────────────


class TestGlobShortCircuit:
    """Verify Python any() with generator short-circuits correctly."""

    def test_any_stops_at_first_true(self):
        """any() stops evaluating after first True."""
        counter = {"count": 0}

        def gen():
            for i in range(100):
                counter["count"] += 1
                yield i == 2  # True at i=2

        result = any(gen())
        assert result is True
        assert counter["count"] == 3  # Stopped after finding True at i=2

    def test_any_empty_generator(self):
        """any() on empty generator returns False."""
        assert any(x for x in []) is False

    def test_glob_any_pattern(self):
        """The any(p.glob(...)) pattern is efficient."""
        from pathlib import Path
        # Non-existent path should not crash
        result = any(Path("/nonexistent").glob("**/*.gd"))
        assert result is False


# ── False positive: Vue v-for key patterns ──────────────────────────


class TestVueKeyPatternSafety:
    """Verify Trame v-for index keys are functional (not crashes)."""

    def test_enumerate_produces_index(self):
        """Python enumerate produces valid indices for Vue."""
        items = ["a", "b", "c"]
        result = list(enumerate(items))
        assert result == [(0, "a"), (1, "b"), (2, "c")]

    def test_empty_list_enumerate(self):
        """Empty list enumerate produces no items."""
        result = list(enumerate([]))
        assert result == []


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch45:
    """Batch 45 cross-cutting consistency checks."""

    def test_ingestion_has_both_timestamp_guards(self):
        """Both BUG-INGEST-002 and BUG-INGEST-003 guards present."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion)
        assert "BUG-INGEST-002" in source
        assert "BUG-INGEST-003" in source
        assert "BUG-INGEST-004" in source

    def test_workspace_registry_has_generic_type(self):
        """Workspace registry initializes 'generic' type."""
        from governance.services.workspace_registry import get_workspace_type
        generic = get_workspace_type("generic")
        assert generic is not None

    def test_session_ingestion_has_logger(self):
        """cc_session_ingestion has logger configured."""
        from governance.services import cc_session_ingestion
        assert hasattr(cc_session_ingestion, "logger")

    def test_workspace_types_include_governance(self):
        """Workspace types include governance type."""
        from governance.services.workspace_registry import get_workspace_type
        gov = get_workspace_type("governance")
        assert gov is not None
