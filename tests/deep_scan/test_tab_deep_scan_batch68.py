"""
Batch 68 — Deep Scan: Orchestrator retry logic + TypeQL completeness audit.

Fixes verified:
- BUG-ORCH-RETRY-001: Retry loop now re-specs same task instead of popping new from backlog
- Full TypeDB query escaping completeness audit across all layers
"""
import inspect
import re
from unittest.mock import patch, MagicMock

import pytest


# ===========================================================================
# BUG-ORCH-RETRY-001: Orchestrator retry skips gate/backlog
# ===========================================================================

class TestOrchestratorRetry:
    """Verify retry logic re-specs same task without re-entering gate/backlog."""

    def test_retry_flag_exists_in_fallback(self):
        """_run_fallback_workflow must have _retrying flag for loop control."""
        from governance.workflows.orchestrator.graph import _run_fallback_workflow
        src = inspect.getsource(_run_fallback_workflow)
        assert "_retrying" in src

    def test_retry_skips_gate_on_loop(self):
        """When _retrying is True, gate_node and backlog_node should be skipped."""
        from governance.workflows.orchestrator.graph import _run_fallback_workflow
        src = inspect.getsource(_run_fallback_workflow)
        # Gate/backlog should be guarded by 'if not _retrying'
        assert "if not _retrying" in src

    def test_retry_resets_after_spec(self):
        """_retrying flag must be reset after entering spec path."""
        from governance.workflows.orchestrator.graph import _run_fallback_workflow
        src = inspect.getsource(_run_fallback_workflow)
        # _retrying = False before spec_node
        reset_idx = src.find("_retrying = False")
        spec_idx = src.find("spec_node(state)")
        # Must reset BEFORE spec_node is called
        assert reset_idx < spec_idx, "Must reset _retrying before spec_node"

    def test_retry_sets_flag_true(self):
        """loop_to_spec branch must set _retrying = True."""
        from governance.workflows.orchestrator.graph import _run_fallback_workflow
        src = inspect.getsource(_run_fallback_workflow)
        assert "_retrying = True" in src

    @patch("governance.workflows.orchestrator.graph.gate_node")
    @patch("governance.workflows.orchestrator.graph.check_gate_decision")
    @patch("governance.workflows.orchestrator.graph.backlog_node")
    @patch("governance.workflows.orchestrator.graph.spec_node")
    @patch("governance.workflows.orchestrator.graph.implement_node")
    @patch("governance.workflows.orchestrator.graph.validate_node")
    @patch("governance.workflows.orchestrator.graph.check_validation_result")
    @patch("governance.workflows.orchestrator.graph.complete_cycle_node")
    @patch("governance.workflows.orchestrator.graph.certify_node")
    @patch("governance.workflows.orchestrator.graph.complete_node")
    def test_retry_does_not_pop_new_task(
        self, mock_complete, mock_certify, mock_cc, mock_cvr,
        mock_validate, mock_impl, mock_spec, mock_backlog,
        mock_gate_dec, mock_gate
    ):
        """On retry, backlog_node should NOT be called again."""
        from governance.workflows.orchestrator.graph import _run_fallback_workflow

        # Set up mocks: first cycle fails validation, second succeeds
        mock_gate.return_value = {"gate_decision": "backlog"}
        mock_gate_dec.side_effect = ["backlog", "complete"]
        mock_backlog.return_value = {"current_task": "TASK-1"}
        mock_spec.return_value = {}
        mock_impl.return_value = {}
        mock_validate.return_value = {}
        mock_cvr.side_effect = ["loop_to_spec", "complete_cycle"]
        mock_cc.return_value = {}
        mock_certify.return_value = {}
        mock_complete.return_value = {}

        state = {"backlog": ["TASK-1"], "max_cycles": 5}
        _run_fallback_workflow(state)

        # backlog_node should be called only ONCE (not on retry)
        assert mock_backlog.call_count == 1, (
            f"backlog_node called {mock_backlog.call_count} times, expected 1"
        )
        # spec_node should be called TWICE (initial + retry)
        assert mock_spec.call_count == 2, (
            f"spec_node called {mock_spec.call_count} times, expected 2"
        )


