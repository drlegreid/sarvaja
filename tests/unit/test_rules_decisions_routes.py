"""
Unit tests for Decisions CRUD Routes.

Per DOC-SIZE-01-v1: Tests for routes/rules/decisions.py module.
Tests: list_decisions, get_decision, create_decision,
       update_decision, link_rule_to_decision, delete_decision.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
from fastapi import HTTPException

_P = "governance.routes.rules.decisions"


def _mock_decision(id="D-001", name="Test", status="APPROVED", date=None):
    d = MagicMock()
    d.id = id
    d.name = name
    d.context = "Context"
    d.rationale = "Rationale"
    d.status = status
    d.decision_date = date or datetime(2026, 1, 1)
    return d


# ── list_decisions ──────────────────────────────────────────────


class TestListDecisions:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.decisions import list_decisions
        client = MagicMock()
        client.get_all_decisions.return_value = [_mock_decision()]
        client.get_decision_impacts.return_value = ["RULE-001"]
        with patch(f"{_P}.get_client", return_value=client):
            result = await list_decisions(offset=0, limit=50, status=None)
        assert result.pagination.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_status_filter(self):
        from governance.routes.rules.decisions import list_decisions
        client = MagicMock()
        client.get_all_decisions.return_value = [
            _mock_decision(id="D-1", status="APPROVED"),
            _mock_decision(id="D-2", status="PENDING"),
        ]
        client.get_decision_impacts.return_value = []
        with patch(f"{_P}.get_client", return_value=client):
            result = await list_decisions(offset=0, limit=50, status="PENDING")
        assert result.pagination.total == 1
        assert result.items[0].id == "D-2"

    @pytest.mark.asyncio
    async def test_pagination(self):
        from governance.routes.rules.decisions import list_decisions
        client = MagicMock()
        decisions = [_mock_decision(id=f"D-{i}") for i in range(5)]
        client.get_all_decisions.return_value = decisions
        client.get_decision_impacts.return_value = []
        with patch(f"{_P}.get_client", return_value=client):
            result = await list_decisions(offset=0, limit=2, status=None)
        assert result.pagination.total == 5
        assert len(result.items) == 2
        assert result.pagination.has_more is True

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.rules.decisions import list_decisions
        with patch(f"{_P}.get_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await list_decisions(offset=0, limit=50, status=None)
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_impact_failure_continues(self):
        from governance.routes.rules.decisions import list_decisions
        client = MagicMock()
        client.get_all_decisions.return_value = [_mock_decision()]
        client.get_decision_impacts.side_effect = Exception("fail")
        with patch(f"{_P}.get_client", return_value=client):
            result = await list_decisions(offset=0, limit=50, status=None)
        assert len(result.items) == 1
        assert result.items[0].linked_rules == []


# ── get_decision ────────────────────────────────────────────────


class TestGetDecision:
    @pytest.mark.asyncio
    async def test_found(self):
        from governance.routes.rules.decisions import get_decision
        client = MagicMock()
        client.get_all_decisions.return_value = [_mock_decision(id="D-001")]
        client.get_decision_impacts.return_value = ["RULE-001"]
        with patch(f"{_P}.get_client", return_value=client):
            result = await get_decision("D-001")
        assert result.id == "D-001"
        assert result.linked_rules == ["RULE-001"]

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.decisions import get_decision
        client = MagicMock()
        client.get_all_decisions.return_value = []
        with patch(f"{_P}.get_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await get_decision("D-MISSING")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.rules.decisions import get_decision
        with patch(f"{_P}.get_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await get_decision("D-001")
            assert exc.value.status_code == 503


# ── create_decision ─────────────────────────────────────────────


class TestCreateDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.decisions import create_decision
        from governance.models import DecisionCreate
        client = MagicMock()
        client.get_all_decisions.return_value = []
        created = _mock_decision(id="D-NEW")
        client.create_decision.return_value = created
        with patch(f"{_P}.get_client", return_value=client):
            req = DecisionCreate(
                decision_id="D-NEW", name="New", context="ctx", rationale="rat",
            )
            result = await create_decision(req)
        assert result.id == "D-NEW"

    @pytest.mark.asyncio
    async def test_duplicate(self):
        from governance.routes.rules.decisions import create_decision
        from governance.models import DecisionCreate
        client = MagicMock()
        client.get_all_decisions.return_value = [_mock_decision(id="D-DUP")]
        with patch(f"{_P}.get_client", return_value=client):
            req = DecisionCreate(
                decision_id="D-DUP", name="Dup", context="ctx", rationale="rat",
            )
            with pytest.raises(HTTPException) as exc:
                await create_decision(req)
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.rules.decisions import create_decision
        from governance.models import DecisionCreate
        with patch(f"{_P}.get_client", return_value=None):
            req = DecisionCreate(
                decision_id="D-X", name="X", context="c", rationale="r",
            )
            with pytest.raises(HTTPException) as exc:
                await create_decision(req)
            assert exc.value.status_code == 503


# ── update_decision ─────────────────────────────────────────────


class TestUpdateDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.decisions import update_decision
        from governance.models import DecisionUpdate
        client = MagicMock()
        updated = _mock_decision(id="D-1", name="Updated")
        client.update_decision.return_value = updated
        client.get_decision_impacts.return_value = []
        with patch(f"{_P}.get_client", return_value=client):
            result = await update_decision("D-1", DecisionUpdate(name="Updated"))
        assert result.name == "Updated"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.decisions import update_decision
        from governance.models import DecisionUpdate
        client = MagicMock()
        client.update_decision.return_value = None
        with patch(f"{_P}.get_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await update_decision("D-MISSING", DecisionUpdate(name="X"))
            assert exc.value.status_code == 404


# ── link_rule_to_decision ───────────────────────────────────────


class TestLinkRuleToDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.decisions import link_rule_to_decision
        client = MagicMock()
        client.link_decision_to_rule.return_value = True
        client.get_decision_impacts.return_value = ["RULE-001"]
        with patch(f"{_P}.get_client", return_value=client):
            result = await link_rule_to_decision("D-1", "RULE-001")
        assert result["rule_id"] == "RULE-001"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.decisions import link_rule_to_decision
        client = MagicMock()
        client.link_decision_to_rule.return_value = False
        with patch(f"{_P}.get_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await link_rule_to_decision("D-X", "RULE-X")
            assert exc.value.status_code == 404


# ── delete_decision ─────────────────────────────────────────────


class TestDeleteDecision:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.decisions import delete_decision
        client = MagicMock()
        client.delete_decision.return_value = True
        with patch(f"{_P}.get_client", return_value=client):
            await delete_decision("D-1")

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.decisions import delete_decision
        client = MagicMock()
        client.delete_decision.return_value = False
        with patch(f"{_P}.get_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await delete_decision("D-MISSING")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.rules.decisions import delete_decision
        with patch(f"{_P}.get_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await delete_decision("D-1")
            assert exc.value.status_code == 503
