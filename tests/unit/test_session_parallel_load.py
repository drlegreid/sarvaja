"""
Unit tests for Phase 4: Parallel Session Loading.

EPIC-PERF-TELEM-V1 P4 — verifies:
1. 7 loaders execute in parallel via ThreadPoolExecutor
2. Error isolation — one failure doesn't block others
3. Timeline built AFTER tools + thoughts complete
4. Loaders return data dict (fetch_* API) without mutating state
"""

import time
import threading
from unittest.mock import MagicMock, patch

import pytest


_LOADERS_MOD = "agent.governance_ui.controllers.sessions_detail_loaders"
_SESSIONS_MOD = "agent.governance_ui.controllers.sessions"


# ── Helpers ──────────────────────────────────────────────────────


def _make_mock_responses():
    """Default 200 responses for all session detail endpoints."""
    return {
        "/tools": (200, {"tool_calls": [{"name": "Read", "tool_name": "Read",
                                          "timestamp": "2026-01-01T10:00:01"}]}),
        "/thoughts": (200, {"thinking_blocks": [{"thought_type": "reasoning",
                                                   "chars": 100,
                                                   "timestamp": "2026-01-01T10:00:00"}]}),
        "/evidence/rendered": (200, {"html": "<p>evidence</p>"}),
        "/evidence": (200, {"evidence_files": [{"name": "ev.json"}]}),
        "/tasks": (200, {"tasks": [{"task_id": "T-1"}]}),
        "/transcript": (200, {"entries": [{"role": "user"}], "page": 1,
                              "total": 1, "has_more": False}),
        "/validate": (200, {"valid": True, "checks": []}),
    }


def _build_mock_client(responses=None):
    """Build a mock httpx.Client context manager with URL-based routing."""
    defaults = _make_mock_responses()
    if responses:
        defaults.update(responses)

    def _mock_get(url, **kwargs):
        resp = MagicMock()
        # Match longest substring first to avoid prefix collisions
        for substr in sorted(defaults.keys(), key=len, reverse=True):
            if substr in url:
                code, data = defaults[substr]
                resp.status_code = code
                resp.json.return_value = data
                return resp
        resp.status_code = 404
        resp.json.return_value = {}
        return resp

    mock_client = MagicMock()
    mock_client.get.side_effect = _mock_get
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


def _register_loaders(state=None, responses=None):
    """Register loaders with mocked httpx. Returns (loaders, patcher).

    Caller must use the returned loaders INSIDE the patcher context.
    """
    if state is None:
        state = MagicMock()
        state.session_transcript_include_thinking = False
        state.session_transcript_include_user = True
        state.selected_session = {"session_id": "S-1"}

    mock_client = _build_mock_client(responses)
    patcher = patch(f"{_LOADERS_MOD}.httpx")
    mock_httpx = patcher.start()
    mock_httpx.Client.return_value = mock_client

    from agent.governance_ui.controllers.sessions_detail_loaders import (
        register_session_detail_loaders,
    )
    loaders = register_session_detail_loaders(state, "http://test:8082")
    return loaders, state, patcher


# ── Fetcher API tests (sessions_detail_loaders) ─────────────────


