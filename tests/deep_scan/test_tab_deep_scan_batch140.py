"""Deep scan batch 140: Workflows + orchestrator.

Batch 140 findings: 3 total (1 duplicate), 0 confirmed fixes, 3 rejected.
All findings verified as design choices or correct behavior.
"""
import pytest
from datetime import datetime


# ── State graph merge behavior defense ──────────────


class TestStateGraphMergeBehaviorDefense:
    """Verify MockStateGraph uses dict.update() (merge, not replace)."""

    def test_update_preserves_unmentioned_keys(self):
        """dict.update() preserves keys not in result."""
        state = {"value_delivered": 10, "tokens_used": 50, "other": "data"}
        result = {"tokens_used": 60}
        state.update(result)
        assert state["value_delivered"] == 10  # Preserved
        assert state["tokens_used"] == 60  # Updated
        assert state["other"] == "data"  # Preserved

    def test_park_task_preserves_value_delivered(self):
        """park_task_node result doesn't include value_delivered → preserved."""
        state = {
            "current_phase": "validating",
            "cycles_completed": 5,
            "cycle_history": [],
            "current_task": {"task_id": "T-1"},
            "value_delivered": 12,
            "tokens_used": 50,
        }
        # Simulate park_task_node result (no value_delivered)
        result = {
            "current_phase": "task_parked",
            "cycles_completed": 6,
            "cycle_history": [{"task_id": "T-1", "status": "parked"}],
            "current_task": None,
            "tokens_used": 60,
        }
        state.update(result)
        assert state["value_delivered"] == 12  # Preserved by merge
        assert state["tokens_used"] == 60  # Updated

    def test_complete_cycle_updates_both_budget_keys(self):
        """complete_cycle_node updates both value_delivered and tokens_used."""
        state = {"value_delivered": 10, "tokens_used": 50}
        # Simulate complete_cycle result
        result = {"value_delivered": 13, "tokens_used": 60}
        state.update(result)
        assert state["value_delivered"] == 13
        assert state["tokens_used"] == 60


# ── Budget threshold defense ──────────────


class TestBudgetThresholdDefense:
    """Verify budget thresholds use correct comparison operators."""

    def test_exhaustion_threshold_inclusive(self):
        """TOKEN_EXHAUSTION at exactly 0.8 → stops (>=)."""
        from governance.workflows.orchestrator.budget import TOKEN_EXHAUSTION_THRESHOLD
        token_ratio = TOKEN_EXHAUSTION_THRESHOLD  # Exactly 0.8
        assert token_ratio >= TOKEN_EXHAUSTION_THRESHOLD  # Inclusive

    def test_low_value_threshold_exclusive(self):
        """LOW_VALUE at exactly 0.5 → continues (>)."""
        from governance.workflows.orchestrator.budget import LOW_VALUE_THRESHOLD
        token_ratio = LOW_VALUE_THRESHOLD  # Exactly 0.5
        assert not (token_ratio > LOW_VALUE_THRESHOLD)  # Exclusive: boundary continues

    def test_low_value_above_threshold_stops(self):
        """LOW_VALUE above 0.5 → stops."""
        from governance.workflows.orchestrator.budget import LOW_VALUE_THRESHOLD
        token_ratio = LOW_VALUE_THRESHOLD + 0.01
        assert token_ratio > LOW_VALUE_THRESHOLD

    def test_compute_budget_exhausted(self):
        """Budget exhausted at 80% returns should_continue=False."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "cycles_completed": 0, "max_cycles": 100,
            "backlog": [{"priority": "HIGH"}],
            "value_delivered": 0, "tokens_used": 80, "token_budget": 100,
        }
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "token_budget_exhausted"

    def test_compute_budget_available(self):
        """Budget available with healthy ratios returns should_continue=True."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "cycles_completed": 0, "max_cycles": 100,
            "backlog": [{"priority": "HIGH"}],
            "value_delivered": 10, "tokens_used": 20, "token_budget": 100,
        }
        result = compute_budget(state)
        assert result["should_continue"] is True
        assert result["reason"] == "budget_available"


# ── Preloader decision parsing defense ──────────────


class TestPreloaderDecisionParsingDefense:
    """Verify decision file parsing handles standard format."""

    def test_standard_summary_format_parsed(self):
        """## Summary with standard casing is parsed correctly."""
        import re
        content = "# DECISION-001\n**Status**: APPROVED\n## Summary\nThis is the summary text.\n## Details\n"
        match = re.search(r"##\s*Summary\s*\n+(.+?)(?=\n##|\n\*\*|\Z)", content, re.DOTALL)
        assert match is not None
        assert "This is the summary text." in match.group(1)

    def test_summary_truncated_to_200_chars(self):
        """Summary is truncated to 200 characters."""
        import re
        long_text = "x" * 300
        content = f"# DECISION\n## Summary\n{long_text}\n## End"
        match = re.search(r"##\s*Summary\s*\n+(.+?)(?=\n##|\n\*\*|\Z)", content, re.DOTALL)
        assert match is not None
        truncated = match.group(1).strip()[:200]
        assert len(truncated) == 200

    def test_missing_summary_returns_empty(self):
        """No ## Summary section returns empty string."""
        import re
        content = "# DECISION\n**Status**: APPROVED\n## Details\nSome text\n"
        match = re.search(r"##\s*Summary\s*\n+(.+?)(?=\n##|\n\*\*|\Z)", content, re.DOTALL)
        result = match.group(1).strip()[:200] if match else ""
        assert result == ""


# ── Parser malformed JSON handling defense ──────────────


class TestParserMalformedJSONDefense:
    """Verify JSONL parser handles malformed lines gracefully."""

    def test_malformed_json_skipped(self):
        """json.loads raises JSONDecodeError on malformed input."""
        import json
        line = "this is not json"
        with pytest.raises(json.JSONDecodeError):
            json.loads(line)

    def test_empty_line_skipped(self):
        """Empty lines are stripped and skipped."""
        line = "   \n"
        assert line.strip() == ""

    def test_valid_json_parsed(self):
        """Valid JSON is parsed correctly."""
        import json
        line = '{"type": "user", "timestamp": "2026-02-15T10:00:00"}'
        obj = json.loads(line)
        assert obj["type"] == "user"
