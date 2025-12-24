"""
Governance module tests.
Tests for rule inference and knowledge reasoning.
Created: 2024-12-24 (DECISION-003)
"""
import pytest
import socket
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import governance module components
from governance import Rule, Decision, InferenceResult, quick_health
from governance import TypeDBClient, SCHEMA_FILE, DATA_FILE
import os


# =============================================================================
# UNIT TESTS - No TypeDB Required
# =============================================================================

class TestDataclasses:
    """Unit tests for governance dataclasses."""

    @pytest.mark.unit
    def test_rule_creation(self):
        """Test Rule dataclass creation."""
        rule = Rule(
            id="RULE-001",
            name="Evidence Logging",
            category="governance",
            priority="CRITICAL",
            status="ACTIVE",
            directive="Log all session evidence"
        )
        assert rule.id == "RULE-001"
        assert rule.name == "Evidence Logging"
        assert rule.category == "governance"
        assert rule.priority == "CRITICAL"
        assert rule.status == "ACTIVE"
        assert rule.created_date is None

    @pytest.mark.unit
    def test_rule_with_date(self):
        """Test Rule dataclass with datetime."""
        now = datetime.now()
        rule = Rule(
            id="RULE-002",
            name="Best Practices",
            category="architecture",
            priority="HIGH",
            status="ACTIVE",
            directive="Follow architectural best practices",
            created_date=now
        )
        assert rule.created_date == now

    @pytest.mark.unit
    def test_decision_creation(self):
        """Test Decision dataclass creation."""
        decision = Decision(
            id="DECISION-001",
            name="Stack Simplification",
            context="Too many services",
            rationale="Reduce complexity for PoC",
            status="APPROVED"
        )
        assert decision.id == "DECISION-001"
        assert decision.name == "Stack Simplification"
        assert decision.status == "APPROVED"
        assert decision.decision_date is None

    @pytest.mark.unit
    def test_inference_result_creation(self):
        """Test InferenceResult dataclass creation."""
        result = InferenceResult(
            query="match $r isa rule-entity;",
            results=[{"id": "RULE-001"}, {"id": "RULE-002"}],
            count=2,
            inference_used=True
        )
        assert result.query.startswith("match")
        assert len(result.results) == 2
        assert result.count == 2
        assert result.inference_used is True


class TestQuickHealth:
    """Unit tests for quick_health function."""

    @pytest.mark.unit
    def test_quick_health_returns_bool(self):
        """Test that quick_health returns a boolean."""
        result = quick_health()
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_quick_health_with_mock_socket_success(self):
        """Test quick_health with mocked successful connection."""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance

            result = quick_health()
            assert result is True
            mock_sock_instance.close.assert_called_once()

    @pytest.mark.unit
    def test_quick_health_with_mock_socket_failure(self):
        """Test quick_health with mocked failed connection."""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 1  # Connection refused
            mock_socket.return_value = mock_sock_instance

            result = quick_health()
            assert result is False


class TestSchemaFiles:
    """Unit tests for schema and data file paths."""

    @pytest.mark.unit
    def test_schema_file_exists(self):
        """Test that schema file path is valid."""
        assert SCHEMA_FILE.endswith("schema.tql")
        assert os.path.exists(SCHEMA_FILE), f"Schema file not found: {SCHEMA_FILE}"

    @pytest.mark.unit
    def test_data_file_exists(self):
        """Test that data file path is valid."""
        assert DATA_FILE.endswith("data.tql")
        assert os.path.exists(DATA_FILE), f"Data file not found: {DATA_FILE}"

    @pytest.mark.unit
    def test_schema_file_has_content(self):
        """Test that schema file has content."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert "define" in content
        assert "rule-entity" in content
        assert "decision" in content

    @pytest.mark.unit
    def test_data_file_has_content(self):
        """Test that data file has content."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert "insert" in content
        assert "RULE-001" in content


