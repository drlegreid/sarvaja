"""
Unit tests for Access Log Middleware.

Per DOC-SIZE-01-v1: Tests for governance/middleware/access_log.py.
Tests: AccessLogMiddleware — skip paths, status code logging, debug mode.
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from governance.middleware.access_log import AccessLogMiddleware, _SKIP_PATHS


def _make_request(method="GET", path="/api/sessions", query="", content_length=None):
    req = MagicMock()
    req.method = method
    req.url.path = path
    req.url.query = query
    req.headers = {}
    if content_length:
        req.headers["content-length"] = content_length
    return req


def _make_response(status_code=200, content_length="123"):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-length": content_length} if content_length else {}
    return resp


# ── _SKIP_PATHS ────────────────────────────────────────


class TestSkipPaths:
    def test_health_in_skip(self):
        assert "/api/health" in _SKIP_PATHS

    def test_docs_in_skip(self):
        assert "/api/docs" in _SKIP_PATHS

    def test_api_sessions_not_skipped(self):
        assert "/api/sessions" not in _SKIP_PATHS


# ── dispatch ───────────────────────────────────────────


class TestDispatch:
    @pytest.mark.asyncio
    async def test_skips_health_path(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request(path="/api/health")
        expected_response = _make_response()
        call_next = AsyncMock(return_value=expected_response)

        result = await middleware.dispatch(request, call_next)

        assert result is expected_response
        call_next.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_logs_normal_request(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request()
        call_next = AsyncMock(return_value=_make_response(200))

        with patch("governance.middleware.access_log.logger") as mock_logger:
            result = await middleware.dispatch(request, call_next)

            mock_logger.info.assert_called_once()
            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["method"] == "GET"
            assert logged["path"] == "/api/sessions"
            assert logged["status"] == 200

    @pytest.mark.asyncio
    async def test_logs_500_as_warning(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request()
        call_next = AsyncMock(return_value=_make_response(500))

        with patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_400_as_info(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request()
        call_next = AsyncMock(return_value=_make_response(404))

        with patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_bytes_in_log(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request()
        call_next = AsyncMock(return_value=_make_response(200, "456"))

        with patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["bytes"] == "456"

    @pytest.mark.asyncio
    async def test_missing_content_length(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request()
        call_next = AsyncMock(return_value=_make_response(200, None))

        with patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["bytes"] == "-"

    @pytest.mark.asyncio
    async def test_debug_mode_includes_query(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request(query="limit=10&offset=0")
        call_next = AsyncMock(return_value=_make_response(200))

        with patch("governance.middleware.access_log._DEBUG", True), \
             patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert "query" in logged
            assert "limit=10" in logged["query"]

    @pytest.mark.asyncio
    async def test_non_debug_excludes_query(self):
        app = MagicMock()
        middleware = AccessLogMiddleware(app)
        request = _make_request(query="limit=10")
        call_next = AsyncMock(return_value=_make_response(200))

        with patch("governance.middleware.access_log._DEBUG", False), \
             patch("governance.middleware.access_log.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert "query" not in logged
