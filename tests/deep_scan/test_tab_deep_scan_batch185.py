"""Deep scan batch 185: Workflow + MCP tools layer.

Batch 185 findings: 16 total, 3 confirmed fixes, 13 rejected/deferred.
- BUG-B185-005: rules_crud rule_delete missing except block.
- BUG-B185-006: decisions governance_get_decision_impacts missing except.
- BUG-B185-007: tasks_linking 8 functions missing except blocks.
"""
import pytest
from pathlib import Path


# ── MCP exception handling consistency ──────────────


class TestMCPExceptionConsistency:
    """Verify all MCP tools have try/except/finally pattern."""

    def _count_patterns(self, src: str):
        """Count try/finally and try/except/finally patterns."""
        try_count = src.count("        try:")
        finally_count = src.count("        finally:")
        except_count = src.count("        except Exception")
        return try_count, except_count, finally_count

    def test_tasks_linking_all_have_except(self):
        """tasks_linking.py: every try/finally has an except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        try_c, except_c, finally_c = self._count_patterns(src)
        # Every function with try/finally should also have except
        assert except_c >= finally_c, (
            f"tasks_linking.py: {except_c} except vs {finally_c} finally"
        )

    def test_rules_crud_all_have_except(self):
        """rules_crud.py: every try/finally has an except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/rules_crud.py").read_text()
        try_c, except_c, finally_c = self._count_patterns(src)
        assert except_c >= finally_c, (
            f"rules_crud.py: {except_c} except vs {finally_c} finally"
        )

    def test_decisions_has_except(self):
        """decisions.py: governance_get_decision_impacts has except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/decisions.py").read_text()
        # Find the specific function
        start = src.index("def governance_get_decision_impacts")
        end = src.index("\n    @mcp.tool()", start + 1) if "\n    @mcp.tool()" in src[start + 1:] else len(src)
        func = src[start:end]
        assert "except Exception" in func

    def test_rule_delete_has_except(self):
        """rule_delete has except block matching rule_create."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/rules_crud.py").read_text()
        start = src.index("def rule_delete")
        # End is EOF or next tool
        rest = src[start:]
        func = rest  # Last function in file
        assert "except Exception" in func

    def test_task_link_session_has_except(self):
        """task_link_session has except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        start = src.index("def task_link_session")
        end = src.index("\n    @mcp.tool()", start + 1)
        func = src[start:end]
        assert "except Exception" in func

    def test_task_get_evidence_has_except(self):
        """task_get_evidence has except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        start = src.index("def task_get_evidence")
        end = src.index("\n    @mcp.tool()", start + 1)
        func = src[start:end]
        assert "except Exception" in func

    def test_task_get_commits_has_except(self):
        """task_get_commits has except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        start = src.index("def task_get_commits")
        end = src.index("\n    @mcp.tool()", start + 1)
        func = src[start:end]
        assert "except Exception" in func

    def test_task_update_details_has_except(self):
        """task_update_details has except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        start = src.index("def task_update_details")
        end = src.index("\n    @mcp.tool()", start + 1)
        func = src[start:end]
        assert "except Exception" in func

    def test_task_get_details_has_except(self):
        """task_get_details has except block (last function)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_linking.py").read_text()
        start = src.index("def task_get_details")
        func = src[start:]
        assert "except Exception" in func


# ── MCP tools common pattern defense ──────────────


class TestMCPToolsCommonPattern:
    """Verify MCP tools use format_mcp_result for errors."""

    def test_format_mcp_result_importable(self):
        """format_mcp_result is importable from common."""
        from governance.mcp_tools.common import format_mcp_result
        assert callable(format_mcp_result)

    def test_format_mcp_result_returns_string(self):
        """format_mcp_result returns a string (JSON or TOON)."""
        from governance.mcp_tools.common import format_mcp_result
        result = format_mcp_result({"test": True})
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain the key somewhere in the output
        assert "test" in result

    def test_get_typedb_client_importable(self):
        """get_typedb_client is importable from common."""
        from governance.mcp_tools.common import get_typedb_client
        assert callable(get_typedb_client)


# ── Workflow orchestrator defense ──────────────


class TestWorkflowOrchestratorDefense:
    """Verify workflow orchestrator structure."""

    def test_budget_module_importable(self):
        """Budget module is importable."""
        from governance.workflows.orchestrator import budget
        assert budget is not None

    def test_compute_budget_exists(self):
        """compute_budget function exists."""
        from governance.workflows.orchestrator.budget import compute_budget
        assert callable(compute_budget)

    def test_spec_tiers_importable(self):
        """spec_tiers module is importable."""
        from governance.workflows.orchestrator import spec_tiers
        assert spec_tiers is not None
