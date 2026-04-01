"""TDD Tests: Session detail data loaders.

Per DOC-SIZE-01-v1: Tests for extracted sessions_detail_loaders module.
Validates tool_calls, thinking_items, timeline, evidence, tasks loaders.
"""
from unittest.mock import MagicMock, patch

import pytest


_MOD = "agent.governance_ui.controllers.sessions_detail_loaders"


@pytest.fixture
def state():
    return MagicMock()


@pytest.fixture
def loaders(state):
    from agent.governance_ui.controllers.sessions_detail_loaders import (
        register_session_detail_loaders,
    )
    return register_session_detail_loaders(state, "http://test:8082")


class TestLoaderRegistration:
    """Loader factory returns all expected functions."""

    def test_returns_dict_with_all_keys(self, loaders):
        # P4: load_* (state-mutating) + fetch_* (pure HTTP) + build_timeline_data
        expected = {"load_tool_calls", "load_thinking_items", "build_timeline",
                    "load_evidence_rendered", "load_evidence", "load_tasks",
                    "load_transcript", "load_transcript_entry",
                    "load_validation",
                    "fetch_tool_calls", "fetch_thinking_items",
                    "fetch_evidence_rendered", "fetch_evidence",
                    "fetch_tasks", "fetch_transcript", "fetch_validation",
                    "build_timeline_data"}
        assert set(loaders.keys()) == expected

    def test_all_values_callable(self, loaders):
        for fn in loaders.values():
            assert callable(fn)


class TestLoadToolCalls:
    """Tool calls loader populates state correctly."""

    @patch(f"{_MOD}.httpx.Client")
    def test_loads_tool_calls_on_200(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tool_calls": [{"name": "Bash", "timestamp": "T1"}]
        }
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock(get=lambda *a, **k: mock_resp)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_tool_calls"]("S-1")
        calls = state.session_tool_calls
        assert len(calls) == 1
        assert calls[0]["tool_name"] == "Bash"

    def test_no_session_id_skips(self, state, loaders):
        loaders["load_tool_calls"](None)
        # Should not crash

    @patch(f"{_MOD}.httpx.Client")
    def test_exception_clears_state(self, mock_client_cls, state, loaders):
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_tool_calls"]("S-1")
        assert state.session_tool_calls == []


class TestLoadThinkingItems:
    """Thinking items loader populates state correctly."""

    @patch(f"{_MOD}.httpx.Client")
    def test_loads_thinking_on_200(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "thinking_blocks": [{"chars": 100, "thought_type": "reasoning"}]
        }
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock(get=lambda *a, **k: mock_resp)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_thinking_items"]("S-1")
        items = state.session_thinking_items
        assert len(items) == 1
        assert items[0]["char_count"] == 100


class TestBuildTimeline:
    """Timeline builder merges and sorts tool_calls + thoughts."""

    def test_empty_produces_empty(self, state, loaders):
        state.session_tool_calls = []
        state.session_thinking_items = []
        loaders["build_timeline"]()
        assert state.session_timeline == []

    def test_merges_and_sorts(self, state, loaders):
        state.session_tool_calls = [
            {"tool_name": "Read", "timestamp": "2026-02-15T10:00:03", "success": True, "duration_ms": 0}
        ]
        state.session_thinking_items = [
            {"thought_type": "plan", "timestamp": "2026-02-15T10:00:01", "thought": "x", "chars": 10}
        ]
        loaders["build_timeline"]()
        tl = state.session_timeline
        assert len(tl) == 2
        assert tl[0]["title"] == "plan"
        assert tl[1]["title"] == "Read"

    def test_tool_call_detail_truncated(self, state, loaders):
        state.session_tool_calls = [
            {"tool_name": "Bash", "timestamp": "T1", "result": "x" * 500, "success": True, "duration_ms": 0}
        ]
        state.session_thinking_items = []
        loaders["build_timeline"]()
        assert len(state.session_timeline[0]["detail"]) <= 200


class TestLoadEvidenceRendered:
    """Evidence rendered loader sets HTML state."""

    @patch(f"{_MOD}.httpx.Client")
    def test_loads_html_on_200(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"html": "<h1>Evidence</h1>"}
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock(get=lambda *a, **k: mock_resp)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_evidence_rendered"]("S-1")
        assert state.session_evidence_html == "<h1>Evidence</h1>"
        assert state.session_evidence_loading is False

    def test_no_session_id_skips(self, state, loaders):
        loaders["load_evidence_rendered"](None)
        # Should not crash


class TestLoadEvidence:
    """Evidence file list loader merges into selected_session."""

    @patch(f"{_MOD}.httpx.Client")
    def test_loads_evidence_files(self, mock_client_cls, state, loaders):
        state.selected_session = {"session_id": "S-1"}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"evidence_files": ["ev1.md", "ev2.md"]}
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock(get=lambda *a, **k: mock_resp)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_evidence"]("S-1")
        # selected_session should be updated with evidence_files
        updated = state.selected_session
        assert updated["evidence_files"] == ["ev1.md", "ev2.md"]


class TestLoadTasks:
    """Tasks loader populates session_tasks with loading state."""

    @patch(f"{_MOD}.httpx.Client")
    def test_loads_tasks_on_200(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tasks": [{"task_id": "T-1", "status": "DONE"}]}
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock(get=lambda *a, **k: mock_resp)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        loaders["load_tasks"]("S-1")
        assert state.session_tasks_loading is False
        tasks = state.session_tasks
        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "T-1"
