"""
Batch 71 — Deep Scan: MCP ingestion format fix + orchestrator null guards.

Fixes verified:
- BUG-MCP-INGESTION-FORMAT-001: format_mcp_result called with 2 args, discarding data
- BUG-ORCH-NULL-TASK-001: spec_node/implement_node/validate_node crash on None task
- BUG-SPEC-TIER-NULL-001: export_to_robot crashes on None tier_1/tier_2
"""
import inspect
from unittest.mock import patch, MagicMock

import pytest


# ===========================================================================
# BUG-MCP-INGESTION-FORMAT-001: format_mcp_result called with wrong signature
# ===========================================================================

class TestIngestionFormatFix:
    """Verify ingestion MCP tools call format_mcp_result with single data arg."""

    def test_no_two_arg_calls(self):
        """ingestion.py must NOT call format_mcp_result with 2 positional args."""
        import governance.mcp_tools.ingestion as mod
        src = inspect.getsource(mod)
        # Old pattern: format_mcp_result("ok", result) — 2 args
        import re
        two_arg_calls = re.findall(r'format_mcp_result\(\s*"(?:ok|error)"', src)
        assert len(two_arg_calls) == 0, (
            f"Found {len(two_arg_calls)} two-arg format_mcp_result calls"
        )

    def test_result_dict_passed_as_data(self):
        """All format_mcp_result calls must pass dict/object as first arg."""
        import governance.mcp_tools.ingestion as mod
        src = inspect.getsource(mod)
        # Should have format_mcp_result(result) or format_mcp_result({...})
        import re
        calls = re.findall(r'format_mcp_result\(([^)]+)\)', src)
        for call in calls:
            # Should not start with a string literal
            stripped = call.strip()
            assert not stripped.startswith('"'), f"format_mcp_result called with string: {stripped}"

    def test_ingest_session_content_returns_result(self):
        """ingest_session_content must return actual result, not 'ok' string."""
        import governance.mcp_tools.ingestion as mod
        src = inspect.getsource(mod.register_ingestion_tools)
        # The return line must be format_mcp_result(result), not format_mcp_result("ok", result)
        assert 'format_mcp_result(result)' in src

    def test_error_calls_pass_dict(self):
        """Error returns must pass error dict, not ("error", dict) two-arg form."""
        import governance.mcp_tools.ingestion as mod
        src = inspect.getsource(mod)
        # Error calls should be format_mcp_result({"error": ...})
        import re
        # Match: format_mcp_result(\n{whitespace}{"error":
        error_calls = re.findall(r'format_mcp_result\(\s*\n\s*\{"error":', src)
        assert len(error_calls) >= 3, f"Expected 3+ error dict calls, found {len(error_calls)}"

    def test_list_checkpoints_returns_dict(self):
        """_list_all_checkpoints must return actual data dict."""
        import governance.mcp_tools.ingestion as mod
        src = inspect.getsource(mod._list_all_checkpoints)
        assert 'format_mcp_result({"checkpoints":' in src


# ===========================================================================
# BUG-ORCH-NULL-TASK-001: Orchestrator nodes null task guard
# ===========================================================================

class TestOrchestratorNullTaskGuard:
    """Verify orchestrator nodes handle None current_task gracefully."""

    def test_spec_node_guards_null_task(self):
        """spec_node must check for None current_task."""
        from governance.workflows.orchestrator.nodes import spec_node
        src = inspect.getsource(spec_node)
        assert "state.get(\"current_task\")" in src or 'state.get("current_task")' in src

    def test_implement_node_guards_null_task(self):
        """implement_node must check for None current_task."""
        from governance.workflows.orchestrator.nodes import implement_node
        src = inspect.getsource(implement_node)
        assert "state.get(\"current_task\")" in src or 'state.get("current_task")' in src

    def test_validate_node_guards_null_task(self):
        """validate_node must check for None current_task."""
        from governance.workflows.orchestrator.nodes import validate_node
        src = inspect.getsource(validate_node)
        assert "state.get(\"current_task\")" in src or 'state.get("current_task")' in src

    def test_spec_node_returns_error_on_null(self):
        """spec_node with None current_task returns error dict, not crash."""
        from governance.workflows.orchestrator.nodes import spec_node
        result = spec_node({"current_task": None})
        assert "error" in result.get("current_phase", "") or "error_message" in result

    def test_implement_node_returns_error_on_null(self):
        """implement_node with None current_task returns error dict."""
        from governance.workflows.orchestrator.nodes import implement_node
        result = implement_node({"current_task": None})
        assert "error" in result.get("current_phase", "") or "error_message" in result

    def test_validate_node_returns_error_on_null(self):
        """validate_node with None current_task returns error dict."""
        from governance.workflows.orchestrator.nodes import validate_node
        result = validate_node({"current_task": None})
        assert "error" in result.get("current_phase", "") or "error_message" in result

    def test_spec_node_works_with_valid_task(self):
        """spec_node still works with a valid current_task."""
        from governance.workflows.orchestrator.nodes import spec_node
        state = {"current_task": {"task_id": "TASK-1", "description": "Test task"}}
        result = spec_node(state)
        assert result["current_phase"] == "specified"
        assert result["specification"]["task_id"] == "TASK-1"

    def test_implement_node_works_with_valid_task(self):
        """implement_node still works with a valid current_task."""
        from governance.workflows.orchestrator.nodes import implement_node
        state = {
            "current_task": {"task_id": "TASK-1", "description": "Test task"},
            "specification": {"files_to_modify": ["test.py"]},
        }
        result = implement_node(state)
        assert result["current_phase"] == "implemented"


# ===========================================================================
# BUG-SPEC-TIER-NULL-001: export_to_robot None tier guard
# ===========================================================================

class TestSpecTierNullGuard:
    """Verify export_to_robot handles None tier_1/tier_2 gracefully."""

    def test_export_uses_get_for_tier_1(self):
        """export_to_robot must use .get() for tier_1 access."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        src = inspect.getsource(export_to_robot)
        assert "spec.get('tier_1')" in src or 'spec.get("tier_1")' in src

    def test_export_uses_get_for_tier_2(self):
        """export_to_robot must use .get() for tier_2 access."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        src = inspect.getsource(export_to_robot)
        assert "spec.get('tier_2')" in src or 'spec.get("tier_2")' in src

    def test_export_handles_none_tiers(self):
        """export_to_robot must not crash when tier_1/tier_2 are None."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {
            "task_id": "TASK-1",
            "tier_1": None,
            "tier_2": None,
        }
        # Should NOT raise AttributeError
        result = export_to_robot(spec)
        assert "TASK-1" in result

    def test_export_handles_empty_tiers(self):
        """export_to_robot must handle empty string tiers."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {
            "task_id": "TASK-2",
            "tier_1": "",
            "tier_2": "",
        }
        result = export_to_robot(spec)
        assert "TASK-2" in result