class TestLoadersFetchAPI:
    """Each loader must expose a fetch_* function that returns data dict
    WITHOUT mutating state."""

    def test_fetch_tool_calls_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_tool_calls"]("S-1")
            assert isinstance(result, dict)
            assert "session_tool_calls" in result
            assert len(result["session_tool_calls"]) > 0
        finally:
            patcher.stop()

    def test_fetch_thinking_items_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_thinking_items"]("S-1")
            assert isinstance(result, dict)
            assert "session_thinking_items" in result
            assert len(result["session_thinking_items"]) > 0
        finally:
            patcher.stop()

    def test_fetch_tasks_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_tasks"]("S-1")
            assert isinstance(result, dict)
            assert "session_tasks" in result
            assert len(result["session_tasks"]) > 0
        finally:
            patcher.stop()

    def test_fetch_evidence_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_evidence"]("S-1")
            assert isinstance(result, dict)
            assert "evidence_files" in result
        finally:
            patcher.stop()

    def test_fetch_evidence_rendered_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_evidence_rendered"]("S-1")
            assert isinstance(result, dict)
            assert "session_evidence_html" in result
            assert result["session_evidence_html"] == "<p>evidence</p>"
        finally:
            patcher.stop()

    def test_fetch_transcript_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_transcript"]("S-1")
            assert isinstance(result, dict)
            assert "session_transcript" in result
        finally:
            patcher.stop()

    def test_fetch_validation_returns_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            result = loaders["fetch_validation"]("S-1")
            assert isinstance(result, dict)
            assert "session_validation_data" in result
        finally:
            patcher.stop()

    def test_fetch_does_not_mutate_state(self):
        """fetch_* must NOT write to state."""
        writes = []

        class TrackingState:
            def __init__(self):
                self._data = {}
                self.session_transcript_include_thinking = False
                self.session_transcript_include_user = True
                self.selected_session = {"session_id": "S-1"}

            def __setattr__(self, name, value):
                if name.startswith("_") or name in (
                    "session_transcript_include_thinking",
                    "session_transcript_include_user",
                    "selected_session",
                ):
                    object.__setattr__(self, name, value)
                    return
                writes.append(name)
                object.__setattr__(self, name, value)

            def __getattr__(self, name):
                if name.startswith("_"):
                    raise AttributeError(name)
                return self._data.get(name)

        state = TrackingState()
        loaders, _, patcher = _register_loaders(state=state)
        try:
            writes.clear()
            for key, fn in loaders.items():
                if key.startswith("fetch_"):
                    fn("S-1")
            # P5: trace_* writes are allowed (traced HTTP emits trace bar events)
            non_trace = [w for w in writes if not w.startswith("trace_")]
            assert non_trace == [], f"fetch_* functions wrote to state: {non_trace}"
        finally:
            patcher.stop()


# ── BDD: build_timeline_data ────────────────────────────────────


class TestBuildTimelineData:
    """Timeline must be built from fetched data, not from state."""

    def test_build_timeline_from_data_returns_list(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            _build_timeline_from_data,
        )
        tool_calls = [{"name": "Read", "tool_name": "Read",
                       "timestamp": "2026-01-01T10:00:01"}]
        thinking = [{"thought_type": "reasoning", "chars": 50,
                     "timestamp": "2026-01-01T10:00:00"}]
        result = _build_timeline_from_data(tool_calls, thinking)
        assert isinstance(result, list)
        assert len(result) == 2
        # Thought (earlier timestamp) should come first
        assert result[0]["type"] == "thought"
        assert result[1]["type"] == "tool_call"

    def test_build_timeline_data_in_loaders_dict(self):
        loaders, _, patcher = _register_loaders()
        try:
            assert "build_timeline_data" in loaders
            result = loaders["build_timeline_data"]([], [])
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            patcher.stop()


# ── BDD: Parallel session loading (select_session) ──────────────


class TestSelectSessionParallel:
    """select_session must use ThreadPoolExecutor for 7 loaders."""

    @patch(f"{_SESSIONS_MOD}.ThreadPoolExecutor")
    @patch(f"{_SESSIONS_MOD}.httpx")
    def test_uses_thread_pool_executor(self, mock_httpx, mock_tpe_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "session_id": "S-1", "duration": "00:10:00", "source_type": "API",
        }
        mock_httpx.get.return_value = mock_resp

        mock_executor = MagicMock()
        mock_tpe_cls.return_value.__enter__ = MagicMock(return_value=mock_executor)
        mock_tpe_cls.return_value.__exit__ = MagicMock(return_value=False)
        future = MagicMock()
        future.result.return_value = {}
        mock_executor.submit.return_value = future

        state = MagicMock()
        state.sessions = [{"session_id": "S-1"}]
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec
        ctrl.trigger = _trigger

        with patch(f"{_SESSIONS_MOD}.register_sessions_pagination",
                   return_value=MagicMock()), \
             patch(f"{_SESSIONS_MOD}.register_session_detail_loaders") as mock_reg:
            mock_reg.return_value = {
                "fetch_evidence": MagicMock(return_value={}),
                "fetch_tasks": MagicMock(return_value={}),
                "fetch_tool_calls": MagicMock(return_value={}),
                "fetch_thinking_items": MagicMock(return_value={}),
                "fetch_evidence_rendered": MagicMock(return_value={}),
                "fetch_transcript": MagicMock(return_value={}),
                "fetch_validation": MagicMock(return_value={}),
                "build_timeline_data": MagicMock(return_value=[]),
                "load_tool_calls": MagicMock(),
                "load_thinking_items": MagicMock(),
                "build_timeline": MagicMock(),
                "load_evidence_rendered": MagicMock(),
                "load_evidence": MagicMock(),
                "load_tasks": MagicMock(),
                "load_transcript": MagicMock(),
                "load_transcript_entry": MagicMock(),
                "load_validation": MagicMock(),
            }
            from agent.governance_ui.controllers.sessions import (
                register_sessions_controllers,
            )
            register_sessions_controllers(state, ctrl, "http://test:8082")

        triggers["select_session"]("S-1")
        mock_tpe_cls.assert_called()
        assert mock_executor.submit.call_count >= 7


