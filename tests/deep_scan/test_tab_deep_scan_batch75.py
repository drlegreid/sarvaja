"""
Batch 75 — Deep Scan: TypeDB CRUD + Workflow layer triage.

Fixes verified:
- REVERT BUG-TIMESTAMP-FORMAT-001: Task timestamps are datetime (no quotes)
- BUG-TASK-DETAIL-MISSING-ESCAPE: task_id now escaped in details.py
- BUG-DECISION-DOUBLE-TRANSACTION: Atomic single transaction
- BUG-ORCH-PARK-001: Park task tracks tokens_used

Triage summary: 29 findings → 3 confirmed + 1 revert, 25 rejected.
"""
import inspect
from unittest.mock import patch, MagicMock

import pytest


# ===========================================================================
# REVERT BUG-TIMESTAMP-FORMAT-001: TypeDB datetime attributes = no quotes
# ===========================================================================

class TestTimestampSchemaConsistency:
    """Verify all TypeDB datetime inserts use unquoted format consistently."""

    def test_session_started_at_unquoted(self):
        """Session started-at must be unquoted (datetime type)."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        assert "has started-at {timestamp_str}" in src
        assert 'has started-at "{timestamp_str}"' not in src

    def test_session_completed_at_unquoted(self):
        """Session completed-at must be unquoted (datetime type)."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.end_session)
        assert "has completed-at {timestamp_str}" in src
        assert 'has completed-at "{timestamp_str}"' not in src

    def test_task_claimed_at_unquoted(self):
        """Task claimed-at must be unquoted (datetime type)."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "has task-claimed-at {timestamp_str}" in src
        assert 'has task-claimed-at "{timestamp_str}"' not in src

    def test_task_completed_at_unquoted(self):
        """Task completed-at must be unquoted (datetime type)."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "has task-completed-at {timestamp_str}" in src
        assert 'has task-completed-at "{timestamp_str}"' not in src

    def test_evidence_created_at_unquoted(self):
        """Evidence created-at must be unquoted (datetime type)."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        src = inspect.getsource(TaskLinkingOperations.link_evidence_to_task)
        assert "has evidence-created-at {timestamp_str}" in src
        assert 'has evidence-created-at "{timestamp_str}"' not in src

    def test_session_mutation_started_at_unquoted(self):
        """Session mutation started-at updates must be unquoted."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.update_session)
        assert "$s has started-at {ts}" in src
        assert '$s has started-at "{ts}"' not in src

    def test_session_mutation_completed_at_unquoted(self):
        """Session mutation completed-at updates must be unquoted."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.update_session)
        assert "$s has completed-at {ts}" in src or "$s has completed-at {timestamp_str}" in src


# ===========================================================================
# BUG-TASK-DETAIL-MISSING-ESCAPE: task_id escaped in details.py
# ===========================================================================

class TestTaskDetailEscaping:
    """Verify task_id is escaped in detail section operations."""

    def test_update_detail_escapes_task_id(self):
        """_update_task_detail must escape task_id."""
        from governance.typedb.queries.tasks.details import TaskDetailOperations
        src = inspect.getsource(TaskDetailOperations._update_task_detail)
        assert 'task_id_escaped = task_id.replace' in src

    def test_update_detail_uses_escaped_id_in_delete(self):
        """Delete query must use escaped task_id."""
        from governance.typedb.queries.tasks.details import TaskDetailOperations
        src = inspect.getsource(TaskDetailOperations._update_task_detail)
        assert 'task-id "{task_id_escaped}"' in src

    def test_update_detail_uses_escaped_id_in_insert(self):
        """Insert query must use escaped task_id."""
        from governance.typedb.queries.tasks.details import TaskDetailOperations
        src = inspect.getsource(TaskDetailOperations._update_task_detail)
        # Count occurrences of escaped ID in match clauses
        assert src.count('task-id "{task_id_escaped}"') >= 2


# ===========================================================================
# BUG-DECISION-DOUBLE-TRANSACTION: Atomic single transaction
# ===========================================================================

class TestDecisionAtomicUpdate:
    """Verify decision attribute updates use a single transaction."""

    def test_single_transaction_pattern(self):
        """_update_decision_attr must use one 'with' block, not two."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries._update_decision_attr)
        # Count 'with self._driver.transaction' — should be exactly 1
        count = src.count("with self._driver.transaction")
        assert count == 1, f"Expected 1 transaction block, found {count}"

    def test_delete_in_try_except(self):
        """Delete should be in try/except for missing attributes."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries._update_decision_attr)
        assert "except Exception:" in src
        assert "pass  # Attribute may not exist" in src

    def test_has_bug_comment(self):
        """Fix should reference the bug ID."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries._update_decision_attr)
        assert "BUG-DECISION-DOUBLE-TRANSACTION" in src


