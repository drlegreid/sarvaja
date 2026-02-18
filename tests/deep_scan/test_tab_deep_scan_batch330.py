"""
Deep Scan Batch 330-333 Defense Tests.

Validates 6 production fixes:
- BUG-332-CRUD-001: tasks/crud.py _update_attribute uses 'is not None' (not truthiness)
- BUG-332-CRUD-002: tasks/crud.py insert_task guards name against None
- BUG-331-MEM-001: memory_tiers.py thread-safe _short_memory access
- BUG-331-TRACE-001: traceability.py None guard on rule/task IDs in trace chains
- BUG-333-PANEL-001: trust/panels.py + workflow_proposals.py type_ for VAlert
- BUG-333-WF-001: workflow_proposals.py null guards on impact_score/risk_level
"""

import ast
import re
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-332-CRUD-001: _update_attribute identity check
# ============================================================

class TestUpdateAttributeIdentityCheck:
    """Verify _update_attribute uses 'is not None' instead of truthiness."""

    def _get_source(self):
        p = ROOT / "governance" / "typedb" / "queries" / "tasks" / "crud.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-332-CRUD-001" in src

    def test_is_not_none_used(self):
        """_update_attribute must use 'is not None' for old_value check."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_update_attribute":
                func_src = ast.get_source_segment(src, node)
                assert "old_value is not None" in func_src, \
                    "_update_attribute must use 'is not None' check"
                break
        else:
            raise AssertionError("_update_attribute not found")

    def test_no_bare_truthiness_check(self):
        """_update_attribute must NOT use bare 'if old_value:' check."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_update_attribute":
                func_src = ast.get_source_segment(src, node)
                # Should not have a bare truthiness check line
                lines = func_src.split("\n")
                for line in lines:
                    stripped = line.strip()
                    # Reject 'if old_value:' but allow 'if old_value is not None:'
                    if stripped == "if old_value:":
                        raise AssertionError(
                            "Found bare 'if old_value:' — must use 'if old_value is not None:'"
                        )
                break


# ============================================================
# BUG-332-CRUD-002: insert_task name guard
# ============================================================

class TestInsertTaskNameGuard:
    """Verify insert_task guards name against None."""

    def _get_source(self):
        p = ROOT / "governance" / "typedb" / "queries" / "tasks" / "crud.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-332-CRUD-002" in src

    def test_name_guard_before_escape(self):
        """insert_task must check name before calling .replace()."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "insert_task":
                func_src = ast.get_source_segment(src, node)
                assert "if not name:" in func_src, \
                    "insert_task must guard against None/empty name"
                # Guard must appear before the escape line
                guard_idx = func_src.index("if not name:")
                escape_idx = func_src.index("name_escaped = name.replace")
                assert guard_idx < escape_idx, \
                    "Name guard must appear before name escaping"
                break
        else:
            raise AssertionError("insert_task not found")


# ============================================================
# BUG-331-MEM-001: memory_tiers.py thread safety
# ============================================================

class TestMemoryTiersThreadSafety:
    """Verify memory_tiers.py uses threading.Lock for _short_memory."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "memory_tiers.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-331-MEM-001" in src

    def test_threading_import(self):
        src = self._get_source()
        assert "import threading" in src

    def test_lock_defined(self):
        src = self._get_source()
        assert "_short_memory_lock" in src

    def test_lock_used_in_save(self):
        """memory_save L1 path must use _short_memory_lock."""
        src = self._get_source()
        assert "with _short_memory_lock:" in src

    def test_snapshot_in_recall(self):
        """memory_recall must snapshot _short_memory before iteration."""
        src = self._get_source()
        # Should take a snapshot: list(_short_memory.items())
        assert "_snapshot = list(_short_memory.items())" in src

    def test_lock_used_for_snapshot(self):
        """The snapshot should be taken under the lock."""
        src = self._get_source()
        snapshot_idx = src.index("_snapshot = list(_short_memory.items())")
        # Find the nearest preceding 'with _short_memory_lock:' before the snapshot
        lock_idx = src.rfind("with _short_memory_lock:", 0, snapshot_idx)
        assert lock_idx != -1, "No _short_memory_lock context before snapshot"
        between = src[lock_idx:snapshot_idx]
        # Should be within a few lines (lock → snapshot)
        assert between.count("\n") < 5


