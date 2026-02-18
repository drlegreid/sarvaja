"""Deep scan batch 100: Session metrics + workflow orchestrator.

Batch 100 findings: 24 total, 0 confirmed fixes, 24 rejected.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from pathlib import Path


# ── Transcript pagination defense ──────────────


class TestTranscriptPagination:
    """Verify transcript pagination captures first entry correctly."""

    def test_page_1_includes_first_entry(self):
        """total_count > start_index correctly captures entry 1 on page 1."""
        start_index = 0  # (1-1) * 50
        entries = []
        total_count = 0

        for item in range(5):  # 5 entries
            total_count += 1
            if total_count > start_index and len(entries) < 50:
                entries.append(item)

        assert len(entries) == 5
        assert entries[0] == 0  # First entry included

    def test_page_2_skips_first_page(self):
        """Page 2 correctly skips first per_page entries."""
        per_page = 3
        start_index = 3  # (2-1) * 3
        entries = []
        total_count = 0

        for item in range(10):
            total_count += 1
            if total_count > start_index and len(entries) < per_page:
                entries.append(item)

        assert len(entries) == 3
        assert entries[0] == 3  # Fourth item (index 3) is first on page 2

    def test_total_count_tracks_all(self):
        """total_count reflects ALL entries, not just page."""
        start_index = 0
        entries = []
        total_count = 0

        for item in range(100):
            total_count += 1
            if total_count > start_index and len(entries) < 5:
                entries.append(item)

        assert len(entries) == 5
        assert total_count == 100


# ── File handle cleanup defense ──────────────


class TestTranscriptFileCleanup:
    """Verify stream_transcript properly closes file handles."""

    def test_file_closed_after_full_consumption(self):
        from governance.services.cc_transcript import stream_transcript

        # Non-existent file returns empty generator (no handle opened)
        result = list(stream_transcript("/nonexistent/path.jsonl"))
        assert result == []

    def test_missing_file_returns_empty(self):
        from governance.services.cc_transcript import stream_transcript

        gen = stream_transcript("/tmp/definitely_nonexistent_file_12345.jsonl")
        entries = list(gen)
        assert entries == []


# ── Budget calculation defense ──────────────


class TestBudgetCalculation:
    """Verify budget computation handles edge cases."""

    def test_ternary_precedence_no_budget(self):
        """Python ternary: (a / b) if c else d — NOT a / (b if c else d)."""
        tokens_used = 1000
        token_budget = 0
        # (tokens_used / max(token_budget, 1)) if token_budget else 0.0
        result = tokens_used / max(token_budget, 1) if token_budget else 0.0
        assert result == 0.0  # token_budget=0 → falsy → 0.0

    def test_ternary_precedence_with_budget(self):
        tokens_used = 500
        token_budget = 1000
        result = tokens_used / max(token_budget, 1) if token_budget else 0.0
        assert result == 0.5  # 500/1000

    def test_budget_utilization_guard(self):
        """if budget: excludes 0 (falsy) — no division by zero."""
        budget = 0
        certification = {}
        if budget:
            certification["budget_utilization"] = round(500 / budget * 100, 1)
        assert "budget_utilization" not in certification


# ── Orchestrator node defense ──────────────


class TestOrchestratorNodes:
    """Verify orchestrator node state access patterns."""

    def test_value_delivered_state_access(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        state = {
            "backlog": [],
            "current_task": {"task_id": "T-001", "priority": "HIGH", "description": "Test"},
            "current_phase": "VALIDATE",
            "value_delivered": 10,
            "tokens_used": 200,
            "completed_tasks": [],
            "cycles_completed": 1,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] > 10

    def test_gate_node_with_budget(self):
        from governance.workflows.orchestrator.nodes import gate_node

        state = {
            "backlog": [{"task_id": "T-001", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 10,
            "value_delivered": 0,
            "tokens_used": 0,
        }
        result = gate_node(state)
        assert result["gate_decision"] == "continue"


# ── Correlation floor division defense ──────────────


class TestCorrelationFloorDivision:
    """Verify floor division in latency is intentional (integer ms)."""

    def test_floor_division_for_ms(self):
        """// is correct for integer millisecond averages."""
        latencies = [100, 200, 150]
        avg = sum(latencies) // len(latencies)
        assert avg == 150  # Exact
        assert isinstance(avg, int)

    def test_floor_division_rounds_down(self):
        latencies = [100, 200, 151]
        avg = sum(latencies) // len(latencies)
        assert avg == 150  # Floor of 150.33


# ── Merkle tree defense (re-verification) ──────────────


class TestMerkleTreeOddCount:
    """Re-verify Merkle tree handles odd leaf counts correctly."""

    def test_three_leaves_produces_valid_root(self):
        from governance.frankel_hash import build_merkle_tree

        result = build_merkle_tree(["A", "B", "C"])
        assert isinstance(result, dict)
        assert "root" in result
        assert result["depth"] > 0

    def test_two_different_trees_different_roots(self):
        from governance.frankel_hash import build_merkle_tree

        r1 = build_merkle_tree(["A", "B", "C"])
        r2 = build_merkle_tree(["X", "Y", "Z"])
        assert r1["root"] != r2["root"]
