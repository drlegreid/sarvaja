"""
Unit tests for Rules CRUD Routes.

Per DOC-SIZE-01-v1: Tests for routes/rules/crud.py module.
Tests: list_rules, get_rule, create_rule, update_rule, delete_rule,
       get_rule_tasks, dependency_overview, get_rule_dependencies,
       create_rule_dependency.
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

_P = "governance.routes.rules.crud"
_SVC = f"{_P}.rule_service"


# ── list_rules ───────────────────────────────────────────────────


class TestListRules:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import list_rules
        svc_result = {
            "items": [{"id": "R-1", "name": "R", "category": "governance",
                        "priority": "HIGH", "directive": "d", "status": "ACTIVE"}],
            "total": 1, "offset": 0, "limit": 50, "has_more": False,
        }
        with patch(f"{_SVC}.list_rules", return_value=svc_result):
            result = await list_rules(
                offset=0, limit=50, sort_by="id", order="asc",
                status=None, category=None, priority=None, search=None,
            )
        assert result.pagination.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import list_rules
        with patch(f"{_SVC}.list_rules", side_effect=ConnectionError("no db")):
            with pytest.raises(HTTPException) as exc:
                await list_rules(
                    offset=0, limit=50, sort_by="id", order="asc",
                    status=None, category=None, priority=None, search=None,
                )
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_generic_error(self):
        from governance.routes.rules.crud import list_rules
        with patch(f"{_SVC}.list_rules", side_effect=RuntimeError("fail")):
            with pytest.raises(HTTPException) as exc:
                await list_rules(
                    offset=0, limit=50, sort_by="id", order="asc",
                    status=None, category=None, priority=None, search=None,
                )
            assert exc.value.status_code == 500


# ── get_rule ─────────────────────────────────────────────────────


class TestGetRule:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import get_rule
        data = {"id": "R-1", "name": "R", "category": "governance",
                "priority": "HIGH", "directive": "d", "status": "ACTIVE"}
        with patch(f"{_SVC}.get_rule", return_value=data):
            result = await get_rule("R-1")
        assert result.id == "R-1"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.crud import get_rule
        with patch(f"{_SVC}.get_rule", side_effect=KeyError("R-MISS")):
            with pytest.raises(HTTPException) as exc:
                await get_rule("R-MISS")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import get_rule
        with patch(f"{_SVC}.get_rule", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await get_rule("R-1")
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_value_error(self):
        from governance.routes.rules.crud import get_rule
        with patch(f"{_SVC}.get_rule", side_effect=ValueError("bad")):
            with pytest.raises(HTTPException) as exc:
                await get_rule("R-1")
            assert exc.value.status_code == 422


# ── create_rule ──────────────────────────────────────────────────


class TestCreateRule:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import create_rule
        from governance.models import RuleCreate
        data = {"id": "R-NEW", "name": "New", "category": "governance",
                "priority": "LOW", "directive": "d", "status": "ACTIVE"}
        rule = RuleCreate(rule_id="R-NEW", name="New", category="governance",
                          priority="LOW", directive="d")
        with patch(f"{_SVC}.create_rule", return_value=data):
            result = await create_rule(rule)
        assert result.id == "R-NEW"

    @pytest.mark.asyncio
    async def test_conflict(self):
        from governance.routes.rules.crud import create_rule
        from governance.models import RuleCreate
        rule = RuleCreate(rule_id="R-DUP", name="Dup", category="governance",
                          priority="LOW", directive="d")
        with patch(f"{_SVC}.create_rule", side_effect=ValueError("exists")):
            with pytest.raises(HTTPException) as exc:
                await create_rule(rule)
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import create_rule
        from governance.models import RuleCreate
        rule = RuleCreate(rule_id="R-1", name="X", category="governance",
                          priority="LOW", directive="d")
        with patch(f"{_SVC}.create_rule", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await create_rule(rule)
            assert exc.value.status_code == 503


# ── update_rule ──────────────────────────────────────────────────


class TestUpdateRule:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import update_rule
        from governance.models import RuleUpdate
        data = {"id": "R-1", "name": "Updated", "category": "governance",
                "priority": "HIGH", "directive": "d", "status": "ACTIVE"}
        update = RuleUpdate(name="Updated")
        with patch(f"{_SVC}.update_rule", return_value=data):
            result = await update_rule("R-1", update)
        assert result.name == "Updated"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.crud import update_rule
        from governance.models import RuleUpdate
        update = RuleUpdate(name="X")
        with patch(f"{_SVC}.update_rule", side_effect=KeyError("R-MISS")):
            with pytest.raises(HTTPException) as exc:
                await update_rule("R-MISS", update)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import update_rule
        from governance.models import RuleUpdate
        update = RuleUpdate(name="X")
        with patch(f"{_SVC}.update_rule", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await update_rule("R-1", update)
            assert exc.value.status_code == 503


# ── delete_rule ──────────────────────────────────────────────────


class TestDeleteRule:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import delete_rule
        with patch(f"{_SVC}.delete_rule", return_value=True):
            result = await delete_rule("R-1", archive=True)
        assert result is None

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.crud import delete_rule
        with patch(f"{_SVC}.delete_rule", side_effect=KeyError("R-MISS")):
            with pytest.raises(HTTPException) as exc:
                await delete_rule("R-MISS", archive=True)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_returns_false(self):
        from governance.routes.rules.crud import delete_rule
        with patch(f"{_SVC}.delete_rule", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await delete_rule("R-1", archive=True)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import delete_rule
        with patch(f"{_SVC}.delete_rule", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await delete_rule("R-1", archive=True)
            assert exc.value.status_code == 503


# ── get_rule_tasks ───────────────────────────────────────────────


class TestGetRuleTasks:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import get_rule_tasks
        with patch(f"{_SVC}.get_rule_tasks", return_value={"tasks": []}):
            result = await get_rule_tasks("R-1")
        assert result["tasks"] == []

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import get_rule_tasks
        with patch(f"{_SVC}.get_rule_tasks", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await get_rule_tasks("R-1")
            assert exc.value.status_code == 503


# ── dependency_overview ──────────────────────────────────────────


class TestDependencyOverview:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import dependency_overview
        with patch(f"{_SVC}.dependency_overview", return_value={"deps": []}):
            result = await dependency_overview()
        assert result["deps"] == []

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import dependency_overview
        with patch(f"{_SVC}.dependency_overview", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await dependency_overview()
            assert exc.value.status_code == 503


# ── get_rule_dependencies ────────────────────────────────────────


class TestGetRuleDependencies:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import get_rule_dependencies
        with patch(f"{_SVC}.get_rule_dependencies", return_value={"deps": ["R-2"]}):
            result = await get_rule_dependencies("R-1")
        assert result["deps"] == ["R-2"]

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.crud import get_rule_dependencies
        with patch(f"{_SVC}.get_rule_dependencies", side_effect=KeyError("R-MISS")):
            with pytest.raises(HTTPException) as exc:
                await get_rule_dependencies("R-MISS")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import get_rule_dependencies
        with patch(f"{_SVC}.get_rule_dependencies", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await get_rule_dependencies("R-1")
            assert exc.value.status_code == 503


# ── create_rule_dependency ───────────────────────────────────────


class TestCreateRuleDependency:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.rules.crud import create_rule_dependency
        with patch(f"{_SVC}.create_rule_dependency", return_value=True):
            result = await create_rule_dependency("R-1", "R-2")
        assert result["created"] is True
        assert result["dependent"] == "R-1"

    @pytest.mark.asyncio
    async def test_failure(self):
        from governance.routes.rules.crud import create_rule_dependency
        with patch(f"{_SVC}.create_rule_dependency", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await create_rule_dependency("R-1", "R-2")
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.rules.crud import create_rule_dependency
        with patch(f"{_SVC}.create_rule_dependency", side_effect=KeyError("R-MISS")):
            with pytest.raises(HTTPException) as exc:
                await create_rule_dependency("R-1", "R-MISS")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from governance.routes.rules.crud import create_rule_dependency
        with patch(f"{_SVC}.create_rule_dependency", side_effect=ConnectionError):
            with pytest.raises(HTTPException) as exc:
                await create_rule_dependency("R-1", "R-2")
            assert exc.value.status_code == 503
