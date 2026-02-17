"""
Deep Scan Batch 322-325 Defense Tests.

Validates 6 production fixes:
- BUG-322-ORCH-001: Path containment via relative_to() instead of startswith()
- BUG-323-TASK-001: list_tasks offset/limit clamping
- BUG-323-PRJ-001: list_projects offset/limit clamping + N+1 cap
- BUG-324-ING-001: ingestion_estimate path validation
- BUG-324-DEC-001: DSM state read_text encoding
- BUG-325-OBS-001: release_lock resource validation
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-322-ORCH-001: Path containment via relative_to()
# ============================================================

class TestPathContainmentRelativeTo:
    """Verify ingestion_orchestrator uses relative_to() not startswith()."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "ingestion_orchestrator.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-322-ORCH-001" in src

    def test_relative_to_used(self):
        src = self._get_source()
        assert "relative_to(" in src, "Should use relative_to() for path containment"

    def test_startswith_not_in_code(self):
        """startswith() should NOT be used in code (only in comments is OK)."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_validate_jsonl_path":
                # Check AST for .startswith() calls — not in comments
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute) and child.attr == "startswith":
                        raise AssertionError(
                            "_validate_jsonl_path should use relative_to() not startswith()"
                        )
                break

    def test_relative_to_logic_correct(self):
        """Verify the function returns True for valid paths and False for invalid."""
        from governance.services.ingestion_orchestrator import _validate_jsonl_path
        # Valid path under project root
        valid_path = ROOT / "governance" / "test_file.jsonl"
        # The function resolves paths, so this tests the relative_to logic
        # We can't guarantee the file exists, but the path containment check
        # should pass for paths under the project root
        result = _validate_jsonl_path(valid_path)
        assert result is True, "Path under project root should be valid"

    def test_relative_to_rejects_outside_path(self):
        """Paths outside allowed bases should be rejected."""
        from governance.services.ingestion_orchestrator import _validate_jsonl_path
        evil_path = Path("/tmp/evil/payload.jsonl")
        result = _validate_jsonl_path(evil_path)
        assert result is False, "Path outside allowed bases should be rejected"


# ============================================================
# BUG-323-TASK-001: list_tasks offset/limit bounds
# ============================================================

class TestTasksListBounds:
    """Verify tasks.py list_tasks clamps offset and limit."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "tasks.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-323-TASK-001" in src

    def test_offset_clamped(self):
        src = self._get_source()
        assert "max(0, offset)" in src, "offset should be clamped to non-negative"

    def test_limit_upper_bound(self):
        src = self._get_source()
        assert "min(limit, 500)" in src, "limit should have upper bound of 500"

    def test_limit_lower_bound(self):
        src = self._get_source()
        assert "max(1," in src, "limit should have lower bound of 1"


# ============================================================
# BUG-323-PRJ-001/002: list_projects bounds + N+1 cap
# ============================================================

class TestProjectsListBounds:
    """Verify projects.py list_projects clamps params and caps N+1 loop."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "projects.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_prj_001(self):
        src = self._get_source()
        assert "BUG-323-PRJ-001" in src

    def test_bug_marker_prj_002(self):
        src = self._get_source()
        assert "BUG-323-PRJ-002" in src

    def test_offset_clamped(self):
        src = self._get_source()
        assert "max(0, offset)" in src

    def test_limit_upper_bound(self):
        src = self._get_source()
        assert "min(limit, 200)" in src, "project limit should cap at 200"

    def test_n_plus_1_enrichment_capped(self):
        """N+1 enrichment loop should be capped via slice."""
        src = self._get_source()
        assert "projects[:50]" in src, "N+1 enrichment loop should be capped at 50"


# ============================================================
# BUG-324-ING-001: ingestion_estimate path validation
# ============================================================

class TestIngestionEstimatePathValidation:
    """Verify ingestion_estimate routes through _resolve_jsonl_path."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "ingestion.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-324-ING-001" in src

    def test_resolve_jsonl_path_called(self):
        """ingestion_estimate should validate path via _resolve_jsonl_path."""
        src = self._get_source()
        # Find the ingestion_estimate function body
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "ingestion_estimate":
                func_src = ast.get_source_segment(src, node)
                assert "_resolve_jsonl_path" in func_src, \
                    "ingestion_estimate should call _resolve_jsonl_path for validation"
                break
        else:
            # Function might be nested inside register_ingestion_tools
            assert "_resolve_jsonl_path" in src, \
                "ingestion.py should reference _resolve_jsonl_path"

    def test_error_on_invalid_path(self):
        """Should return error result for invalid paths."""
        src = self._get_source()
        # Verify error handling exists after _resolve_jsonl_path returns None
        assert '"Invalid or inaccessible path"' in src or \
               "'Invalid or inaccessible path'" in src


# ============================================================
# BUG-324-DEC-001: DSM state read_text encoding
# ============================================================

class TestDecisionsDsmEncoding:
    """Verify decisions.py specifies encoding for dsm_state.read_text."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "decisions.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-324-DEC-001" in src

    def test_encoding_specified(self):
        """dsm_state.read_text() should specify encoding='utf-8'."""
        src = self._get_source()
        # Find the line with dsm_state.read_text
        lines = src.split("\n")
        for line in lines:
            if "dsm_state.read_text" in line:
                assert 'encoding="utf-8"' in line or "encoding='utf-8'" in line, \
                    f"dsm_state.read_text() missing encoding: {line.strip()}"
                break
        else:
            raise AssertionError("dsm_state.read_text() not found in decisions.py")


# ============================================================
# BUG-325-OBS-001: release_lock resource validation
# ============================================================

class TestReleaseLockResourceValidation:
    """Verify observability.py validates resource name in release_lock."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "agents" / "observability.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-325-OBS-001" in src

    def test_regex_validation_in_release_lock(self):
        """release_lock should validate resource with regex."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "release_lock":
                func_src = ast.get_source_segment(src, node)
                assert "re.match" in func_src or "_re.match" in func_src, \
                    "release_lock should validate resource name with regex"
                assert "422" in func_src, \
                    "release_lock should return 422 for invalid resource"
                break
        else:
            raise AssertionError("release_lock function not found")

    def test_acquire_and_release_have_same_validation(self):
        """Both acquire_lock and release_lock should validate resource names."""
        src = self._get_source()
        # Count regex validation patterns in the file
        pattern_count = src.count("Invalid resource name")
        assert pattern_count >= 2, \
            f"Both acquire_lock and release_lock should validate resource names, found {pattern_count} validation(s)"


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch322Imports:
    """Verify all fixed modules import without errors."""

    def test_import_ingestion_orchestrator(self):
        import governance.services.ingestion_orchestrator
        assert hasattr(governance.services.ingestion_orchestrator, '_validate_jsonl_path')

    def test_import_tasks(self):
        import governance.services.tasks
        assert hasattr(governance.services.tasks, 'list_tasks')

    def test_import_projects(self):
        import governance.services.projects
        assert hasattr(governance.services.projects, 'list_projects')

    def test_import_decisions(self):
        import governance.mcp_tools.decisions
        assert hasattr(governance.mcp_tools.decisions, 'register_decision_tools')

    def test_import_observability(self):
        import governance.routes.agents.observability