# ===========================================================================
# Full TypeDB escaping completeness audit — ALL layers
# ===========================================================================

class TestFullTypeDBEscapingCompleteness:
    """Final comprehensive audit of TypeQL escaping across entire TypeDB layer."""

    def test_all_crud_files_escape(self):
        """Every CRUD file must have .replace() calls for escaping."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations

        for cls, name in [
            (TaskCRUDOperations, "tasks/crud"),
            (SessionCRUDOperations, "sessions/crud"),
            (RuleCRUDOperations, "rules/crud"),
            (ProjectCRUDOperations, "projects/crud"),
        ]:
            src = inspect.getsource(cls)
            assert '.replace(' in src, f"{name} missing escaping"

    def test_all_linking_files_escape(self):
        """Every linking file must have .replace() calls."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations

        for cls, name in [
            (SessionLinkingOperations, "sessions/linking"),
            (ProjectLinkingOperations, "projects/linking"),
        ]:
            src = inspect.getsource(cls)
            escape_count = src.count('.replace(')
            assert escape_count >= 8, f"{name} has only {escape_count} escapes"

    def test_all_read_files_escape(self):
        """Every read query file must escape user-provided IDs."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        from governance.typedb.queries.tasks.read import TaskReadQueries
        from governance.typedb.queries.rules.read import RuleReadQueries

        for cls, name in [
            (SessionReadQueries, "sessions/read"),
            (TaskReadQueries, "tasks/read"),
            (RuleReadQueries, "rules/read"),
        ]:
            src = inspect.getsource(cls)
            assert '.replace(' in src, f"{name} missing escaping"

    def test_status_and_mutation_files_escape(self):
        """Status update and mutation files must escape."""
        from governance.typedb.queries.tasks.status import update_task_status
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations

        for item, name in [
            (update_task_status, "tasks/status"),
            (SessionMutationOperations, "sessions/mutations"),
        ]:
            src = inspect.getsource(item)
            assert '.replace(' in src, f"{name} missing escaping"

    def test_agents_file_escapes(self):
        """Agent queries must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 6, f"agents.py has only {escape_count} escapes"

    def test_decisions_file_escapes(self):
        """Decision queries must escape decision_id and rule_id."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 10, f"decisions.py has only {escape_count} escapes"

    def test_no_unescaped_session_id_in_any_write_query(self):
        """Cross-file: no raw session_id in any session write query file."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations

        for cls, name in [
            (SessionCRUDOperations, "crud"),
            (SessionMutationOperations, "mutations"),
            (SessionLinkingOperations, "linking"),
        ]:
            src = inspect.getsource(cls)
            raw = re.findall(r'session-id "\{session_id\}"', src)
            assert len(raw) == 0, f"{name} has {len(raw)} unescaped session_id"

    def test_no_unescaped_task_id_in_any_write_query(self):
        """Cross-file: no raw task_id in any task write query file."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        from governance.typedb.queries.tasks.status import update_task_status

        for item, name in [
            (TaskCRUDOperations, "crud"),
            (update_task_status, "status"),
        ]:
            src = inspect.getsource(item)
            raw = re.findall(r'task-id "\{task_id\}"', src)
            assert len(raw) == 0, f"{name} has {len(raw)} unescaped task_id"

    def test_no_unescaped_rule_id_in_any_write_query(self):
        """Cross-file: no raw rule_id in any rule write query file."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        from governance.typedb.queries.rules.decisions import DecisionQueries

        for cls, name in [
            (RuleCRUDOperations, "crud"),
            (DecisionQueries, "decisions"),
        ]:
            src = inspect.getsource(cls)
            raw = re.findall(r'rule-id "\{rule_id\}"', src)
            assert len(raw) == 0, f"{name} has {len(raw)} unescaped rule_id"

    def test_no_unescaped_project_id_in_any_query(self):
        """Cross-file: no raw project_id in any project query file."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations

        for cls, name in [
            (ProjectCRUDOperations, "crud"),
            (ProjectLinkingOperations, "linking"),
        ]:
            src = inspect.getsource(cls)
            raw = re.findall(r'project-id "\{project_id\}"', src)
            assert len(raw) == 0, f"{name} has {len(raw)} unescaped project_id"
