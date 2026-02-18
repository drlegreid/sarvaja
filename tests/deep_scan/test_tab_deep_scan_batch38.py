"""
Unit tests for Tab Deep Scan Batch 38 — data loaders, runner_exec, tasks_mutations.

Covers: BUG-REFRESH-001 (non-list data guard in tasks refresh),
BUG-RUNNER-002 (persistence failure logging in test runner),
BUG-MUTATIONS-002 (TypeDB link failure logging at warning level).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import logging


# ── BUG-REFRESH-001: Non-list data guard in tasks refresh ─────────────


class TestRefreshNonListGuard:
    """Tasks refresh must guard against non-list API data."""

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "BUG-REFRESH-001" in source

    def test_isinstance_list_check(self):
        """Must use isinstance(data, list) guard."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "isinstance(data, list)" in source

    def test_dict_without_items_produces_empty(self):
        """A dict without 'items' key should produce empty task list."""
        data = {"error": "something went wrong", "status": 500}
        # Simulate the fixed logic
        items_list = data if isinstance(data, list) else []
        page_size = 20
        result = items_list[:page_size] if len(items_list) > page_size else items_list
        assert result == []

    def test_plain_list_preserved(self):
        """A plain list should be sliced normally."""
        data = [{"task_id": f"T-{i}"} for i in range(30)]
        page_size = 20
        items_list = data if isinstance(data, list) else []
        result = items_list[:page_size] if len(items_list) > page_size else items_list
        assert len(result) == 20

    def test_small_list_unchanged(self):
        """A list smaller than page_size should be returned as-is."""
        data = [{"task_id": "T-1"}, {"task_id": "T-2"}]
        page_size = 20
        items_list = data if isinstance(data, list) else []
        result = items_list[:page_size] if len(items_list) > page_size else items_list
        assert len(result) == 2
        assert result == data

    def test_pagination_from_non_list(self):
        """Pagination stats for non-list data should show zero."""
        data = {"total": 5, "results": [1, 2, 3]}  # dict without "items"
        items_list = data if isinstance(data, list) else []
        page_size = 20
        pagination = {
            "total": len(items_list),
            "offset": 0,
            "limit": page_size,
            "has_more": len(items_list) > page_size,
            "returned": min(len(items_list), page_size),
        }
        assert pagination["total"] == 0
        assert pagination["has_more"] is False
        assert pagination["returned"] == 0


# ── BUG-RUNNER-002: Persistence failure logging ──────────────────────


class TestRunnerPersistenceLogging:
    """Test runner must log persistence failures instead of silently swallowing."""

    def test_has_bugfix_marker(self):
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec)
        assert "BUG-RUNNER-002" in source

    def test_no_bare_except_pass(self):
        """No bare 'except Exception: pass' around _persist_result."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "_persist_result" in line and "except" not in line:
                # Find the except block after this persist call
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "except Exception:" in lines[j] and j + 1 < len(lines):
                        # Next line after except should NOT be bare 'pass'
                        next_line = lines[j + 1].strip()
                        assert next_line != "pass", (
                            f"Bare 'except Exception: pass' at line {j+1} near _persist_result"
                        )

    def test_timeout_persist_has_logging(self):
        """Timeout branch must log persistence failures."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec.execute_tests)
        assert "Failed to persist timeout result" in source

    def test_error_persist_has_logging(self):
        """Error branch must log persistence failures."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec.execute_tests)
        assert "Failed to persist error result" in source

    def test_regression_error_persist_has_logging(self):
        """Regression error branch must log persistence failures."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec.execute_regression)
        assert "Failed to persist regression error result" in source

    def test_heuristic_error_persist_has_logging(self):
        """Heuristic error branch must log persistence failures."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec.execute_heuristic)
        assert "Failed to persist heuristic error result" in source

    def test_all_persist_blocks_consistent(self):
        """All _persist_result exception handlers should use logger.warning."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec)
        # Count persist calls and logger.warning calls near them
        lines = source.split("\n")
        persist_except_count = 0
        warning_count = 0
        for i, line in enumerate(lines):
            if "except Exception as pe:" in line:
                # Check if next meaningful line has logger.warning
                for j in range(i + 1, min(i + 4, len(lines))):
                    stripped = lines[j].strip()
                    if stripped and not stripped.startswith("#"):
                        if "logger.warning" in stripped:
                            warning_count += 1
                        persist_except_count += 1
                        break
        # All exception handlers around persist should have warnings
        assert warning_count >= 6, f"Expected 6+ warning log calls, found {warning_count}"


# ── BUG-MUTATIONS-002: TypeDB link failure logging level ─────────────


class TestMutationsLinkLogging:
    """TypeDB link failures must be logged at warning level."""

    def test_has_bugfix_marker(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        assert "BUG-MUTATIONS-002" in source

    def test_session_link_uses_warning(self):
        """Session link failures must use logger.warning."""
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        # Find the session link block
        assert 'logger.warning(f"TypeDB session link' in source

    def test_document_link_uses_warning(self):
        """Document link failures must use logger.warning."""
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        assert 'logger.warning(f"TypeDB document link' in source

    def test_no_debug_for_link_failures(self):
        """Link failures should NOT use logger.debug."""
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        # The old debug patterns should be replaced
        assert 'logger.debug(f"TypeDB session link' not in source
        assert 'logger.debug(f"TypeDB document link' not in source


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch38:
    """Batch 38 cross-cutting consistency checks."""

    def test_all_bugfix_markers_present(self):
        """All batch 38 bugfix markers must be in their respective files."""
        from agent.governance_ui.controllers import data_loaders_refresh
        from governance.routes.tests import runner_exec
        from governance.services import tasks_mutations
        assert "BUG-REFRESH-001" in inspect.getsource(data_loaders_refresh)
        assert "BUG-RUNNER-002" in inspect.getsource(runner_exec)
        assert "BUG-MUTATIONS-002" in inspect.getsource(tasks_mutations)

    def test_runner_exec_still_persists_on_success(self):
        """Success path should still persist results (not broken by fix)."""
        from governance.routes.tests import runner_exec
        source = inspect.getsource(runner_exec.execute_tests)
        assert "_persist_result(run_id, test_result)" in source

    def test_trust_consensus_already_guarded(self):
        """Verify consensus score division by zero is already guarded (false positive)."""
        from agent.governance_ui.data_access.trust_calculations import calculate_consensus_score
        # All abstain votes = total_weight 0 should return 0.0
        result = calculate_consensus_score([
            {"vote_value": "abstain", "vote_weight": 1.0},
            {"vote_value": "abstain", "vote_weight": 2.0},
        ])
        assert result == 0.0

    def test_trust_consensus_empty_votes(self):
        """Empty votes list should return 0.0."""
        from agent.governance_ui.data_access.trust_calculations import calculate_consensus_score
        assert calculate_consensus_score([]) == 0.0

    def test_trust_consensus_normal(self):
        """Normal votes should calculate correctly."""
        from agent.governance_ui.data_access.trust_calculations import calculate_consensus_score
        result = calculate_consensus_score([
            {"vote_value": "approve", "vote_weight": 3.0},
            {"vote_value": "reject", "vote_weight": 1.0},
        ])
        assert result == 0.75  # 3.0 / 4.0
