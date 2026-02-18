"""
File Watcher Main Module.

Per GAP-SYNC-AUTO-001: Auto-sync coordinator.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Provides the main FileWatcher class and singleton accessor.

Created: 2026-01-21
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

try:
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore

from governance.file_watcher.handler import DocumentChangeHandler
from governance.file_watcher.queue import (
    FileEvent,
    FileEventQueue,
    FileEventType,
    SyncCategory,
)


logger = logging.getLogger(__name__)


# Sync callbacks by category
SyncCallback = Callable[[List[FileEvent]], None]


@dataclass
class WatcherStats:
    """Statistics for the file watcher."""
    started_at: Optional[float] = None
    events_processed: int = 0
    last_sync_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    syncs_by_category: Dict[str, int] = field(default_factory=dict)


class FileWatcher:
    """
    Main file watcher coordinator.

    Monitors directories for file changes and triggers sync operations.
    """

    def __init__(
        self,
        base_path: str,
        debounce_seconds: float = 2.0,
        poll_interval: float = 1.0,
    ):
        """
        Initialize file watcher.

        Args:
            base_path: Root directory to watch
            debounce_seconds: Wait time before syncing
            poll_interval: How often to check queue
        """
        self.base_path = Path(base_path)
        self.debounce_seconds = debounce_seconds
        self.poll_interval = poll_interval

        self.queue = FileEventQueue(debounce_seconds=debounce_seconds)
        self.handler: Optional[DocumentChangeHandler] = None
        self.observer: Optional[Observer] = None
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self.stats = WatcherStats()

        # Sync callbacks by category
        self._callbacks: Dict[SyncCategory, List[SyncCallback]] = {
            cat: [] for cat in SyncCategory
        }

    def register_callback(
        self,
        category: SyncCategory,
        callback: SyncCallback
    ) -> None:
        """Register sync callback for a category."""
        self._callbacks[category].append(callback)

    @property
    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running

    async def start(self) -> bool:
        """
        Start file watching.

        Returns:
            True if started successfully
        """
        if not WATCHDOG_AVAILABLE:
            logger.error("watchdog library not installed")
            return False

        if self._running:
            logger.warning("Watcher already running")
            return True

        try:
            # Get event loop for async queue operations
            loop = asyncio.get_running_loop()

            # Create handler and observer
            self.handler = DocumentChangeHandler(self.queue, loop)
            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.base_path),
                recursive=True
            )

            # Start observer thread
            self.observer.start()
            self._running = True
            self.stats.started_at = time.time()

            # Start worker task
            self._worker_task = asyncio.create_task(self._process_queue())

            logger.info(f"File watcher started for {self.base_path}")
            return True

        except Exception as e:
            # BUG-474-FWA-1: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"Failed to start file watcher: {type(e).__name__}", exc_info=True)
            self.stats.errors.append(str(e))
            return False

    async def stop(self) -> None:
        """Stop file watching."""
        self._running = False

        # Stop worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        # Stop observer
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None

        logger.info("File watcher stopped")

    async def _process_queue(self) -> None:
        """Background worker to process queued events."""
        while self._running:
            try:
                # Get batch of events
                batch = await self.queue.get_batch()

                if batch:
                    await self._dispatch_batch(batch)

                # Wait before next poll
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # BUG-474-FWA-2: Sanitize logger message + add exc_info for stack trace preservation
                logger.error(f"Error processing queue: {type(e).__name__}", exc_info=True)
                self.stats.errors.append(str(e))
                await asyncio.sleep(self.poll_interval)

    async def _dispatch_batch(self, events: List[FileEvent]) -> None:
        """Dispatch events to registered callbacks by category."""
        # Group events by category
        by_category: Dict[SyncCategory, List[FileEvent]] = {}
        for event in events:
            if event.category not in by_category:
                by_category[event.category] = []
            by_category[event.category].append(event)

        # Dispatch to callbacks
        for category, category_events in by_category.items():
            callbacks = self._callbacks.get(category, [])
            for callback in callbacks:
                try:
                    callback(category_events)
                    self.stats.events_processed += len(category_events)
                    cat_key = category.value
                    self.stats.syncs_by_category[cat_key] = (
                        self.stats.syncs_by_category.get(cat_key, 0) + 1
                    )
                except Exception as e:
                    # BUG-474-FWA-3: Sanitize logger message + add exc_info for stack trace preservation
                    logger.error(f"Callback error for {category}: {type(e).__name__}", exc_info=True)
                    self.stats.errors.append(f"{category}: {e}")

        self.stats.last_sync_time = time.time()

    def get_status(self) -> dict:
        """Get watcher status for API."""
        return {
            "running": self._running,
            "base_path": str(self.base_path),
            "queue": self.queue.get_stats(),
            "stats": {
                "started_at": self.stats.started_at,
                "events_processed": self.stats.events_processed,
                "last_sync_time": self.stats.last_sync_time,
                "syncs_by_category": self.stats.syncs_by_category,
                "errors_count": len(self.stats.errors),
                "recent_errors": self.stats.errors[-5:] if self.stats.errors else [],
            },
        }


# Singleton instance
_watcher_instance: Optional[FileWatcher] = None


def get_watcher(base_path: Optional[str] = None) -> Optional[FileWatcher]:
    """
    Get or create the global file watcher instance.

    Args:
        base_path: Root path to watch (required on first call)

    Returns:
        FileWatcher instance or None if not initialized
    """
    global _watcher_instance

    if _watcher_instance is None and base_path:
        _watcher_instance = FileWatcher(base_path)

    return _watcher_instance


def reset_watcher() -> None:
    """Reset the global watcher instance (for testing)."""
    global _watcher_instance
    _watcher_instance = None