# ============================================================
# BUG-331-TRACE-001: traceability.py None guard
# ============================================================

class TestTraceabilityNoneGuard:
    """Verify traceability.py guards against None/empty IDs in trace chains."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "traceability.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-331-TRACE-001" in src

    def test_rid_guard_in_depth2(self):
        """depth>=2 block must guard 'if rid and rid not in known'."""
        src = self._get_source()
        assert "if rid and rid not in known" in src

    def test_tid_guard_in_session_chain(self):
        """trace_session_chain must guard task IDs."""
        src = self._get_source()
        assert "for tid in result[\"task_ids\"] if tid]" in src

    def test_rid_guard_in_session_chain(self):
        """trace_session_chain must guard rule IDs."""
        src = self._get_source()
        assert "for rid in result[\"rules_applied\"] if rid]" in src


# ============================================================
# BUG-333-PANEL-001: VAlert type_ usage
# ============================================================

class TestVAlertTypeUnderscore:
    """Verify VAlert uses type_ instead of type (Python reserved keyword)."""

    def _check_file(self, rel_path):
        p = ROOT / rel_path
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for VAlert calls with keyword 'type' (not 'type_')
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "VAlert":
                    for kw in node.keywords:
                        if kw.arg == "type":
                            # Get value for error msg
                            line = getattr(kw, "lineno", "?")
                            raise AssertionError(
                                f"VAlert at line {line} uses type= instead of type_="
                            )
        return True

    def test_panels_no_bare_type(self):
        self._check_file("agent/governance_ui/views/trust/panels.py")

    def test_workflow_proposals_no_bare_type(self):
        self._check_file("agent/governance_ui/views/workflow_proposals.py")

    def test_bug_marker_in_panels(self):
        p = ROOT / "agent" / "governance_ui" / "views" / "trust" / "panels.py"
        src = p.read_text(encoding="utf-8")
        assert "BUG-333-PANEL-001" in src

    def test_bug_marker_in_proposals(self):
        p = ROOT / "agent" / "governance_ui" / "views" / "workflow_proposals.py"
        src = p.read_text(encoding="utf-8")
        assert "BUG-333-PANEL-001" in src


# ============================================================
# BUG-333-WF-001: workflow_proposals.py null guards
# ============================================================

class TestWorkflowProposalNullGuards:
    """Verify workflow_proposals.py guards impact_score and risk_level."""

    def _get_source(self):
        p = ROOT / "agent" / "governance_ui" / "views" / "workflow_proposals.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-333-WF-001" in src

    def test_impact_score_guarded(self):
        src = self._get_source()
        assert "p.impact_score || 'N/A'" in src

    def test_risk_level_guarded(self):
        src = self._get_source()
        assert "p.risk_level || 'N/A'" in src


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch330Imports:
    """Verify all fixed modules import without errors."""

    def test_import_tasks_crud(self):
        import governance.typedb.queries.tasks.crud
        assert hasattr(governance.typedb.queries.tasks.crud, '_update_attribute')

    def test_import_memory_tiers(self):
        import governance.mcp_tools.memory_tiers
        assert hasattr(governance.mcp_tools.memory_tiers, '_short_memory_lock')

    def test_import_traceability(self):
        import governance.mcp_tools.traceability
        assert hasattr(governance.mcp_tools.traceability, 'register_traceability_tools')

    def test_import_panels(self):
        import agent.governance_ui.views.trust.panels

    def test_import_workflow_proposals(self):
        import agent.governance_ui.views.workflow_proposals
