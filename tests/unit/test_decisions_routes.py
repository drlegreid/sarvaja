"""
Unit tests for Decisions CRUD Routes.

Per DOC-SIZE-01-v1: Tests for routes/rules/decisions.py module.
Tests: list_decisions, get_decision, create_decision, update_decision,
       link_rule_to_decision, delete_decision.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

_P_CLIENT = "governance.routes.rules.decisions.get_client"


def _make_decision(decision_id="DECISION-001", name="Test Decision",
                   context="Context", rationale="Rationale",
                   status="APPROVED", decision_date=None):
    d = MagicMock()
    d.id = decision_id
    d.name = name
    d.context = context
    d.rationale = rationale
    d.status = status
    d.decision_date = decision_date
    return d


class TestListDecisions:
    @pytest.mark.asyncio
    async def test_success(self):
        client = MagicMock()
        client.get_all_decisions.return_value = [_make_decision()]
        client.get_decision_impacts.return_value = ["RULE-001"]

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import list_decisions
            result = await list_decisions(offset=0, limit=50, status=None)
        assert result.pagination.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_with_status_filter(self):
        client = MagicMock()
        client.get_all_decisions.return_value = [
            _make_decision(decision_id="D-1", status="APPROVED"),
            _make_decision(decision_id="D-2", status="PENDING"),
        ]
        client.get_decision_impacts.return_value = []

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import list_decisions
            result = await list_decisions(offset=0, limit=50, status="APPROVED")
        assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_pagination(self):
        client = MagicMock()
        decisions = [_make_decision(decision_id=f"D-{i}") for i in range(5)]
        client.get_all_decisions.return_value = decisions
        client.get_decision_impacts.return_value = []

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import list_decisions
            result = await list_decisions(offset=2, limit=2, status=None)
        assert result.pagination.total == 5
        assert len(result.items) == 2
        assert result.pagination.has_more is True

    @pytest.mark.asyncio
    async def test_no_client(self):
        from fastapi import HTTPException
        with patch(_P_CLIENT, return_value=None):
            from governance.routes.rules.decisions import list_decisions
            with pytest.raises(HTTPException) as exc_info:
                await list_decisions(offset=0, limit=50, status=None)
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_impact_error_ignored(self):
        client = MagicMock()
        client.get_all_decisions.return_value = [_make_decision()]
        client.get_decision_impacts.side_effect = Exception("impact error")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import list_decisions
            result = await list_decisions(offset=0, limit=50, status=None)
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_with_decision_date(self):
        client = MagicMock()
        dt = datetime(2026, 1, 15, 10, 0, 0)
        client.get_all_decisions.return_value = [
            _make_decision(decision_date=dt),
        ]
        client.get_decision_impacts.return_value = []

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import list_decisions
            result = await list_decisions(offset=0, limit=50, status=None)
        assert result.items[0].decision_date is not None


class TestGetDecision:
    @pytest.mark.asyncio
    async def test_found(self):
        client = MagicMock()
        client.get_all_decisions.return_value = [_make_decision()]
        client.get_decision_impacts.return_value = ["RULE-001"]

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import get_decision
            result = await get_decision("DECISION-001")
        assert result.id == "DECISION-001"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_all_decisions.return_value = []

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import get_decision
            with pytest.raises(HTTPException) as exc_info:
                await get_decision("NONEXISTENT")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_no_client(self):
        from fastapi import HTTPException
        with patch(_P_CLIENT, return_value=None):
            from governance.routes.rules.decisions import get_decision
            with pytest.raises(HTTPException) as exc_info:
                await get_decision("D-1")
            assert exc_info.value.status_code == 503


class TestCreateDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = _make_decision()

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Test",
                context="C", rationale="R",
            )
            result = await create_decision(data)
        assert result.id == "DECISION-001"

    @pytest.mark.asyncio
    async def test_conflict(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_all_decisions.return_value = [_make_decision()]

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Dup",
                context="C", rationale="R",
            )
            with pytest.raises(HTTPException) as exc_info:
                await create_decision(data)
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_failure(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = None

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="D-NEW", name="New",
                context="C", rationale="R",
            )
            with pytest.raises(HTTPException) as exc_info:
                await create_decision(data)
            assert exc_info.value.status_code == 500


class TestUpdateDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        updated = _make_decision(name="Updated")
        client = MagicMock()
        client.update_decision.return_value = updated
        client.get_decision_impacts.return_value = []

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import update_decision
            from governance.models import DecisionUpdate
            data = DecisionUpdate(name="Updated")
            result = await update_decision("DECISION-001", data)
        assert result.name == "Updated"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.update_decision.return_value = None

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import update_decision
            from governance.models import DecisionUpdate
            data = DecisionUpdate(name="X")
            with pytest.raises(HTTPException) as exc_info:
                await update_decision("NONEXISTENT", data)
            assert exc_info.value.status_code == 404


class TestLinkRuleToDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        client = MagicMock()
        client.link_decision_to_rule.return_value = True
        client.get_decision_impacts.return_value = ["RULE-001"]

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import link_rule_to_decision
            result = await link_rule_to_decision("DECISION-001", "RULE-001")
        assert result["rule_id"] == "RULE-001"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.link_decision_to_rule.return_value = False

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import link_rule_to_decision
            with pytest.raises(HTTPException) as exc_info:
                await link_rule_to_decision("D-1", "R-1")
            assert exc_info.value.status_code == 404


class TestDeleteDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        client = MagicMock()
        client.delete_decision.return_value = True

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import delete_decision
            result = await delete_decision("DECISION-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        client = MagicMock()
        client.delete_decision.return_value = False

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import delete_decision
            with pytest.raises(HTTPException) as exc_info:
                await delete_decision("NONEXISTENT")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_no_client(self):
        from fastapi import HTTPException
        with patch(_P_CLIENT, return_value=None):
            from governance.routes.rules.decisions import delete_decision
            with pytest.raises(HTTPException) as exc_info:
                await delete_decision("D-1")
            assert exc_info.value.status_code == 503


class TestCreateDecisionWithRules:
    """GAP-DECISION-RULES-001: rules_applied links rules at creation."""

    @pytest.mark.asyncio
    async def test_rules_applied_links_rules(self):
        """Creating a decision with rules_applied should call link_decision_to_rule."""
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = _make_decision()
        client.link_decision_to_rule.return_value = True

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Test",
                context="C", rationale="R",
                rules_applied=["RULE-001", "RULE-002"],
            )
            result = await create_decision(data)

        assert result.linked_rules == ["RULE-001", "RULE-002"]
        assert client.link_decision_to_rule.call_count == 2
        client.link_decision_to_rule.assert_any_call("DECISION-001", "RULE-001")
        client.link_decision_to_rule.assert_any_call("DECISION-001", "RULE-002")

    @pytest.mark.asyncio
    async def test_empty_rules_applied_no_linking(self):
        """No rules_applied means no link calls."""
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = _make_decision()

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Test",
                context="C", rationale="R",
            )
            result = await create_decision(data)

        assert result.linked_rules == []
        client.link_decision_to_rule.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_link_failure(self):
        """If one rule link fails, others should still succeed."""
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = _make_decision()
        # First link succeeds, second fails
        client.link_decision_to_rule.side_effect = [True, False]

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Test",
                context="C", rationale="R",
                rules_applied=["RULE-001", "RULE-002"],
            )
            result = await create_decision(data)

        # Only first rule linked successfully
        assert result.linked_rules == ["RULE-001"]

    @pytest.mark.asyncio
    async def test_link_exception_handled(self):
        """Exceptions in link_decision_to_rule should be caught gracefully."""
        client = MagicMock()
        client.get_all_decisions.return_value = []
        client.create_decision.return_value = _make_decision()
        client.link_decision_to_rule.side_effect = Exception("TypeDB error")

        with patch(_P_CLIENT, return_value=client):
            from governance.routes.rules.decisions import create_decision
            from governance.models import DecisionCreate
            data = DecisionCreate(
                decision_id="DECISION-001", name="Test",
                context="C", rationale="R",
                rules_applied=["RULE-001"],
            )
            result = await create_decision(data)

        # Decision created but no rules linked due to error
        assert result.id == "DECISION-001"
        assert result.linked_rules == []
