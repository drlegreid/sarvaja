"""Batch 261 — Session lifecycle timestamp consistency tests.

Validates fixes for:
- BUG-261-LIFECYCLE-001: Single end_time capture in end_session TypeDB path
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-261-LIFECYCLE-001: Consistent end_time ──────────────────────

class TestEndSessionTimestampConsistency:
    """end_session must capture end_time once and reuse it."""

    def test_end_time_captured_once(self):
        """end_time_str should be assigned once before use."""
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("def end_session")
        block = src[idx:idx + 3000]
        assert "end_time_str = datetime.now().isoformat()" in block

    def test_end_time_reused_in_evidence(self):
        """Evidence generation should use end_time_str, not datetime.now()."""
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("def end_session")
        block = src[idx:idx + 3000]
        assert 'session_dict["end_time"] = end_time_str' in block

    def test_end_time_reused_in_store(self):
        """Fallback store update should use end_time_str, not datetime.now()."""
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("def end_session")
        block = src[idx:idx + 3000]
        assert '["end_time"] = end_time_str' in block

    def test_no_extra_datetime_now_in_typedb_path(self):
        """TypeDB path should not have multiple datetime.now() for end_time."""
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("def end_session")
        # Find the TypeDB path (before fallback)
        fallback_marker = "# Fallback to in-memory"
        fallback_idx = src.index(fallback_marker, idx)
        typedb_block = src[idx:fallback_idx]
        # Count datetime.now().isoformat() calls — should be exactly 1 (end_time_str)
        count = typedb_block.count("datetime.now().isoformat()")
        assert count == 1, f"Expected 1 datetime.now().isoformat() in TypeDB path, found {count}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "BUG-261-LIFECYCLE-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch261Imports:
    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None

    def test_ingestion_orchestrator_importable(self):
        import governance.services.ingestion_orchestrator
        assert governance.services.ingestion_orchestrator is not None
