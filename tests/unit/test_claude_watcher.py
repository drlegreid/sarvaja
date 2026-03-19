"""
Unit tests for the Claude Watcher daemon.

Per P2-10a: Event-driven JSONL file monitoring for CC session ingestion.
TDD — tests written before implementation.

Created: 2026-03-19
"""

import asyncio
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from tests.fixtures.cc_jsonl_factory import CCJsonlFactory


_M = "governance.services.claude_watcher"


# ---------------------------------------------------------------------------
# JsonlChangeHandler tests
# ---------------------------------------------------------------------------


class TestJsonlChangeHandler:
    """Tests for the JSONL-specific file change handler."""

    def test_accepts_jsonl_files(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        handler = JsonlChangeHandler(MagicMock())
        assert handler._should_process("/home/user/.claude/projects/foo/bar.jsonl")

    def test_rejects_non_jsonl_files(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        handler = JsonlChangeHandler(MagicMock())
        assert not handler._should_process("/home/user/.claude/projects/foo/bar.md")
        assert not handler._should_process("/home/user/.claude/projects/foo/bar.py")
        assert not handler._should_process("/home/user/.claude/projects/foo/bar.json")

    def test_rejects_dotfiles(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        handler = JsonlChangeHandler(MagicMock())
        assert not handler._should_process("/home/user/.claude/projects/.hidden.jsonl")

    def test_rejects_tmp_files(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        handler = JsonlChangeHandler(MagicMock())
        assert not handler._should_process("/home/user/.claude/projects/foo.jsonl.tmp")
        assert not handler._should_process("/home/user/.claude/projects/foo.jsonl.swp")

    def test_on_created_queues_event(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        callback = MagicMock()
        handler = JsonlChangeHandler(callback)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/home/user/.claude/projects/test-proj/session.jsonl"
        handler.on_created(event)
        callback.assert_called_once()
        call_args = callback.call_args
        assert call_args[0][0] == event.src_path
        assert call_args[0][1] == "created"

    def test_on_modified_queues_event(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        callback = MagicMock()
        handler = JsonlChangeHandler(callback)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/home/user/.claude/projects/test-proj/session.jsonl"
        handler.on_modified(event)
        callback.assert_called_once()
        assert callback.call_args[0][1] == "modified"

    def test_ignores_directory_events(self):
        from governance.services.claude_watcher import JsonlChangeHandler
        callback = MagicMock()
        handler = JsonlChangeHandler(callback)
        event = MagicMock()
        event.is_directory = True
        event.src_path = "/home/user/.claude/projects/test-proj/"
        handler.on_created(event)
        handler.on_modified(event)
        callback.assert_not_called()


# ---------------------------------------------------------------------------
# ClaudeWatcher tests
# ---------------------------------------------------------------------------


class TestClaudeWatcher:
    """Tests for the main ClaudeWatcher coordinator."""

    def test_creation_with_defaults(self):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher()
        assert not watcher.is_running
        assert watcher.debounce_seconds == 3.0
        assert watcher.watch_path is not None

    def test_creation_with_custom_path(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path), debounce_seconds=1.0)
        assert watcher.watch_path == tmp_path
        assert watcher.debounce_seconds == 1.0

    def test_not_running_initially(self):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher()
        assert not watcher.is_running

    def test_get_status_not_running(self):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher()
        status = watcher.get_status()
        assert status["running"] is False
        assert status["events_processed"] == 0
        assert status["sessions_ingested"] == 0

    @pytest.mark.asyncio
    async def test_start_creates_observer(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path))
        with patch(f"{_M}.WATCHDOG_AVAILABLE", True), \
             patch(f"{_M}.Observer") as mock_obs_cls:
            mock_obs = MagicMock()
            mock_obs_cls.return_value = mock_obs
            started = await watcher.start()
            assert started is True
            assert watcher.is_running
            mock_obs.schedule.assert_called_once()
            mock_obs.start.assert_called_once()
            await watcher.stop()

    @pytest.mark.asyncio
    async def test_start_fails_without_watchdog(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path))
        with patch(f"{_M}.WATCHDOG_AVAILABLE", False):
            started = await watcher.start()
            assert started is False
            assert not watcher.is_running

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path))
        with patch(f"{_M}.WATCHDOG_AVAILABLE", True), \
             patch(f"{_M}.Observer") as mock_obs_cls:
            mock_obs = MagicMock()
            mock_obs_cls.return_value = mock_obs
            await watcher.start()
            await watcher.stop()
            assert not watcher.is_running
            mock_obs.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_double_start_is_noop(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path))
        with patch(f"{_M}.WATCHDOG_AVAILABLE", True), \
             patch(f"{_M}.Observer") as mock_obs_cls:
            mock_obs = MagicMock()
            mock_obs_cls.return_value = mock_obs
            await watcher.start()
            first_obs = watcher._observer
            await watcher.start()  # Should be noop
            assert watcher._observer is first_obs
            await watcher.stop()


