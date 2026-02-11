"""
Unit tests for File Event Queue.

Per DOC-SIZE-01-v1: Tests for extracted file_watcher/queue.py module.
Tests: FileEventType, SyncCategory, FileEvent, FileEventQueue.
"""

import asyncio
import time
import pytest

from governance.file_watcher.queue import (
    FileEventType,
    SyncCategory,
    FileEvent,
    FileEventQueue,
)


class TestFileEventType:
    """Tests for FileEventType enum."""

    def test_values(self):
        assert FileEventType.CREATED == "created"
        assert FileEventType.MODIFIED == "modified"
        assert FileEventType.DELETED == "deleted"
        assert FileEventType.MOVED == "moved"


class TestSyncCategory:
    """Tests for SyncCategory enum."""

    def test_values(self):
        assert SyncCategory.RULES == "rules"
        assert SyncCategory.TASKS == "tasks"
        assert SyncCategory.EVIDENCE == "evidence"
        assert SyncCategory.GAPS == "gaps"
        assert SyncCategory.OTHER == "other"


class TestFileEventCategorize:
    """Tests for FileEvent.categorize()."""

    def test_rules(self):
        assert FileEvent.categorize("/docs/rules/leaf/R-01.md") == SyncCategory.RULES

    def test_tasks_todo(self):
        assert FileEvent.categorize("/project/TODO.md") == SyncCategory.TASKS

    def test_tasks_backlog(self):
        assert FileEvent.categorize("/docs/backlog/items.md") == SyncCategory.TASKS

    def test_evidence(self):
        assert FileEvent.categorize("/evidence/SESSION-2026.md") == SyncCategory.EVIDENCE

    def test_gaps(self):
        assert FileEvent.categorize("/docs/gaps/GAP-001.md") == SyncCategory.GAPS

    def test_other(self):
        assert FileEvent.categorize("/src/main.py") == SyncCategory.OTHER

    def test_case_insensitive(self):
        assert FileEvent.categorize("/DOCS/RULES/LEAF/R-01.MD") == SyncCategory.RULES


class TestFileEvent:
    """Tests for FileEvent dataclass."""

    def test_basic(self):
        e = FileEvent(path="/a.md", event_type=FileEventType.CREATED)
        assert e.path == "/a.md"
        assert e.event_type == FileEventType.CREATED
        assert e.timestamp > 0
        assert e.category == SyncCategory.OTHER

    def test_with_category(self):
        e = FileEvent(
            path="/docs/rules/leaf/R-01.md",
            event_type=FileEventType.MODIFIED,
            category=SyncCategory.RULES,
        )
        assert e.category == SyncCategory.RULES


class TestFileEventQueue:
    """Tests for FileEventQueue."""

    @pytest.mark.asyncio
    async def test_add_event(self):
        q = FileEventQueue()
        e = FileEvent(path="/a.md", event_type=FileEventType.CREATED)
        await q.add_event(e)
        assert await q.size() == 1

    @pytest.mark.asyncio
    async def test_dedupes_by_path(self):
        q = FileEventQueue()
        e1 = FileEvent(path="/a.md", event_type=FileEventType.CREATED)
        e2 = FileEvent(path="/a.md", event_type=FileEventType.MODIFIED)
        await q.add_event(e1)
        await q.add_event(e2)
        assert await q.size() == 1

    @pytest.mark.asyncio
    async def test_get_batch_empty(self):
        q = FileEventQueue()
        batch = await q.get_batch()
        assert batch == []

    @pytest.mark.asyncio
    async def test_get_batch_before_debounce(self):
        q = FileEventQueue(debounce_seconds=10)
        e = FileEvent(path="/a.md", event_type=FileEventType.CREATED)
        await q.add_event(e)
        batch = await q.get_batch()
        assert batch == []  # debounce not elapsed

    @pytest.mark.asyncio
    async def test_get_batch_after_debounce(self):
        q = FileEventQueue(debounce_seconds=0)
        e = FileEvent(path="/a.md", event_type=FileEventType.CREATED)
        await q.add_event(e)
        q._last_event_time = time.time() - 1  # simulate time passing
        batch = await q.get_batch()
        assert len(batch) == 1
        assert await q.size() == 0  # cleared after get

    @pytest.mark.asyncio
    async def test_batch_sorted_by_priority(self):
        q = FileEventQueue(debounce_seconds=0)
        await q.add_event(FileEvent("/evidence/e.md", FileEventType.CREATED, category=SyncCategory.EVIDENCE))
        await q.add_event(FileEvent("/docs/rules/r.md", FileEventType.CREATED, category=SyncCategory.RULES))
        await q.add_event(FileEvent("/TODO.md", FileEventType.CREATED, category=SyncCategory.TASKS))
        q._last_event_time = time.time() - 1
        batch = await q.get_batch()
        assert batch[0].category == SyncCategory.RULES
        assert batch[1].category == SyncCategory.TASKS
        assert batch[2].category == SyncCategory.EVIDENCE

    @pytest.mark.asyncio
    async def test_clear(self):
        q = FileEventQueue()
        await q.add_event(FileEvent("/a.md", FileEventType.CREATED))
        await q.add_event(FileEvent("/b.md", FileEventType.CREATED))
        count = await q.clear()
        assert count == 2
        assert await q.size() == 0

    def test_get_stats(self):
        q = FileEventQueue()
        stats = q.get_stats()
        assert stats["queue_size"] == 0
        assert stats["debounce_seconds"] == 2.0
        assert "categories" in stats

    @pytest.mark.asyncio
    async def test_max_batch_size(self):
        q = FileEventQueue(debounce_seconds=0, max_batch_size=3)
        for i in range(5):
            await q.add_event(FileEvent(f"/file{i}.md", FileEventType.CREATED))
        q._last_event_time = time.time() - 1
        batch = await q.get_batch()
        assert len(batch) == 3
