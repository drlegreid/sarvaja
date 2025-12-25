"""
Data Router Tests (P7.3)
Created: 2024-12-25

Tests for routing new data to TypeDB.
Strategic Goal: All new rules/decisions/sessions automatically stored in TypeDB.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class TestDataRouterModule:
    """Verify P7.3 data router module exists."""

    @pytest.mark.unit
    def test_data_router_module_exists(self):
        """Data router module must exist."""
        router_file = GOVERNANCE_DIR / "data_router.py"
        assert router_file.exists(), "governance/data_router.py not found"

    @pytest.mark.unit
    def test_data_router_class(self):
        """DataRouter class must be importable."""
        from governance.data_router import DataRouter

        router = DataRouter()
        assert router is not None

    @pytest.mark.unit
    def test_router_has_required_methods(self):
        """Router must have required methods."""
        from governance.data_router import DataRouter

        router = DataRouter()

        assert hasattr(router, 'route_rule')
        assert hasattr(router, 'route_decision')
        assert hasattr(router, 'route_session')
        assert hasattr(router, 'route_auto')


class TestRuleRouting:
    """Tests for rule routing to TypeDB."""

    @pytest.mark.unit
    def test_route_new_rule(self):
        """Should route new rule to TypeDB."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_rule(
            rule_id="RULE-TEST-001",
            name="Test Rule",
            directive="Do the thing",
            category="testing",
            priority="HIGH"
        )

        assert result['success'] is True
        assert result['destination'] == 'typedb'

    @pytest.mark.unit
    def test_route_rule_generates_embedding(self):
        """Routing should generate embedding."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True, embed=True)
        result = router.route_rule(
            rule_id="RULE-TEST-002",
            name="Test Rule with Embedding",
            directive="Do the other thing"
        )

        assert result['embedded'] is True

    @pytest.mark.unit
    def test_route_rule_validation(self):
        """Should validate rule data."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)

        # Missing required field
        result = router.route_rule(rule_id="", name="No ID")
        assert result['success'] is False
        assert 'error' in result


class TestDecisionRouting:
    """Tests for decision routing."""

    @pytest.mark.unit
    def test_route_new_decision(self):
        """Should route new decision to TypeDB."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_decision(
            decision_id="DECISION-TEST-001",
            name="Test Decision",
            context="Test context for decision",
            rationale="Because testing"
        )

        assert result['success'] is True
        assert result['destination'] == 'typedb'

    @pytest.mark.unit
    def test_route_decision_with_evidence(self):
        """Should create evidence file for decision."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_decision(
            decision_id="DECISION-TEST-002",
            name="Test Decision",
            context="Context",
            create_evidence=True
        )

        assert 'evidence_file' in result


class TestSessionRouting:
    """Tests for session routing."""

    @pytest.mark.unit
    def test_route_new_session(self):
        """Should route new session to TypeDB."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_session(
            session_id="SESSION-2024-12-25-TEST",
            content="Session evidence content here"
        )

        assert result['success'] is True

    @pytest.mark.unit
    def test_route_session_extracts_metadata(self):
        """Should extract session metadata."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_session(
            session_id="SESSION-2024-12-25-PHASE9-TESTING",
            content="# Test Session\n\nContent here"
        )

        assert result['metadata']['phase'] == 'PHASE9'
        assert result['metadata']['topic'] == 'TESTING'