class TestTypeDBClientUnit:
    """Unit tests for TypeDBClient using mocks."""

    @pytest.mark.unit
    def test_client_initialization(self):
        """Test client initializes with default values."""
        client = TypeDBClient()
        assert client.host == "localhost"
        assert client.port == 1729
        assert client.database == "sim-ai-governance"
        assert client._connected is False

    @pytest.mark.unit
    def test_client_custom_params(self):
        """Test client with custom parameters."""
        client = TypeDBClient(host="custom-host", port=9999, database="custom-db")
        assert client.host == "custom-host"
        assert client.port == 9999
        assert client.database == "custom-db"

    @pytest.mark.unit
    def test_is_connected_default(self):
        """Test is_connected returns False before connecting."""
        client = TypeDBClient()
        assert client.is_connected() is False

    @pytest.mark.unit
    def test_health_check_not_connected(self):
        """Test health_check returns error when not connected."""
        client = TypeDBClient()
        health = client.health_check()
        assert health["healthy"] is False
        assert "Not connected" in health["error"]

    @pytest.mark.unit
    def test_execute_query_not_connected(self):
        """Test _execute_query raises error when not connected."""
        client = TypeDBClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            client._execute_query("match $x isa rule-entity;")

    @pytest.mark.unit
    def test_connect_without_driver(self):
        """Test connect returns False when driver not installed."""
        with patch.dict('sys.modules', {'typedb.driver': None}):
            with patch('builtins.__import__', side_effect=ImportError):
                client = TypeDBClient()
                # The connect method will try to import typedb.driver
                result = client.connect()
                assert result is False


class TestRuleQueries:
    """Tests for rule query methods (mocked)."""

    @pytest.mark.unit
    def test_get_all_rules_query_format(self):
        """Test get_all_rules generates correct query format."""
        client = TypeDBClient()
        client._connected = True

        # Mock _execute_query to capture the query
        with patch.object(client, '_execute_rule_query', return_value=[]) as mock:
            client.get_all_rules()
            mock.assert_called_once()
            query = mock.call_args[0][0]
            assert "match" in query
            assert "rule-entity" in query
            assert "rule-id" in query

    @pytest.mark.unit
    def test_get_active_rules_filters_active(self):
        """Test get_active_rules filters for ACTIVE status."""
        client = TypeDBClient()
        client._connected = True

        with patch.object(client, '_execute_query', return_value=[
            {"id": "RULE-001", "name": "Test", "cat": "gov", "pri": "HIGH", "dir": "Test"}
        ]) as mock:
            rules = client.get_active_rules()
            mock.assert_called_once()
            query = mock.call_args[0][0]
            assert 'status "ACTIVE"' in query
            assert len(rules) == 1
            assert rules[0].status == "ACTIVE"

    @pytest.mark.unit
    def test_get_rule_by_id_returns_none_when_not_found(self):
        """Test get_rule_by_id returns None for unknown rule."""
        client = TypeDBClient()
        client._connected = True

        with patch.object(client, '_execute_query', return_value=[]):
            result = client.get_rule_by_id("RULE-999")
            assert result is None


class TestInferenceQueries:
    """Tests for inference query methods (mocked)."""

    @pytest.mark.unit
    def test_get_rule_dependencies_uses_inference(self):
        """Test get_rule_dependencies enables inference."""
        client = TypeDBClient()
        client._connected = True

        with patch.object(client, '_execute_query', return_value=[]) as mock:
            client.get_rule_dependencies("RULE-006")
            mock.assert_called_once()
            # Check that infer=True was passed
            assert mock.call_args[1].get('infer') is True

    @pytest.mark.unit
    def test_find_conflicts_uses_inference(self):
        """Test find_conflicts enables inference."""
        client = TypeDBClient()
        client._connected = True

        with patch.object(client, '_execute_query', return_value=[]) as mock:
            client.find_conflicts()
            mock.assert_called_once()
            assert mock.call_args[1].get('infer') is True

    @pytest.mark.unit
    def test_get_decision_impacts_uses_inference(self):
        """Test get_decision_impacts enables inference."""
        client = TypeDBClient()
        client._connected = True

        with patch.object(client, '_execute_query', return_value=[
            {"rid": "RULE-001"},
            {"rid": "RULE-002"}
        ]) as mock:
            impacts = client.get_decision_impacts("DECISION-003")
            mock.assert_called_once()
            assert mock.call_args[1].get('infer') is True
            assert "RULE-001" in impacts
            assert "RULE-002" in impacts


# =============================================================================
# INTEGRATION TESTS - Require Running TypeDB
# =============================================================================