# ---------------------------------------------------------------------------
# Debounce + ingest pipeline tests
# ---------------------------------------------------------------------------


class TestClaudeWatcherDebounce:
    """Tests for debouncing and ingestion triggering."""

    @pytest.mark.asyncio
    async def test_event_triggers_ingestion(self, tmp_path):
        """A single JSONL file event should trigger ingestion after debounce."""
        from governance.services.claude_watcher import ClaudeWatcher

        watcher = ClaudeWatcher(
            watch_path=str(tmp_path),
            debounce_seconds=0.1,
        )

        # Create a test JSONL file
        factory = CCJsonlFactory()
        proj_dir = tmp_path / "-home-user-test-project"
        proj_dir.mkdir()
        jsonl_path = factory.write_session_file(proj_dir, turns=2)

        with patch(f"{_M}.ingest_single_session") as mock_ingest:
            mock_ingest.return_value = {"session_id": "SESSION-2026-03-19-CC-TEST"}

            # Simulate the file event callback
            watcher._on_jsonl_change(str(jsonl_path), "created")

            # Wait for debounce + processing
            await asyncio.sleep(0.3)
            await watcher._process_pending()

            assert mock_ingest.call_count >= 1
            assert watcher._stats["events_processed"] >= 1

    @pytest.mark.asyncio
    async def test_rapid_events_debounce_to_one(self, tmp_path):
        """Multiple rapid events for same file should collapse into one ingestion."""
        from governance.services.claude_watcher import ClaudeWatcher

        watcher = ClaudeWatcher(
            watch_path=str(tmp_path),
            debounce_seconds=0.2,
        )

        # Create the file so _ingest_file doesn't skip it
        proj_dir = tmp_path / "test-proj"
        proj_dir.mkdir()
        jsonl_file = proj_dir / "session.jsonl"
        jsonl_file.write_text('{"type":"user"}\n')
        path = str(jsonl_file)

        with patch(f"{_M}.ingest_single_session") as mock_ingest:
            mock_ingest.return_value = {"session_id": "S-1"}

            # Fire 5 rapid events for same file
            for _ in range(5):
                watcher._on_jsonl_change(path, "modified")
                await asyncio.sleep(0.01)

            # Wait for debounce
            await asyncio.sleep(0.4)
            await watcher._process_pending()

            # Should only trigger ingestion ONCE (debounced)
            assert mock_ingest.call_count == 1

    @pytest.mark.asyncio
    async def test_different_files_not_collapsed(self, tmp_path):
        """Events for different files should trigger separate ingestions."""
        from governance.services.claude_watcher import ClaudeWatcher

        watcher = ClaudeWatcher(
            watch_path=str(tmp_path),
            debounce_seconds=0.1,
        )

        # Create both files so _ingest_file doesn't skip them
        (tmp_path / "file1.jsonl").write_text('{"type":"user"}\n')
        (tmp_path / "file2.jsonl").write_text('{"type":"user"}\n')

        with patch(f"{_M}.ingest_single_session") as mock_ingest:
            mock_ingest.return_value = {"session_id": "S-1"}

            watcher._on_jsonl_change(str(tmp_path / "file1.jsonl"), "created")
            watcher._on_jsonl_change(str(tmp_path / "file2.jsonl"), "created")

            await asyncio.sleep(0.3)
            await watcher._process_pending()

            assert mock_ingest.call_count == 2

    @pytest.mark.asyncio
    async def test_ingestion_error_does_not_crash(self, tmp_path):
        """Ingestion errors should be captured, not crash the watcher."""
        from governance.services.claude_watcher import ClaudeWatcher

        watcher = ClaudeWatcher(
            watch_path=str(tmp_path),
            debounce_seconds=0.1,
        )

        # Create file so _ingest_file doesn't skip it
        (tmp_path / "fail.jsonl").write_text('{"type":"user"}\n')

        with patch(f"{_M}.ingest_single_session") as mock_ingest:
            mock_ingest.side_effect = RuntimeError("DB connection lost")

            watcher._on_jsonl_change(str(tmp_path / "fail.jsonl"), "created")
            await asyncio.sleep(0.3)
            await watcher._process_pending()

            assert watcher._stats["errors"] >= 1
            # Watcher should still be functional
            assert watcher._stats["events_processed"] >= 1


