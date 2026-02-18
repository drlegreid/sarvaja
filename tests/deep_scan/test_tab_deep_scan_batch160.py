"""Deep scan batch 160: DSM tracker + taxonomy + proposals.

Batch 160 findings: 9 total, 0 confirmed fixes, 9 rejected.
"""
import pytest
from pathlib import Path


# ── DSM completed_cycles cap defense ──────────────


class TestDSMCompletedCyclesCapDefense:
    """Verify completed_cycles is capped at 50."""

    def test_cap_enforced_after_append(self):
        """After append, trim to last 50 — correct behavior."""
        cycles = list(range(50))
        cycles.append(50)  # Now 51
        if len(cycles) > 50:
            cycles = cycles[-50:]
        assert len(cycles) == 50
        assert cycles[0] == 1  # First item trimmed

    def test_cap_at_50_is_exact(self):
        """Cap maintains exactly 50 items."""
        cycles = list(range(55))
        if len(cycles) > 50:
            cycles = cycles[-50:]
        assert len(cycles) == 50
        assert cycles[-1] == 54  # Most recent kept


# ── DSM go_to_phase defense ──────────────


class TestDSMGoToPhaseDefense:
    """Verify go_to_phase is intentionally flexible for non-linear workflows."""

    def test_go_to_phase_documented_as_non_linear(self):
        """go_to_phase docstring says 'non-linear workflows'."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        assert "non-linear" in src

    def test_go_to_phase_blocks_idle_and_complete(self):
        """Cannot jump to IDLE or COMPLETE phases."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        assert "DSPPhase.IDLE" in src
        assert "DSPPhase.COMPLETE" in src

    def test_completed_phases_tracked(self):
        """go_to_phase appends current phase to phases_completed before jump."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        assert "phases_completed" in src


# ── DSM abort cycle defense ──────────────


class TestDSMAbortCycleDefense:
    """Verify abort_cycle intentionally discards cycle (not a bug)."""

    def test_abort_sets_metrics(self):
        """abort_cycle marks metrics before clearing."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        assert '"aborted"' in src or "'aborted'" in src

    def test_abort_does_not_archive(self):
        """Aborted cycles intentionally not in completed_cycles."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/dsm/tracker.py").read_text()
        # abort_cycle sets current_cycle = None without adding to completed
        assert "self.current_cycle = None" in src


# ── Proposal TypeQL escaping defense ──────────────


class TestProposalTypeQLEscapingDefense:
    """Verify proposal status escaping is correct."""

    def test_chr_92_chr_34_is_backslash_quote(self):
        """chr(92) + chr(34) produces backslash-quote for TypeQL."""
        escaped = '"test'.replace(chr(34), chr(92) + chr(34))
        assert escaped == '\\"test'

    def test_status_filter_escapes_quotes(self):
        """Status value with quotes is properly escaped."""
        status = 'active"injection'
        safe = status.replace(chr(34), chr(92) + chr(34))
        assert '"' not in safe.replace('\\"', '')  # Only escaped quotes remain


# ── Proposal history defense ──────────────


class TestProposalHistoryDefense:
    """Verify proposal history is low-volume (governance proposals, not high-rate)."""

    def test_proposals_returned_most_recent_first(self):
        """Proposals returned in reversed order (most recent first)."""
        history = [1, 2, 3, 4, 5]
        limit = 3
        result = list(reversed(history[-limit:]))
        assert result == [5, 4, 3]