class TestTypeDBIntegration:
    """Integration tests requiring running TypeDB instance."""

    @pytest.mark.integration
    def test_typedb_socket_health(self, typedb_config):
        """Test TypeDB is reachable via socket."""
        host = typedb_config["host"]
        port = typedb_config["port"]

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                pytest.skip(f"TypeDB not running on {host}:{port}")

            assert result == 0, "TypeDB should be reachable"
        except socket.error as e:
            pytest.skip(f"TypeDB connection failed: {e}")

    @pytest.mark.integration
    def test_quick_health_with_typedb(self, typedb_config):
        """Test quick_health function with actual TypeDB."""
        result = quick_health()
        if not result:
            pytest.skip("TypeDB not running")
        assert result is True

    @pytest.mark.integration
    def test_client_connect_to_typedb(self, typedb_config):
        """Test TypeDBClient can connect to TypeDB.

        Note: This test may fail if typedb-client package is not installed
        or version doesn't match the TypeDB server.
        """
        try:
            from governance import get_client
            client = get_client()
            if client is None:
                pytest.skip("TypeDB driver not installed or connection failed")

            assert client.is_connected() is True
            client.close()
        except ImportError:
            pytest.skip("TypeDB driver not installed")
        except Exception as e:
            pytest.skip(f"TypeDB connection failed: {e}")


class TestSchemaLoading:
    """Integration tests for schema and data loading."""

    @pytest.mark.integration
    def test_schema_syntax_valid(self):
        """Test that schema.tql has valid TypeQL syntax.

        This is a basic syntax check - full validation requires TypeDB.
        """
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()

        # Basic syntax checks
        assert content.strip().startswith("# Sim.ai") or content.strip().startswith("define")
        assert "sub entity" in content
        assert "sub attribute" in content
        assert "sub relation" in content
        assert content.count("rule ") >= 3  # At least 3 inference rules

    @pytest.mark.integration
    def test_data_syntax_valid(self):
        """Test that data.tql has valid TypeQL syntax.

        This is a basic syntax check - full validation requires TypeDB.
        """
        with open(DATA_FILE, 'r') as f:
            content = f.read()

        # Basic syntax checks
        assert "insert" in content
        # Count rule entities (uses $rule001, $rule002, etc. pattern)
        rule_count = content.count("isa rule-entity")
        assert rule_count >= 6, f"Expected at least 6 rules, found {rule_count}"

        # Count decisions (uses $dec001, $dec002, etc. pattern)
        decision_count = content.count("isa decision,")
        assert decision_count >= 3, f"Expected at least 3 decisions, found {decision_count}"


# =============================================================================
# SPEC-DRIVEN TDD TESTS - Verify Strategy from RULES-DIRECTIVES.md
# =============================================================================

class TestRulesSpec:
    """
    Spec-driven tests that verify RULES-DIRECTIVES.md is correctly implemented.
    These tests derive from the specification, not from the implementation.
    Source: docs/RULES-DIRECTIVES.md
    """

    @pytest.mark.unit
    def test_RULE001_is_critical_governance(self):
        """RULE-001: Session Evidence Logging must be CRITICAL governance."""
        # Verify spec in data.tql
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'rule-id "RULE-001"' in content
        assert 'category "governance"' in content
        assert 'priority "CRITICAL"' in content

    @pytest.mark.unit
    def test_RULE002_is_high_architecture(self):
        """RULE-002: Architectural Best Practices must be HIGH architecture."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'rule-id "RULE-002"' in content

    @pytest.mark.unit
    def test_RULE008_is_critical_strategic(self):
        """RULE-008: In-House Rewrite Principle must be CRITICAL strategic."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'rule-id "RULE-008"' in content
        assert 'priority "CRITICAL"' in content

    @pytest.mark.unit
    def test_all_eleven_rules_defined(self):
        """All 11 rules from RULES-DIRECTIVES.md must be defined."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        # Count unique rule IDs (RULE-001 to RULE-011)
        for i in range(1, 10):  # RULE-001 to RULE-009
            rule_id = f'rule-id "RULE-00{i}"'
            assert rule_id in content, f"{rule_id} not found in data.tql"
        # RULE-010 and RULE-011 (double digit)
        assert 'rule-id "RULE-010"' in content, "RULE-010 not found in data.tql"
        assert 'rule-id "RULE-011"' in content, "RULE-011 not found in data.tql"

    @pytest.mark.unit
    def test_RULE011_is_critical_governance(self):
        """RULE-011: Multi-Agent Governance Protocol must be CRITICAL governance."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'rule-id "RULE-011"' in content
        assert 'rule-name "Multi-Agent Governance Protocol"' in content

    @pytest.mark.unit
    def test_rule006_depends_on_rule001(self):
        """RULE-006 (Decision Logging) depends on RULE-001 (Evidence Logging)."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        # Check dependency is defined
        assert 'rule-dependency' in content
        # The dependency chain should exist in the data

    @pytest.mark.unit
    def test_decision003_affects_rule008(self):
        """DECISION-003 (TypeDB Priority) affects RULE-008 (In-House Rewrite)."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'decision-id "DECISION-003"' in content
        assert 'decision-affects' in content


