"""Deep scan batch 106: Route handlers + heuristic checks.

Batch 106 findings: 26 total, 0 confirmed fixes, 26 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Route handler defense ──────────────


class TestRouteHandlerDefense:
    """Verify route handlers handle edge cases correctly."""

    def test_get_session_returns_dict(self):
        """get_session() returns dict, not SessionResponse — .get() is safe."""
        from governance.services.sessions import get_session
        import inspect

        sig = inspect.signature(get_session)
        # Return annotation confirms Dict, not SessionResponse
        ret = str(sig.return_annotation)
        assert "Dict" in ret or "dict" in ret

    def test_session_detail_404_on_none(self):
        """session_detail raises 404 when session not found."""
        from governance.routes.sessions.detail import session_detail
        from fastapi import HTTPException

        with patch("governance.routes.sessions.detail.get_session_detail", return_value=None):
            with pytest.raises(HTTPException) as exc:
                session_detail("NON-EXISTENT", zoom=1, page=1, per_page=20)
            assert exc.value.status_code == 404

    def test_session_tools_returns_structure(self):
        """session_tools returns expected dict structure."""
        from governance.routes.sessions.detail import session_tools

        mock_result = {
            "tool_calls": [{"name": "Read", "input": "file.py"}],
            "tool_calls_total": 1,
        }
        with patch("governance.routes.sessions.detail.get_session_detail", return_value=mock_result):
            result = session_tools("SESSION-TEST", page=1, per_page=20)
            assert result["session_id"] == "SESSION-TEST"
            assert result["total"] == 1
            assert len(result["tool_calls"]) == 1

    def test_session_thoughts_returns_structure(self):
        """session_thoughts returns expected dict structure."""
        from governance.routes.sessions.detail import session_thoughts

        mock_result = {
            "thinking_blocks": [{"content": "thinking..."}],
            "thinking_blocks_total": 1,
        }
        with patch("governance.routes.sessions.detail.get_session_detail", return_value=mock_result):
            result = session_thoughts("SESSION-TEST", page=1, per_page=20)
            assert result["session_id"] == "SESSION-TEST"
            assert result["total"] == 1

    def test_evidence_rendered_validates_path(self):
        """session_evidence_rendered rejects path traversal."""
        from governance.routes.sessions.detail import session_evidence_rendered
        from fastapi import HTTPException

        mock_session = {"file_path": "/etc/passwd"}
        with patch("governance.services.sessions.get_session", return_value=mock_session):
            with pytest.raises(HTTPException) as exc:
                session_evidence_rendered("SESSION-TEST")
            assert exc.value.status_code == 403

    def test_evidence_rendered_404_no_session(self):
        """session_evidence_rendered returns 404 for missing session."""
        from governance.routes.sessions.detail import session_evidence_rendered
        from fastapi import HTTPException

        with patch("governance.services.sessions.get_session", return_value=None):
            with pytest.raises(HTTPException) as exc:
                session_evidence_rendered("NON-EXISTENT")
            assert exc.value.status_code == 404


# ── Agent CRUD route defense ──────────────


class TestAgentCrudRouteDefense:
    """Verify agent CRUD routes handle errors."""

    def test_create_agent_409_on_duplicate(self):
        """create_agent raises 409 when agent exists."""
        from governance.routes.agents.crud import create_agent
        from governance.models import AgentCreate
        from fastapi import HTTPException
        import asyncio

        body = AgentCreate(
            agent_id="test-agent",
            name="Test Agent",
            agent_type="code",
        )
        with patch("governance.services.agents.create_agent", return_value=None):
            with pytest.raises(HTTPException) as exc:
                asyncio.get_event_loop().run_until_complete(create_agent(body))
            assert exc.value.status_code == 409

    def test_list_agents_catches_exceptions(self):
        """list_agents has try-except that returns 500."""
        from governance.routes.agents.crud import list_agents
        from fastapi import HTTPException
        import asyncio

        with patch("governance.services.agents.list_agents", side_effect=RuntimeError("DB down")):
            with pytest.raises(HTTPException) as exc:
                asyncio.get_event_loop().run_until_complete(
                    list_agents(offset=0, limit=50, sort_by="trust_score",
                                order="desc", agent_type=None, status=None)
                )
            assert exc.value.status_code == 500


# ── Heuristic exploratory check defense ──────────────


class TestHeuristicExploratoryDefense:
    """Verify exploratory heuristic checks handle edge cases."""

    def test_api_get_returns_list_on_error(self):
        """_api_get returns empty list when request fails."""
        from governance.routes.tests.heuristic_checks_exploratory import _api_get

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx:
            mock_httpx.get.side_effect = ConnectionError("refused")
            result = _api_get("http://localhost:8082", "/api/sessions")
            assert result == []

    def test_api_get_extracts_items(self):
        """_api_get unwraps paginated 'items' from dict response."""
        from governance.routes.tests.heuristic_checks_exploratory import _api_get

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [{"id": 1}, {"id": 2}], "total": 2}

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx:
            mock_httpx.get.return_value = mock_resp
            result = _api_get("http://localhost:8082", "/api/sessions")
            assert len(result) == 2

    def test_api_get_returns_list_response_directly(self):
        """_api_get returns list responses as-is."""
        from governance.routes.tests.heuristic_checks_exploratory import _api_get

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"id": 1}]

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx:
            mock_httpx.get.return_value = mock_resp
            result = _api_get("http://localhost:8082", "/api/sessions")
            assert result == [{"id": 1}]

    def test_is_self_referential_detects_localhost(self):
        """_is_self_referential detects localhost URLs."""
        from governance.routes.tests.heuristic_checks_exploratory import _is_self_referential

        assert _is_self_referential("http://localhost:8082") is True
        assert _is_self_referential("http://127.0.0.1:8082") is True
        assert _is_self_referential("http://remote-host:8082") is False

    def test_explr001_skips_self_referential(self):
        """H-EXPLR-001 returns SKIP for self-referential API."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )

        result = check_chat_session_count_accuracy("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_explr002_skips_self_referential(self):
        """H-EXPLR-002 returns SKIP for self-referential API."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_monitor_event_count_consistency,
        )

        result = check_monitor_event_count_consistency("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_explr001_result_has_required_keys(self):
        """H-EXPLR-001 always returns status, message, violations."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )

        # Self-referential path
        result = check_chat_session_count_accuracy("http://localhost:8082")
        assert "status" in result
        assert "message" in result
        assert "violations" in result

    def test_explr002_consistent_event_count(self):
        """H-EXPLR-002 passes when counter matches event count."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_monitor_event_count_consistency,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [{"id": 1}, {"id": 2}, {"id": 3}],
            "total": 3,
        }

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx:
            mock_httpx.get.return_value = mock_resp
            result = check_monitor_event_count_consistency("http://remote:9999")
            assert result["status"] == "PASS"


# ── Heuristic check result structure defense ──────────────


class TestHeuristicCheckResultStructure:
    """Verify all heuristic checks return well-formed results."""

    def test_session_check_result_keys(self):
        """Session checks return status, message, violations."""
        from governance.routes.tests.heuristic_checks_session import (
            check_session_evidence_files,
        )

        result = check_session_evidence_files("http://localhost:8082")
        assert "status" in result
        assert "violations" in result

    def test_cross_check_result_keys(self):
        """Cross checks return status, message, violations."""
        from governance.routes.tests.heuristic_checks_cross import (
            check_rule_document_paths,
        )

        result = check_rule_document_paths("http://localhost:8082")
        assert "status" in result
        assert "violations" in result

    def test_cc_check_result_keys(self):
        """CC checks return status, message, violations."""
        from governance.routes.tests.heuristic_checks_cc import (
            check_cc_session_uuid,
        )

        result = check_cc_session_uuid("http://localhost:8082")
        assert "status" in result
        assert "violations" in result