class TestAutoRouting:
    """Tests for automatic routing detection."""

    @pytest.mark.unit
    def test_auto_detect_rule(self):
        """Should auto-detect rule from ID pattern."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_auto(
            identifier="RULE-023",
            data={"name": "New Rule", "directive": "Do stuff"}
        )

        assert result['type'] == 'rule'

    @pytest.mark.unit
    def test_auto_detect_decision(self):
        """Should auto-detect decision from ID pattern."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_auto(
            identifier="DECISION-005",
            data={"name": "New Decision", "context": "Context"}
        )

        assert result['type'] == 'decision'

    @pytest.mark.unit
    def test_auto_detect_session(self):
        """Should auto-detect session from ID pattern."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        result = router.route_auto(
            identifier="SESSION-2024-12-25-PHASE10-NEWFEATURE",
            data={"content": "Session content"}
        )

        assert result['type'] == 'session'


class TestBatchRouting:
    """Tests for batch routing operations."""

    @pytest.mark.unit
    def test_route_batch(self):
        """Should route multiple items in batch."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        items = [
            {"type": "rule", "rule_id": "RULE-B1", "name": "Batch Rule 1"},
            {"type": "rule", "rule_id": "RULE-B2", "name": "Batch Rule 2"},
        ]

        result = router.route_batch(items)

        assert result['total'] == 2
        assert result['succeeded'] == 2

    @pytest.mark.unit
    def test_batch_continues_on_error(self):
        """Batch should continue if one item fails."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True)
        items = [
            {"type": "rule", "rule_id": "RULE-B1", "name": "Good Rule"},
            {"type": "rule", "rule_id": "", "name": "Bad Rule"},  # Invalid
            {"type": "rule", "rule_id": "RULE-B3", "name": "Good Rule 2"},
        ]

        result = router.route_batch(items)

        assert result['total'] == 3
        assert result['succeeded'] == 2
        assert result['failed'] == 1


class TestRoutingHooks:
    """Tests for routing hooks and callbacks."""

    @pytest.mark.unit
    def test_pre_route_hook(self):
        """Should call pre-route hook."""
        from governance.data_router import DataRouter

        called = []

        def pre_hook(item_type, data):
            called.append(item_type)
            return data

        router = DataRouter(dry_run=True, pre_route_hook=pre_hook)
        router.route_rule(rule_id="RULE-HOOK", name="Hook Test")

        assert 'rule' in called

    @pytest.mark.unit
    def test_post_route_hook(self):
        """Should call post-route hook."""
        from governance.data_router import DataRouter

        results = []

        def post_hook(item_type, result):
            results.append(result)

        router = DataRouter(dry_run=True, post_route_hook=post_hook)
        router.route_rule(rule_id="RULE-HOOK", name="Hook Test")

        assert len(results) == 1
        assert results[0]['success'] is True


class TestTypeQLGeneration:
    """Tests for TypeQL query generation."""

    @pytest.mark.unit
    def test_generate_rule_typeql(self):
        """Should generate valid TypeQL for rule."""
        from governance.data_router import DataRouter

        router = DataRouter()
        typeql = router._generate_rule_typeql(
            rule_id="RULE-001",
            name="Test Rule",
            directive="Do the thing",
            category="testing",
            priority="HIGH",
            status="ACTIVE"
        )

        assert "insert $r isa rule-entity" in typeql
        assert '"RULE-001"' in typeql
        assert '"Test Rule"' in typeql

    @pytest.mark.unit
    def test_generate_decision_typeql(self):
        """Should generate valid TypeQL for decision."""
        from governance.data_router import DataRouter

        router = DataRouter()
        typeql = router._generate_decision_typeql(
            decision_id="DECISION-001",
            name="Test Decision",
            context="Context here"
        )

        assert "insert $d isa decision" in typeql
        assert '"DECISION-001"' in typeql


class TestRouterIntegration:
    """Integration tests for data router."""

    @pytest.mark.unit
    def test_router_uses_embedding_pipeline(self):
        """Router should integrate with embedding pipeline."""
        from governance.data_router import DataRouter

        router = DataRouter(dry_run=True, embed=True)
        assert router.embedding_pipeline is not None

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory should create router."""
        from governance.data_router import create_data_router

        router = create_data_router()
        assert router is not None

    @pytest.mark.unit
    def test_factory_with_options(self):
        """Factory should accept options."""
        from governance.data_router import create_data_router

        router = create_data_router(dry_run=True, embed=False)
        assert router.dry_run is True
        assert router.embed is False