# ---------------------------------------------------------------------------
# ingest_single_session tests
# ---------------------------------------------------------------------------


class TestIngestSingleSession:
    """Tests for the single-session ingestion function."""

    @patch(f"{_M}.scan_jsonl_metadata")
    @patch(f"{_M}.build_session_id")
    def test_creates_session_from_jsonl(self, mock_build_id, mock_scan):
        from governance.services.claude_watcher import ingest_single_session

        mock_scan.return_value = {
            "slug": "test-session",
            "session_uuid": "abc-123",
            "first_ts": "2026-03-19T10:00:00Z",
            "last_ts": "2026-03-19T11:00:00Z",
            "user_count": 5,
            "assistant_count": 5,
            "tool_use_count": 3,
            "thinking_chars": 500,
            "models": ["claude-opus-4-6"],
            "file_path": "/tmp/test.jsonl",
            "file_size": 50000,
        }
        mock_build_id.return_value = "SESSION-2026-03-19-CC-TEST-SESSION"

        # Patch lazy imports at their source modules
        with patch("governance.services.sessions.get_session", return_value=None), \
             patch("governance.services.projects.get_project", return_value={"project_id": "PROJ-TEST"}), \
             patch("governance.services.sessions.create_session") as mock_create:
            mock_create.return_value = {"session_id": "SESSION-2026-03-19-CC-TEST-SESSION"}

            result = ingest_single_session(
                Path("/tmp/test.jsonl"),
                project_slug="test",
            )
            assert result is not None
            assert result["session_id"] == "SESSION-2026-03-19-CC-TEST-SESSION"
            mock_create.assert_called_once()

    @patch(f"{_M}.scan_jsonl_metadata")
    def test_returns_none_for_empty_file(self, mock_scan):
        from governance.services.claude_watcher import ingest_single_session

        mock_scan.return_value = None
        result = ingest_single_session(Path("/tmp/empty.jsonl"), "test")
        assert result is None

    @patch(f"{_M}.scan_jsonl_metadata")
    @patch(f"{_M}.build_session_id")
    def test_skips_already_ingested_session(self, mock_build_id, mock_scan):
        from governance.services.claude_watcher import ingest_single_session

        mock_scan.return_value = {
            "slug": "existing",
            "session_uuid": "abc",
            "first_ts": "2026-03-19T10:00:00Z",
            "last_ts": "2026-03-19T11:00:00Z",
            "user_count": 5,
            "assistant_count": 5,
            "tool_use_count": 3,
            "thinking_chars": 500,
            "models": [],
            "file_path": "/tmp/existing.jsonl",
            "file_size": 10000,
        }
        mock_build_id.return_value = "SESSION-2026-03-19-CC-EXISTING"

        with patch("governance.services.sessions.get_session") as mock_get_session:
            mock_get_session.return_value = {"session_id": "SESSION-2026-03-19-CC-EXISTING"}

            result = ingest_single_session(Path("/tmp/existing.jsonl"), "test")
            assert result is not None
            assert result["session_id"] == "SESSION-2026-03-19-CC-EXISTING"
            # Should return existing session, not create a new one


# ---------------------------------------------------------------------------
# Singleton + startup integration tests
# ---------------------------------------------------------------------------


class TestClaudeWatcherSingleton:
    def test_get_watcher_returns_same_instance(self):
        import governance.services.claude_watcher as mod
        mod._watcher_instance = None  # Reset

        from governance.services.claude_watcher import get_claude_watcher
        w1 = get_claude_watcher("/tmp/test1")
        w2 = get_claude_watcher("/tmp/test2")
        assert w1 is w2  # Singleton — first call wins
        mod._watcher_instance = None  # Cleanup

    def test_get_watcher_returns_none_without_path(self):
        import governance.services.claude_watcher as mod
        mod._watcher_instance = None

        from governance.services.claude_watcher import get_claude_watcher
        w = get_claude_watcher()
        assert w is None
        mod._watcher_instance = None


# ---------------------------------------------------------------------------
# Status + stats tests
# ---------------------------------------------------------------------------


