"""
RF-004: Robot Framework Library for File Watcher.

Wraps governance/file_watcher for Robot Framework tests.
Per GAP-SYNC-AUTO-001: Auto-sync file watching.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_async(coro):
    """Run async coroutine in event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class FileWatcherLibrary:
    """Robot Framework library for File Watcher testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._watcher = None
        self._queue = None

    # =========================================================================
    # File Event Categorization Tests
    # =========================================================================

    def categorize_rules_path(self, path: str) -> str:
        """Categorize a rules path."""
        from governance.file_watcher.queue import FileEvent
        return FileEvent.categorize(path).value

    def categorize_tasks_path(self, path: str) -> str:
        """Categorize a tasks path."""
        from governance.file_watcher.queue import FileEvent
        return FileEvent.categorize(path).value

    def categorize_evidence_path(self, path: str) -> str:
        """Categorize an evidence path."""
        from governance.file_watcher.queue import FileEvent
        return FileEvent.categorize(path).value

    def categorize_gaps_path(self, path: str) -> str:
        """Categorize a gaps path."""
        from governance.file_watcher.queue import FileEvent
        return FileEvent.categorize(path).value

    def categorize_other_path(self, path: str) -> str:
        """Categorize an unknown path."""
        from governance.file_watcher.queue import FileEvent
        return FileEvent.categorize(path).value

    # =========================================================================
    # FileEvent Tests
    # =========================================================================

    def create_file_event(self) -> Dict[str, Any]:
        """Create a FileEvent and return its fields."""
        from governance.file_watcher.queue import FileEvent, FileEventType

        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.MODIFIED,
        )
        return {
            "path": event.path,
            "event_type": event.event_type.value,
            "timestamp_positive": event.timestamp > 0
        }

    def create_event_with_category(self) -> str:
        """Create FileEvent with auto-categorization."""
        from governance.file_watcher.queue import FileEvent, FileEventType

        event = FileEvent(
            path="/docs/rules/RULE-001.md",
            event_type=FileEventType.CREATED,
            category=FileEvent.categorize("/docs/rules/RULE-001.md"),
        )
        return event.category.value

    # =========================================================================
    # FileEventQueue Tests
    # =========================================================================

    def queue_add_event(self) -> int:
        """Add event to queue and return size."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType

        async def _test():
            queue = FileEventQueue()
            event = FileEvent(
                path="/docs/rules/RULE-001.md",
                event_type=FileEventType.MODIFIED,
            )
            await queue.add_event(event)
            return await queue.size()

        return run_async(_test())

    def queue_deduplication(self) -> int:
        """Test queue deduplication returns single event."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType

        async def _test():
            queue = FileEventQueue()
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
            return await queue.size()

        return run_async(_test())

    def queue_debounce_returns_empty(self) -> int:
        """Test debounce returns empty during period."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType

        async def _test():
            queue = FileEventQueue(debounce_seconds=10.0)  # Long debounce
            event = FileEvent(
                path="/docs/rules/RULE-001.md",
                event_type=FileEventType.MODIFIED,
            )
            await queue.add_event(event)
            batch = await queue.get_batch()
            return len(batch)

        return run_async(_test())

    def queue_batch_after_debounce(self) -> Dict[str, Any]:
        """Test batch returns events after debounce."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType

        async def _test():
            queue = FileEventQueue(debounce_seconds=0.1)
            event = FileEvent(
                path="/docs/rules/RULE-001.md",
                event_type=FileEventType.MODIFIED,
            )
            await queue.add_event(event)
            await asyncio.sleep(0.15)
            batch = await queue.get_batch()
            return {
                "count": len(batch),
                "path": batch[0].path if batch else None
            }

        return run_async(_test())

    def queue_priority_ordering(self) -> List[str]:
        """Test batch priority ordering."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType, SyncCategory

        async def _test():
            queue = FileEventQueue(debounce_seconds=0.1)
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
            return [e.category.value for e in batch]

        return run_async(_test())

    def queue_clear(self) -> Dict[str, Any]:
        """Test queue clear."""
        from governance.file_watcher.queue import FileEventQueue, FileEvent, FileEventType

        async def _test():
            queue = FileEventQueue()
            await queue.add_event(FileEvent(
                path="/docs/rules/RULE-001.md",
                event_type=FileEventType.MODIFIED,
            ))
            count = await queue.clear()
            size_after = await queue.size()
            return {"cleared": count, "size_after": size_after}

        return run_async(_test())

    def queue_get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        from governance.file_watcher.queue import FileEventQueue

        queue = FileEventQueue(debounce_seconds=2.0)
        stats = queue.get_stats()
        return {
            "has_queue_size": "queue_size" in stats,
            "has_debounce_seconds": "debounce_seconds" in stats,
            "debounce_value": stats.get("debounce_seconds")
        }

    # =========================================================================
    # DocumentChangeHandler Tests
    # =========================================================================

    def handler_should_process_markdown(self, path: str) -> bool:
        """Test handler processes markdown files."""
        from governance.file_watcher.queue import FileEventQueue
        from governance.file_watcher.handler import DocumentChangeHandler

        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)
        return handler._should_process(path)

    def handler_should_ignore_path(self, path: str) -> bool:
        """Test handler ignores non-markdown, .git, .venv paths."""
        from governance.file_watcher.queue import FileEventQueue
        from governance.file_watcher.handler import DocumentChangeHandler

        queue = FileEventQueue()
        handler = DocumentChangeHandler(queue)
        return not handler._should_process(path)

    # =========================================================================
    # FileWatcher Tests
    # =========================================================================

    def watcher_creation(self) -> Dict[str, Any]:
        """Test FileWatcher creation."""
        from governance.file_watcher.watcher import FileWatcher, reset_watcher

        reset_watcher()
        watcher = FileWatcher("/tmp/test")
        return {
            "base_path": watcher.base_path.as_posix(),
            "is_running": watcher.is_running
        }

    def watcher_get_status(self) -> Dict[str, Any]:
        """Test watcher get_status when not running."""
        from governance.file_watcher.watcher import FileWatcher, reset_watcher

        reset_watcher()
        watcher = FileWatcher("/tmp/test")
        status = watcher.get_status()
        return {
            "running": status["running"],
            "has_queue": "queue" in status,
            "has_stats": "stats" in status
        }

    def watcher_register_callback(self) -> bool:
        """Test callback registration."""
        from governance.file_watcher.watcher import FileWatcher, reset_watcher
        from governance.file_watcher.queue import SyncCategory

        reset_watcher()
        watcher = FileWatcher("/tmp/test")
        callback = Mock()
        watcher.register_callback(SyncCategory.RULES, callback)
        return callback in watcher._callbacks[SyncCategory.RULES]

    def watcher_start_without_watchdog(self) -> Dict[str, Any]:
        """Test start fails gracefully without watchdog."""
        from governance.file_watcher.watcher import FileWatcher, reset_watcher

        async def _test():
            reset_watcher()
            watcher = FileWatcher("/tmp/test")
            with patch('governance.file_watcher.watcher.WATCHDOG_AVAILABLE', False):
                result = await watcher.start()
            return {
                "result": result,
                "is_running": watcher.is_running
            }

        return run_async(_test())
