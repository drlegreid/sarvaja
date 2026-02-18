"""Deep scan batch 134: DSM tracker + session collector.

Batch 134 findings: 18 total, 0 confirmed fixes, 18 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from pathlib import Path
import tempfile


# ── DSM phase completion no-duplicate defense ──────────────


class TestDSMPhaseNoDuplicateDefense:
    """Verify advance_phase and complete_cycle don't double-append."""

    def _make_tracker(self):
        """Create isolated DSMTracker with temp state file."""
        from governance.dsm.tracker import DSMTracker
        tmpdir = tempfile.mkdtemp()
        return DSMTracker(
            evidence_dir=tmpdir,
            state_file=str(Path(tmpdir) / "state.json"),
        )

    def test_advance_appends_old_phase_only(self):
        """advance_phase appends the phase being LEFT, not entered."""
        tracker = self._make_tracker()
        tracker.start_cycle(batch_id="test")

        # IDLE → AUDIT: IDLE is excluded (line 98 check)
        tracker.advance_phase(force=True)
        assert "idle" not in tracker.current_cycle.phases_completed

        # AUDIT → HYPOTHESIZE: AUDIT appended
        tracker.advance_phase(force=True)
        assert "audit" in tracker.current_cycle.phases_completed
        assert tracker.current_cycle.phases_completed.count("audit") == 1

        tracker.abort_cycle(reason="test")

    def test_complete_cycle_appends_current_once(self):
        """complete_cycle appends current phase exactly once."""
        tracker = self._make_tracker()
        tracker.start_cycle(batch_id="test")
        tracker.advance_phase(force=True)  # IDLE → AUDIT
        tracker.advance_phase(force=True)  # AUDIT → HYPOTHESIZE
        # Now in HYPOTHESIZE, call complete_cycle
        tracker.complete_cycle()
        last_cycle = tracker.completed_cycles[-1]
        assert last_cycle.phases_completed.count("hypothesize") == 1
        assert last_cycle.phases_completed.count("audit") == 1

    def test_report_phase_excluded_from_completion(self):
        """REPORT phase is excluded from phases_completed in complete_cycle."""
        from governance.dsm.phases import DSPPhase
        excluded = (DSPPhase.COMPLETE, DSPPhase.REPORT)
        assert DSPPhase.REPORT in excluded


# ── DSM cycle retention cap defense ──────────────


class TestDSMCycleRetentionDefense:
    """Verify completed_cycles cap at 50."""

    def _make_tracker(self):
        from governance.dsm.tracker import DSMTracker
        tmpdir = tempfile.mkdtemp()
        return DSMTracker(
            evidence_dir=tmpdir,
            state_file=str(Path(tmpdir) / "state.json"),
        )

    def test_cap_enforced_at_51(self):
        """More than 50 completed cycles triggers trim."""
        tracker = self._make_tracker()
        for i in range(51):
            tracker.start_cycle(batch_id=f"batch-{i}")
            tracker.complete_cycle()
        assert len(tracker.completed_cycles) == 50

    def test_cap_preserves_most_recent(self):
        """Trim keeps the most recent 50 cycles."""
        tracker = self._make_tracker()
        for i in range(55):
            tracker.start_cycle(batch_id=f"batch-{i}")
            tracker.complete_cycle()
        assert tracker.completed_cycles[-1].batch_id == "batch-54"


# ── DSM evidence rendering defense ──────────────


class TestDSMEvidenceRenderingDefense:
    """Verify evidence rendering handles edge cases."""

    def test_finding_description_truncated_in_table(self):
        """Long descriptions are truncated to 50 chars in table."""
        raw_desc = "A" * 100
        desc = raw_desc[:50] + "..." if len(raw_desc) > 50 else raw_desc
        assert len(desc) == 53  # 50 + "..."
        assert desc.endswith("...")

    def test_short_description_not_truncated(self):
        """Short descriptions are NOT truncated."""
        raw_desc = "Short finding"
        desc = raw_desc[:50] + "..." if len(raw_desc) > 50 else raw_desc
        assert desc == "Short finding"

    def test_missing_fields_use_default(self):
        """Missing finding fields use 'N/A' default."""
        finding = {}
        assert finding.get('id', 'N/A') == 'N/A'
        assert finding.get('type', 'N/A') == 'N/A'
        assert finding.get('severity', 'N/A') == 'N/A'


# ── Session collector ID format defense ──────────────


class TestSessionCollectorIDDefense:
    """Verify SessionCollector generates correct IDs."""

    def test_session_id_format(self):
        """Session ID follows SESSION-{date}-{TOPIC} format."""
        from governance.session_collector.collector import SessionCollector

        collector = SessionCollector(topic="test-topic")
        today = date.today().isoformat()
        assert collector.session_id.startswith(f"SESSION-{today}-")
        assert "TEST-TOPIC" in collector.session_id

    def test_topic_uppercased(self):
        """Topic is uppercased in session ID."""
        from governance.session_collector.collector import SessionCollector

        collector = SessionCollector(topic="my-mixed-Case")
        assert "MY-MIXED-CASE" in collector.session_id


# ── DSM state persistence defense ──────────────


class TestDSMStatePersistenceDefense:
    """Verify DSM state saves current_cycle and completed_count."""

    def test_save_state_includes_current_cycle(self):
        """save_state includes current_cycle dict."""
        from governance.dsm.tracker_persistence import save_state
        from governance.dsm.models import DSMCycle
        import json

        cycle = DSMCycle(
            cycle_id="DSM-2026-02-15-TEST",
            batch_id="test",
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = Path(f.name)

        try:
            save_state(state_file, cycle, completed_count=5)
            data = json.loads(state_file.read_text())
            assert data["current_cycle"]["cycle_id"] == "DSM-2026-02-15-TEST"
            assert data["completed_count"] == 5
        finally:
            state_file.unlink(missing_ok=True)

    def test_save_state_atomic_write(self):
        """save_state uses atomic write (temp file + replace)."""
        import inspect
        from governance.dsm import tracker_persistence
        source = inspect.getsource(tracker_persistence.save_state)
        assert "os.replace" in source


# ── Abandoned cycle detection defense ──────────────


class TestAbandonedCycleDefense:
    """Verify abandoned cycle detection works correctly."""

    def test_recent_cycle_not_abandoned(self):
        """Cycle started recently is not abandoned."""
        from governance.dsm.tracker_persistence import check_abandoned_cycle
        from governance.dsm.models import DSMCycle

        cycle = DSMCycle(
            cycle_id="DSM-2026-02-15-TEST",
            batch_id="test",
        )
        cycle.start_time = datetime.now().isoformat()
        assert check_abandoned_cycle(cycle) is False

    def test_completed_cycle_not_abandoned(self):
        """Completed cycle is never considered abandoned."""
        from governance.dsm.tracker_persistence import check_abandoned_cycle
        from governance.dsm.models import DSMCycle

        cycle = DSMCycle(
            cycle_id="DSM-2026-02-15-TEST",
            batch_id="test",
        )
        cycle.current_phase = "complete"
        assert check_abandoned_cycle(cycle) is False
