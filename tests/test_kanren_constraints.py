"""
Tests for Kanren Constraint Engine (KAN-002).

Per RULE-023: Test Coverage Protocol

Note: kanren is an optional dependency. Tests are skipped if not installed.
Install with: pip install kanren
"""

import pytest

# Try to import kanren module - skip all tests if not available
try:
    from governance.kanren_constraints import (
        trust_level,
        requires_supervisor,
        can_execute_priority,
        task_requires_evidence,
        valid_task_assignment,
        valid_rag_chunk,
        filter_rag_chunks,
        conflicting_priorities,
        find_rule_conflicts,
        assemble_context,
        validate_agent_for_task,
        AgentContext,
        TaskContext,
        RuleContext,
    )
    KANREN_AVAILABLE = True
except ImportError:
    KANREN_AVAILABLE = False

# Skip entire module if kanren not installed
pytestmark = pytest.mark.skipif(
    not KANREN_AVAILABLE,
    reason="kanren not installed - optional dependency"
)


# =============================================================================
# Trust Level Tests (RULE-011)
# =============================================================================

class TestTrustLevel:
    """Trust level determination per RULE-011."""

    def test_expert_trust(self):
        """Score >= 0.9 is expert."""
        assert trust_level(0.95) == "expert"
        assert trust_level(0.90) == "expert"
        assert trust_level(1.0) == "expert"

    def test_trusted_trust(self):
        """Score >= 0.7 and < 0.9 is trusted."""
        assert trust_level(0.89) == "trusted"
        assert trust_level(0.75) == "trusted"
        assert trust_level(0.70) == "trusted"

    def test_supervised_trust(self):
        """Score >= 0.5 and < 0.7 is supervised."""
        assert trust_level(0.69) == "supervised"
        assert trust_level(0.55) == "supervised"
        assert trust_level(0.50) == "supervised"

    def test_restricted_trust(self):
        """Score < 0.5 is restricted."""
        assert trust_level(0.49) == "restricted"
        assert trust_level(0.25) == "restricted"
        assert trust_level(0.0) == "restricted"


class TestRequiresSupervisor:
    """Supervisor requirement per RULE-011."""

    def test_restricted_requires_supervisor(self):
        """Restricted agents need supervisor."""
        result = requires_supervisor("restricted")
        assert len(result) > 0
        assert result[0] is True

    def test_supervised_requires_supervisor(self):
        """Supervised agents need supervisor."""
        result = requires_supervisor("supervised")
        assert len(result) > 0
        assert result[0] is True

    def test_trusted_no_supervisor(self):
        """Trusted agents don't need supervisor."""
        result = requires_supervisor("trusted")
        assert len(result) > 0
        assert result[0] is False

    def test_expert_no_supervisor(self):
        """Expert agents don't need supervisor."""
        result = requires_supervisor("expert")
        assert len(result) > 0
        assert result[0] is False


class TestCanExecutePriority:
    """Task execution permissions per RULE-011."""

    def test_critical_expert_can_execute(self):
        """Expert can execute CRITICAL tasks."""
        result = can_execute_priority("expert", "CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_critical_trusted_can_execute(self):
        """Trusted can execute CRITICAL tasks."""
        result = can_execute_priority("trusted", "CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_critical_supervised_cannot_execute(self):
        """Supervised cannot execute CRITICAL tasks."""
        result = can_execute_priority("supervised", "CRITICAL")
        assert len(result) > 0
        assert result[0] is False

    def test_critical_restricted_cannot_execute(self):
        """Restricted cannot execute CRITICAL tasks."""
        result = can_execute_priority("restricted", "CRITICAL")
        assert len(result) > 0
        assert result[0] is False

    def test_high_supervised_can_execute(self):
        """Supervised can execute HIGH tasks."""
        result = can_execute_priority("supervised", "HIGH")
        assert len(result) > 0
        assert result[0] is True

    def test_high_restricted_cannot_execute(self):
        """Restricted cannot execute HIGH tasks."""
        result = can_execute_priority("restricted", "HIGH")
        assert len(result) > 0
        assert result[0] is False

    def test_medium_all_can_execute(self):
        """All trust levels can execute MEDIUM tasks."""
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "MEDIUM")
            assert len(result) > 0
            assert result[0] is True

    def test_low_all_can_execute(self):
        """All trust levels can execute LOW tasks."""
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "LOW")
            assert len(result) > 0
            assert result[0] is True


