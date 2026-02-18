"""Batch 270-273 — TypeQL escape regression, division-by-zero, len(None),
CWD-relative path, unbounded dict, missing except handler tests.

Validates fixes for:
- BUG-272-CRUD-001: Backslash escape in linked_rules/linked_sessions (CRITICAL)
- BUG-270-TRACKER-001: Division by zero guard in tracker.py get_status()
- BUG-271-TASKSLINK-001: or [] guard on get_task_evidence/commits/documents
- BUG-270-EXEC-001: Evidence path anchored to __file__, not CWD
- BUG-271-MEMORY-001: _short_memory size cap (500 entries)
- BUG-273-TASKS-001: Broad except handler in list_tasks route
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-272-CRUD-001: TypeQL escape regression in tasks/crud.py ──────

class TestTasksCrudEscapeRegression:
    """linked_rules and linked_sessions must use two-step escape."""

    def test_linked_rules_has_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        idx = src.index("if linked_rules:")
        block = src[idx:idx + 600]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_linked_sessions_has_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        idx = src.index("if linked_sessions:")
        block = src[idx:idx + 600]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_no_quote_only_escape_in_linked_rules(self):
        """Must NOT have quote-only escape (the regression pattern)."""
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        idx = src.index("if linked_rules:")
        block = src[idx:idx + 600]
        # The old broken pattern: .replace('"', '\\"') without backslash first
        # After fix, the line should have BOTH replaces
        lines = block.split("\n")
        for line in lines:
            if "rid = rule_id.replace" in line:
                assert "replace('\\\\', '\\\\\\\\')" in line, \
                    f"rid escape must include backslash step: {line.strip()}"
                break

    def test_no_quote_only_escape_in_linked_sessions(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        idx = src.index("if linked_sessions:")
        block = src[idx:idx + 600]
        lines = block.split("\n")
        for line in lines:
            if "sid = session_id.replace" in line:
                assert "replace('\\\\', '\\\\\\\\')" in line, \
                    f"sid escape must include backslash step: {line.strip()}"
                break

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        assert "BUG-272-CRUD-001" in src


# ── BUG-270-TRACKER-001: Division by zero in tracker.py ──────────────

class TestTrackerDivisionByZero:
    """get_status() must guard against total_phases == 0."""

    def test_progress_percent_has_zero_guard(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        idx = src.index("def get_status")
        block = src[idx:idx + 1200]
        assert "total_phases else" in block

    def test_no_bare_division(self):
        """Must not have bare division without guard."""
        src = (SRC / "governance/dsm/tracker.py").read_text()
        idx = src.index("def get_status")
        block = src[idx:idx + 1200]
        lines = block.split("\n")
        for line in lines:
            if "progress_percent" in line and "/" in line:
                assert "if total_phases" in line or "total_phases else" in line, \
                    f"Division must be guarded: {line.strip()}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        assert "BUG-270-TRACKER-001" in src


# ── BUG-271-TASKSLINK-001: None guard in tasks_linking.py ────────────

class TestTasksLinkingNoneGuard:
    """get_task_evidence/commits/documents must guard against None returns."""

    def test_evidence_has_or_guard(self):
        src = (SRC / "governance/mcp_tools/tasks_linking.py").read_text()
        idx = src.index("def task_get_evidence")
        block = src[idx:idx + 600]
        assert "or []" in block

    def test_commits_has_or_guard(self):
        src = (SRC / "governance/mcp_tools/tasks_linking.py").read_text()
        idx = src.index("def task_get_commits")
        block = src[idx:idx + 600]
        assert "or []" in block

    def test_documents_has_or_guard(self):
        src = (SRC / "governance/mcp_tools/tasks_linking.py").read_text()
        idx = src.index("def task_get_documents")
        block = src[idx:idx + 600]
        assert "or []" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/tasks_linking.py").read_text()
        assert "BUG-271-TASKSLINK-001" in src


# ── BUG-270-EXEC-001: Evidence path anchored to __file__ ─────────────

class TestNodesExecutionEvidencePath:
    """report_node must anchor evidence path to project root, not CWD."""

    def test_no_bare_cwd_evidence(self):
        """Must NOT have _Path('./evidence') — CWD-relative is fragile."""
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        idx = src.index("def report_node")
        block = src[idx:idx + 1800]
        assert '_Path("./evidence")' not in block

    def test_anchored_to_file(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        idx = src.index("def report_node")
        block = src[idx:idx + 1800]
        assert "__file__" in block

    def test_project_root_pattern(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        idx = src.index("def report_node")
        block = src[idx:idx + 1800]
        assert "_PROJECT_ROOT" in block or "project_root" in block.lower()

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert "BUG-270-EXEC-001" in src


# ── BUG-271-MEMORY-001: _short_memory size cap ──────────────────────

class TestMemoryTiersSizeCap:
    """_short_memory dict must have a size cap to prevent unbounded growth."""

    def test_max_constant_defined(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        assert "_SHORT_MEMORY_MAX" in src

    def test_eviction_in_save(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        idx = src.index("def memory_save")
        block = src[idx:idx + 1500]
        assert "_SHORT_MEMORY_MAX" in block

    def test_cap_value_reasonable(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        assert "_SHORT_MEMORY_MAX = 500" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        assert "BUG-271-MEMORY-001" in src


# ── BUG-273-TASKS-001: Broad except in list_tasks route ──────────────

class TestListTasksBroadExcept:
    """list_tasks must have a broad except handler like other endpoints."""

    def test_broad_except_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        idx = src.index("async def list_tasks")
        block = src[idx:idx + 2000]
        assert "except Exception as e:" in block

    def test_returns_500_on_unexpected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        idx = src.index("async def list_tasks")
        block = src[idx:idx + 2000]
        assert "status_code=500" in block

    def test_logs_error(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        idx = src.index("async def list_tasks")
        block = src[idx:idx + 2000]
        assert "logger.error" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "BUG-273-TASKS-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch270Imports:
    def test_tasks_crud_importable(self):
        import governance.typedb.queries.tasks.crud
        assert governance.typedb.queries.tasks.crud is not None

    def test_tracker_importable(self):
        import governance.dsm.tracker
        assert governance.dsm.tracker is not None

    def test_tasks_linking_importable(self):
        import governance.mcp_tools.tasks_linking
        assert governance.mcp_tools.tasks_linking is not None

    def test_nodes_execution_importable(self):
        import governance.dsm.langgraph.nodes_execution
        assert governance.dsm.langgraph.nodes_execution is not None

    def test_memory_tiers_importable(self):
        import governance.mcp_tools.memory_tiers
        assert governance.mcp_tools.memory_tiers is not None

    def test_routes_tasks_crud_importable(self):
        import governance.routes.tasks.crud
        assert governance.routes.tasks.crud is not None