# ===========================================================================
# BUG-ORCH-PARK-001: Park task tracks tokens_used
# ===========================================================================

class TestParkTaskBudgetTracking:
    """Verify park_task_node tracks token usage for budget consistency."""

    def test_park_tracks_tokens_used(self):
        """park_task_node must update tokens_used when budget is active."""
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-001", "priority": "LOW"},
            "cycles_completed": 2,
            "cycle_history": [],
            "tokens_used": 20,
        }
        result = park_task_node(state)
        assert "tokens_used" in result
        assert result["tokens_used"] == 30  # 20 + TOKEN_COST_PER_CYCLE (10)

    def test_park_without_budget_no_tokens(self):
        """park_task_node must not add tokens_used when budget not set."""
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-001", "priority": "LOW"},
            "cycles_completed": 2,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert "tokens_used" not in result

    def test_park_records_parked_status(self):
        """park_task_node must record parked status in history."""
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-002", "priority": "HIGH"},
            "cycles_completed": 1,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["cycle_history"][0]["status"] == "parked"
        assert result["cycle_history"][0]["task_id"] == "TASK-002"

    def test_park_increments_cycles_completed(self):
        """park_task_node must increment cycles_completed."""
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-003", "priority": "MEDIUM"},
            "cycles_completed": 5,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["cycles_completed"] == 6


# ===========================================================================
# Rejected findings — confirm code is correct
# ===========================================================================

class TestRejectedTypeDBFindings:
    """Confirm rejected TypeDB CRUD findings are non-issues."""

    def test_session_escaping_consistent(self):
        """BUG-SESSION-ESCAPE-INCONSISTENT: Escaping IS consistent."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations.update_session)
        # session_id escaped once at top, reused throughout
        assert 'session_id_escaped = session_id.replace' in src
        # String fields escaped before use
        assert 'desc_escaped = description.replace' in src
        assert 'agent_escaped = agent_id.replace' in src

    def test_rule_update_is_atomic(self):
        """BUG-RULE-UPDATE-ATOMIC-001: Rule update IS atomic."""
        from governance.typedb.queries.rules.crud import RuleCRUDOperations
        src = inspect.getsource(RuleCRUDOperations.update_rule)
        # All updates in single transaction
        count = src.count("tx.commit()")
        assert count == 1, f"Expected exactly 1 commit, found {count}"

    def test_linking_operations_escape_ids(self):
        """BUG-TASK-LINK-MISSING-ESCAPE: Linking operations DO escape."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        src = inspect.getsource(TaskLinkingOperations.link_task_to_session)
        assert 'task_id_escaped = task_id.replace' in src
        assert 'session_id_escaped = session_id.replace' in src

    def test_batch_query_has_try_except(self):
        """BUG-BATCH-QUERY-NULLCHECK-001: Batch queries wrapped in try/except."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._batch_fetch_session_attributes)
        assert "except Exception:" in src


class TestRejectedWorkflowFindings:
    """Confirm rejected workflow findings are non-issues."""

    def test_budget_division_guarded(self):
        """BUG-ORCH-BUDGET-001: Division is guarded by max()."""
        from governance.workflows.orchestrator.budget import compute_budget
        src = inspect.getsource(compute_budget)
        assert "max(tokens_used, 1)" in src
        assert "max(token_budget, 1)" in src

    def test_implement_node_guards_task(self):
        """BUG-ORCH-IMPL-001: implement_node guards current_task."""
        from governance.workflows.orchestrator.nodes import implement_node
        src = inspect.getsource(implement_node)
        assert 'task = state.get("current_task")' in src
        assert "if not task:" in src

    def test_chunk_empty_returns_list_with_content(self):
        """BUG-CHUNK-EMPTY-001: Returns [''] by design for consistent iteration."""
        from governance.embedding_pipeline.chunking import chunk_content
        result = chunk_content("")
        assert result == [""]
        # Non-empty content returns actual chunks
        result2 = chunk_content("hello")
        assert result2 == ["hello"]

    def test_chunk_content_splits_at_boundary(self):
        """BUG-ORCH-CHUNK-001: Chunking handles line boundaries correctly."""
        from governance.embedding_pipeline.chunking import chunk_content
        # Content that fits in one chunk
        result = chunk_content("line1\nline2\nline3", chunk_size=100)
        assert len(result) == 1
        # Content that needs splitting
        result2 = chunk_content("a" * 50 + "\n" + "b" * 50, chunk_size=60)
        assert len(result2) == 2