# =============================================================================
# Task Validation Tests (RULE-014, RULE-028)
# =============================================================================

class TestTaskRequiresEvidence:
    """Evidence requirements per RULE-028."""

    def test_critical_requires_evidence(self):
        """CRITICAL tasks require evidence."""
        result = task_requires_evidence("CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_high_requires_evidence(self):
        """HIGH tasks require evidence."""
        result = task_requires_evidence("HIGH")
        assert len(result) > 0
        assert result[0] is True

    def test_medium_no_evidence(self):
        """MEDIUM tasks don't require evidence."""
        result = task_requires_evidence("MEDIUM")
        assert len(result) > 0
        assert result[0] is False

    def test_low_no_evidence(self):
        """LOW tasks don't require evidence."""
        result = task_requires_evidence("LOW")
        assert len(result) > 0
        assert result[0] is False


class TestValidTaskAssignment:
    """Task assignment validation per RULE-011, RULE-014."""

    def test_expert_critical_valid(self):
        """Expert can be assigned CRITICAL tasks."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is False
        assert result["requires_evidence"] is True

    def test_supervised_critical_invalid(self):
        """Supervised cannot be assigned CRITICAL tasks."""
        agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
        task = TaskContext("TASK-002", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is False
        assert result["trust_level"] == "supervised"
        assert result["can_execute"] is False
        assert result["requires_supervisor"] is True

    def test_supervised_medium_valid(self):
        """Supervised can be assigned MEDIUM tasks."""
        agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
        task = TaskContext("TASK-003", "MEDIUM", False)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is True
        assert result["trust_level"] == "supervised"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is True
        assert result["requires_evidence"] is False

    def test_constraints_checked_included(self):
        """Validation result includes constraints checked."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert "constraints_checked" in result
        assert len(result["constraints_checked"]) >= 3
        assert any("RULE-011" in c for c in result["constraints_checked"])


# =============================================================================
# RAG Validation Tests (RULE-007)
# =============================================================================

class TestValidRagChunk:
    """RAG chunk validation per RULE-007."""

    def test_valid_typedb_chunk(self):
        """Valid TypeDB chunk passes validation."""
        result = valid_rag_chunk("typedb", True, "rule")
        assert len(result) > 0
        assert result[0] is True

    def test_valid_chromadb_chunk(self):
        """Valid ChromaDB chunk passes validation."""
        result = valid_rag_chunk("chromadb", True, "evidence")
        assert len(result) > 0
        assert result[0] is True

    def test_invalid_source(self):
        """Invalid source fails validation."""
        result = valid_rag_chunk("external", True, "rule")
        assert len(result) == 0  # No valid solutions

    def test_unverified_chunk(self):
        """Unverified chunk fails validation."""
        result = valid_rag_chunk("typedb", False, "rule")
        assert len(result) == 0  # No valid solutions

    def test_invalid_type(self):
        """Invalid chunk type fails validation."""
        result = valid_rag_chunk("typedb", True, "unknown")
        assert len(result) == 0  # No valid solutions


class TestFilterRagChunks:
    """RAG chunk filtering per RULE-007."""

    def test_filter_mixed_chunks(self):
        """Filters mixed valid/invalid chunks."""
        chunks = [
            {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
            {"id": 2, "source": "external", "verified": False, "type": "unknown"},
            {"id": 3, "source": "chromadb", "verified": True, "type": "evidence"},
            {"id": 4, "source": "evidence", "verified": True, "type": "decision"},
        ]
        valid = filter_rag_chunks(chunks)

        assert len(valid) == 3
        assert all(c["source"] in ["typedb", "chromadb", "evidence"] for c in valid)

    def test_filter_empty_list(self):
        """Handles empty chunk list."""
        valid = filter_rag_chunks([])
        assert valid == []

    def test_filter_all_invalid(self):
        """Returns empty when all chunks invalid."""
        chunks = [
            {"id": 1, "source": "external", "verified": False, "type": "unknown"},
        ]
        valid = filter_rag_chunks(chunks)
        assert valid == []


# =============================================================================
# Rule Conflict Detection Tests (RULE-011)
# =============================================================================

class TestRuleConflicts:
    """Rule conflict detection per RULE-011."""

    def test_conflicting_priorities(self):
        """Detects priority conflicts in same category."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "governance")

        assert conflicting_priorities(rule1, rule2) is True

    def test_no_conflict_different_category(self):
        """No conflict for different categories."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "technical")

        assert conflicting_priorities(rule1, rule2) is False

    def test_no_conflict_same_priority(self):
        """No conflict for same priority."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "CRITICAL", "ACTIVE", "governance")

        assert conflicting_priorities(rule1, rule2) is False

    def test_find_all_conflicts(self):
        """Finds all conflicts in rule set."""
        rules = [
            RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance"),
            RuleContext("RULE-002", "HIGH", "ACTIVE", "governance"),
            RuleContext("RULE-003", "MEDIUM", "ACTIVE", "governance"),
            RuleContext("RULE-004", "HIGH", "ACTIVE", "technical"),
        ]
        conflicts = find_rule_conflicts(rules)

        # RULE-001 conflicts with RULE-002 and RULE-003
        # RULE-002 conflicts with RULE-003
        assert len(conflicts) == 3


# =============================================================================
# Context Assembly Tests
# =============================================================================

class TestAssembleContext:
    """Context assembly for LLM prompts."""

    def test_assemble_valid_context(self):
        """Assembles valid context with filtered chunks."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        chunks = [
            {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
            {"id": 2, "source": "external", "verified": False, "type": "unknown"},
        ]

        context = assemble_context(agent, task, chunks)

        assert context["assignment_valid"] is True
        assert context["agent"]["trust_level"] == "expert"
        assert context["task"]["requires_evidence"] is True
        assert len(context["rag_chunks"]) == 1
        assert "RULE-007: RAG validation" in context["constraints_applied"]


class TestValidateAgentForTask:
    """Quick validation helper function."""

    def test_validate_expert_critical(self):
        """Quick validation for expert + CRITICAL."""
        result = validate_agent_for_task("AGENT-001", 0.95, "CRITICAL")
        assert result["valid"] is True

    def test_validate_restricted_critical(self):
        """Quick validation for restricted + CRITICAL."""
        result = validate_agent_for_task("AGENT-002", 0.35, "CRITICAL")
        assert result["valid"] is False


# =============================================================================
# KAN-003: RAG Filter Integration Tests
# =============================================================================

class TestKanrenRAGFilter:
    """Tests for KanrenRAGFilter class (KAN-003)."""

    def test_filter_import(self):
        """KanrenRAGFilter can be imported."""
        from governance.kanren_constraints import KanrenRAGFilter
        assert KanrenRAGFilter is not None

    def test_filter_instantiation(self):
        """KanrenRAGFilter can be instantiated."""
        from governance.kanren_constraints import KanrenRAGFilter
        rag_filter = KanrenRAGFilter()
        assert rag_filter is not None
        assert rag_filter._store is None  # Lazy load

    def test_filter_with_mock_store(self):
        """KanrenRAGFilter works with injected mock store."""
        from unittest.mock import MagicMock
        from governance.kanren_constraints import KanrenRAGFilter

        # Create mock store
        mock_store = MagicMock()
        mock_result = MagicMock()
        mock_result.vector_id = "vec-001"
        mock_result.content = "Test content"
        mock_result.source_type = "rule"
        mock_result.score = 0.85
        mock_result.source = "RULE-001"
        mock_store.search.return_value = [mock_result]

        # Create filter with mock
        rag_filter = KanrenRAGFilter(vector_store=mock_store)

        # Test search_validated
        results = rag_filter.search_validated(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5
        )

        # Verify mock was called
        mock_store.search.assert_called_once()

        # Results should be filtered through Kanren
        # High score rule from typedb should pass
        assert len(results) == 1
        assert results[0]["source"] == "typedb"
        assert results[0]["type"] == "rule"

    def test_results_to_chunks_conversion(self):
        """_results_to_chunks correctly converts SimilarityResult format."""
        from unittest.mock import MagicMock
        from governance.kanren_constraints import KanrenRAGFilter

        mock_store = MagicMock()
        rag_filter = KanrenRAGFilter(vector_store=mock_store)

        # Create mock results
        mock_results = []
        for source_type, expected_source in [("rule", "typedb"), ("decision", "typedb"), ("session", "chromadb")]:
            r = MagicMock()
            r.vector_id = f"vec-{source_type}"
            r.content = f"Content for {source_type}"
            r.source_type = source_type
            r.score = 0.8
            r.source = f"SOURCE-{source_type.upper()}"
            mock_results.append(r)

        chunks = rag_filter._results_to_chunks(mock_results)

        assert len(chunks) == 3
        assert chunks[0]["source"] == "typedb"
        assert chunks[1]["source"] == "typedb"
        assert chunks[2]["source"] == "chromadb"

    def test_search_for_task_validation(self):
        """search_for_task validates agent-task assignment."""
        from unittest.mock import MagicMock
        from governance.kanren_constraints import KanrenRAGFilter, AgentContext, TaskContext

        # Create mock store
        mock_store = MagicMock()
        mock_vec = MagicMock()
        mock_vec.id = "vec-001"
        mock_vec.content = "governance rule content"
        mock_vec.source_type = "rule"
        mock_vec.source = "RULE-001"
        mock_store.get_all_vectors.return_value = [mock_vec]

        rag_filter = KanrenRAGFilter(vector_store=mock_store)

        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)

        result = rag_filter.search_for_task(
            query_text="governance",
            task_context=task,
            agent_context=agent
        )

        assert result["assignment_valid"] is True
        assert result["agent"]["trust_level"] == "expert"
        assert result["task"]["requires_evidence"] is True
        assert "constraints_applied" in result

    def test_low_score_chunk_filtered(self):
        """Chunks with low similarity score (< 0.5) are marked unverified and filtered."""
        from unittest.mock import MagicMock
        from governance.kanren_constraints import KanrenRAGFilter

        mock_store = MagicMock()
        mock_result = MagicMock()
        mock_result.vector_id = "vec-low"
        mock_result.content = "Low score content"
        mock_result.source_type = "rule"
        mock_result.score = 0.3  # Below threshold
        mock_result.source = "RULE-LOW"
        mock_store.search.return_value = [mock_result]

        rag_filter = KanrenRAGFilter(vector_store=mock_store)

        results = rag_filter.search_validated(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5
        )

        # Low score chunks should be filtered out (verified=False fails Kanren)
        assert len(results) == 0


# =============================================================================
# KAN-004: TypeDB -> Kanren Loader Tests
# =============================================================================

class TestTypeDBKanrenLoader:
    """Tests for KAN-004: TypeDB -> Kanren constraint loader."""

    def test_loader_imports(self):
        """Loader module can be imported."""
        from governance.kanren import (
            RuleConstraint,
            TypeDBKanrenBridge,
            load_rules_from_typedb,
            populate_kanren_facts,
            query_critical_rules,
        )
        assert RuleConstraint is not None
        assert TypeDBKanrenBridge is not None
        assert load_rules_from_typedb is not None

    def test_rule_constraint_from_dict(self):
        """RuleConstraint creates from TypeDB query result."""
        from governance.kanren import RuleConstraint

        data = {
            "id": "RULE-011",
            "semantic_id": "GOV-BICAM-01-v1",
            "name": "Multi-Agent Governance Protocol",
            "category": "governance",
            "priority": "CRITICAL",
            "directive": "Bicameral model",
            "rule_type": "FOUNDATIONAL",
        }

        constraint = RuleConstraint.from_dict(data)

        assert constraint.rule_id == "RULE-011"
        assert constraint.semantic_id == "GOV-BICAM-01-v1"
        assert constraint.priority == "CRITICAL"
        assert constraint.rule_type == "FOUNDATIONAL"

    def test_load_rules_from_json(self):
        """load_rules_from_typedb parses JSON correctly."""
        from governance.kanren import load_rules_from_typedb

        json_result = '''[
            {"id": "RULE-001", "priority": "CRITICAL", "category": "governance", "rule_type": "FOUNDATIONAL"},
            {"id": "RULE-002", "priority": "HIGH", "category": "testing", "rule_type": "OPERATIONAL"}
        ]'''

        rules = load_rules_from_typedb(json_result)

        assert len(rules) == 2
        assert rules[0].rule_id == "RULE-001"
        assert rules[0].priority == "CRITICAL"
        assert rules[1].rule_id == "RULE-002"
        assert rules[1].priority == "HIGH"

    def test_load_rules_empty_input(self):
        """load_rules_from_typedb handles empty input."""
        from governance.kanren import load_rules_from_typedb

        assert load_rules_from_typedb(None) == []
        assert load_rules_from_typedb("") == []
        assert load_rules_from_typedb("invalid json") == []

    def test_populate_kanren_facts(self):
        """populate_kanren_facts creates Kanren relations."""
        from governance.kanren import load_rules_from_typedb, populate_kanren_facts

        json_result = '''[
            {"id": "TEST-RULE-001", "priority": "CRITICAL", "category": "governance", "rule_type": "FOUNDATIONAL"},
            {"id": "TEST-RULE-002", "priority": "HIGH", "category": "testing", "rule_type": "OPERATIONAL"},
            {"id": "TEST-RULE-003", "priority": "CRITICAL", "category": "autonomy", "rule_type": "TECHNICAL"}
        ]'''

        rules = load_rules_from_typedb(json_result)
        counts = populate_kanren_facts(rules)

        assert counts["priority"] == 3
        assert counts["critical"] == 2  # Two CRITICAL rules
        assert counts["rule_type"] == 3
        assert counts["category"] == 3

    def test_typedb_kanren_bridge_lifecycle(self):
        """TypeDBKanrenBridge manages load/validate lifecycle."""
        from governance.kanren import TypeDBKanrenBridge

        bridge = TypeDBKanrenBridge()

        # Initially not loaded
        assert bridge.is_loaded() is False

        # Validation fails when not loaded
        result = bridge.validate_rule("RULE-001")
        assert result["compliant"] is False
        assert "Rules not loaded" in result["violations"][0]

        # Load rules
        json_result = '''[
            {"id": "RULE-001", "priority": "HIGH", "category": "governance", "rule_type": "FOUNDATIONAL"}
        ]'''
        counts = bridge.load_from_mcp(json_result)

        assert bridge.is_loaded() is True
        assert counts["priority"] == 1
        assert len(bridge.get_rules()) == 1

    def test_validate_rule_compliance_expert(self):
        """Expert agent can comply with any rule."""
        from governance.kanren import TypeDBKanrenBridge

        bridge = TypeDBKanrenBridge()
        json_result = '''[
            {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
        ]'''
        bridge.load_from_mcp(json_result)

        # Expert with evidence can comply with CRITICAL rule
        result = bridge.validate_rule(
            "RULE-CRITICAL",
            has_evidence=True,
            agent_trust=0.95
        )

        assert result["compliant"] is True
        assert result["trust_level"] == "expert"

    def test_validate_rule_compliance_low_trust(self):
        """Low trust agent cannot comply with CRITICAL rules."""
        from governance.kanren import TypeDBKanrenBridge

        bridge = TypeDBKanrenBridge()
        json_result = '''[
            {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
        ]'''
        bridge.load_from_mcp(json_result)

        # Restricted agent cannot comply with CRITICAL rule
        result = bridge.validate_rule(
            "RULE-CRITICAL",
            has_evidence=True,
            agent_trust=0.3
        )

        assert result["compliant"] is False
        assert "Trust level 'restricted' cannot execute CRITICAL priority" in result["violations"]

    def test_validate_rule_missing_evidence(self):
        """Missing evidence causes compliance failure for CRITICAL rules."""
        from governance.kanren import TypeDBKanrenBridge

        bridge = TypeDBKanrenBridge()
        json_result = '''[
            {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
        ]'''
        bridge.load_from_mcp(json_result)

        # Expert without evidence fails for CRITICAL rule
        result = bridge.validate_rule(
            "RULE-CRITICAL",
            has_evidence=False,
            agent_trust=0.95
        )

        assert result["compliant"] is False
        assert any("requires evidence" in v for v in result["violations"])

    def test_get_rules_by_category(self):
        """Bridge filters rules by category."""
        from governance.kanren import TypeDBKanrenBridge

        bridge = TypeDBKanrenBridge()
        json_result = '''[
            {"id": "RULE-001", "priority": "CRITICAL", "category": "governance"},
            {"id": "RULE-002", "priority": "HIGH", "category": "testing"},
            {"id": "RULE-003", "priority": "HIGH", "category": "governance"}
        ]'''
        bridge.load_from_mcp(json_result)

        gov_rules = bridge.get_rules_by_category("governance")
        test_rules = bridge.get_rules_by_category("testing")

        assert len(gov_rules) == 2
        assert len(test_rules) == 1
        assert all(r.category == "governance" for r in gov_rules)
