"""
TDD tests for EPIC-TASK-QUALITY-V3 Phase 11B: Agent ID Governance Gaps.

Per TEST-FIX-01-v1: Failing tests written FIRST, then implementation.

Bugs:
- SRVJ-BUG-021: MCP task_update missing agent_id parameter
- SRVJ-BUG-022: create_task(status=IN_PROGRESS) skips H-TASK-002 auto-assign
- SRVJ-BUG-023: No agent_id validation against registered agents
"""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# SRVJ-BUG-021: MCP task_update must expose agent_id parameter
# ============================================================================

class TestBug021MCPTaskUpdateAgentId:
    """SRVJ-BUG-021: MCP task_update must accept agent_id."""

    def test_mcp_task_update_has_agent_id_param(self):
        """MCP task_update function signature must include agent_id."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        import inspect
        sig = inspect.signature(captured["task_update"])
        assert "agent_id" in sig.parameters, \
            "MCP task_update must expose agent_id parameter"

    def test_mcp_task_update_passes_agent_id_to_service(self):
        """MCP task_update must pass agent_id through to svc_update_task."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        with patch("governance.mcp_tools.tasks_crud.svc_update_task") as mock_svc:
            mock_svc.return_value = {"task_id": "T-1", "status": "IN_PROGRESS"}
            captured["task_update"](task_id="T-1", agent_id="code-agent",
                                    status="IN_PROGRESS")
            mock_svc.assert_called_once()
            _, kwargs = mock_svc.call_args
            assert kwargs.get("agent_id") == "code-agent", \
                "agent_id must be passed to svc_update_task"

    def test_mcp_task_update_allows_done_with_agent_id(self):
        """MCP task_update(status=DONE, agent_id=code-agent) should not reject for missing agent."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        with patch("governance.mcp_tools.tasks_crud.svc_update_task") as mock_svc:
            mock_svc.return_value = {"task_id": "T-1", "status": "DONE"}
            result = captured["task_update"](
                task_id="T-1", status="DONE", agent_id="code-agent",
            )
            # Should succeed, not raise ValueError about agent_id
            assert "error" not in result.lower() or "agent_id" not in result.lower()


# ============================================================================
# SRVJ-BUG-022: create_task(status=IN_PROGRESS) must auto-assign agent_id
# ============================================================================

class TestBug022CreateTaskAutoAgent:
    """SRVJ-BUG-022: create_task with IN_PROGRESS must trigger H-TASK-002."""

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_in_progress_auto_assigns_agent(self, mock_client_fn):
        """create_task(status=IN_PROGRESS) must set agent_id=code-agent."""
        from governance.services.tasks import create_task

        client = MagicMock()
        client.get_task.return_value = None
        created_task = MagicMock()
        created_task.created_at = datetime(2026, 3, 23)
        client.insert_task.return_value = created_task
        mock_client_fn.return_value = client

        with patch("governance.services.tasks.task_to_response") as mock_resp:
            mock_resp.return_value = MagicMock(
                created_at="2026-03-23T00:00:00",
            )
            create_task("T-AUTO", description="Test", status="IN_PROGRESS")

        # insert_task must be called with agent_id="code-agent"
        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["agent_id"] == "code-agent", \
            "H-TASK-002: create_task(status=IN_PROGRESS) must auto-assign code-agent"

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_in_progress_preserves_explicit_agent(self, mock_client_fn):
        """create_task(status=IN_PROGRESS, agent_id=X) must keep explicit value."""
        from governance.services.tasks import create_task

        client = MagicMock()
        client.get_task.return_value = None
        created_task = MagicMock()
        created_task.created_at = datetime(2026, 3, 23)
        client.insert_task.return_value = created_task
        mock_client_fn.return_value = client

        with patch("governance.services.tasks.task_to_response") as mock_resp:
            mock_resp.return_value = MagicMock(
                created_at="2026-03-23T00:00:00",
            )
            create_task("T-EXPL", description="Test",
                        status="IN_PROGRESS", agent_id="task-orchestrator")

        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["agent_id"] == "task-orchestrator", \
            "Explicit agent_id must NOT be overridden by H-TASK-002"

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_open_does_not_auto_assign(self, mock_client_fn):
        """create_task(status=OPEN) must NOT auto-assign agent_id."""
        from governance.services.tasks import create_task

        client = MagicMock()
        client.get_task.return_value = None
        created_task = MagicMock()
        created_task.created_at = datetime(2026, 3, 23)
        client.insert_task.return_value = created_task
        mock_client_fn.return_value = client

        with patch("governance.services.tasks.task_to_response") as mock_resp:
            mock_resp.return_value = MagicMock(
                created_at="2026-03-23T00:00:00",
            )
            create_task("T-OPEN", description="Test", status="OPEN")

        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["agent_id"] is None, \
            "OPEN tasks must NOT get auto-assigned agent_id"


# ============================================================================
# SRVJ-BUG-023: agent_id must be validated against registered agents
# ============================================================================

class TestBug023AgentIdValidation:
    """SRVJ-BUG-023: agent_id must be from _AGENT_BASE_CONFIG."""

    def test_valid_agents_exported(self):
        """VALID_AGENT_IDS must be importable from agents store."""
        from governance.stores.agents import VALID_AGENT_IDS
        assert isinstance(VALID_AGENT_IDS, (set, frozenset))
        assert "code-agent" in VALID_AGENT_IDS
        assert "task-orchestrator" in VALID_AGENT_IDS
        assert "rules-curator" in VALID_AGENT_IDS
        assert "research-agent" in VALID_AGENT_IDS
        assert "local-assistant" in VALID_AGENT_IDS
        assert len(VALID_AGENT_IDS) == 5

    def test_default_agent_id_exported(self):
        """DEFAULT_AGENT_ID must be importable and be a valid agent."""
        from governance.stores.agents import DEFAULT_AGENT_ID, VALID_AGENT_IDS
        assert DEFAULT_AGENT_ID == "code-agent"
        assert DEFAULT_AGENT_ID in VALID_AGENT_IDS

    def test_valid_agent_ids_derived_from_config(self):
        """VALID_AGENT_IDS must be derived from _AGENT_BASE_CONFIG (DRY)."""
        from governance.stores.agents import VALID_AGENT_IDS, _AGENT_BASE_CONFIG
        assert VALID_AGENT_IDS == frozenset(_AGENT_BASE_CONFIG.keys())

    def test_validate_agent_id_accepts_valid(self):
        """validate_agent_id must accept all 5 valid agents."""
        from governance.services.task_rules import validate_agent_id
        for agent in ["code-agent", "task-orchestrator", "rules-curator",
                       "research-agent", "local-assistant"]:
            errors = validate_agent_id(agent)
            assert len(errors) == 0, f"Valid agent '{agent}' should not produce errors"

    def test_validate_agent_id_rejects_invalid(self):
        """validate_agent_id must reject unregistered agent IDs."""
        from governance.services.task_rules import validate_agent_id
        for invalid in ["banana", "test-agent", "rogue-agent", "explicit-agent"]:
            errors = validate_agent_id(invalid)
            assert len(errors) == 1, f"Invalid agent '{invalid}' must produce 1 error"
            assert errors[0].rule == "InvalidAgent"

    def test_validate_agent_id_accepts_none(self):
        """validate_agent_id(None) must return no errors (optional field)."""
        from governance.services.task_rules import validate_agent_id
        errors = validate_agent_id(None)
        assert len(errors) == 0

    def test_task_rules_validate_on_complete_checks_agent(self):
        """DONE gate must reject invalid agent_id values."""
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_id="T-1", summary="Test", agent_id="banana",
            completed_at="2026-03-23T00:00:00",
            linked_sessions=["S-1"], linked_documents=["doc.md"],
        )
        agent_errors = [e for e in errors if e.field == "agent_id"]
        assert len(agent_errors) >= 1, \
            "DONE gate must reject invalid agent_id 'banana'"

    @patch("governance.services.tasks_mutations._tasks_store", {})
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_rejects_invalid_agent(self, mock_client_fn):
        """update_task(agent_id='banana') must raise ValueError."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        client = MagicMock()
        task_obj = MagicMock()
        task_obj.name = "Test"
        task_obj.phase = "P11"
        task_obj.status = "OPEN"
        task_obj.agent_id = None
        task_obj.created_at = datetime(2026, 1, 1)
        client.get_task.return_value = task_obj
        mock_client_fn.return_value = client

        _tasks_store["T-BAD"] = {"task_id": "T-BAD", "status": "OPEN"}

        with pytest.raises(ValueError, match="[Ii]nvalid agent"):
            update_task("T-BAD", agent_id="banana", status="IN_PROGRESS")

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_rejects_invalid_agent(self, mock_client_fn):
        """create_task(agent_id='rogue') must raise ValueError."""
        from governance.services.tasks import create_task

        mock_client_fn.return_value = None

        with pytest.raises(ValueError, match="[Ii]nvalid agent"):
            create_task("T-ROGUE", description="Test",
                        agent_id="rogue-agent")
