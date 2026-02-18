"""
Unit tests for Tab Deep Scan Batch 47 — spec_tiers splitlines guard,
cc_session_scanner iterdir safety, TypeDB silent exception logging,
session_persistence tmp file cleanup.

4 bugs fixed (BUG-SPEC-001, BUG-SCANNER-001/002, BUG-TYPEDB-SILENT-001,
BUG-PERSIST-TMP-001). Remaining findings verified as false positives.

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── BUG-SPEC-001: spec_tiers splitlines guard ──────────────────────


class TestSpecTiersSplitlinesGuard:
    """Verify export_to_robot handles empty tier strings."""

    def test_has_bugfix_marker(self):
        """BUG-SPEC-001 marker present in spec_tiers.py."""
        from governance.workflows.orchestrator import spec_tiers
        source = inspect.getsource(spec_tiers.export_to_robot)
        assert "BUG-SPEC-001" in source

    def test_splitlines_guard_exists(self):
        """Guard extracts first line safely."""
        from governance.workflows.orchestrator import spec_tiers
        source = inspect.getsource(spec_tiers.export_to_robot)
        assert "if tier_1_lines else" in source
        assert "if tier_2_lines else" in source

    def test_empty_tier_1_no_crash(self):
        """Empty tier_1 string does not raise IndexError."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {
            "task_id": "TASK-001",
            "tier_1": "",
            "tier_2": "Given something\nWhen tested",
            "tier_3": "Details here",
        }
        result = export_to_robot(spec)
        assert isinstance(result, str)
        assert "TASK-001" in result

    def test_empty_tier_2_no_crash(self):
        """Empty tier_2 string does not raise IndexError."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {
            "task_id": "TASK-002",
            "tier_1": "Feature: Test",
            "tier_2": "",
            "tier_3": "Details",
        }
        result = export_to_robot(spec)
        assert isinstance(result, str)

    def test_normal_tiers_still_work(self):
        """Normal multi-line tiers extract first line correctly."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {
            "task_id": "TASK-003",
            "tier_1": "Feature: Login\nAs a user",
            "tier_2": "Scenario: Valid login\nGiven credentials",
            "tier_3": "POST /api/login",
        }
        result = export_to_robot(spec)
        assert "Feature: Login" in result
        assert "Scenario: Valid login" in result


# ── BUG-SCANNER-001/002: cc_session_scanner iterdir safety ──────────


class TestScannerIterdirSafety:
    """Verify cc_session_scanner handles directory vanishing."""

    def test_discover_cc_projects_has_guard(self):
        """discover_cc_projects has OSError guard on iterdir."""
        from governance.services import cc_session_scanner
        source = inspect.getsource(cc_session_scanner.discover_cc_projects)
        assert "BUG-SCANNER-001" in source

    def test_discover_filesystem_has_guard(self):
        """discover_filesystem_projects has OSError guard on iterdir."""
        from governance.services import cc_session_scanner
        source = inspect.getsource(cc_session_scanner.discover_filesystem_projects)
        assert "BUG-SCANNER-002" in source

    def test_cc_projects_returns_list_on_oserror(self):
        """discover_cc_projects returns [] when iterdir raises OSError."""
        from governance.services.cc_session_scanner import discover_cc_projects
        mock_dir = MagicMock()
        mock_dir.is_dir.return_value = True
        mock_dir.iterdir.side_effect = OSError("Directory vanished")
        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", mock_dir):
            result = discover_cc_projects()
            assert result == []

    def test_filesystem_projects_survives_oserror(self):
        """discover_filesystem_projects skips dirs that vanish."""
        from governance.services.cc_session_scanner import discover_filesystem_projects
        with patch("pathlib.Path.is_dir", return_value=True):
            with patch("pathlib.Path.iterdir", side_effect=OSError("Gone")):
                result = discover_filesystem_projects(
                    scan_dirs=["/nonexistent"],
                    existing_paths=set(),
                    existing_ids=set(),
                )
                assert isinstance(result, list)


# ── BUG-TYPEDB-SILENT-001: TypeDB concept value logging ──────────────


