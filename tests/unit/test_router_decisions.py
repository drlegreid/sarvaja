"""
Unit tests for Decision Routing Mixin.

Per DOC-SIZE-01-v1: Tests for router/decisions.py module.
Tests: DecisionRoutingMixin.route_decision, _generate_decision_typeql,
       _create_decision_evidence.
"""

import pytest
from unittest.mock import MagicMock

from governance.router.decisions import DecisionRoutingMixin


class _TestDecisionRouter(DecisionRoutingMixin):
    """Concrete class for testing the decision routing mixin."""

    def __init__(self, dry_run=True, embed=False):
        self.dry_run = dry_run
        self.embed = embed
        self.embedding_pipeline = MagicMock() if embed else None
        self.pre_route_hook = None
        self.post_route_hook = None

    def _execute_typeql(self, typeql: str) -> bool:
        return True

    def _escape(self, value: str) -> str:
        return value.replace('"', '\\"').replace("\\", "\\\\")


# ---------------------------------------------------------------------------
# route_decision
# ---------------------------------------------------------------------------
class TestRouteDecision:
    """Tests for route_decision()."""

    def test_empty_decision_id_fails(self):
        router = _TestDecisionRouter()
        result = router.route_decision("", "Test Decision")
        assert result["success"] is False
        assert "required" in result["error"]

    def test_none_decision_id_fails(self):
        router = _TestDecisionRouter()
        result = router.route_decision(None, "Test")
        assert result["success"] is False

    def test_valid_decision_succeeds(self):
        router = _TestDecisionRouter()
        result = router.route_decision("DECISION-001", "Test Decision")
        assert result["success"] is True
        assert result["item_type"] == "decision"
        assert result["item_id"] == "DECISION-001"
        assert result["destination"] == "typedb"

    def test_dry_run_no_execute(self):
        router = _TestDecisionRouter(dry_run=True)
        result = router.route_decision("DECISION-001", "Test")
        assert result["success"] is True

    def test_dry_run_with_embed_flag(self):
        router = _TestDecisionRouter(dry_run=True, embed=True)
        result = router.route_decision("DECISION-001", "Test")
        assert result["embedded"] is True

    def test_embed_with_execute(self):
        router = _TestDecisionRouter(dry_run=False, embed=True)
        result = router.route_decision("DECISION-001", "Test", context="ctx")
        assert result["embedded"] is True
        router.embedding_pipeline.embed_decision.assert_called_once()

    def test_pre_hook_called(self):
        router = _TestDecisionRouter()
        hook = MagicMock(side_effect=lambda t, d: d)
        router.pre_route_hook = hook
        router.route_decision("DECISION-001", "Test")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "decision"

    def test_post_hook_called(self):
        router = _TestDecisionRouter()
        hook = MagicMock()
        router.post_route_hook = hook
        router.route_decision("DECISION-001", "Test")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "decision"

    def test_dry_run_create_evidence(self):
        router = _TestDecisionRouter(dry_run=True)
        result = router.route_decision(
            "DECISION-001", "Test", create_evidence=True
        )
        assert result["evidence_file"] is not None
        assert "dry run" in result["evidence_file"]

    def test_no_evidence_by_default(self):
        router = _TestDecisionRouter()
        result = router.route_decision("DECISION-001", "Test")
        assert result["evidence_file"] is None


# ---------------------------------------------------------------------------
# _generate_decision_typeql
# ---------------------------------------------------------------------------
class TestGenerateDecisionTypeql:
    """Tests for _generate_decision_typeql()."""

    def test_contains_decision_id(self):
        router = _TestDecisionRouter()
        query = router._generate_decision_typeql("DECISION-001", "Test")
        assert "DECISION-001" in query

    def test_contains_name(self):
        router = _TestDecisionRouter()
        query = router._generate_decision_typeql("D-1", "Important Decision")
        assert "Important Decision" in query

    def test_contains_all_fields(self):
        router = _TestDecisionRouter()
        query = router._generate_decision_typeql(
            "D-1", "Test",
            context="Context text",
            rationale="Rationale text",
            impacts="Impact text",
            status="ACTIVE",
        )
        assert "Context text" in query
        assert "Rationale text" in query
        assert "Impact text" in query
        assert "ACTIVE" in query

    def test_contains_insert_keyword(self):
        router = _TestDecisionRouter()
        query = router._generate_decision_typeql("D-1", "Test")
        assert "insert" in query


# ---------------------------------------------------------------------------
# _create_decision_evidence
# ---------------------------------------------------------------------------
class TestCreateDecisionEvidence:
    """Tests for _create_decision_evidence()."""

    def test_creates_evidence_file(self, tmp_path):
        import governance.router.decisions as mod
        original = mod.EVIDENCE_DIR
        mod.EVIDENCE_DIR = tmp_path
        try:
            router = _TestDecisionRouter()
            data = {
                "decision_id": "DECISION-TEST",
                "name": "Test Decision",
                "context": "Test context",
                "rationale": "Test rationale",
                "impacts": "Test impacts",
                "status": "ACTIVE",
            }
            filepath = router._create_decision_evidence(data)
            assert "DECISION-TEST.md" in filepath
            content = (tmp_path / "DECISION-TEST.md").read_text()
            assert "# DECISION-TEST: Test Decision" in content
            assert "Test context" in content
            assert "Test rationale" in content
            assert "Test impacts" in content
        finally:
            mod.EVIDENCE_DIR = original

    def test_evidence_contains_status(self, tmp_path):
        import governance.router.decisions as mod
        original = mod.EVIDENCE_DIR
        mod.EVIDENCE_DIR = tmp_path
        try:
            router = _TestDecisionRouter()
            data = {
                "decision_id": "D-2",
                "name": "Test",
                "status": "DRAFT",
            }
            router._create_decision_evidence(data)
            content = (tmp_path / "D-2.md").read_text()
            assert "DRAFT" in content
        finally:
            mod.EVIDENCE_DIR = original
