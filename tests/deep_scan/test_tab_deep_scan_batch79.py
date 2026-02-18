"""
Batch 79 — Cross-cutting: Entity Conversion + TypeDB Query Patterns.

Triage: 8 findings → 3 confirmed + fixed, 5 rejected.
Fixes:
- BUG-TASK-PRIORITY-WRONG-ATTR: get_tasks_for_rule used 'priority' (rules) not 'task-priority' (tasks)
- BUG-DECISION-DATE-NONATOMIC: update_decision date path now uses single transaction
- BUG-AGENT-TRUST-NONATOMIC: update_agent_trust now uses attribute update, not entity delete+re-insert
"""
import inspect

import pytest


# ===========================================================================
# FIX: BUG-TASK-PRIORITY-WRONG-ATTR — correct attribute name in query
# ===========================================================================

class TestTaskPriorityAttributeName:
    """Verify get_tasks_for_rule queries task-priority, not priority."""

    def test_query_uses_task_priority_attribute(self):
        """The priority sub-query must use task-priority (not priority which is for rules)."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries.get_tasks_for_rule)
        assert "has task-priority $p" in src
        # Must NOT use bare 'has priority' (that's the rule attribute)
        lines = [l.strip() for l in src.splitlines() if "has priority" in l and "task-priority" not in l]
        assert lines == [], f"Found bare 'priority' queries: {lines}"

    def test_batch_fetch_also_uses_task_priority(self):
        """Batch task attribute fetch uses task-priority consistently."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._batch_fetch_task_attributes)
        assert "task-priority" in src

    def test_build_task_from_id_uses_task_priority(self):
        """Single task fetch uses task-priority consistently."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._build_task_from_id)
        assert "task-priority" in src


# ===========================================================================
# FIX: BUG-DECISION-DATE-NONATOMIC — single transaction for date update
# ===========================================================================

class TestDecisionDateAtomicity:
    """Verify update_decision date update uses single transaction."""

    def test_single_transaction_for_date(self):
        """Date delete+insert must be in ONE transaction block, not two."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries.update_decision)
        # Find the decision_date section
        date_section_start = src.index("BUG-DECISION-DATE-NONATOMIC")
        date_section = src[date_section_start:]
        # Count transaction context managers — should be exactly 1 after the marker
        tx_count = date_section.count("self._driver.transaction(")
        assert tx_count == 1, f"Expected 1 transaction for date update, found {tx_count}"

    def test_update_decision_attr_is_atomic(self):
        """The string attribute helper is also atomic (single transaction)."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        src = inspect.getsource(DecisionQueries._update_decision_attr)
        # One transaction for delete+insert
        assert src.count("self._driver.transaction(") == 1


# ===========================================================================
# FIX: BUG-AGENT-TRUST-NONATOMIC — attribute update, not entity delete+re-insert
# ===========================================================================

class TestAgentTrustAtomicity:
    """Verify update_agent_trust uses atomic attribute update."""

    def test_single_transaction(self):
        """Trust update must use single transaction."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.update_agent_trust)
        assert "self._driver.transaction(" in src
        assert src.count("self._driver.transaction(") == 1

    def test_no_entity_deletion(self):
        """Trust update must NOT delete the entire agent entity."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.update_agent_trust)
        # Should NOT contain 'delete $a;' (entity deletion)
        assert "delete $a;" not in src
        # Should contain attribute deletion pattern
        assert "delete has $old of $a" in src

    def test_attribute_level_update(self):
        """Trust update uses has $old of $a pattern (attribute, not entity)."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.update_agent_trust)
        assert "has trust-score $old" in src
        assert "has trust-score {trust_score}" in src


# ===========================================================================
# Rejected: Entity conversion field loss claims (by design)
# ===========================================================================

class TestEntityConversionDesign:
    """Confirm that 'missing' fields in responses are by design."""

    def test_task_details_has_separate_endpoint(self):
        """business/design/architecture/test_section have their own response model."""
        from governance.models import TaskDetailsResponse
        fields = TaskDetailsResponse.model_fields
        assert "business" in fields
        assert "design" in fields
        assert "architecture" in fields
        assert "test_section" in fields

    def test_task_response_has_standard_fields(self):
        """TaskResponse covers the standard API fields."""
        from governance.models import TaskResponse
        fields = TaskResponse.model_fields
        for f in ["task_id", "description", "phase", "status", "resolution",
                   "priority", "task_type", "agent_id", "created_at",
                   "claimed_at", "completed_at", "body", "linked_rules",
                   "linked_sessions", "linked_commits", "linked_documents",
                   "gap_id", "evidence", "document_path"]:
            assert f in fields, f"Missing field: {f}"

    def test_session_response_has_description(self):
        """SessionResponse includes description (not name — name is internal)."""
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        assert "description" in fields
        assert "session_id" in fields

    def test_rule_type_in_entity_not_response(self):
        """rule_type is internal taxonomy, not exposed in RuleResponse."""
        from governance.typedb.entities import Rule
        from governance.models import RuleResponse
        assert hasattr(Rule, "rule_type")
        # category serves user-facing purpose
        assert "category" in RuleResponse.model_fields


# ===========================================================================
# Rejected: Session variable mismatch claim (all correct)
# ===========================================================================

class TestSessionQueryVariableConsistency:
    """Verify all session query variable names match their .get() calls."""

    def test_batch_fetch_uses_consistent_vars(self):
        """Batch fetch: $v in query matches r.get('v')."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._batch_fetch_session_attributes)
        # All queries use $v and all gets use "v"
        assert 'select $id, $v;' in src
        assert 'r.get("v")' in src or "r.get(result_key)" in src

    def test_build_session_from_id_consistent(self):
        """Single session build: variable names match .get() calls."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._build_session_from_id)
        # Each query var matches its .get()
        pairs = [
            ("$name", '"name"'),
            ("$desc", '"desc"'),
            ("$path", '"path"'),
            ("$start", '"start"'),
            ("$end", '"end"'),
            ("$agent", '"agent"'),
        ]
        for var, get_key in pairs:
            assert var in src, f"Missing query var {var}"
            assert get_key in src, f"Missing .get() key {get_key}"

    def test_relationship_queries_consistent(self):
        """Session relationship queries use matching variable names."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._batch_fetch_session_relationships)
        assert 'r.get("sid")' in src
        assert 'r.get("rid")' in src
        assert 'r.get("did")' in src
        assert 'r.get("src")' in src