class TestClaudeWatcherStats:
    def test_status_includes_all_fields(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(watch_path=str(tmp_path))
        status = watcher.get_status()
        assert "running" in status
        assert "watch_path" in status
        assert "debounce_seconds" in status
        assert "events_processed" in status
        assert "sessions_ingested" in status
        assert "errors" in status
        assert "pending_events" in status

    @pytest.mark.asyncio
    async def test_stats_accumulate(self, tmp_path):
        from governance.services.claude_watcher import ClaudeWatcher
        watcher = ClaudeWatcher(
            watch_path=str(tmp_path),
            debounce_seconds=0.05,
        )

        # Create files so _ingest_file doesn't skip them
        (tmp_path / "a.jsonl").write_text('{"type":"user"}\n')
        (tmp_path / "b.jsonl").write_text('{"type":"user"}\n')

        with patch(f"{_M}.ingest_single_session") as mock_ingest:
            mock_ingest.return_value = {"session_id": "S-1"}

            watcher._on_jsonl_change(str(tmp_path / "a.jsonl"), "created")
            await asyncio.sleep(0.2)
            await watcher._process_pending()

            watcher._on_jsonl_change(str(tmp_path / "b.jsonl"), "created")
            await asyncio.sleep(0.2)
            await watcher._process_pending()

            status = watcher.get_status()
            assert status["events_processed"] == 2
            assert status["sessions_ingested"] == 2


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------


class TestWatcherRoute:
    """Tests for the /api/ingestion/watcher endpoint."""

    def _get_client(self):
        from fastapi.testclient import TestClient
        from governance.routes.ingestion import router
        from fastapi import FastAPI

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api")
        return TestClient(test_app)

    @patch("governance.services.claude_watcher.get_claude_watcher")
    def test_watcher_status_when_running(self, mock_get):
        mock_w = MagicMock()
        mock_w.get_status.return_value = {
            "running": True,
            "watch_path": "/home/user/.claude/projects",
            "debounce_seconds": 3.0,
            "events_processed": 10,
            "sessions_ingested": 5,
            "errors": 1,
            "pending_events": 0,
            "started_at": 1742400000.0,
        }
        mock_get.return_value = mock_w

        client = self._get_client()
        resp = client.get("/api/ingestion/watcher")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is True
        assert data["events_processed"] == 10
        assert data["sessions_ingested"] == 5

    @patch("governance.services.claude_watcher.get_claude_watcher")
    def test_watcher_status_not_initialized(self, mock_get):
        mock_get.return_value = None

        client = self._get_client()
        resp = client.get("/api/ingestion/watcher")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is False
        assert "not initialized" in data.get("message", "").lower()


# ---------------------------------------------------------------------------
# api_startup integration tests
# ---------------------------------------------------------------------------


class TestApiStartupWatcherIntegration:
    """Verify api_startup.discover_cc_sessions() starts the watcher."""

    @pytest.mark.asyncio
    @patch("governance.services.claude_watcher.get_claude_watcher")
    @patch("governance.services.ingestion_scheduler.get_scheduler")
    async def test_startup_starts_watcher(self, mock_sched_get, mock_watcher_get):
        mock_sched = MagicMock()
        mock_sched_get.return_value = mock_sched

        mock_watcher = AsyncMock()
        mock_watcher.start = AsyncMock(return_value=True)
        mock_watcher_get.return_value = mock_watcher

        from governance.api_startup import discover_cc_sessions
        await discover_cc_sessions()

        mock_sched.start.assert_called_once()
        mock_watcher.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("governance.services.claude_watcher.get_claude_watcher")
    @patch("governance.services.ingestion_scheduler.get_scheduler")
    async def test_watcher_failure_does_not_block_startup(self, mock_sched_get, mock_watcher_get):
        mock_sched = MagicMock()
        mock_sched_get.return_value = mock_sched

        mock_watcher_get.side_effect = RuntimeError("watchdog not installed")

        from governance.api_startup import discover_cc_sessions
        # Should not raise
        await discover_cc_sessions()
        mock_sched.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_watcher_graceful(self):
        from governance.api_startup import stop_claude_watcher

        with patch("governance.services.claude_watcher.get_claude_watcher") as mock_get:
            mock_w = AsyncMock()
            mock_w.is_running = True
            mock_w.stop = AsyncMock()
            mock_get.return_value = mock_w

            await stop_claude_watcher()
            mock_w.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_watcher_noop_when_none(self):
        from governance.api_startup import stop_claude_watcher

        with patch("governance.services.claude_watcher.get_claude_watcher") as mock_get:
            mock_get.return_value = None
            # Should not raise
            await stop_claude_watcher()