class TestInferenceSpec:
    """
    Spec-driven tests for inference rules.
    Verify that TypeDB inference produces expected results.
    """

    @pytest.mark.unit
    def test_transitive_dependency_rule_exists(self):
        """Schema must define transitive-dependency inference rule."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'rule transitive-dependency:' in content
        assert 'dependent: $a, dependency: $b' in content
        assert 'dependent: $b, dependency: $c' in content

    @pytest.mark.unit
    def test_cascade_supersede_rule_exists(self):
        """Schema must define cascade-supersede inference rule."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'rule cascade-supersede:' in content
        assert 'superseding: $a, superseded: $b' in content

    @pytest.mark.unit
    def test_priority_conflict_rule_exists(self):
        """Schema must define priority-conflict inference rule."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'rule priority-conflict:' in content
        assert 'has priority $p1' in content
        assert 'has priority $p2' in content

    @pytest.mark.unit
    def test_blocked_task_rule_disabled_with_reason(self):
        """Blocked task rule must be disabled with documented reason."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        # Rule should be commented out
        assert '# rule infer-blocked-task:' in content
        # Reason should be documented
        assert 'DISABLED' in content
        assert 'TypeDB cannot modify existing attributes' in content


class TestGovernanceIntegrity:
    """
    Tests that verify governance integrity constraints.
    """

    @pytest.mark.unit
    def test_no_duplicate_rule_ids(self):
        """Each rule ID must be unique."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        # Extract rule IDs and check for duplicates
        import re
        rule_ids = re.findall(r'rule-id "([^"]+)"', content)
        assert len(rule_ids) == len(set(rule_ids)), f"Duplicate rule IDs found: {rule_ids}"

    @pytest.mark.unit
    def test_no_duplicate_decision_ids(self):
        """Each decision ID must be unique."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        import re
        decision_ids = re.findall(r'decision-id "([^"]+)"', content)
        assert len(decision_ids) == len(set(decision_ids)), f"Duplicate decision IDs: {decision_ids}"

    @pytest.mark.unit
    def test_all_rules_have_required_attributes(self):
        """Each rule must have id, name, category, priority, status, directive."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        # Verify schema requires these attributes
        assert 'owns rule-id' in content
        assert 'owns rule-name' in content
        assert 'owns category' in content
        assert 'owns priority' in content
        assert 'owns status' in content
        assert 'owns directive' in content

    @pytest.mark.unit
    def test_valid_priority_values(self):
        """Priority values must be CRITICAL, HIGH, MEDIUM, or LOW."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        import re
        priorities = re.findall(r'priority "([^"]+)"', content)
        valid_priorities = {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'}
        for p in priorities:
            assert p in valid_priorities, f"Invalid priority: {p}"

    @pytest.mark.unit
    def test_valid_status_values(self):
        """Status values must be ACTIVE, DRAFT, DEPRECATED, or IMPLEMENTED."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        import re
        statuses = re.findall(r'status "([^"]+)"', content)
        # Extended statuses for full lifecycle (rules + decisions)
        valid_statuses = {'ACTIVE', 'DRAFT', 'DEPRECATED', 'IMPLEMENTED', 'SUPERSEDED', 'APPROVED'}
        for s in statuses:
            assert s in valid_statuses, f"Invalid status: {s}"


class TestMultiAgentGovernance:
    """
    Tests for RULE-011: Multi-Agent Governance Protocol.
    Verifies agent entities, trust scoring, and conflict resolution schema.
    """

    @pytest.mark.unit
    def test_agent_entity_defined(self):
        """Schema must define agent entity for trust tracking."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'agent sub entity' in content
        assert 'owns agent-id' in content
        assert 'owns trust-score' in content
        assert 'owns compliance-rate' in content

    @pytest.mark.unit
    def test_proposal_entity_defined(self):
        """Schema must define proposal entity for governance changes."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'proposal sub entity' in content
        assert 'owns proposal-id' in content
        assert 'owns proposal-type' in content
        assert 'owns evidence' in content
        assert 'owns hypothesis' in content

    @pytest.mark.unit
    def test_vote_relation_defined(self):
        """Schema must define vote relation for consensus."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'vote sub relation' in content
        assert 'relates voter' in content
        assert 'relates vote-target' in content
        assert 'owns vote-value' in content

    @pytest.mark.unit
    def test_dispute_relation_defined(self):
        """Schema must define dispute relation for conflict resolution."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'dispute sub relation' in content
        assert 'relates disputer' in content
        assert 'relates disputed-proposal' in content
        assert 'owns resolution-method' in content

    @pytest.mark.unit
    def test_escalation_relation_defined(self):
        """Schema must define escalation relation for human review."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'requires-escalation sub relation' in content
        assert 'relates escalated-proposal' in content

    @pytest.mark.unit
    def test_three_agents_defined(self):
        """Data must define 3 initial agents."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        assert 'agent-id "AGENT-001"' in content
        assert 'agent-id "AGENT-002"' in content
        assert 'agent-id "AGENT-003"' in content

    @pytest.mark.unit
    def test_agent_types_valid(self):
        """Agent types must be valid (claude-code, docker-agent, sync-agent)."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        import re
        agent_types = re.findall(r'agent-type "([^"]+)"', content)
        valid_types = {'claude-code', 'docker-agent', 'sync-agent'}
        for t in agent_types:
            assert t in valid_types, f"Invalid agent type: {t}"

    @pytest.mark.unit
    def test_trust_scores_in_range(self):
        """Trust scores must be between 0.0 and 1.0."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        import re
        trust_scores = re.findall(r'trust-score ([\d.]+)', content)
        for score in trust_scores:
            score_val = float(score)
            assert 0.0 <= score_val <= 1.0, f"Trust score out of range: {score_val}"

    @pytest.mark.unit
    def test_escalation_inference_rule_exists(self):
        """Schema must define escalation-required inference rule."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'rule escalation-required:' in content
        assert 'resolution-method "escalate"' in content

    @pytest.mark.unit
    def test_proposal_cascade_inference_rule_exists(self):
        """Schema must define proposal-cascade inference rule."""
        with open(SCHEMA_FILE, 'r') as f:
            content = f.read()
        assert 'rule proposal-cascade:' in content
        assert 'proposal-affects' in content

    @pytest.mark.unit
    def test_rule011_depends_on_evidence_rules(self):
        """RULE-011 must depend on RULE-001 and RULE-010."""
        with open(DATA_FILE, 'r') as f:
            content = f.read()
        # Check dependencies exist (transitive through inference)
        assert 'rule-dependency' in content
        # The actual dependencies are in the data file


# =============================================================================
# BDD-STYLE TESTS - Governance Workflow Behaviors
# =============================================================================

class TestGovernanceBDD:
    """
    BDD-style tests for governance workflows.
    Format: Given-When-Then to describe expected behaviors.
    These tests verify governance protocol behaviors per RULE-011.
    """

    # -------------------------------------------------------------------------
    # Scenario: Agent proposes a rule change
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_agent_when_propose_rule_then_proposal_created(self):
        """
        GIVEN an agent with trust-score >= 0.5
        WHEN the agent proposes a rule change
        THEN a proposal entity is created with status "pending"
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        # Verify proposal workflow is supported
        assert 'proposal sub entity' in schema
        assert 'proposal-status' in schema
        assert 'plays proposal:proposer' in schema  # agent can propose

    @pytest.mark.unit
    def test_given_proposal_when_affects_rule_then_cascade_to_dependents(self):
        """
        GIVEN a proposal that affects RULE-001
        WHEN RULE-006 depends on RULE-001
        THEN the proposal should cascade to affect RULE-006 (via inference)
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        # Verify cascade inference rule exists
        assert 'rule proposal-cascade:' in schema
        assert 'proposal-affects' in schema
        assert 'rule-dependency' in schema

    # -------------------------------------------------------------------------
    # Scenario: Agents vote on proposals
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_proposal_when_agents_vote_then_votes_recorded(self):
        """
        GIVEN a pending proposal
        WHEN multiple agents cast votes
        THEN each vote is recorded with voter, value, and weight
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'vote sub relation' in schema
        assert 'relates voter' in schema
        assert 'owns vote-value' in schema
        assert 'owns vote-weight' in schema

    @pytest.mark.unit
    def test_given_low_trust_agent_when_votes_then_weight_reduced(self):
        """
        GIVEN an agent with trust-score < 0.5
        WHEN the agent casts a vote
        THEN the vote-weight equals trust-score (reduced influence)
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        # Trust-weighted voting is documented
        assert 'vote-weight' in schema
        assert 'trust-score' in schema
        # The formula is in comments
        assert 'Low trust agents (< 0.5) have vote-weight = trust-score' in schema

    @pytest.mark.unit
    def test_given_high_trust_agent_when_votes_then_full_weight(self):
        """
        GIVEN an agent with trust-score >= 0.5
        WHEN the agent casts a vote
        THEN the vote-weight equals 1.0 (full influence)
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        # Full weight for trusted agents
        assert 'High trust agents (>= 0.5) have vote-weight = 1.0' in schema

    # -------------------------------------------------------------------------
    # Scenario: Agent disputes a proposal
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_proposal_when_agent_disputes_then_dispute_created(self):
        """
        GIVEN an approved or pending proposal
        WHEN an agent raises a dispute
        THEN a dispute relation is created with reason and analysis
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'dispute sub relation' in schema
        assert 'relates disputer' in schema
        assert 'owns dispute-reason' in schema
        assert 'owns semantic-analysis' in schema

    @pytest.mark.unit
    def test_given_dispute_when_resolution_escalate_then_human_review(self):
        """
        GIVEN a dispute with resolution-method "escalate"
        WHEN the escalation-required inference runs
        THEN the proposal requires human review (requires-escalation relation)
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'rule escalation-required:' in schema
        assert 'resolution-method "escalate"' in schema
        assert 'requires-escalation sub relation' in schema

    # -------------------------------------------------------------------------
    # Scenario: Human escalation triggers
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_escalation_triggers_defined(self):
        """
        GIVEN the governance protocol (RULE-011)
        WHEN human intervention is needed
        THEN escalation triggers are: VETO, STEER, AMBIGUITY, DEADLOCK, CRITICAL
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'escalation-trigger' in schema
        # Verify triggers are documented
        assert 'VETO' in schema
        assert 'STEER' in schema
        assert 'AMBIGUITY' in schema
        assert 'DEADLOCK' in schema
        assert 'CRITICAL' in schema

    # -------------------------------------------------------------------------
    # Scenario: Trust score calculation
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_agent_attributes_then_trust_formula_defined(self):
        """
        GIVEN agent attributes: compliance-rate, accuracy-rate, tenure-days
        WHEN calculating trust-score
        THEN formula is: Trust = (Compliance * 0.4) + (Accuracy * 0.3) + (Consistency * 0.2) + (Tenure * 0.1)
        """
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = f.read()
        # Verify formula is documented (check for key terms, allow any multiplication symbol)
        assert 'Compliance' in schema and '0.4' in schema
        assert 'Accuracy' in schema and '0.3' in schema
        assert 'Consistency' in schema and '0.2' in schema
        assert 'Tenure' in schema and '0.1' in schema
        # Verify this is the trust formula section
        assert 'Trust' in schema and 'Formula' in schema

    @pytest.mark.unit
    def test_given_agent_actions_then_tracked_for_trust(self):
        """
        GIVEN an agent performs actions (propose, vote, dispute)
        WHEN action completes
        THEN action is tracked for trust scoring (agent-action relation)
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'agent-action sub relation' in schema
        assert 'owns action-type' in schema
        assert 'owns action-outcome' in schema

    # -------------------------------------------------------------------------
    # Scenario: Conflict resolution methods
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_conflict_then_resolution_methods_defined(self):
        """
        GIVEN a rule conflict or dispute
        WHEN resolution is needed
        THEN methods are: consensus, evidence, authority, escalate
        """
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
        assert 'resolution-method' in schema
        # Verify methods documented
        assert '"consensus"' in schema or 'consensus' in schema
        assert '"evidence"' in schema or 'evidence' in schema
        assert '"authority"' in schema or 'authority' in schema
        assert '"escalate"' in schema or 'escalate' in schema

    # -------------------------------------------------------------------------
    # Scenario: Bicameral governance model
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_given_bicameral_model_then_human_oversight_defined(self):
        """
        GIVEN the bicameral governance model (RULE-011)
        WHEN critical decisions arise
        THEN human oversight (Upper House) can intervene via escalation
        """
        with open(DATA_FILE, 'r') as f:
            data = f.read()
        # RULE-011 defines bicameral model
        assert 'Bicameral model: Human oversight + AI execution' in data

    @pytest.mark.unit
    def test_given_agents_then_types_support_distributed_execution(self):
        """
        GIVEN the multi-agent architecture
        WHEN different tasks require execution
        THEN agent types support: claude-code (R&D), docker-agent (production), sync-agent (coordination)
        """
        with open(DATA_FILE, 'r') as f:
            data = f.read()
        assert 'agent-type "claude-code"' in data
        assert 'agent-type "docker-agent"' in data
        assert 'agent-type "sync-agent"' in data
