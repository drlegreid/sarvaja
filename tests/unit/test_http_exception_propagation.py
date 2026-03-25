"""
TDD tests for BUG-013: HTTPException must propagate through catch-all handlers.

Anti-pattern: `except Exception` swallows HTTPException raised inside the try block,
turning intended 404/422/etc. into 500. Fix: `except HTTPException: raise` before catch-all.

Tests cover:
- governance/routes/sessions/crud.py — get_session (already fixed, regression test)
- governance/routes/reports.py — get_session_executive_report (BUG-013 DRY)
- governance/routes/rules/crud.py — delete_rule (BUG-013 DRY)
- governance/routes/rules/crud.py — create_rule_dependency (BUG-013 DRY)
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Session GET — already fixed, regression test
# ---------------------------------------------------------------------------

_P_SESSION_SVC = "governance.routes.sessions.crud.session_service"


class TestSessionGet404Propagation:
    """get_session must return 404 (not 500) when session not found."""

    @pytest.mark.asyncio
    async def test_nonexistent_session_returns_404(self):
        with patch(_P_SESSION_SVC) as mock_svc:
            mock_svc.get_session.return_value = None
            from governance.routes.sessions.crud import get_session
            with pytest.raises(HTTPException) as exc_info:
                await get_session("NONEXISTENT-ID")
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_valid_session_returns_200(self):
        from governance.models import SessionResponse
        resp = SessionResponse(
            session_id="SESSION-VALID",
            start_time="2026-03-25T10:00:00",
            status="ACTIVE",
            tasks_completed=0,
        )
        with patch(_P_SESSION_SVC) as mock_svc:
            mock_svc.get_session.return_value = resp
            from governance.routes.sessions.crud import get_session
            result = await get_session("SESSION-VALID")
            assert result.session_id == "SESSION-VALID"


# ---------------------------------------------------------------------------
# Executive Report — session lookup 404 must not become 500
# ---------------------------------------------------------------------------

_P_REPORT_SESSIONS = "governance.routes.reports._sessions_store"
_P_REPORT_CLIENT = "governance.routes.reports.get_typedb_client"


class TestReportSession404Propagation:
    """get_session_executive_report must return 404 when session not found,
    not catch HTTPException(404) in the except Exception block."""

    @pytest.mark.asyncio
    async def test_nonexistent_session_returns_404_not_500(self):
        mock_client = MagicMock()
        mock_client.get_session.return_value = None
        with (
            patch(_P_REPORT_SESSIONS, {}),
            patch(_P_REPORT_CLIENT, return_value=mock_client),
        ):
            from governance.routes.reports import get_session_executive_report
            with pytest.raises(HTTPException) as exc_info:
                await get_session_executive_report("NONEXISTENT-ID")
            # BUG-013 DRY: must be 404, not 500
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_typedb_client_exception_returns_404(self):
        """When TypeDB raises a non-HTTP exception, 404 is acceptable (session not found)."""
        mock_client = MagicMock()
        mock_client.get_session.side_effect = ConnectionError("down")
        with (
            patch(_P_REPORT_SESSIONS, {}),
            patch(_P_REPORT_CLIENT, return_value=mock_client),
        ):
            from governance.routes.reports import get_session_executive_report
            with pytest.raises(HTTPException) as exc_info:
                await get_session_executive_report("NONEXISTENT-ID")
            # Connection errors during lookup → 404 is the existing behavior
            assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Rules delete — HTTPException from inside try must propagate
# ---------------------------------------------------------------------------

_P_RULE_SVC = "governance.routes.rules.crud.rule_service"


class TestRuleDelete404Propagation:
    """delete_rule raises HTTPException(500) when result is falsy.
    The catch-all must NOT swallow it into another 500 with different detail."""

    @pytest.mark.asyncio
    async def test_delete_rule_falsy_result_returns_500_not_caught(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.delete_rule.return_value = None  # falsy → HTTPException(500)
            from governance.routes.rules.crud import delete_rule
            with pytest.raises(HTTPException) as exc_info:
                await delete_rule("NONEXISTENT-RULE", archive=True)
            assert exc_info.value.status_code == 500
            assert "Failed to delete rule" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_rule_key_error_returns_404(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.delete_rule.side_effect = KeyError("not found")
            from governance.routes.rules.crud import delete_rule
            with pytest.raises(HTTPException) as exc_info:
                await delete_rule("NONEXISTENT-RULE", archive=True)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_success_returns_none(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.delete_rule.return_value = True
            from governance.routes.rules.crud import delete_rule
            result = await delete_rule("RULE-001", archive=True)
            assert result is None


# ---------------------------------------------------------------------------
# Rules create_dependency — HTTPException from inside try must propagate
# ---------------------------------------------------------------------------


class TestRuleCreateDependency404Propagation:
    """create_rule_dependency raises HTTPException(500) when result is falsy.
    The catch-all must NOT swallow it."""

    @pytest.mark.asyncio
    async def test_create_dep_falsy_result_returns_500_not_caught(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.create_rule_dependency.return_value = None  # falsy
            from governance.routes.rules.crud import create_rule_dependency
            with pytest.raises(HTTPException) as exc_info:
                await create_rule_dependency("RULE-A", "RULE-B")
            assert exc_info.value.status_code == 500
            assert "Failed to create dependency" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_dep_key_error_returns_404(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.create_rule_dependency.side_effect = KeyError("not found")
            from governance.routes.rules.crud import create_rule_dependency
            with pytest.raises(HTTPException) as exc_info:
                await create_rule_dependency("RULE-A", "RULE-B")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_dep_success(self):
        with patch(_P_RULE_SVC) as mock_svc:
            mock_svc.create_rule_dependency.return_value = True
            from governance.routes.rules.crud import create_rule_dependency
            result = await create_rule_dependency("RULE-A", "RULE-B")
            assert result["created"] is True
            assert result["dependent"] == "RULE-A"
            assert result["dependency"] == "RULE-B"
