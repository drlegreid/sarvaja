"""TDD tests for Phase 6: Slow-request alerting in access log middleware.

BDD Scenarios:
  - Fast request logged at INFO (no "slow" flag)
  - Slow request logged at WARNING with "slow":true
  - SLOW_REQUEST_MS env configurable
  - X-Request-ID generated and included as "rid" in log entry
  - X-Request-ID returned in response headers

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 6
"""
import json
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(path="/api/sessions", method="GET"):
    """Build a minimal Starlette-like Request mock."""
    req = MagicMock()
    req.method = method
    req.url.path = path
    req.url.query = ""
    req.headers = {}
    return req


def _make_response(status=200, content_length="100"):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = {"content-length": content_length}
    return resp


# ---------------------------------------------------------------------------
# Scenario: Fast request logged at INFO (no "slow" flag)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fast_request_logged_at_info():
    """Given SLOW_REQUEST_MS=1000, request takes ~0ms → INFO, no 'slow' key."""
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "1000"}, clear=False):
        # Re-import to pick up env
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()
        response = _make_response()

        async def instant_next(_req):
            return response

        with patch.object(mod.logger, "info") as mock_info, \
             patch.object(mod.logger, "warning") as mock_warn:
            await middleware.dispatch(request, instant_next)

            # Should log at INFO, not WARNING
            assert mock_info.called
            assert not mock_warn.called

            logged = json.loads(mock_info.call_args[0][0])
            assert "slow" not in logged


# ---------------------------------------------------------------------------
# Scenario: Slow request logged at WARNING with "slow":true
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_slow_request_logged_at_warning():
    """Given SLOW_REQUEST_MS=1000, request takes >1000ms → WARNING + slow:true."""
    import time
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "1000"}, clear=False):
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()
        response = _make_response()

        async def slow_next(_req):
            # Simulate slow by patching time.monotonic
            return response

        # Patch monotonic to simulate 1500ms duration
        original_monotonic = time.monotonic
        call_count = [0]

        def fake_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0.0  # start
            return 1.5  # end → 1500ms

        with patch.object(mod.time, "monotonic", side_effect=fake_monotonic), \
             patch.object(mod.logger, "info") as mock_info, \
             patch.object(mod.logger, "warning") as mock_warn:
            await middleware.dispatch(request, slow_next)

            # Should log at WARNING (not INFO) for 200 OK but slow
            assert mock_warn.called
            logged = json.loads(mock_warn.call_args[0][0])
            assert logged["slow"] is True
            assert logged["ms"] > 1000


# ---------------------------------------------------------------------------
# Scenario: SLOW_REQUEST_MS is env-configurable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_slow_threshold_env_configurable():
    """SLOW_REQUEST_MS=500 → 600ms request triggers WARNING."""
    import time
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "500"}, clear=False):
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()
        response = _make_response()

        call_count = [0]

        def fake_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0.0
            return 0.6  # 600ms

        async def next_fn(_req):
            return response

        with patch.object(mod.time, "monotonic", side_effect=fake_monotonic), \
             patch.object(mod.logger, "warning") as mock_warn:
            await middleware.dispatch(request, next_fn)
            assert mock_warn.called
            logged = json.loads(mock_warn.call_args[0][0])
            assert logged["slow"] is True


# ---------------------------------------------------------------------------
# Scenario: X-Request-ID generated and included as "rid" in log entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rid_in_log_entry():
    """Every access log entry includes 'rid' field."""
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "1000"}, clear=False):
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()
        response = _make_response()

        async def next_fn(_req):
            return response

        with patch.object(mod.logger, "info") as mock_info:
            await middleware.dispatch(request, next_fn)
            logged = json.loads(mock_info.call_args[0][0])
            assert "rid" in logged
            assert len(logged["rid"]) == 8  # uuid4[:8]


# ---------------------------------------------------------------------------
# Scenario: X-Request-ID returned in response headers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rid_in_response_header():
    """Response includes X-Request-ID header matching log rid."""
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "1000"}, clear=False):
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()

        # Use a real dict for response headers so middleware can set them
        resp_headers = {"content-length": "100"}
        response = MagicMock()
        response.status_code = 200
        response.headers = resp_headers

        async def next_fn(_req):
            return response

        with patch.object(mod.logger, "info") as mock_info:
            result = await middleware.dispatch(request, next_fn)
            logged = json.loads(mock_info.call_args[0][0])
            assert resp_headers.get("X-Request-ID") == logged["rid"]


# ---------------------------------------------------------------------------
# Scenario: Slow 200 still triggers WARNING (overrides status-based logic)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_slow_200_logged_at_warning_not_info():
    """A 200 OK that exceeds threshold → WARNING (slow trumps status)."""
    import time
    with patch.dict(os.environ, {"SLOW_REQUEST_MS": "1000"}, clear=False):
        import importlib
        import governance.middleware.access_log as mod
        importlib.reload(mod)

        middleware = mod.AccessLogMiddleware(app=MagicMock())
        request = _make_request()
        response = _make_response(status=200)

        call_count = [0]

        def fake_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0.0
            return 2.0  # 2000ms

        async def next_fn(_req):
            return response

        with patch.object(mod.time, "monotonic", side_effect=fake_monotonic), \
             patch.object(mod.logger, "info") as mock_info, \
             patch.object(mod.logger, "warning") as mock_warn:
            await middleware.dispatch(request, next_fn)
            assert mock_warn.called
            assert not mock_info.called


# ---------------------------------------------------------------------------
# Scenario: Skipped paths still skipped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_path_still_skipped():
    """Health endpoint should not generate access log entry or rid."""
    import importlib
    import governance.middleware.access_log as mod
    importlib.reload(mod)

    middleware = mod.AccessLogMiddleware(app=MagicMock())
    request = _make_request(path="/api/health")
    response = _make_response()

    async def next_fn(_req):
        return response

    with patch.object(mod.logger, "info") as mock_info, \
         patch.object(mod.logger, "warning") as mock_warn:
        await middleware.dispatch(request, next_fn)
        assert not mock_info.called
        assert not mock_warn.called
