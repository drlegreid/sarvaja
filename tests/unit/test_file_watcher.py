"""
Unit Tests for File Watcher Module.

Per GAP-SYNC-AUTO-001: Auto-sync file watching.
Tests the queue, handler, and watcher components.

Created: 2026-01-21
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from governance.file_watcher.queue import (
    FileEvent,
    FileEventType,
    FileEventQueue,
    SyncCategory,
)
from governance.file_watcher.handler import DocumentChangeHandler
from governance.file_watcher.watcher import FileWatcher, reset_watcher


class TestFileEventCategorization:
    """Tests for file event categorization."""

    def test_categorize_rules_path(self):
        """Rules path is categorized correctly."""
        assert FileEvent.categorize("/docs/rules/RULE-001.md") == SyncCategory.RULES
        assert FileEvent.categorize("/docs/rules/leaf/TEST-TDD-01-v1.md") == SyncCategory.RULES

    def test_categorize_tasks_path(self):
        """Tasks paths are categorized correctly."""
        assert FileEvent.categorize("/TODO.md") == SyncCategory.TASKS
        assert FileEvent.categorize("/docs/backlog/phases/PHASE-10.md") == SyncCategory.TASKS

    def test_categorize_evidence_path(self):
        """Evidence paths are categorized correctly."""
        assert FileEvent.categorize("/evidence/SESSION-2026-01-21.md") == SyncCategory.EVIDENCE

    def test_categorize_gaps_path(self):
        """Gaps paths are categorized correctly."""
        assert FileEvent.categorize("/docs/gaps/GAP-INDEX.md") == SyncCategory.GAPS
        assert FileEvent.categorize("/docs/gaps/evidence/GAP-001.md") == SyncCategory.GAPS

    def test_categorize_other_path(self):
        """Unknown paths are categorized as OTHER."""
        assert FileEvent.categorize("/README.md") == SyncCategory.OTHER
        assert FileEvent.categorize("/src/main.py") == SyncCategory.OTHER


class TestFileEvent:
    """Tests for FileEvent dataclass."""

    def test_event_creation(self):
        """FileEvent is created with correct fields."""
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )
        assert event.path == "/docs/rules/RULE-001.md"
        assert event.event_type == FileEventType.MODIFIED
        assert event.timestamp > 0

    def test_event_auto_categorization(self):
        """FileEvent can auto-categorize path."""
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.CREATED,
            category=FileEvent.categorize("/docs/rules/RULE-001.md"),
        )
        assert event.category == SyncCategory.RULES


class TestFileEventQueue:
    """Tests for FileEventQueue."""

    @pytest.mark.asyncio
    async def test_add_event(self):
        """Events can be added to queue."""
        queue = FileEventQueue()
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )

        await queue.add_event(event)
        assert await queue.size() == 1

    @pytest.mark.asyncio
    async def test_deduplication(self):
        """Later events for same path replace earlier ones."""
        queue = FileEventQueue()

        # Add two events for same path
        event1 = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.CREATED,
        )
        event2 = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )

        await queue.add_event(event1)
        await queue.add_event(event2)

        # Should only have one event
        assert await queue.size() == 1

    @pytest.mark.asyncio
    async def test_debounce_returns_empty(self):
        """get_batch returns empty during debounce period."""
        queue = FileEventQueue(debounce_seconds=10.0)  # Long debounce
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )

        await queue.add_event(event)
        batch = await queue.get_batch()

        # Should be empty - debounce not elapsed
        assert len(batch) == 0

    @pytest.mark.asyncio
    async def test_batch_after_debounce(self):
        """get_batch returns events after debounce elapsed."""
        queue = FileEventQueue(debounce_seconds=0.1)  # Short debounce
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )

        await queue.add_event(event)
        await asyncio.sleep(0.15)  # Wait for debounce

        batch = await queue.get_batch()
        assert len(batch) == 1
        assert batch[0].path == "/docs/rules/RULE-001.md"

    @pytest.mark.asyncio
    async def test_batch_priority_ordering(self):
        """Events are ordered by priority (rules > tasks > evidence)."""
        queue = FileEventQueue(debounce_seconds=0.1)

        # Add in reverse priority order
        await queue.add_event(FileEvent(
            path="/evidence/SESSION.md",
            event_type=FileEventType.MODIFIED,
            category=SyncCategory.EVIDENCE,
        ))
        await queue.add_event(FileEvent(
            path="/TODO.md",
            event_type=FileEventType.MODIFIED,
            category=SyncCategory.TASKS,
        ))
        await queue.add_event(FileEvent(
            path="/docs/rules/RULE.md",
            event_type=FileEventType.MODIFIED,
            category=SyncCategory.RULES,
        ))

        await asyncio.sleep(0.15)
        batch = await queue.get_batch()

        # Should be sorted: RULES, TASKS, EVIDENCE
        assert batch[0].category == SyncCategory.RULES
        assert batch[1].category == SyncCategory.TASKS
        assert batch[2].category == SyncCategory.EVIDENCE

    @pytest.mark.asyncio
    async def test_clear(self):
        """clear() removes all events."""
        queue = FileEventQueue()
        await queue.add_event(FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        ))

        count = await queue.clear()
        assert count == 1
        assert await queue.size() == 0

    def test_get_stats(self):
        """get_stats returns queue statistics."""
        queue = FileEventQueue(debounce_seconds=2.0)
        stats = queue.get_stats()

        assert "queue_size" in stats
        assert "debounce_seconds" in stats
        assert stats["debounce_seconds"] == 2.0


class TestDocumentChangeHandler:
    """Tests for DocumentChangeHandler."""

    def test_should_process_markdown(self):
        """Markdown files should be processed."""
        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)

        assert handler._should_process("/docs/rules/RULE-001.md")
        assert handler._should_process("/TODO.md")

    def test_should_ignore_non_markdown(self):
        """Non-markdown files should be ignored."""
        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)

        assert not handler._should_process("/src/main.py")
        assert not handler._should_process("/image.png")

    def test_should_ignore_git_directory(self):
        """Files in .git should be ignored."""
        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)

        assert not handler._should_process("/.git/config")
        assert not handler._should_process("/project/.git/HEAD")

    def test_should_ignore_venv(self):
        """Files in .venv should be ignored."""
        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)

        assert not handler._should_process("/.venv/lib/something.md")

    def test_should_process_yaml(self):
        """YAML files should be processed."""
        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)

        assert handler._should_process("/config.yaml")
        assert handler._should_process("/docker-compose.yml")


class TestFileWatcher:
    """Tests for FileWatcher."""

    def setup_method(self):
        """Reset watcher singleton before each test."""
        reset_watcher()

    def test_watcher_creation(self):
        """FileWatcher is created correctly."""
        watcher = FileWatcher("/tmp/test")
        assert watcher.base_path.as_posix() == "/tmp/test"
        assert not watcher.is_running

    def test_get_status_not_running(self):
        """get_status returns correct info when not running."""
        watcher = FileWatcher("/tmp/test")
        status = watcher.get_status()

        assert status["running"] is False
        assert "queue" in status
        assert "stats" in status

    def test_register_callback(self):
        """Callbacks can be registered by category."""
        watcher = FileWatcher("/tmp/test")
        callback = Mock()

        watcher.register_callback(SyncCategory.RULES, callback)

        assert callback in watcher._callbacks[SyncCategory.RULES]

    @pytest.mark.asyncio
    async def test_start_without_watchdog(self):
        """start() fails gracefully without watchdog."""
        watcher = FileWatcher("/tmp/test")

        # Mock watchdog as unavailable
        with patch('governance.file_watcher.watcher.WATCHDOG_AVAILABLE', False):
            result = await watcher.start()

        assert result is False
        assert not watcher.is_running


class TestFileWatcherIntegration:
    """Integration tests for file watcher (requires watchdog)."""

    def setup_method(self):
        """Reset watcher singleton before each test."""
        reset_watcher()

    @pytest.mark.asyncio
    async def test_full_sync_cycle(self):
        """Test full event to callback cycle."""
        # Create watcher with short debounce
        watcher = FileWatcher("/tmp", debounce_seconds=0.1)

        # Track callback invocations
        received_events = []

        def on_rules_change(events):
            received_events.extend(events)

        watcher.register_callback(SyncCategory.RULES, on_rules_change)

        # Manually add event to queue (simulating watchdog event)
        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
            category=SyncCategory.RULES,
        )
        await watcher.queue.add_event(event)

        # Wait for debounce
        await asyncio.sleep(0.15)

        # Manually dispatch (since observer not running)
        batch = await watcher.queue.get_batch()
        if batch:
            await watcher._dispatch_batch(batch)

        # Verify callback received event
        assert len(received_events) == 1
        assert received_events[0].path == "/docs/rules/RULE-001.md"
