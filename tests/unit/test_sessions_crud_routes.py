"""
Unit tests for Sessions CRUD Routes.

Per DOC-SIZE-01-v1: Tests for routes/sessions/crud.py module.
Tests: _ensure_response, list_sessions, create_session, get_session,
       update_session, delete_session, end_session.
"""

from unittest.mock import patch, MagicMock

import pytest

from governance.models import SessionResponse


_P_SVC = "governance.routes.sessions.crud.session_service"


def _make_response(**kwargs):
    defaults = {
        "session_id": "SESSION-2026-02-11-TEST",
        "start_time": "2026-02-11T10:00:00",
        "status": "ACTIVE",
        "tasks_completed": 0,
    }
    defaults.update(kwargs)
    return SessionResponse(**defaults)


class TestEnsureResponse:
    def test_session_response_passthrough(self):
        from governance.routes.sessions.crud import _ensure_response
        resp = _make_response()
        assert _ensure_response(resp) is resp

    def test_dict_conversion(self):
        from governance.routes.sessions.crud import _ensure_response
        d = {
            "session_id": "S-1",
            "start_time": "2026-02-11T10:00:00",
            "status": "ACTIVE",
            "tasks_completed": 0,
        }
        result = _ensure_response(d)
        assert isinstance(result, SessionResponse)
        assert result.session_id == "S-1"


class TestListSessions:
    @pytest.mark.asyncio
    async def test_success(self):
        svc_result = {
            "total": 1,
            "offset": 0,
            "limit": 50,
            "has_more": False,
            "items": [_make_response()],
        }
        with patch(_P_SVC) as mock_svc:
            mock_svc.list_sessions.return_value = svc_result
            from governance.routes.sessions.crud import list_sessions
            result = await list_sessions()
        assert result.pagination.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_typedb_unavailable(self):
        from fastapi import HTTPException
        from governance.stores import TypeDBUnavailable
        with patch(_P_SVC) as mock_svc:
            mock_svc.list_sessions.side_effect = TypeDBUnavailable("down")
            from governance.routes.sessions.crud import list_sessions
            with pytest.raises(HTTPException) as exc_info:
                await list_sessions()
            assert exc_info.value.status_code == 503


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_success(self):
        with patch(_P_SVC) as mock_svc:
            mock_svc.create_session.return_value = _make_response()
            from governance.routes.sessions.crud import create_session
            from governance.models import SessionCreate
            data = SessionCreate(session_id="S-1", description="Test")
            result = await create_session(data)
        assert result.session_id == "SESSION-2026-02-11-TEST"

    @pytest.mark.asyncio
    async def test_conflict(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.create_session.side_effect = ValueError("already exists")
            from governance.routes.sessions.crud import create_session
            from governance.models import SessionCreate
            data = SessionCreate(session_id="S-1", description="Test")
            with pytest.raises(HTTPException) as exc_info:
                await create_session(data)
            assert exc_info.value.status_code == 409


class TestGetSession:
    @pytest.mark.asyncio
    async def test_found(self):
        with patch(_P_SVC) as mock_svc:
            mock_svc.get_session.return_value = _make_response()
            from governance.routes.sessions.crud import get_session
            result = await get_session("S-1")
        assert result.session_id == "SESSION-2026-02-11-TEST"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.get_session.return_value = None
            from governance.routes.sessions.crud import get_session
            with pytest.raises(HTTPException) as exc_info:
                await get_session("NONEXISTENT")
            assert exc_info.value.status_code == 404


class TestUpdateSession:
    @pytest.mark.asyncio
    async def test_success(self):
        with patch(_P_SVC) as mock_svc:
            mock_svc.update_session.return_value = _make_response(status="COMPLETED")
            from governance.routes.sessions.crud import update_session
            from governance.models import SessionUpdate
            data = SessionUpdate(status="COMPLETED")
            result = await update_session("S-1", data)
        assert result.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.update_session.return_value = None
            from governance.routes.sessions.crud import update_session
            from governance.models import SessionUpdate
            data = SessionUpdate(status="COMPLETED")
            with pytest.raises(HTTPException) as exc_info:
                await update_session("S-1", data)
            assert exc_info.value.status_code == 404


class TestDeleteSession:
    @pytest.mark.asyncio
    async def test_success(self):
        with patch(_P_SVC) as mock_svc:
            mock_svc.delete_session.return_value = True
            from governance.routes.sessions.crud import delete_session
            result = await delete_session("S-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.delete_session.return_value = False
            from governance.routes.sessions.crud import delete_session
            with pytest.raises(HTTPException) as exc_info:
                await delete_session("NONEXISTENT")
            assert exc_info.value.status_code == 404


class TestEndSession:
    @pytest.mark.asyncio
    async def test_success(self):
        with patch(_P_SVC) as mock_svc:
            mock_svc.end_session.return_value = _make_response(status="COMPLETED")
            from governance.routes.sessions.crud import end_session
            result = await end_session("S-1")
        assert result.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.end_session.return_value = None
            from governance.routes.sessions.crud import end_session
            with pytest.raises(HTTPException) as exc_info:
                await end_session("NONEXISTENT")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_conflict(self):
        from fastapi import HTTPException
        with patch(_P_SVC) as mock_svc:
            mock_svc.end_session.side_effect = ValueError("already ended")
            from governance.routes.sessions.crud import end_session
            with pytest.raises(HTTPException) as exc_info:
                await end_session("S-1")
            assert exc_info.value.status_code == 409