# ── BDD: Error isolation ────────────────────────────────────────


class TestSessionErrorIsolation:
    """One loader failure must not block others."""

    def test_tools_failure_doesnt_block_tasks(self):
        """If /tools 500s, tasks still populate."""
        responses = {"/tools": (500, {})}
        loaders, _, patcher = _register_loaders(responses=responses)
        try:
            # Tools should return empty (500 response)
            tools_result = loaders["fetch_tool_calls"]("S-1")
            assert "session_tool_calls" not in tools_result or \
                   tools_result.get("session_tool_calls") == []

            # Tasks should succeed independently
            tasks_result = loaders["fetch_tasks"]("S-1")
            assert "session_tasks" in tasks_result
            assert len(tasks_result["session_tasks"]) > 0
        finally:
            patcher.stop()


# ── BDD: Timeline order ─────────────────────────────────────────


class TestSessionTimelineOrder:
    """Timeline must be built AFTER tools + thoughts complete."""

    def test_timeline_uses_fetched_data(self):
        loaders, _, patcher = _register_loaders()
        try:
            tools_data = loaders["fetch_tool_calls"]("S-1")
            thoughts_data = loaders["fetch_thinking_items"]("S-1")

            timeline = loaders["build_timeline_data"](
                tools_data.get("session_tool_calls", []),
                thoughts_data.get("session_thinking_items", []),
            )
            assert isinstance(timeline, list)
            types = {e["type"] for e in timeline}
            assert "tool_call" in types
            assert "thought" in types
        finally:
            patcher.stop()


# ── BDD: Wall clock ─────────────────────────────────────────────


class TestSessionWallClock:
    """Parallel must be faster than serial."""

    def test_parallel_faster_than_serial(self):
        delay = 0.1

        def _slow_get(url, **kwargs):
            time.sleep(delay)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "tool_calls": [], "thinking_blocks": [],
                "html": "", "evidence_files": [],
                "tasks": [], "entries": [], "page": 1,
                "total": 0, "has_more": False, "valid": True,
                "checks": [], "session_id": "S-1",
                "description": "Test", "duration": "00:01:00",
                "source_type": "API",
            }
            return resp

        state = MagicMock()
        state.sessions = [{"session_id": "S-1"}]
        state.session_transcript_include_thinking = False
        state.session_transcript_include_user = True
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec
        ctrl.trigger = _trigger

        with patch(f"{_SESSIONS_MOD}.httpx") as mock_httpx, \
             patch(f"{_SESSIONS_MOD}.register_sessions_pagination",
                   return_value=MagicMock()), \
             patch(f"{_LOADERS_MOD}.httpx") as mock_ldr_httpx:
            mock_httpx.get.side_effect = _slow_get
            mock_client = MagicMock()
            mock_client.get.side_effect = _slow_get
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_ldr_httpx.Client.return_value = mock_client

            from agent.governance_ui.controllers.sessions import (
                register_sessions_controllers,
            )
            register_sessions_controllers(state, ctrl, "http://test:8082")

        start = time.monotonic()
        triggers["select_session"]("S-1")
        elapsed = time.monotonic() - start

        # Serial: 1 detail + 7 loaders = 8 * 0.1 = 0.8s
        # Parallel: ~0.3s (detail + pool of 7 in 4 workers)
        serial_sum = 8 * delay
        assert elapsed < serial_sum, (
            f"Parallel took {elapsed:.3f}s, serial would be {serial_sum:.3f}s"
        )