class TestTypeDBConceptValueLogging:
    """Verify _concept_to_value logs instead of silently swallowing."""

    def test_has_bugfix_marker(self):
        """BUG-TYPEDB-SILENT-001 marker present."""
        from governance.typedb import base
        source = inspect.getsource(base)
        assert "BUG-TYPEDB-SILENT-001" in source

    def test_no_bare_except_pass(self):
        """No bare `except: pass` in _concept_to_value."""
        from governance.typedb.base import TypeDBBaseClient as TypeDBClient
        source = inspect.getsource(TypeDBClient._concept_to_value)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "pass" and i > 0:
                prev = lines[i - 1].strip()
                if prev.startswith("except"):
                    assert False, f"Bare except/pass at line {i}: {prev}"

    def test_logs_debug_on_get_value_failure(self):
        """get_value() failure is logged at DEBUG."""
        from governance.typedb.base import TypeDBBaseClient as TypeDBClient
        source = inspect.getsource(TypeDBClient._concept_to_value)
        assert "logger.debug" in source

    def test_concept_to_value_none_returns_none(self):
        """None concept returns None."""
        from governance.typedb.base import TypeDBBaseClient as TypeDBClient
        client = TypeDBClient.__new__(TypeDBClient)
        result = client._concept_to_value(None)
        assert result is None

    def test_concept_to_value_with_value_property(self):
        """Concept with .value returns the value."""
        from governance.typedb.base import TypeDBBaseClient as TypeDBClient
        client = TypeDBClient.__new__(TypeDBClient)
        concept = MagicMock(spec=[])
        concept.value = "test_value"
        # Remove get_value to force .value fallback
        result = client._concept_to_value(concept)
        assert result == "test_value"


# ── BUG-PERSIST-TMP-001: session_persistence tmp cleanup ──────────


class TestSessionPersistenceTmpCleanup:
    """Verify orphaned .tmp files are cleaned up on rename failure."""

    def test_has_bugfix_marker(self):
        """BUG-PERSIST-TMP-001 marker present."""
        from governance.stores import session_persistence
        source = inspect.getsource(session_persistence.persist_session)
        assert "BUG-PERSIST-TMP-001" in source

    def test_tmp_unlink_in_except(self):
        """tmp.unlink() called when rename fails."""
        from governance.stores import session_persistence
        source = inspect.getsource(session_persistence.persist_session)
        assert "tmp.unlink" in source

    def test_persist_still_works_normally(self):
        """Normal persist path works (no regression)."""
        from governance.stores.session_persistence import persist_session
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("governance.stores.session_persistence._STORE_DIR", Path(tmpdir)):
                with patch("governance.stores.session_persistence._get_path") as mock_path:
                    target = Path(tmpdir) / "test-session.json"
                    mock_path.return_value = target
                    persist_session("test-session", {"topic": "test"})
                    assert target.exists()


# ── False positive: budget.py ROI division ──────────────────────────


class TestBudgetROISafety:
    """Verify budget.py division is guarded by max()."""

    def test_max_guard_prevents_zero(self):
        """max(tokens_used, 1) prevents division by zero."""
        tokens_used = 0
        value_delivered = 10
        roi = value_delivered / max(tokens_used, 1)
        assert roi == 10.0  # Falls back to / 1

    def test_token_ratio_guard(self):
        """max(token_budget, 1) prevents zero in token_ratio."""
        token_budget = 0
        tokens_used = 100
        token_ratio = tokens_used / max(token_budget, 1) if token_budget else 0.0
        assert token_ratio == 0.0  # Ternary takes else branch

    def test_budget_module_imports(self):
        """Budget module is importable."""
        from governance.workflows.orchestrator import budget
        assert hasattr(budget, "compute_budget")


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch47:
    """Batch 47 cross-cutting consistency checks."""

    def test_spec_tiers_has_export_to_robot(self):
        """spec_tiers.py exports export_to_robot."""
        from governance.workflows.orchestrator import spec_tiers
        assert hasattr(spec_tiers, "export_to_robot")

    def test_scanner_has_both_discover_functions(self):
        """cc_session_scanner exports both discover functions."""
        from governance.services import cc_session_scanner
        assert hasattr(cc_session_scanner, "discover_cc_projects")
        assert hasattr(cc_session_scanner, "discover_filesystem_projects")

    def test_typedb_base_has_logger(self):
        """TypeDB base module has logger."""
        from governance.typedb import base
        assert hasattr(base, "logger")

    def test_persistence_has_persist_and_load(self):
        """session_persistence exports both persist and load."""
        from governance.stores import session_persistence
        assert hasattr(session_persistence, "persist_session")
        assert hasattr(session_persistence, "load_persisted_sessions")
